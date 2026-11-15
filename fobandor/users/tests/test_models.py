import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user_with_email_successful():
    """Valida la creación de un usuario estándar basado en email (ADR-011)."""
    user = User.objects.create_user(
        email="cliente@test.com",
        password="Password123!",
        first_name="Juan",
        last_name="Perez",
    )
    assert user.email == "cliente@test.com"
    assert user.first_name == "Juan"
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.is_active is True
    assert user.check_password("Password123!") is True


@pytest.mark.django_db
def test_create_superuser_successful():
    """Valida la creación de un superusuario basado en email."""
    admin_user = User.objects.create_superuser(
        email="admin@test.com",
        password="AdminPassword123!",
    )
    assert admin_user.email == "admin@test.com"
    assert admin_user.is_staff is True
    assert admin_user.is_superuser is True


@pytest.mark.django_db
def test_create_user_without_email_raises_error():
    """Valida que intentar crear un usuario sin email arroja ValueError."""
    with pytest.raises(ValueError, match="El correo electrónico es obligatorio."):
        User.objects.create_user(email="", password="Password123!")
