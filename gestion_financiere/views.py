# gestion_financiere/views.py
from django.views.generic import ListView, CreateView, UpdateView, View
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Don, Depense
from .forms import DonForm, DepenseForm

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