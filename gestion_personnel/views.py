# =======================================================================
# IMPORTS
# =======================================================================
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, FormView, View

from .models import Employe
from .forms import EmployeCreateForm, EmployeUpdateForm

# =======================================================================
# VUES CONCERNANT LE MODÈLE EMPLOYE
# =======================================================================

class EmployeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Employe
    template_name = 'gestion_personnel/employe_list.html'
    context_object_name = 'employes'
    permission_required = 'gestion_personnel.view_employe'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        # Optimisation : pre-charge les données de l'utilisateur et du site en une seule requête
        queryset = Employe.objects.filter(is_active=True).select_related('utilisateur')

        # Rôles globaux (Superuser, ou 'Directeur'/'RH' sans sites spécifiques)
        is_global_role = user.groups.filter(name__in=['Directeur', 'RH']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset.order_by('nom', 'prenom')
        
        # Utilisateurs locaux (limités à leurs sites assignés)
        # distinct() évite les doublons si un employé est lié à plusieurs sites que l'utilisateur peut voir
        return queryset.filter(utilisateur__sites__in=user.sites.all()).order_by('nom', 'prenom').distinct()

class EmployeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Employe
    template_name = 'gestion_personnel/employe_detail.html'
    context_object_name = 'employe'
    permission_required = 'gestion_personnel.view_employe'

    def get_queryset(self):
        user = self.request.user
        queryset = Employe.objects.select_related('utilisateur')
        
        is_global_role = user.groups.filter(name__in=['Directeur', 'RH']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset
            
        return queryset.filter(utilisateur__sites__in=user.sites.all()).distinct()

class EmployeCreateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'gestion_personnel/employe_form.html'
    form_class = EmployeCreateForm
    permission_required = 'gestion_personnel.add_employe'
    success_url = reverse_lazy('gestion_personnel:employe_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        employe = form.save()
        messages.success(self.request, f"La fiche de {employe.prenom} {employe.nom} a été créée avec succès.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Le formulaire contient des erreurs. Veuillez corriger les champs indiqués.")
        return super().form_invalid(form)

class EmployeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'gestion_personnel/employe_form.html'
    form_class = EmployeUpdateForm
    permission_required = 'gestion_personnel.change_employe'
    success_url = reverse_lazy('gestion_personnel:employe_list')

    def get_object(self):
        return get_object_or_404(Employe, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.get_object()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "La fiche de l'employé a été mise à jour.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Le formulaire de modification contient des erreurs.")
        return super().form_invalid(form)

class EmployeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'gestion_personnel.delete_employe'

    def post(self, request, *args, **kwargs):
        employe = get_object_or_404(Employe, pk=kwargs['pk'])
        
        can_delete = False
        user = request.user
        is_global_role = user.groups.filter(name__in=['Directeur', 'RH']).exists() and not user.sites.exists()
        
        if user.is_superuser or is_global_role:
            can_delete = True
        elif employe.utilisateur and set(user.sites.all()).intersection(set(employe.utilisateur.sites.all())):
            can_delete = True
        
        if can_delete:
            employe.is_active = False
            employe.save()
            messages.success(request, f"La fiche de {employe} a été archivée.")
        else:
            messages.error(request, "Action non autorisée.")
        
        return redirect('gestion_personnel:employe_list')