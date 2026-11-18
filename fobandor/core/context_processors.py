from fobandor.cms.models import CompanyProfile, OfficialSocialLink


def social_links(request):
    """Inyecta las redes sociales oficiales activas en todas las plantillas."""
    return {
        'social_links': OfficialSocialLink.objects.filter(is_active=True).order_by('order'),
    }


def company(request):
    """Inyecta el singleton institucional en todas las plantillas."""
    return {
        'company': CompanyProfile.load(),
    }
