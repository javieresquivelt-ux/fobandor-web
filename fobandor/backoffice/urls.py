from django.urls import path

from . import views

app_name = 'backoffice'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    # Servicios
    path('servicios/', views.ServiceCategoryListView.as_view(), name='service-list'),
    path('servicios/nuevo/', views.ServiceCategoryCreateView.as_view(), name='service-create'),
    path('servicios/<int:pk>/editar/', views.ServiceCategoryUpdateView.as_view(), name='service-update'),
    path('servicios/<int:pk>/eliminar/', views.ServiceCategoryDeleteView.as_view(), name='service-delete'),
    # Proyectos
    path('proyectos/', views.ProjectListView.as_view(), name='project-list'),
    path('proyectos/nuevo/', views.ProjectCreateView.as_view(), name='project-create'),
    path('proyectos/<int:pk>/editar/', views.ProjectUpdateView.as_view(), name='project-update'),
    path('proyectos/<int:pk>/eliminar/', views.ProjectDeleteView.as_view(), name='project-delete'),
    # Redes Sociales
    path('redes-sociales/', views.OfficialSocialLinkListView.as_view(), name='social-list'),
    path('redes-sociales/<int:pk>/editar/', views.OfficialSocialLinkUpdateView.as_view(), name='social-update'),
    # Perfil Corporativo (singleton)
    path('empresa/', views.CompanyProfileUpdateView.as_view(), name='company-profile'),
    # Órdenes SLA (Fulfillment)
    path('entregas/', views.FulfillmentOrderListView.as_view(), name='fulfillment-list'),
    path('entregas/<int:pk>/entregar/', views.FulfillmentOrderDeliverView.as_view(), name='fulfillment-deliver'),
]
