import json
from datetime import date
from itertools import chain
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum, Q, F
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView

from .models import CompteFinancier, Parrainage, Transaction, Enfant
from .forms import TransactionForm, ParrainageForm, FinanceExportForm
from .resources import TransactionResource
from sites_gestion.models import SiteOrphelinat


# =======================================================================
# VUES POUR LES TRANSACTIONS
# =======================================================================

class TransactionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Transaction
    template_name = 'gestion_financiere/transaction_list.html'
    context_object_name = 'transactions'
    permission_required = 'gestion_financiere.view_transaction'
    paginate_by = 25

    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(is_active=True).select_related('compte', 'parrainage_lie__enfant', 'cree_par')
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            return queryset
        return queryset.filter(compte__site__in=user.sites.all())

class EntreeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'gestion_financiere/transaction_form.html'
    permission_required = 'gestion_financiere.add_transaction'
    success_url = reverse_lazy('gestion_financiere:transaction_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "Enregistrer une Entrée (Don, Parrainage...)"
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['transaction_type'] = 'entree'
        return kwargs

    def get_initial(self):
        return {'type_transaction': 'entree'}

    def form_valid(self, form):
        form.instance.cree_par = self.request.user
        messages.success(self.request, "L'entrée a été enregistrée avec succès.")
        return super().form_valid(form)

class SortieCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'gestion_financiere/transaction_form.html'
    permission_required = 'gestion_financiere.add_transaction'
    success_url = reverse_lazy('gestion_financiere:transaction_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "Enregistrer une Sortie (Dépense)"
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['transaction_type'] = 'sortie'
        return kwargs

    def get_initial(self):
        return {'type_transaction': 'sortie'}

    def form_valid(self, form):
        form.instance.cree_par = self.request.user
        messages.success(self.request, "La sortie a été enregistrée avec succès.")
        return super().form_valid(form)

class TransactionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'gestion_financiere/transaction_form.html'
    permission_required = 'gestion_financiere.change_transaction'
    success_url = reverse_lazy('gestion_financiere:transaction_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        # La vue de modification passe le type de la transaction existante
        kwargs['transaction_type'] = self.object.type_transaction
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = "Modifier une Transaction"
        return context

    def form_valid(self, form):
        messages.success(self.request, "La transaction a été mise à jour avec succès.")
        return super().form_valid(form)
    
        
class TransactionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'gestion_financiere.delete_transaction'

    def post(self, request, *args, **kwargs):
        transaction_obj = get_object_or_404(Transaction, pk=kwargs['pk'])
        can_delete = False
        user = request.user
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            can_delete = True
        elif transaction_obj.compte.site in user.sites.all():
            can_delete = True

        if can_delete:
            transaction_obj.is_active = False
            transaction_obj.save()
            messages.success(request, "La transaction a été archivée.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('gestion_financiere:transaction_list')

# =======================================================================
# VUES CONCERNANT LE MODÈLE PARRAINAGE
# =======================================================================

class ParrainageListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Parrainage
    template_name = 'gestion_financiere/parrainage_list.html'
    context_object_name = 'parrainages'
    permission_required = 'gestion_financiere.view_parrainage'

    def get_queryset(self):
        user = self.request.user
        queryset = Parrainage.objects.filter(is_active=True).select_related('enfant__site').order_by('-date_debut')
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            return queryset
        return queryset.filter(enfant__site__in=user.sites.all())

class ParrainageDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Parrainage
    template_name = 'gestion_financiere/parrainage_detail.html'
    context_object_name = 'parrainage'
    permission_required = 'gestion_financiere.view_parrainage'

    def get_queryset(self):
        user = self.request.user
        queryset = Parrainage.objects.select_related('enfant__site').prefetch_related('transactions__compte')
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            return queryset
        return queryset.filter(enfant__site__in=user.sites.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial_data = {
            'type_transaction': 'entree',
            'categorie': 'Parrainage',
            'parrainage_lie': self.object,
            'montant': self.object.montant_mensuel,
            'description': f'Versement pour {self.object}'
        }
        context['versement_form'] = TransactionForm(user=self.request.user, transaction_type='entree', initial=initial_data)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = TransactionForm(request.POST, user=request.user, transaction_type='entree')

        if form.is_valid():
            versement = form.save(commit=False)
            versement.cree_par = request.user
            versement.parrainage_lie = self.object
            versement.type_transaction = 'entree'
            versement.categorie = 'Parrainage'
            versement.save()
            messages.success(request, "Le versement a été ajouté avec succès.")
        else:
            messages.error(request, f"Erreur dans le formulaire de versement : {form.errors.as_text()}")
        return redirect('gestion_financiere:parrainage_detail', pk=self.object.pk)

class ParrainageCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Parrainage
    form_class = ParrainageForm
    template_name = 'gestion_financiere/parrainage_form.html'
    permission_required = 'gestion_financiere.add_parrainage'
    success_url = reverse_lazy('gestion_financiere:parrainage_list')

    def form_valid(self, form):
        messages.success(self.request, f"Le parrainage pour {form.instance.enfant} a été créé avec succès.")
        return super().form_valid(form)

class ParrainageUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Parrainage
    form_class = ParrainageForm
    template_name = 'gestion_financiere/parrainage_form.html'
    permission_required = 'gestion_financiere.change_parrainage'
    success_url = reverse_lazy('gestion_financiere:parrainage_list')

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            return queryset
        return queryset.filter(enfant__site__in=user.sites.all())

    def form_valid(self, form):
        messages.success(self.request, f"Le parrainage pour {form.instance.enfant} a été mis à jour.")
        return super().form_valid(form)
    

class ParrainageDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'gestion_financiere.delete_parrainage'

    def post(self, request, *args, **kwargs):
        parrainage = get_object_or_404(Parrainage, pk=kwargs['pk'])
        can_delete = False
        user = request.user
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            can_delete = True
        elif parrainage.enfant.site in user.sites.all():
            can_delete = True
        if can_delete:
            parrainage.is_active = False
            parrainage.save()
            messages.success(request, "Le parrainage a été archivé.")
        else:
            messages.error(request, "Action non autorisée.")
        return redirect('gestion_financiere:parrainage_list')

# =======================================================================
# VUES DES RAPPORTS ET API
# =======================================================================

class RapportFinancierView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'gestion_financiere/rapport_financier.html'
    permission_required = 'gestion_financiere.view_transaction'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        comptes_queryset = CompteFinancier.objects.filter(is_active=True)
        transactions_queryset = Transaction.objects.filter(is_active=True)
        
        is_global_finance = (user.is_superuser or user.is_comptable_central)
        if is_global_finance:
            context['all_sites'] = SiteOrphelinat.objects.all()
            site_id = self.request.GET.get('site')
            if site_id:
                comptes_queryset = comptes_queryset.filter(site__id=site_id)
                transactions_queryset = transactions_queryset.filter(compte__site__id=site_id)
                context['selected_site'] = get_object_or_404(SiteOrphelinat, pk=site_id)
        else:
            sites_autorises = user.sites.all()
            comptes_queryset = comptes_queryset.filter(site__in=sites_autorises)
            transactions_queryset = transactions_queryset.filter(compte__site__in=sites_autorises)
        
        comptes_data = []
        for compte in comptes_queryset:
            entrees = transactions_queryset.filter(compte=compte, type_transaction='entree').aggregate(total=Sum('montant'))['total'] or 0
            sorties = transactions_queryset.filter(compte=compte, type_transaction='sortie').aggregate(total=Sum('montant'))['total'] or 0
            solde_actuel = (compte.solde_initial + entrees) - sorties
            comptes_data.append({'nom': compte.nom, 'solde_actuel': solde_actuel, 'total_entrees': entrees, 'total_depenses': sorties, 'solde_initial': compte.solde_initial})
            
        total_entrees_general = transactions_queryset.filter(type_transaction='entree').aggregate(total=Sum('montant'))['total'] or 0
        total_depenses_general = transactions_queryset.filter(type_transaction='sortie').aggregate(total=Sum('montant'))['total'] or 0
        solde_initial_general = comptes_queryset.aggregate(total=Sum('solde_initial'))['total'] or 0
        solde_final_general = (solde_initial_general + total_entrees_general) - total_depenses_general

        toutes_transactions = transactions_queryset.order_by('-date_transaction')
        context['comptes_data'] = comptes_data
        context['total_entrees_general'] = total_entrees_general
        context['total_depenses_general'] = total_depenses_general
        context['solde_final_general'] = solde_final_general
        context['transactions_recentes'] = toutes_transactions[:10]
        context['chart_labels'] = json.dumps(['Total des Entrées', 'Total des Dépenses'])
        context['chart_data'] = json.dumps([float(total_entrees_general), float(total_depenses_general)])

        return context

def get_comptes_for_site(request, site_id):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({}, status=401)
    
    can_view = False
    is_global_finance = (user.is_superuser or user.is_comptable_central)
    if is_global_finance:
        can_view = True
    elif user.sites.filter(pk=site_id).exists():
        can_view = True
    
    if not can_view:
        return JsonResponse({'error': 'Action non autorisée'}, status=403)
    
    comptes = CompteFinancier.objects.filter(site__id=site_id, is_active=True).values('id', 'nom')
    return JsonResponse(list(comptes), safe=False)