# =======================================================================
# IMPORTS
# =======================================================================
# --- Imports de Django ---
from urllib.parse import urlencode
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView
)

# --- Imports des applications locales ---
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

class EnfantListView(LoginRequiredMixin, ListView):
    model = Enfant
    template_name = 'enfants_gestion/enfant_list.html'
    context_object_name = 'enfant_list'

    def get_queryset(self):
        user = self.request.user
        queryset = Enfant.objects.filter(is_active=True).select_related('site')
        if user.is_superuser:
            site_id = self.request.GET.get('site')
            if site_id:
                queryset = queryset.filter(site__id=site_id)
            return queryset
        return queryset.filter(site=user.site)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_superuser:
            context['all_sites'] = SiteOrphelinat.objects.all()
            context['selected_site_id'] = self.request.GET.get('site')
        return context

class EnfantDetailView(LoginRequiredMixin, DetailView):
    model = Enfant
    template_name = 'enfants_gestion/enfant_detail.html'
    context_object_name = 'enfant'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Enfant.objects.all()
        return Enfant.objects.filter(site=user.site)

class EnfantCreateView(LoginRequiredMixin, CreateView):
    model = Enfant
    form_class = EnfantForm
    template_name = 'enfants_gestion/enfant_form.html'
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
                if not self.request.user.is_superuser:
                    form.instance.site = self.request.user.site
                self.object = form.save()
                document_formset.instance = self.object
                document_formset.save()
            
            messages.success(self.request, f"Le dossier pour {self.object.prenom} a été créé avec succès.")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        # On recrée le contexte du formset en cas d'erreur
        # pour s'assurer qu'il est bien présent
        document_formset = DocumentFormSet(self.request.POST, self.request.FILES, prefix='document_set')
        messages.error(self.request, "Le formulaire contient des erreurs. Veuillez corriger les champs indiqués.")
        return self.render_to_response(
            self.get_context_data(form=form, document_formset=document_formset)
        )
    

class EnfantUpdateView(LoginRequiredMixin, UpdateView):
    model = Enfant
    form_class = EnfantForm
    template_name = 'enfants_gestion/enfant_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'document_formset' not in context:
             context['document_formset'] = DocumentFormSet(instance=self.object, prefix='document_set')
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        document_formset = DocumentFormSet(request.POST, request.FILES, instance=self.object, prefix='document_set')
        if form.is_valid() and document_formset.is_valid():
            return self.form_valid(form, document_formset)
        return self.form_invalid(form, document_formset)

    def form_valid(self, form, document_formset):
        with transaction.atomic():
            self.object = form.save()
            document_formset.save()
        messages.success(self.request, f"Le dossier de {self.object.prenom} a été mis à jour avec succès.")
        return redirect(self.get_success_url())
    
    def form_invalid(self, form, document_formset):
        messages.error(self.request, "Le formulaire contient des erreurs. Veuillez corriger les champs indiqués.")
        return self.render_to_response(
            self.get_context_data(form=form, document_formset=document_formset)
        )

    def get_success_url(self):
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.object.pk})

class EnfantDeleteView(LoginRequiredMixin, View):
    """
    Cette vue gère le "soft delete" (archivage) d'un dossier enfant.
    Elle ne s'active que par une requête POST pour la sécurité.
    """
    def post(self, request, *args, **kwargs):
        # On récupère l'objet Enfant ou on renvoie une erreur 404
        enfant = get_object_or_404(Enfant, pk=kwargs['pk'])
        
        # Sécurité : On vérifie que l'utilisateur a le droit d'archiver ce dossier
        if enfant.site == request.user.site or request.user.is_superuser:
            # On ne supprime pas, on archive en mettant is_active à False
            enfant.is_active = False
            enfant.save()
            
            # On envoie un message de succès à l'utilisateur
            messages.success(request, f"Le dossier de {enfant.prenom} a été archivé avec succès.")
        else:
            # On envoie un message d'erreur si l'action n'est pas autorisée
            messages.error(request, "Action non autorisée.")
            
        # On redirige l'utilisateur vers la liste des enfants
        return redirect('enfants_gestion:enfant_list')

# =======================================================================
# VUES CONCERNANT LE MODÈLE SUIVI MEDICAL
# =======================================================================

