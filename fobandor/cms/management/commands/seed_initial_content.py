from django.core.management.base import BaseCommand

from fobandor.cms.models import (
    ServiceCategory, ServiceItem, OfficialSocialLink, CompanyProfile,
)


CATEGORIES = [
    {
        'slug': 'desarrollo-web',
        'title_es': 'Desarrollo Web con IA',
        'title_en': 'AI-Powered Web Development',
        'icon': '🌐',
        'order': 1,
    },
    {
        'slug': 'desarrollo-apps',
        'title_es': 'Desarrollo de Apps con IA',
        'title_en': 'AI-Powered App Development',
        'icon': '📱',
        'order': 2,
    },
    {
        'slug': 'publicidad',
        'title_es': 'Publicidad con IA',
        'title_en': 'AI-Powered Advertising',
        'icon': '📢',
        'order': 3,
    },
    {
        'slug': 'fobandor-studios',
        'title_es': 'Fobandor Studios',
        'title_en': 'Fobandor Studios',
        'icon': '🎬',
        'order': 4,
    },
]

SOCIAL_LINKS = [
    {'platform': 'instagram', 'url': 'https://www.instagram.com/fobandor.ai',
     'handle': '@fobandor.ai', 'order': 1},
    {'platform': 'tiktok', 'url': 'https://www.tiktok.com/@fobandor',
     'handle': '@fobandor', 'order': 2},
    {'platform': 'x', 'url': 'https://x.com/fobandor',
     'handle': '@fobandor', 'order': 3},
    {'platform': 'youtube', 'url': 'https://www.youtube.com/@fobandor',
     'handle': '@fobandor', 'order': 4},
    {'platform': 'facebook', 'url': 'https://www.facebook.com/share/1EAAc7Qw6x/',
     'handle': 'fobandor', 'order': 5},
]

SERVICE_ITEMS = {
    'desarrollo-web': [
        ('Sitios web corporativos', 'Corporate websites'),
        ('E-commerce', 'E-commerce'),
        ('Landing pages', 'Landing pages'),
        ('Chatbots y asistentes IA', 'AI chatbots and assistants'),
        ('Automatización de procesos', 'Process automation'),
    ],
    'desarrollo-apps': [
        ('Apps iOS / Android', 'iOS / Android apps'),
        ('Aplicaciones web', 'Web applications'),
        ('Apps con asistentes IA', 'Apps with AI assistants'),
        ('Sistemas personalizados', 'Custom systems'),
        ('Integración de APIs y automatizaciones', 'API integrations and automations'),
    ],
    'publicidad': [
        ('Campañas publicitarias', 'Advertising campaigns'),
        ('Videos para redes sociales', 'Social media videos'),
        ('Creatividades con IA', 'AI creatives'),
        ('Avatares y personajes', 'Avatars and characters'),
        ('Copywriting y conceptos', 'Copywriting and concepts'),
        ('Automatización de marketing', 'Marketing automation'),
    ],
    'fobandor-studios': [
        ('Series', 'Series'),
        ('Películas', 'Films'),
        ('Podcasts', 'Podcasts'),
        ('Trailers', 'Trailers'),
        ('Cortometrajes', 'Short films'),
        ('Videoclips', 'Music videos'),
        ('Contenido para YouTube y redes', 'YouTube and social content'),
    ],
}


class Command(BaseCommand):
    help = 'Siembra el contenido inicial del CMS (idempotente — usa get_or_create).'

    def handle(self, *args, **options):
        self.stdout.write('Sembrando categorías de servicio...')
        for data in CATEGORIES:
            obj, created = ServiceCategory.objects.get_or_create(
                slug=data['slug'], defaults=data)
            status = 'CREADA' if created else 'YA EXISTE'
            self.stdout.write(f'  [{status}] {obj.title_es}')

        self.stdout.write('Sembrando ítems de servicio...')
        for slug, items in SERVICE_ITEMS.items():
            category = ServiceCategory.objects.filter(slug=slug).first()
            if not category:
                self.stdout.write(f'  [OMITIDA] Categoría no encontrada: {slug}')
                continue
            for order, (title_es, title_en) in enumerate(items, start=1):
                obj, created = ServiceItem.objects.get_or_create(
                    category=category,
                    title_es=title_es,
                    defaults={'title_en': title_en, 'order': order})
                status = 'CREADO' if created else 'YA EXISTE'
                self.stdout.write(f'  [{status}] {category.title_es} → {obj.title_es}')

        self.stdout.write('Sembrando redes sociales oficiales...')
        for data in SOCIAL_LINKS:
            obj, created = OfficialSocialLink.objects.get_or_create(
                platform=data['platform'], defaults=data)
            status = 'CREADA' if created else 'YA EXISTE'
            self.stdout.write(f'  [{status}] {obj.get_platform_display()} → {obj.handle}')

        self.stdout.write('Sembrando perfil corporativo...')
        profile = CompanyProfile.load()
        if not profile.location:
            profile.location = 'Orlando, Florida, EE.UU.'
            profile.website_url = 'https://www.fobandor.com'
            profile.save()
            self.stdout.write('  [CREADO] FOBANDOR — Perfil Corporativo')
        else:
            self.stdout.write('  [YA EXISTE] FOBANDOR — Perfil Corporativo')

        self.stdout.write(self.style.SUCCESS('✅ seed_initial_content completado.'))
