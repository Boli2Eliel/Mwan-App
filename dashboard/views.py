# dashboard/views.py
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from datetime import date

from enfants_gestion.models import Enfant, SuiviMedical
from sites_gestion.models import SiteOrphelinat
from gestion_financiere.models import Don
from django.db.models.functions import TruncMonth
from django.db.models import Sum
import json


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = date.today()

        enfant_queryset = Enfant.objects.filter(is_active=True)
        if not user.is_superuser and user.site:
            enfant_queryset = enfant_queryset.filter(site=user.site)
        
        context['total_enfants_actifs'] = enfant_queryset.count()

        if user.is_superuser:
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
        ).select_related('history_user').order_by('-history_date')[:3]
        
        context['total_activites'] = Enfant.history.filter(
            id__in=enfant_queryset.values_list('id', flat=True)
        ).count()

         # --- NOUVELLE LOGIQUE POUR LE GRAPHIQUE ---
        dons_queryset = Don.objects.all()
        if not self.request.user.is_superuser and self.request.user.site:
            dons_queryset = dons_queryset.filter(site=self.request.user.site)
            
        # Agréger les dons par mois
        donations_par_mois = dons_queryset.annotate(
            month=TruncMonth('date_don')
        ).values('month').annotate(
            total=Sum('montant')
        ).order_by('month')

        # Formatter les données pour Chart.js
        chart_labels = [d['month'].strftime('%B %Y') for d in donations_par_mois]
        chart_data = [float(d['total']) for d in donations_par_mois]

        context['chart_labels'] = json.dumps(chart_labels)
        context['chart_data'] = json.dumps(chart_data)
        
        return context