# gestion_financiere/views.py
from django.views.generic import ListView, CreateView, UpdateView, View, TemplateView
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Sum, Q
import json
from django.http import JsonResponse


from .models import Don, Depense, CompteFinancier
from .forms import DonForm, DepenseForm
from sites_gestion.models import SiteOrphelinat


class DonListView(LoginRequiredMixin, ListView):
    model = Don
    template_name = 'gestion_financiere/don_list.html'
    context_object_name = 'dons'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user
        queryset = Don.objects.select_related('site').order_by('-date_don')
        if user.is_superuser:
            return queryset
        return queryset.filter(site=user.site)

class DonCreateView(LoginRequiredMixin, CreateView):
    model = Don
    form_class = DonForm
    template_name = 'gestion_financiere/don_form.html'
    success_url = reverse_lazy('gestion_financiere:don_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if not self.request.user.is_superuser:
            form.instance.site = self.request.user.site
        messages.success(self.request, "Le don a été enregistré avec succès.")
        return super().form_valid(form)
    

class DonUpdateView(LoginRequiredMixin, UpdateView):
    model = Don
    form_class = DonForm
    template_name = 'gestion_financiere/don_form.html'
    success_url = reverse_lazy('gestion_financiere:don_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Le don a été mis à jour avec succès.")
        return super().form_valid(form)

class DonDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        don = get_object_or_404(Don, pk=kwargs['pk'])
        if don.site == request.user.site or request.user.is_superuser:
            don.is_active = False
            don.save()
            messages.success(request, "L'enregistrement du don a été archivé.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('gestion_financiere:don_list')
    
# =======================================================================
# VUES CONCERNANT LE MODÈLE DEPENSE
# =======================================================================

class DepenseListView(LoginRequiredMixin, ListView):
    model = Depense
    template_name = 'gestion_financiere/depense_list.html'
    context_object_name = 'depenses'
    paginate_by = 15

    def get_queryset(self):
        user = self.request.user
        queryset = Depense.objects.filter(is_active=True).select_related('site').order_by('-date_depense')
        if user.is_superuser:
            return queryset
        return queryset.filter(site=user.site)

class DepenseCreateView(LoginRequiredMixin, CreateView):
    model = Depense
    form_class = DepenseForm
    template_name = 'gestion_financiere/depense_form.html'
    success_url = reverse_lazy('gestion_financiere:depense_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if not self.request.user.is_superuser:
            form.instance.site = self.request.user.site
        messages.success(self.request, "La dépense a été enregistrée avec succès.")
        return super().form_valid(form)

class DepenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Depense
    form_class = DepenseForm
    template_name = 'gestion_financiere/depense_form.html'
    success_url = reverse_lazy('gestion_financiere:depense_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "La dépense a été mise à jour avec succès.")
        return super().form_valid(form)

class DepenseDeleteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        depense = get_object_or_404(Depense, pk=kwargs['pk'])
        if depense.site == request.user.site or request.user.is_superuser:
            depense.is_active = False
            depense.save()
            messages.success(request, "L'enregistrement de la dépense a été archivé.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('gestion_financiere:depense_list')
    

class RapportFinancierView(LoginRequiredMixin, TemplateView):
    template_name = 'gestion_financiere/rapport_financier.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        comptes_queryset = CompteFinancier.objects.filter(is_active=True)
        selected_site = None

        # --- NOUVELLE LOGIQUE DE FILTRAGE ---
        if user.is_superuser:
            # On passe tous les sites au template pour le menu déroulant
            context['all_sites'] = SiteOrphelinat.objects.all()
            site_id = self.request.GET.get('site')
            if site_id:
                comptes_queryset = comptes_queryset.filter(site__id=site_id)
                selected_site = get_object_or_404(SiteOrphelinat, pk=site_id)
            context['selected_site'] = selected_site
        else:
            # Un utilisateur normal ne voit que les comptes de son site
            comptes_queryset = comptes_queryset.filter(site=user.site)
            selected_site = user.site
        # --- FIN DE LA LOGIQUE ---

        # Le reste du calcul se base sur le queryset déjà filtré
        comptes_data = []
        total_dons_general = 0
        total_depenses_general = 0
        solde_initial_general = 0

        for compte in comptes_queryset:
            dons = Don.objects.filter(compte=compte, is_active=True)
            depenses = Depense.objects.filter(compte=compte, is_active=True)
            
            total_dons = dons.aggregate(Sum('montant'))['montant__sum'] or 0
            total_depenses = depenses.aggregate(Sum('montant'))['montant__sum'] or 0
            solde_actuel = (compte.solde_initial + total_dons) - total_depenses
            
            comptes_data.append({
                'nom': compte.nom, 'solde_actuel': solde_actuel,
                'solde_initial': compte.solde_initial, 'total_dons': total_dons,
                'total_depenses': total_depenses,
            })
            total_dons_general += total_dons
            total_depenses_general += total_depenses
            solde_initial_general += compte.solde_initial
            
        solde_final_general = (solde_initial_general + total_dons_general) - total_depenses_general

        context['comptes_data'] = comptes_data
        context['total_dons_general'] = total_dons_general
        context['total_depenses_general'] = total_depenses_general
        context['solde_final_general'] = solde_final_general
        
        context['chart_labels'] = json.dumps(['Total des Dons', 'Total des Dépenses'])
        context['chart_data'] = json.dumps([float(total_dons_general), float(total_depenses_general)])

        return context
    
def get_comptes_for_site(request, site_id):
    # --- CORRECTION DE LA LOGIQUE DE SÉCURITÉ ---

    # Un super-administrateur a le droit de voir les comptes de n'importe quel site.
    # On ne fait donc aucune vérification pour lui.
    if not request.user.is_superuser:
        # Pour un utilisateur normal, on vérifie qu'il a bien un site
        # ET que le site demandé est bien le sien.
        if not request.user.site or request.user.site.id != site_id:
            return JsonResponse({'error': 'Action non autorisée'}, status=403)

    # Si la sécurité est passée, on exécute la requête.
    comptes = CompteFinancier.objects.filter(site__id=site_id, is_active=True).values('id', 'nom')
    return JsonResponse(list(comptes), safe=False)