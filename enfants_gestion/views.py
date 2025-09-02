# =======================================================================
# IMPORTS
# =======================================================================
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from urllib.parse import urlencode

from .models import Enfant, SuiviMedical, SuiviScolaire, Document
from .forms import (
    EnfantForm, DocumentFormSet, SuiviMedicalForm,
    SuiviScolaireForm, ExportFilterForm
)
from .resources import EnfantResource
from sites_gestion.models import SiteOrphelinat


# =======================================================================
# VUES CONCERNANT LE MODÈLE ENFANT
# =======================================================================

class EnfantListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Enfant
    template_name = 'enfants_gestion/enfant_list.html'
    context_object_name = 'enfant_list'
    permission_required = 'enfants_gestion.view_enfant'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        base_queryset = Enfant.objects.filter(is_active=True).select_related('site')
        site_id_from_url = self.request.GET.get('site')

        # 1. Déterminer la liste complète des sites auxquels l'utilisateur a droit
        allowed_sites = None
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        
        if user.is_superuser or is_global_role:
            allowed_sites = SiteOrphelinat.objects.all()
        else:
            allowed_sites = user.sites.all()

        # 2. Si un site spécifique est demandé dans l'URL (via le filtre)
        if site_id_from_url:
            # On vérifie d'abord si l'utilisateur a le droit de voir ce site
            if allowed_sites.filter(pk=site_id_from_url).exists():
                # Si oui, on filtre la liste des enfants par ce site unique
                return base_queryset.filter(site__id=site_id_from_url).order_by('nom', 'prenom')
            else:
                # Si l'utilisateur essaie d'accéder à un site non autorisé, on renvoie une liste vide
                return base_queryset.none()
        
        # 3. Si aucun site n'est sélectionné dans le filtre
        if user.is_superuser or is_global_role:
            return base_queryset.order_by('nom', 'prenom') # Un utilisateur global voit tout
        else:
            # Un utilisateur local voit tous les enfants de tous ses sites assignés
            return base_queryset.filter(site__in=allowed_sites).order_by('nom', 'prenom')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        is_multi_site_user = user.sites.count() > 1
        
        show_filter = user.is_superuser or is_global_role or is_multi_site_user
        context['show_site_filter'] = show_filter

        if show_filter:
            if user.is_superuser or is_global_role:
                context['sites_for_filter'] = SiteOrphelinat.objects.all()
            else:
                context['sites_for_filter'] = user.sites.all()
            
            context['selected_site_id'] = self.request.GET.get('site')
            
        return context
    

class EnfantDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Enfant
    template_name = 'enfants_gestion/enfant_detail.html'
    context_object_name = 'enfant'
    permission_required = 'enfants_gestion.view_enfant'

    def get_queryset(self):
        user = self.request.user
        queryset = Enfant.objects.prefetch_related('documents', 'suivis_medicaux', 'suivis_scolaires')
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset
        return queryset.filter(site__in=user.sites.all())

class EnfantCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Enfant
    form_class = EnfantForm
    template_name = 'enfants_gestion/enfant_form.html'
    permission_required = 'enfants_gestion.add_enfant'
    success_url = reverse_lazy('enfants_gestion:enfant_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['document_formset'] = DocumentFormSet(self.request.POST, self.request.FILES, prefix='document_set')
        else:
            context['document_formset'] = DocumentFormSet(prefix='document_set')
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        context = self.get_context_data()
        document_formset = context['document_formset']
        if document_formset.is_valid():
            with transaction.atomic():
                if not self.request.user.is_superuser and self.request.user.sites.count() == 1:
                    form.instance.site = self.request.user.sites.first()
                self.object = form.save()
                document_formset.instance = self.object
                document_formset.save()
            messages.success(self.request, f"Le dossier pour {self.object.prenom} a été créé avec succès.")
            return super().form_valid(form)
        return self.form_invalid(form)

    def form_invalid(self, form):
        document_formset = DocumentFormSet(self.request.POST, self.request.FILES, prefix='document_set')
        messages.error(self.request, "Le formulaire contient des erreurs. Veuillez corriger les champs indiqués.")
        return self.render_to_response(
            self.get_context_data(form=form, document_formset=document_formset)
        )

class EnfantUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Enfant
    form_class = EnfantForm
    template_name = 'enfants_gestion/enfant_form.html'
    permission_required = 'enfants_gestion.change_enfant'
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset
        return queryset.filter(site__in=user.sites.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['document_formset'] = DocumentFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='document_set')
        else:
            context['document_formset'] = DocumentFormSet(instance=self.object, prefix='document_set')
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def form_valid(self, form):
        context = self.get_context_data()
        document_formset = context['document_formset']
        if document_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                document_formset.save()
            messages.success(self.request, f"Le dossier de {self.object.prenom} a été mis à jour avec succès.")
            return super().form_valid(form)
        return self.form_invalid(form)
    
    def form_invalid(self, form):
        document_formset = DocumentFormSet(self.request.POST, self.request.FILES, instance=self.object, prefix='document_set')
        messages.error(self.request, "Le formulaire contient des erreurs. Veuillez corriger les champs indiqués.")
        return self.render_to_response(
            self.get_context_data(form=form, document_formset=document_formset)
        )

    def get_success_url(self):
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.object.pk})

class EnfantDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'enfants_gestion.delete_enfant'
    
    def post(self, request, *args, **kwargs):
        enfant = get_object_or_404(Enfant, pk=kwargs['pk'])
        can_delete = False
        user = request.user
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            can_delete = True
        elif enfant.site in user.sites.all():
            can_delete = True
        
        if can_delete:
            enfant.is_active = False
            enfant.save()
            messages.success(request, f"Le dossier de {enfant.prenom} a été archivé.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('enfants_gestion:enfant_list')

# =======================================================================
# VUES CONCERNANT LE MODÈLE SUIVI MEDICAL
# =======================================================================

class SuiviMedicalCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SuiviMedical
    form_class = SuiviMedicalForm
    template_name = 'enfants_gestion/related_item_form.html'
    permission_required = 'enfants_gestion.add_suivimedical'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enfant'] = get_object_or_404(Enfant, pk=self.kwargs['pk'])
        context['view_title'] = "Ajouter un Suivi Médical pour"
        context['icon_svg'] = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2 text-red-500"><path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" /></svg>"""
        return context

    def form_valid(self, form):
        form.instance.enfant = get_object_or_404(Enfant, pk=self.kwargs['pk'])
        messages.success(self.request, "La nouvelle entrée du suivi médical a été ajoutée.")
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.kwargs['pk']})

class SuiviMedicalUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SuiviMedical
    form_class = SuiviMedicalForm
    template_name = 'enfants_gestion/related_item_form.html'
    permission_required = 'enfants_gestion.change_suivimedical'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enfant'] = self.object.enfant
        context['view_title'] = "Modifier le Suivi Médical pour"
        context['icon_svg'] = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2 text-red-500"><path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" /></svg>"""
        return context

    def get_queryset(self):
        user = self.request.user
        queryset = SuiviMedical.objects.all()
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset
        return queryset.filter(enfant__site__in=user.sites.all())
        
    def get_success_url(self):
        messages.success(self.request, "Le suivi médical a été mis à jour.")
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.object.enfant.pk})
    
class SuiviMedicalDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'enfants_gestion.delete_suivimedical'

    def post(self, request, *args, **kwargs):
        suivi = get_object_or_404(SuiviMedical, pk=kwargs['pk'])
        can_delete = False
        user = request.user
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            can_delete = True
        elif suivi.enfant.site in user.sites.all():
            can_delete = True

        if can_delete:
            suivi.is_active = False
            suivi.save()
            messages.success(request, "L'entrée du suivi médical a été archivée.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('enfants_gestion:enfant_detail', pk=suivi.enfant.pk)

# =======================================================================
# VUES CONCERNANT LE MODÈLE SUIVI SCOLAIRE
# =======================================================================

class SuiviScolaireCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SuiviScolaire
    form_class = SuiviScolaireForm
    template_name = 'enfants_gestion/related_item_form.html'
    permission_required = 'enfants_gestion.add_suiviscolaire'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enfant'] = get_object_or_404(Enfant, pk=self.kwargs['pk'])
        context['view_title'] = "Ajouter un Suivi Scolaire pour"
        context['icon_svg'] = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2 text-sky-500"><path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.905 59.905 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0l-.07.003-.02.001-.044.002-.087.004-.176.008a51.994 51.994 0 00-2.299 1.25c-.12.08-.235.166-.346.257m15.482 0l.07.003.02.001.044.002.087.004.176.008a51.994 51.994 0 012.299 1.25c.12.08.235.166.346.257m0 0a48.627 48.627 0 01-10.399-5.84a50.57 50.57 0 01-2.658.813m15.482 0a50.57 50.57 0 002.658.813a59.905 59.905 0 00-10.399-5.84a59.905 59.905 0 00-10.399 5.84c.896-.248 1.783-.52 2.658-.814m15.482 0l-.07-.003-.02-.001-.044-.002-.087-.004-.176-.008a51.994 51.994 0 00-2.299-1.25c-.12-.08-.235-.166-.346-.257m-15.482 0l.07-.003.02-.001.044-.002.087-.004.176-.008a51.994 51.994 0 01-2.299-1.25c-.12-.08-.235-.166-.346-.257m0 0a48.627 48.627 0 0010.399 5.84a50.57 50.57 0 002.658-.813m-15.482 0a50.57 50.57 0 012.658-.813m12.823 0l-12.823 0" /></svg>"""
        return context

    def form_valid(self, form):
        form.instance.enfant = get_object_or_404(Enfant, pk=self.kwargs['pk'])
        messages.success(self.request, "La nouvelle entrée du suivi scolaire a été ajoutée.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.kwargs['pk']})

class SuiviScolaireUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SuiviScolaire
    form_class = SuiviScolaireForm
    template_name = 'enfants_gestion/related_item_form.html'
    permission_required = 'enfants_gestion.change_suiviscolaire'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enfant'] = self.object.enfant
        context['view_title'] = "Modifier le Suivi Scolaire pour"
        context['icon_svg'] = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2 text-sky-500"><path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.905 59.905 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0l-.07.003-.02.001-.044.002-.087.004-.176.008a51.994 51.994 0 00-2.299 1.25c-.12.08-.235.166-.346.257m15.482 0l.07.003.02.001.044.002.087.004.176.008a51.994 51.994 0 012.299 1.25c.12.08.235.166.346.257m0 0a48.627 48.627 0 01-10.399-5.84a50.57 50.57 0 01-2.658.813m15.482 0a50.57 50.57 0 002.658.813a59.905 59.905 0 00-10.399-5.84a59.905 59.905 0 00-10.399 5.84c.896-.248 1.783-.52 2.658-.814m15.482 0l-.07-.003-.02-.001-.044-.002-.087-.004-.176-.008a51.994 51.994 0 00-2.299-1.25c-.12-.08-.235-.166-.346-.257m-15.482 0l.07-.003.02-.001.044-.002.087-.004.176-.008a51.994 51.994 0 01-2.299-1.25c-.12-.08-.235-.166-.346-.257m0 0a48.627 48.627 0 0010.399 5.84a50.57 50.57 0 002.658-.813m-15.482 0a50.57 50.57 0 012.658-.813m12.823 0l-12.823 0" /></svg>"""
        return context

    def get_queryset(self):
        user = self.request.user
        queryset = SuiviScolaire.objects.all()
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset
        return queryset.filter(enfant__site__in=user.sites.all())

    def get_success_url(self):
        messages.success(self.request, "Le suivi scolaire a été mis à jour.")
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.object.enfant.pk})

class SuiviScolaireDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'enfants_gestion.delete_suiviscolaire'

    def post(self, request, *args, **kwargs):
        suivi = get_object_or_404(SuiviScolaire, pk=kwargs['pk'])
        can_delete = False
        user = request.user
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            can_delete = True
        elif suivi.enfant.site in user.sites.all():
            can_delete = True
        
        if can_delete:
            suivi.is_active = False
            suivi.save()
            messages.success(request, "L'entrée du suivi scolaire a été archivée.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('enfants_gestion:enfant_detail', pk=suivi.enfant.pk)

# =======================================================================
# VUES D'HISTORIQUE ET D'EXPORT
# =======================================================================

class EnfantHistoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Enfant.history.model
    template_name = 'enfants_gestion/enfant_history_detail.html'
    context_object_name = 'historical_enfant'
    permission_required = 'enfants_gestion.view_enfant'

    def get_queryset(self):
        user = self.request.user
        queryset = self.model.objects.select_related('history_user', 'site')
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset
        return queryset.filter(site__in=user.sites.all())

class EnfantHistoryListView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Enfant
    template_name = 'enfants_gestion/enfant_history_list.html'
    context_object_name = 'enfant'
    permission_required = 'enfants_gestion.view_enfant'

    def get_queryset(self):
        user = self.request.user
        queryset = Enfant.objects.prefetch_related('history__history_user')
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset
        return queryset.filter(site__in=user.sites.all())

# =======================================================================
# VUES POUR LES RAPPORTS ET EXPORTS
# =======================================================================

class ReportView(LoginRequiredMixin, PermissionRequiredMixin, View):
    form_class = ExportFilterForm
    template_name = 'enfants_gestion/export_page.html'
    permission_required = 'enfants_gestion.view_enfant'

    def get_queryset(self, user, filter_data):
        """
        Méthode centralisée pour filtrer le queryset des enfants.
        Utilisée à la fois pour l'aperçu et le téléchargement.
        """
        # 1. Définir le périmètre de base en fonction des permissions
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            queryset = Enfant.objects.all()
            # Un utilisateur global peut en plus filtrer par site
            site_id = filter_data.get('site')
            if site_id:
                queryset = queryset.filter(site__id=site_id)
        else:
            # Un utilisateur local ne voit que les données de ses sites
            queryset = Enfant.objects.filter(site__in=user.sites.all())
        
        # 2. Appliquer les filtres du formulaire
        statut = filter_data.get('statut')
        if statut == 'actifs':
            queryset = queryset.filter(is_active=True)
        elif statut == 'inactifs':
            queryset = queryset.filter(is_active=False)

        date_debut = filter_data.get('date_debut')
        if date_debut:
            queryset = queryset.filter(date_arrivee__gte=date_debut)

        date_fin = filter_data.get('date_fin')
        if date_fin:
            queryset = queryset.filter(date_arrivee__lte=date_fin)
            
        # 3. Optimiser la requête
        return queryset.select_related('site').order_by('nom')

    def get(self, request, *args, **kwargs):
        # Affiche le formulaire de filtres initial
        form = self.form_class(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        # Traite le formulaire soumis pour afficher l'aperçu
        form = self.form_class(request.POST, user=request.user)
        if form.is_valid():
            queryset = self.get_queryset(request.user, form.cleaned_data)
            
            # Prépare les paramètres pour les liens de téléchargement, en retirant les valeurs vides
            cleaned_params = {
                k: v.strftime('%Y-%m-%d') if isinstance(v, date) else v 
                for k, v in form.cleaned_data.items() if v
            }
            download_params = urlencode(cleaned_params)

            context = {
                'form': form,
                'enfants_list': queryset,
                'download_params': download_params,
            }
            return render(request, 'enfants_gestion/export_preview.html', context)
        
        return render(request, self.template_name, {'form': form})


class DownloadExportView(ReportView): # Hérite de ReportView pour réutiliser get_queryset
    def get(self, request, *args, **kwargs):
        # Récupère les filtres depuis les paramètres de l'URL (?statut=actifs&...)
        filter_data = {
            'site': request.GET.get('site') or None,
            'statut': request.GET.get('statut') or None,
            'date_debut': request.GET.get('date_debut') or None,
            'date_fin': request.GET.get('date_fin') or None,
        }
        
        queryset = self.get_queryset(request.user, filter_data)
        
        # Exporte les données en utilisant la ressource
        enfant_resource = EnfantResource()
        dataset = enfant_resource.export(queryset)
        
        # Génère et renvoie le fichier
        file_format = request.GET.get('format', 'xlsx')
        if file_format == 'xlsx':
            response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="export_enfants.xlsx"'
        else: 
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="export_enfants.csv"'
        
        return response