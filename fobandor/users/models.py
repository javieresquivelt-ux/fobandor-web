from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("El superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("El superusuario debe tener is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField("Correo Electrónico", unique=True)
    phone = models.CharField(
        "Teléfono",
        max_length=16,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^\+[1-9]\d{1,14}$",
                message="Formato E.164 requerido (ej. +14075551234).",
            )
        ],
    )
    preferred_language = models.CharField(
        max_length=5,
        choices=[("es", "Español"), ("en", "English")],
        default="es",
    )
    is_email_verified = models.BooleanField(default=False)
    company_name = models.CharField("Empresa / Marca", max_length=150, blank=True)
    social_handle = models.CharField("Red Social / Arroba", max_length=100, blank=True)
    tax_id = models.CharField("Tax ID / EIN / NIF", max_length=50, blank=True)
    billing_address_line1 = models.CharField("Dirección Línea 1", max_length=255, blank=True)
    billing_address_line2 = models.CharField("Dirección Línea 2", max_length=255, blank=True)
    billing_city = models.CharField("Ciudad", max_length=100, blank=True)
    billing_state = models.CharField("Estado / Provincia", max_length=100, blank=True)
    billing_postal_code = models.CharField("Código Postal", max_length=20, blank=True)
    billing_country = models.CharField(
        "País (ISO-2)",
        max_length=2,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[A-Z]{2}$",
                message="Código ISO 3166-1 alpha-2 (ej. US).",
            )
        ],
    )
    stripe_customer_id = models.CharField(
        max_length=100, blank=True, null=True, unique=True
    )
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    marketing_consent = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.email
