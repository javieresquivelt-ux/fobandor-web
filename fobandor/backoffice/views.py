from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, TemplateView,
)

from fobandor.cms.models import (
    ServiceCategory, Project, OfficialSocialLink, CompanyProfile,
)
from fobandor.billing.forms import SubscriptionPlanForm
from fobandor.billing.models import SubscriptionPlan
from fobandor.fulfillment.models import FulfillmentOrder
from fobandor.users.models import User

from .mixins import StaffRequiredMixin


class BackofficeMixin(LoginRequiredMixin, StaffRequiredMixin):
    """Mixin base para todas las vistas del backoffice."""
    pass


# --- Dashboard ---

class DashboardView(BackofficeMixin, TemplateView):
    template_name = 'backoffice/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        ctx['total_users'] = User.objects.count()
        ctx['total_services'] = ServiceCategory.objects.filter(is_active=True).count()
        ctx['total_projects'] = Project.objects.count()
        return ctx


# --- Servicios ---

class ServiceCategoryListView(BackofficeMixin, ListView):
    model = ServiceCategory
    template_name = 'backoffice/cms/service_list.html'
    context_object_name = 'services'
    ordering = ['order']


class ServiceCategoryCreateView(BackofficeMixin, CreateView):
    model = ServiceCategory
    template_name = 'backoffice/cms/service_form.html'
    fields = ['slug', 'title_es', 'title_en', 'icon', 'order', 'is_active']
    success_url = reverse_lazy('backoffice:service-list')


class ServiceCategoryUpdateView(BackofficeMixin, UpdateView):
    model = ServiceCategory
    template_name = 'backoffice/cms/service_form.html'
    fields = ['slug', 'title_es', 'title_en', 'icon', 'order', 'is_active']
    success_url = reverse_lazy('backoffice:service-list')


class ServiceCategoryDeleteView(BackofficeMixin, DeleteView):
    model = ServiceCategory
    template_name = 'backoffice/cms/service_confirm_delete.html'
    success_url = reverse_lazy('backoffice:service-list')


# --- Proyectos ---

class ProjectListView(BackofficeMixin, ListView):
    model = Project
    template_name = 'backoffice/cms/project_list.html'
    context_object_name = 'projects'
    ordering = ['order', '-created_at']


class ProjectCreateView(BackofficeMixin, CreateView):
    model = Project
    template_name = 'backoffice/cms/project_form.html'
    fields = ['title_es', 'title_en', 'desc_es', 'desc_en',
              'client_name', 'category', 'image', 'url',
              'is_featured', 'order', 'tags']
    success_url = reverse_lazy('backoffice:project-list')


class ProjectUpdateView(BackofficeMixin, UpdateView):
    model = Project
    template_name = 'backoffice/cms/project_form.html'
    fields = ['title_es', 'title_en', 'desc_es', 'desc_en',
              'client_name', 'category', 'image', 'url',
              'is_featured', 'order', 'tags']
    success_url = reverse_lazy('backoffice:project-list')


class ProjectDeleteView(BackofficeMixin, DeleteView):
    model = Project
    template_name = 'backoffice/cms/project_confirm_delete.html'
    success_url = reverse_lazy('backoffice:project-list')


# --- Redes Sociales ---

class OfficialSocialLinkListView(BackofficeMixin, ListView):
    model = OfficialSocialLink
    template_name = 'backoffice/cms/social_link_list.html'
    context_object_name = 'social_links'


class OfficialSocialLinkUpdateView(BackofficeMixin, UpdateView):
    model = OfficialSocialLink
    template_name = 'backoffice/cms/social_link_form.html'
    fields = ['url', 'handle', 'is_active', 'order']
    success_url = reverse_lazy('backoffice:social-list')


# --- Perfil Corporativo (Singleton) ---

class CompanyProfileUpdateView(BackofficeMixin, UpdateView):
    model = CompanyProfile
    template_name = 'backoffice/cms/company_profile_form.html'
    fields = ['logo', 'mission_es', 'mission_en', 'vision_es', 'vision_en',
              'values_es', 'values_en', 'founded_year', 'location', 'website_url',
              'diag_form_subject', 'diag_modal_title_es', 'diag_modal_title_en',
              'diag_success_msg_es', 'diag_success_msg_en',
              'show_services_section', 'show_projects_section',
              'show_about_section', 'show_contact_section']
    success_url = reverse_lazy('backoffice:company-profile')

    def get_object(self, queryset=None):
        """Siempre retorna el singleton (pk=1), creándolo si no existe."""
        return CompanyProfile.load()


# --- Órdenes SLA (Fulfillment) ---

class FulfillmentOrderListView(BackofficeMixin, ListView):
    model = FulfillmentOrder
    template_name = 'backoffice/fulfillment/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        qs = FulfillmentOrder.objects.select_related('user', 'subscription', 'plan', 'assigned_to').order_by('due_date')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_choices'] = FulfillmentOrder.STATUS_CHOICES
        ctx['current_status'] = self.request.GET.get('status', '')
        return ctx


class FulfillmentOrderDeliverView(BackofficeMixin, UpdateView):
    model = FulfillmentOrder
    template_name = 'backoffice/fulfillment/order_detail.html'
    fields = ['assigned_to', 'deliverable_file', 'deliverable_url', 'internal_notes']
    success_url = reverse_lazy('backoffice:fulfillment-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['assigned_to'].queryset = User.objects.filter(
            Q(groups__name__in=['Fulfillment_Operators', 'Content_Editors']) | Q(is_staff=True)
        ).distinct()
        return form

    def form_valid(self, form):
        order = form.save(commit=False)
        if '_start' in self.request.POST:
            order.status = 'EN_PROCESO'
        else:
            order.status = 'ENTREGADA'
            order.delivered_at = timezone.now()
        order.save()
        return redirect(self.success_url)


# --- Planes & Precios (Billing) ---

class SubscriptionPlanListView(BackofficeMixin, ListView):
    model = SubscriptionPlan
    template_name = 'backoffice/billing/plan_list.html'
    context_object_name = 'plans'
    ordering = ['order']


class SubscriptionPlanUpdateView(BackofficeMixin, UpdateView):
    model = SubscriptionPlan
    template_name = 'backoffice/billing/plan_form.html'
    form_class = SubscriptionPlanForm
    success_url = reverse_lazy('backoffice:plan-list')
