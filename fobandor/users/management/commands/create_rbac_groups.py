from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from fobandor.cms.models import (
    ServiceCategory, ServiceItem, Project,
    CompanyProfile, OfficialSocialLink, ContactInquiry,
)


class Command(BaseCommand):
    help = 'Crea los grupos RBAC de FOBANDOR (idempotente).'

    def handle(self, *args, **options):
        # --- Content_Editors ---
        editors_group, _ = Group.objects.get_or_create(name='Content_Editors')
        cms_models = [ServiceCategory, ServiceItem, Project,
                      CompanyProfile, OfficialSocialLink, ContactInquiry]
        editor_perms = []
        for model in cms_models:
            ct = ContentType.objects.get_for_model(model)
            for action in ('add', 'change', 'view'):
                perm = Permission.objects.get(
                    codename=f'{action}_{model._meta.model_name}',
                    content_type=ct)
                editor_perms.append(perm)
        editors_group.permissions.set(editor_perms)
        self.stdout.write('  [OK] Grupo Content_Editors configurado.')

        # --- Fulfillment_Operators ---
        # Se asignarán permisos sobre FulfillmentOrder en Etapa 3
        ops_group, created = Group.objects.get_or_create(name='Fulfillment_Operators')
        status = 'CREADO' if created else 'YA EXISTE'
        self.stdout.write(f'  [{status}] Grupo Fulfillment_Operators (permisos de Etapa 3).')

        self.stdout.write(self.style.SUCCESS('✅ Grupos RBAC configurados.'))
