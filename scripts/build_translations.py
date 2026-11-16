"""Genera el catálogo de traducción EN para FOBANDOR (Stage 1) y lo compila a .mo."""
from pathlib import Path

import polib

BASE_DIR = Path(__file__).resolve().parent.parent
LOCALE_DIR = BASE_DIR / "locale" / "en" / "LC_MESSAGES"

TRANSLATIONS = {
    # navbar
    "Inicio": "Home",
    "Servicios": "Services",
    "Proyectos": "Projects",
    "Precios": "Pricing",
    "Nosotros": "About Us",
    "Contacto": "Contact",
    "Comenzar": "Get Started",
    "Cambiar tema": "Toggle theme",
    "Abrir menú": "Open menu",
    # footer
    "Síguenos": "Follow Us",
    "Ubicación": "Location",
    "Todos los derechos reservados.": "All rights reserved.",
    # home
    "Tu visión. Nuestra tecnología. Sin límites.": "Your vision. Our technology. No limits.",
    "Español & English": "Spanish & English",
    "Ideas, código y creatividad impulsados por IA": "Ideas, code and creativity powered by AI",
    "Comencemos": "Let's Start",
    "Ver proyectos": "View projects",
    "Nuestros Servicios": "Our Services",
    "Cuatro líneas de negocio impulsadas por inteligencia artificial.":
        "Four business lines powered by artificial intelligence.",
    "Desarrollo Web con IA": "AI Web Development",
    "Sitios corporativos, e-commerce, landing pages, chatbots y asistentes IA, y automatización de procesos.":
        "Corporate sites, e-commerce, landing pages, AI chatbots and assistants, and process automation.",
    "Desarrollo de Apps con IA": "AI App Development",
    "Apps iOS y Android, aplicaciones web, sistemas a medida e integración de APIs y automatizaciones.":
        "iOS and Android apps, web apps, custom systems, and API integrations and automations.",
    "Publicidad con IA": "AI Advertising",
    "Campañas publicitarias, videos para redes, creatividades con IA, avatares, copywriting y automatización de marketing.":
        "Ad campaigns, social media videos, AI creatives, avatars, copywriting, and marketing automation.",
    "Fobandor Studios": "Fobandor Studios",
    "Producción audiovisual con IA: series, películas, podcasts, trailers, cortometrajes, videoclips y contenido para YouTube.":
        "AI audiovisual production: series, films, podcasts, trailers, short films, music videos, and YouTube content.",
    "Casos de éxito próximamente.": "Success stories coming soon.",
    "Planes de suscripción próximamente.": "Subscription plans coming soon.",
    "Conoce a FOBANDOR, Orlando, Florida.": "Meet FOBANDOR, Orlando, Florida.",
    "Formulario de contacto próximamente.": "Contact form coming soon.",
    # billing / pricing
    "Planes de Acompañamiento": "Mentorship & Growth Plans",
    "Marketing Digital & Ventas para negocios locales.": "Digital Marketing & Sales for local businesses.",
    "RECOMENDADO": "RECOMMENDED",
    "mes": "month",
    "Acompañamiento mínimo: %(months)s meses": "Minimum commitment: %(months)s months",
    "Planes próximamente.": "Plans coming soon.",
    "Agenda un diagnóstico y descubre cuál plan necesita tu negocio":
        "Schedule a diagnosis and discover which plan your business needs",
    "Hablemos hoy": "Let's talk today",
    "Solicita tu diagnóstico": "Request your diagnosis",
    "Nombre": "Name",
    "Email": "Email",
    "Teléfono": "Phone",
    "Mensaje": "Message",
    "Enviar solicitud": "Send request",
    "Cerrar": "Close",
    # backoffice
    "Planes & Precios": "Plans & Pricing",
}


def main() -> None:
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    po = polib.POFile()
    po.metadata = {
        "Project-Id-Version": "FOBANDOR 1.0",
        "Language": "en",
        "Content-Type": "text/plain; charset=UTF-8",
        "Content-Transfer-Encoding": "8bit",
    }
    for msgid, msgstr in TRANSLATIONS.items():
        po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
    po.save(str(LOCALE_DIR / "django.po"))
    po.save_as_mofile(str(LOCALE_DIR / "django.mo"))
    print(f"Catálogo EN generado en {LOCALE_DIR} ({len(po)} cadenas)")


if __name__ == "__main__":
    main()