class SuiviMedicalCreateView(LoginRequiredMixin, CreateView):
    model = SuiviMedical
    form_class = SuiviMedicalForm
    template_name = 'enfants_gestion/related_item_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # CORRIGÉ : Utiliser 'pk'
        context['enfant'] = get_object_or_404(Enfant, pk=self.kwargs['pk'])
        context['view_title'] = "Ajouter un Suivi Médical pour"
        context['icon_svg'] = """...""" # Votre SVG
        return context

    def form_valid(self, form):
        # CORRIGÉ : Utiliser 'pk'
        form.instance.enfant = get_object_or_404(Enfant, pk=self.kwargs['pk'])
        messages.success(self.request, "La nouvelle entrée du suivi médical a été ajoutée.")
        return super().form_valid(form)
    
    def get_success_url(self):
        # CORRIGÉ : Utiliser 'pk'
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.kwargs['pk']})



class SuiviMedicalUpdateView(LoginRequiredMixin, UpdateView):
    model = SuiviMedical
    form_class = SuiviMedicalForm
    template_name = 'enfants_gestion/related_item_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enfant'] = self.object.enfant
        context['view_title'] = "Modifier le Suivi Médical pour"
        context['icon_svg'] = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2 text-red-500"><path stroke-linecap="round" stroke-linejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" /></svg>"""
        return context

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SuiviMedical.objects.all()
        return SuiviMedical.objects.filter(enfant__site=user.site)
        
    def get_success_url(self):
        messages.success(self.request, "Le suivi médical a été mis à jour.")
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.object.enfant.pk})
    
class SuiviMedicalDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        suivi = get_object_or_404(SuiviMedical, pk=kwargs['pk'])
        if suivi.enfant.site == request.user.site or request.user.is_superuser:
            suivi.is_active = False
            suivi.save()
            messages.success(request, "L'entrée du suivi médical a été archivée.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('enfants_gestion:enfant_detail', pk=suivi.enfant.pk)

# =======================================================================
# VUES CONCERNANT LE MODÈLE SUIVI SCOLAIRE
# =======================================================================

class SuiviScolaireCreateView(LoginRequiredMixin, CreateView):
    model = SuiviScolaire
    form_class = SuiviScolaireForm
    template_name = 'enfants_gestion/related_item_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # CORRIGÉ : Utiliser 'pk'
        context['enfant'] = get_object_or_404(Enfant, pk=self.kwargs['pk'])
        context['view_title'] = "Ajouter un Suivi Scolaire pour"
        context['icon_svg'] = """...""" # Votre SVG
        return context

    def form_valid(self, form):
        # CORRIGÉ : Utiliser 'pk'
        form.instance.enfant = get_object_or_404(Enfant, pk=self.kwargs['pk'])
        messages.success(self.request, "La nouvelle entrée du suivi scolaire a été ajoutée.")
        return super().form_valid(form)

    def get_success_url(self):
        # CORRIGÉ : Utiliser 'pk'
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.kwargs['pk']})

class SuiviScolaireUpdateView(LoginRequiredMixin, UpdateView):
    model = SuiviScolaire
    form_class = SuiviScolaireForm
    template_name = 'enfants_gestion/related_item_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enfant'] = self.object.enfant
        context['view_title'] = "Modifier le Suivi Scolaire pour"
        context['icon_svg'] = """<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2 text-sky-500"><path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.905 59.905 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0l-.07.003-.02.001-.044.002-.087.004-.176.008a51.994 51.994 0 00-2.299 1.25c-.12.08-.235.166-.346.257m15.482 0l.07.003.02.001.044.002.087.004.176.008a51.994 51.994 0 012.299 1.25c.12.08.235.166.346.257m0 0a48.627 48.627 0 01-10.399-5.84a50.57 50.57 0 01-2.658.813m15.482 0a50.57 50.57 0 002.658.813a59.905 59.905 0 00-10.399-5.84a59.905 59.905 0 00-10.399 5.84c.896-.248 1.783-.52 2.658-.814m15.482 0l-.07-.003-.02-.001-.044-.002-.087-.004-.176-.008a51.994 51.994 0 00-2.299-1.25c-.12-.08-.235-.166-.346-.257m-15.482 0l.07-.003.02-.001.044-.002.087-.004.176-.008a51.994 51.994 0 01-2.299-1.25c-.12-.08-.235-.166-.346-.257m0 0a48.627 48.627 0 0010.399 5.84a50.57 50.57 0 002.658-.813m-15.482 0a50.57 50.57 0 012.658-.813m12.823 0l-12.823 0" /></svg>"""
        return context

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SuiviScolaire.objects.all()
        return SuiviScolaire.objects.filter(enfant__site=user.site)

    def get_success_url(self):
        messages.success(self.request, "Le suivi scolaire a été mis à jour.")
        return reverse_lazy('enfants_gestion:enfant_detail', kwargs={'pk': self.object.enfant.pk})

class SuiviScolaireDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        suivi = get_object_or_404(SuiviScolaire, pk=kwargs['pk'])
        if suivi.enfant.site == request.user.site or request.user.is_superuser:
            suivi.is_active = False
            suivi.save()
            messages.success(request, "L'entrée du suivi scolaire a été archivée.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('enfants_gestion:enfant_detail', pk=suivi.enfant.pk)

# =======================================================================
# VUES D'HISTORIQUE ET D'EXPORT
# =======================================================================

class EnfantHistoryDetailView(LoginRequiredMixin, DetailView):
    model = Enfant.history.model
    template_name = 'enfants_gestion/enfant_history_detail.html'
    context_object_name = 'historical_enfant'

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return self.model.objects.all()
        return self.model.objects.filter(instance__site=user.site)

# CETTE VUE REMPLACE L'ANCIENNE EXPORTVIEW
class ReportView(LoginRequiredMixin, View):
    form_class = ExportFilterForm
    template_name = 'enfants_gestion/export_page.html'

    def get_queryset(self, user, filter_data):
        if user.is_superuser:
            base_queryset = Enfant.objects.all()
            site_id = filter_data.get('site')
            if site_id:
                base_queryset = base_queryset.filter(site__id=site_id)
        else:
            base_queryset = Enfant.objects.filter(site=user.site)
        
        statut = filter_data.get('statut')
        if statut == 'actifs':
            base_queryset = base_queryset.filter(is_active=True)
        elif statut == 'inactifs':
            base_queryset = base_queryset.filter(is_active=False)

        date_debut = filter_data.get('date_debut')
        if date_debut:
            base_queryset = base_queryset.filter(date_arrivee__gte=date_debut)

        date_fin = filter_data.get('date_fin')
        if date_fin:
            base_queryset = base_queryset.filter(date_arrivee__lte=date_fin)
            
        return base_queryset

    def get(self, request, *args, **kwargs):
        form = self.form_class(user=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, user=request.user)
        if form.is_valid():
            queryset = self.get_queryset(request.user, form.cleaned_data)
            
            # CORRECTION : On nettoie les paramètres en retirant les valeurs vides
            # pour ne pas générer de "...=None" dans l'URL.
            cleaned_params = {k: v for k, v in form.cleaned_data.items() if v}
            download_params = urlencode(cleaned_params)

            context = {
                'form': form,
                'enfants_list': queryset,
                'download_params': download_params,
            }
            return render(request, 'enfants_gestion/export_preview.html', context)
            
        return render(request, self.template_name, {'form': form})
    

class EnfantHistoryListView(LoginRequiredMixin, DetailView):
    """
    Vue dédiée à l'affichage de l'historique complet d'un enfant.
    """
    model = Enfant
    template_name = 'enfants_gestion/enfant_history_list.html'
    context_object_name = 'enfant'

    def get_queryset(self):
        # On réutilise la même logique de sécurité
        user = self.request.user
        if user.is_superuser:
            return Enfant.objects.all()
        return Enfant.objects.filter(site=user.site)
    

# VUE SUPPLÉMENTAIRE POUR LE TÉLÉCHARGEMENT
class DownloadExportView(ReportView):
    def get(self, request, *args, **kwargs):
        filter_data = {
            'site': request.GET.get('site'),
            'statut': request.GET.get('statut'),
            'date_debut': request.GET.get('date_debut'),
            'date_fin': request.GET.get('date_fin'),
        }

        # --- CORRECTION CI-DESSOUS ---
        # On nettoie les dates spécifiquement. Si date_fin est la chaîne "None" ou une chaîne vide,
        # on la remplace par la vraie valeur Python None.
        if filter_data['date_debut'] in ('', 'None'):
            filter_data['date_debut'] = None
            
        if filter_data['date_fin'] in ('', 'None'):
            filter_data['date_fin'] = None
        # --- FIN DE LA CORRECTION ---

        queryset = self.get_queryset(request.user, filter_data)
        
        enfant_resource = EnfantResource()
        dataset = enfant_resource.export(queryset)
        
        file_format = request.GET.get('format', 'xlsx')
        if file_format == 'xlsx':
            response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="export_enfants.xlsx"'
        else:
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="export_enfants.csv"'
        
        return response