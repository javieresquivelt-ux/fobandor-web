from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fobandor.users"
    label = "users"
    verbose_name = "Usuarios"

    def ready(self):
        from fobandor.users import signals  # noqa: F401
