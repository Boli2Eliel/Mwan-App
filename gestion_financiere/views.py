# =======================================================================
# IMPORTS
# =======================================================================
import json
from urllib.parse import urlencode
from datetime import date

# --- Imports de Django ---
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView

# --- Imports des applications locales ---
from .models import CompteFinancier, Don, Depense
from .forms import DonForm, DepenseForm, FinanceExportForm
from .resources import DonResource, DepenseResource
from sites_gestion.models import SiteOrphelinat
from enfants_gestion.models import Enfant


# =======================================================================
# VUES CONCERNANT LE MODÈLE DON
# =======================================================================

class DonListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Don
    template_name = 'gestion_financiere/don_list.html'
    context_object_name = 'dons'
    permission_required = 'gestion_financiere.view_don'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        # Optimisation : pre-charge les données du site et du compte
        queryset = Don.objects.filter(is_active=True).select_related('site', 'compte').order_by('-date_don')
        
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            return queryset
        
        return queryset.filter(site__in=user.sites.all())

class DonCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Don
    form_class = DonForm
    template_name = 'gestion_financiere/don_form.html'
    permission_required = 'gestion_financiere.add_don'
    success_url = reverse_lazy('gestion_financiere:don_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if not self.request.user.is_superuser:
            # Pour un utilisateur avec un seul site, on l'assigne automatiquement
            if self.request.user.sites.count() == 1:
                form.instance.site = self.request.user.sites.first()
        messages.success(self.request, "Le don a été enregistré avec succès.")
        return super().form_valid(form)

class DonUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Don
    form_class = DonForm
    template_name = 'gestion_financiere/don_form.html'
    permission_required = 'gestion_financiere.change_don'
    success_url = reverse_lazy('gestion_financiere:don_list')

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            return queryset
        return queryset.filter(site__in=user.sites.all())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Le don a été mis à jour avec succès.")
        return super().form_valid(form)

class DonDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'gestion_financiere.delete_don'

    def post(self, request, *args, **kwargs):
        don = get_object_or_404(Don, pk=kwargs['pk'])
        can_delete = False
        user = request.user
        is_global_finance = (user.is_superuser or user.is_comptable_central)

        if is_global_finance:
            can_delete = True
        elif don.site in user.sites.all():
            can_delete = True

        if can_delete:
            don.is_active = False
            don.save()
            messages.success(request, "L'enregistrement du don a été archivé.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('gestion_financiere:don_list')

# =======================================================================
# VUES CONCERNANT LE MODÈLE DEPENSE
# =======================================================================

class DepenseListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Depense
    template_name = 'gestion_financiere/depense_list.html'
    context_object_name = 'depenses'
    permission_required = 'gestion_financiere.view_depense'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        queryset = Depense.objects.filter(is_active=True).select_related('site', 'compte').order_by('-date_depense')
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            return queryset
        return queryset.filter(site__in=user.sites.all())

class DepenseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Depense
    form_class = DepenseForm
    template_name = 'gestion_financiere/depense_form.html'
    permission_required = 'gestion_financiere.add_depense'
    success_url = reverse_lazy('gestion_financiere:depense_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        if not self.request.user.is_superuser:
            if self.request.user.sites.count() == 1:
                form.instance.site = self.request.user.sites.first()
        messages.success(self.request, "La dépense a été enregistrée avec succès.")
        return super().form_valid(form)

class DepenseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Depense
    form_class = DepenseForm
    template_name = 'gestion_financiere/depense_form.html'
    permission_required = 'gestion_financiere.change_depense'
    success_url = reverse_lazy('gestion_financiere:depense_list')

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            return queryset
        return queryset.filter(site__in=user.sites.all())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "La dépense a été mise à jour avec succès.")
        return super().form_valid(form)

class DepenseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'gestion_financiere.delete_depense'

    def post(self, request, *args, **kwargs):
        depense = get_object_or_404(Depense, pk=kwargs['pk'])
        can_delete = False
        user = request.user
        is_global_finance = (user.is_superuser or user.is_comptable_central)

        if is_global_finance:
            can_delete = True
        elif depense.site in user.sites.all():
            can_delete = True

        if can_delete:
            depense.is_active = False
            depense.save()
            messages.success(request, "L'enregistrement de la dépense a été archivé.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('gestion_financiere:depense_list')

# =======================================================================
# VUES DES RAPPORTS ET API
# =======================================================================

class RapportFinancierView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'gestion_financiere/rapport_financier.html'
    permission_required = 'gestion_financiere.view_don'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        comptes_queryset = CompteFinancier.objects.filter(is_active=True)
        selected_site = None
        is_global_finance = (user.is_superuser or user.is_comptable_central)

        if is_global_finance:
            context['all_sites'] = SiteOrphelinat.objects.all()
            site_id = self.request.GET.get('site')
            if site_id:
                comptes_queryset = comptes_queryset.filter(site__id=site_id)
                selected_site = get_object_or_404(SiteOrphelinat, pk=site_id)
            context['selected_site'] = selected_site
        else:
            comptes_queryset = comptes_queryset.filter(site__in=user.sites.all())
        
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
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'error': 'Authentification requise'}, status=401)
    
    can_view = False
    is_global_finance = (user.is_superuser or user.is_comptable_central)
    if is_global_finance:
        can_view = True
    elif int(site_id) in user.sites.all().values_list('id', flat=True):
        can_view = True

    if not can_view:
        return JsonResponse({'error': 'Action non autorisée'}, status=403)

    comptes = CompteFinancier.objects.filter(site__id=site_id, is_active=True).values('id', 'nom')
    return JsonResponse(list(comptes), safe=False)