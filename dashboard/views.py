import json
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView

from enfants_gestion.models import Enfant, SuiviMedical
from gestion_financiere.models import Transaction
from sites_gestion.models import SiteOrphelinat


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()

        # =======================================================================
        # 1. DÉFINIR LES PÉRIMÈTRES DE BASE
        # =======================================================================
        enfant_queryset = Enfant.objects.filter(is_active=True)
        transactions_queryset = Transaction.objects.filter(is_active=True)

        # Définir si l'utilisateur a un rôle à vision globale
        is_global_role = user.groups.filter(name__in=['Directeur', 'Gestionnaire', 'RH']).exists() and not user.sites.exists()
        is_global_finance = user.is_comptable_central

        # Si l'utilisateur n'est pas un admin ou un rôle global, on filtre par ses sites assignés
        if not (user.is_superuser or is_global_role or is_global_finance):
            sites_autorises = user.sites.all()
            enfant_queryset = enfant_queryset.filter(site__in=sites_autorises)
            transactions_queryset = transactions_queryset.filter(compte__site__in=sites_autorises)
        
        # =======================================================================
        # 2. CALCULER LES DONNÉES POUR LES WIDGETS
        # =======================================================================

        # --- STATISTIQUES PRINCIPALES ---
        context['total_enfants_actifs'] = enfant_queryset.count()

        if user.is_superuser or is_global_role:
            context['total_sites'] = SiteOrphelinat.objects.count()
            context['enfants_par_site'] = SiteOrphelinat.objects.annotate(
                count=Count('enfant', filter=Q(enfant__is_active=True))
            ).order_by('-count')

        # --- WIDGET ANNIVERSAIRES ---
        anniversaires_queryset = enfant_queryset.filter(
            date_naissance__month=today.month
        ).order_by('date_naissance__day')
        
        anniversaires_du_mois = []
        for enfant in anniversaires_queryset:
            age = today.year - enfant.date_naissance.year - ((today.month, today.day) < (enfant.date_naissance.month, enfant.date_naissance.day))
            anniversaires_du_mois.append({
                'enfant': enfant,
                'age_a_feter': age + 1
            })
        context['anniversaires_du_mois'] = anniversaires_du_mois
        
        # --- WIDGET SUIVIS MÉDICAUX ---
        context['derniers_suivis_medicaux'] = SuiviMedical.objects.filter(
            enfant__in=enfant_queryset, is_active=True
        ).select_related('enfant').order_by('-date_consultation')[:5]

        # --- WIDGET ACTIVITÉ RÉCENTE ---
        # Note : history.filter ne fonctionne pas avec `site__in`, on filtre donc par les IDs d'enfants autorisés
        enfants_ids_autorises = enfant_queryset.values_list('id', flat=True)
        context['activite_recente'] = Enfant.history.filter(
            id__in=enfants_ids_autorises
        ).select_related('history_user').order_by('-history_date')[:5]
        
        context['total_activites'] = Enfant.history.filter(id__in=enfants_ids_autorises).count()

        # --- DONNÉES POUR LE GRAPHIQUE FINANCIER ---
        entrees_par_mois = transactions_queryset.filter(type_transaction='entree').annotate(
            month=TruncMonth('date_transaction')
        ).values('month').annotate(
            total=Sum('montant')
        ).order_by('month')

        chart_labels = [d['month'].strftime('%B %Y') for d in entrees_par_mois]
        chart_data = [float(d['total']) for d in entrees_par_mois]
        context['chart_labels'] = json.dumps(chart_labels)
        context['chart_data'] = json.dumps(chart_data)
        
        return context