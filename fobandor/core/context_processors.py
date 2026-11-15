from fobandor.cms.models import OfficialSocialLink


def social_links(request):
    """Inyecta las redes sociales oficiales activas en todas las plantillas."""
    return {
        'social_links': OfficialSocialLink.objects.filter(is_active=True).order_by('order'),
    }
