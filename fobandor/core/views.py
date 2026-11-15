from django.shortcuts import render

from fobandor.cms.models import ServiceCategory


def home_view(request):
    services = ServiceCategory.objects.filter(is_active=True).prefetch_related('items').order_by('order')
    return render(request, 'pages/home.html', {'services': services})
