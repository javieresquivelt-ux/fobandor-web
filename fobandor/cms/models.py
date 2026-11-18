from django.db import models


class ServiceCategory(models.Model):
    """4 líneas de negocio: Desarrollo Web, Apps, Publicidad, Studios."""
    slug = models.SlugField(max_length=60, unique=True)
    title_es = models.CharField('Título (ES)', max_length=120)
    title_en = models.CharField('Title (EN)', max_length=120)
    icon = models.CharField('Ícono (SVG/emoji)', max_length=100, blank=True)
    order = models.PositiveSmallIntegerField('Orden', default=0)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Categoría de Servicio'
        verbose_name_plural = 'Categorías de Servicio'

    def __str__(self):
        return self.title_es


class ServiceItem(models.Model):
    """Ítem de servicio anidado bajo una categoría."""
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.CASCADE, related_name='items')
    title_es = models.CharField('Título (ES)', max_length=200)
    title_en = models.CharField('Title (EN)', max_length=200)
    desc_es = models.TextField('Descripción (ES)', blank=True)
    desc_en = models.TextField('Description (EN)', blank=True)
    order = models.PositiveSmallIntegerField('Orden', default=0)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Ítem de Servicio'
        verbose_name_plural = 'Ítems de Servicio'

    def __str__(self):
        return f'{self.category.title_es} → {self.title_es}'


class Project(models.Model):
    """Portafolio de proyectos realizados."""
    title_es = models.CharField('Título (ES)', max_length=200)
    title_en = models.CharField('Title (EN)', max_length=200)
    desc_es = models.TextField('Descripción (ES)', blank=True)
    desc_en = models.TextField('Description (EN)', blank=True)
    client_name = models.CharField('Cliente', max_length=150, blank=True)
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='projects')
    image = models.ImageField('Imagen', upload_to='projects/', blank=True)
    url = models.URLField('URL del proyecto', blank=True)
    is_featured = models.BooleanField('Destacado', default=False)
    order = models.PositiveSmallIntegerField('Orden', default=0)
    tags = models.CharField('Etiquetas (CSV)', max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def __str__(self):
        return self.title_es


class CompanyProfile(models.Model):
    """Singleton: datos institucionales de FOBANDOR (misión, visión, valores)."""
    mission_es = models.TextField('Misión (ES)', blank=True)
    mission_en = models.TextField('Mission (EN)', blank=True)
    vision_es = models.TextField('Visión (ES)', blank=True)
    vision_en = models.TextField('Vision (EN)', blank=True)
    values_es = models.TextField('Valores (ES)', blank=True)
    values_en = models.TextField('Values (EN)', blank=True)
    founded_year = models.PositiveSmallIntegerField('Año de fundación', null=True, blank=True)
    location = models.CharField('Ubicación', max_length=200, blank=True,
                                default='Orlando, Florida, EE.UU.')
    website_url = models.URLField('URL del sitio web', blank=True,
                                  default='https://www.fobandor.com')
    # Formulario de diagnóstico / modal de precios
    diag_form_subject = models.CharField(
        'Asunto del formulario (Formspree)', max_length=200,
        default='Nuevo Formulario Web - FOBANDOR')
    diag_modal_title_es = models.CharField(
        'Título del modal tras envío (ES)', max_length=100,
        default='Solicitud enviada')
    diag_modal_title_en = models.CharField(
        'Modal title after submit (EN)', max_length=100,
        default='Request sent')
    diag_success_msg_es = models.TextField(
        'Mensaje de éxito (ES)',
        default='¡Gracias! Hemos recibido tu solicitud. Nos contactaremos a la brevedad.')
    diag_success_msg_en = models.TextField(
        'Success message (EN)',
        default='Thank you! We received your request. We will get back to you shortly.')
    # Visibilidad de secciones de la landing
    show_services_section = models.BooleanField(
        'Mostrar sección Servicios en Landing', default=True)
    show_projects_section = models.BooleanField(
        'Mostrar sección Proyectos en Landing', default=True)
    show_about_section = models.BooleanField(
        'Mostrar sección Nosotros en Landing', default=True)
    show_contact_section = models.BooleanField(
        'Mostrar sección Contacto en Landing', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil de la Empresa'
        verbose_name_plural = 'Perfil de la Empresa'

    def __str__(self):
        return 'FOBANDOR — Perfil Corporativo'

    def save(self, *args, **kwargs):
        """Garantiza el patrón singleton: solo puede existir un registro."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class OfficialSocialLink(models.Model):
    """Redes sociales oficiales de FOBANDOR."""
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('x', 'X (Twitter)'),
        ('youtube', 'YouTube'),
        ('facebook', 'Facebook'),
    ]
    platform = models.CharField('Plataforma', max_length=20,
                                choices=PLATFORM_CHOICES, unique=True)
    url = models.URLField('URL')
    handle = models.CharField('Handle / @', max_length=100, blank=True)
    is_active = models.BooleanField('Activo', default=True)
    order = models.PositiveSmallIntegerField('Orden', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Red Social Oficial'
        verbose_name_plural = 'Redes Sociales Oficiales'

    def __str__(self):
        return f'{self.get_platform_display()} → {self.handle}'


class ContactInquiry(models.Model):
    """Consultas entrantes desde el formulario de contacto público."""
    STATUS_CHOICES = [
        ('NEW', 'Nueva'),
        ('READ', 'Leída'),
        ('REPLIED', 'Respondida'),
    ]
    name = models.CharField('Nombre', max_length=150)
    email = models.EmailField('Correo')
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    message = models.TextField('Mensaje')
    service_interest = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='inquiries', verbose_name='Servicio de interés')
    status = models.CharField('Estado', max_length=10,
                              choices=STATUS_CHOICES, default='NEW')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Consulta de Contacto'
        verbose_name_plural = 'Consultas de Contacto'

    def __str__(self):
        return f'{self.name} <{self.email}> [{self.status}]'
