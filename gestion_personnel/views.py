from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View

from .models import Employe
from .forms import EmployeForm

class EmployeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Employe
    template_name = 'gestion_personnel/employe_list.html'
    context_object_name = 'employes'
    permission_required = 'gestion_personnel.view_employe'

    def get_queryset(self):
        user = self.request.user
        queryset = Employe.objects.filter(is_active=True).prefetch_related('sites', 'utilisateur')
        is_global_role = user.groups.filter(name__in=['Directeur', 'RH']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset.order_by('nom', 'prenom')
        return queryset.filter(sites__in=user.sites.all()).order_by('nom', 'prenom').distinct()

class EmployeDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Employe
    template_name = 'gestion_personnel/employe_detail.html'
    context_object_name = 'employe'
    permission_required = 'gestion_personnel.view_employe'

    def get_queryset(self):
        user = self.request.user
        queryset = Employe.objects.filter(is_active=True).select_related('utilisateur').prefetch_related('sites')
        is_global_role = user.groups.filter(name__in=['Directeur', 'RH']).exists() and not user.sites.exists()
        if user.is_superuser or is_global_role:
            return queryset
        return queryset.filter(sites__in=user.sites.all()).distinct()

class EmployeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Employe
    form_class = EmployeForm
    template_name = 'gestion_personnel/employe_form.html'
    permission_required = 'gestion_personnel.add_employe'
    success_url = reverse_lazy('gestion_personnel:employe_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        action = self.request.POST.get('user_action', 'none')
        employe = form.save(action=action)
        messages.success(self.request, f"La fiche de {employe.prenom} {employe.nom} a été créée.")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "Le formulaire contient des erreurs. Veuillez corriger les champs indiqués.")
        return super().form_invalid(form)

class EmployeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Employe
    form_class = EmployeForm
    template_name = 'gestion_personnel/employe_form.html'
    permission_required = 'gestion_personnel.change_employe'
    success_url = reverse_lazy('gestion_personnel:employe_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        action = self.request.POST.get('user_action', 'none')
        form.save(action=action)
        messages.success(self.request, "La fiche de l'employé a été mise à jour.")
        return redirect(self.success_url)

class EmployeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'gestion_personnel.delete_employe'

    def post(self, request, *args, **kwargs):
        employe = get_object_or_404(Employe, pk=kwargs['pk'])
        # ... (logique de suppression)
        return redirect('gestion_personnel:employe_list')