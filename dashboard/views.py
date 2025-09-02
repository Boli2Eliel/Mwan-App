from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from datetime import date
import json

from enfants_gestion.models import Enfant, SuiviMedical
from sites_gestion.models import SiteOrphelinat
from gestion_financiere.models import Don

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()

        # =======================================================================
        # NOUVELLE LOGIQUE DE FILTRAGE BASÉE SUR user.sites
        # =======================================================================
        
        # Définir les périmètres de base pour chaque type de données
        enfant_queryset = Enfant.objects.filter(is_active=True)
        dons_queryset = Don.objects.filter(is_active=True)
        comptes_queryset = SiteOrphelinat.objects.all()

        # Définir si l'utilisateur a un rôle global
        is_global_manager = user.groups.filter(name__in=['Directeur', 'Gestionnaire', 'RH']).exists() and not user.sites.exists()
        is_global_finance = user.is_comptable_central

        # Si l'utilisateur n'est pas un admin ou un rôle global, on filtre par ses sites assignés
        if not (user.is_superuser or is_global_manager or is_global_finance):
            sites_autorises = user.sites.all()
            enfant_queryset = enfant_queryset.filter(site__in=sites_autorises)
            dons_queryset = dons_queryset.filter(site__in=sites_autorises)
            comptes_queryset = comptes_queryset.filter(id__in=sites_autorises.values_list('id', flat=True))

        # =======================================================================
        # CALCULS BASÉS SUR LES DONNÉES FILTRÉES
        # =======================================================================

        context['total_enfants_actifs'] = enfant_queryset.count()

        if user.is_superuser or is_global_manager:
            context['total_sites'] = SiteOrphelinat.objects.count()
            context['enfants_par_site'] = SiteOrphelinat.objects.annotate(
                count=Count('enfant', filter=Q(enfant__is_active=True))
            ).order_by('-count')

        context['anniversaires_du_mois'] = enfant_queryset.filter(
            date_naissance__month=today.month
        ).order_by('date_naissance__day')
        
        context['derniers_suivis_medicaux'] = SuiviMedical.objects.filter(
            enfant__in=enfant_queryset, is_active=True
        ).select_related('enfant').order_by('-date_consultation')[:5]

        context['activite_recente'] = Enfant.history.filter(
            id__in=enfant_queryset.values_list('id', flat=True)
        ).select_related('history_user').order_by('-history_date')[:5]
        
        context['total_activites'] = Enfant.history.filter(
            id__in=enfant_queryset.values_list('id', flat=True)
        ).count()

        # Logique pour le graphique des dons
        donations_par_mois = dons_queryset.annotate(
            month=TruncMonth('date_don')
        ).values('month').annotate(
            total=Sum('montant')
        ).order_by('month')

        chart_labels = [d['month'].strftime('%B %Y') for d in donations_par_mois]
        chart_data = [float(d['total']) for d in donations_par_mois]
        context['chart_labels'] = json.dumps(chart_labels)
        context['chart_data'] = json.dumps(chart_data)
        
        return context