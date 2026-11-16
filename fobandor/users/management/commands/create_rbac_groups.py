from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from fobandor.cms.models import (
    ServiceCategory, ServiceItem, Project,
    CompanyProfile, OfficialSocialLink, ContactInquiry,
)
from fobandor.fulfillment.models import FulfillmentOrder


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
        ops_group, _ = Group.objects.get_or_create(name='Fulfillment_Operators')
        ct = ContentType.objects.get_for_model(FulfillmentOrder)
        ops_perms = []
        for action in ('add', 'change', 'view'):
            ops_perms.append(Permission.objects.get(
                codename=f'{action}_{FulfillmentOrder._meta.model_name}',
                content_type=ct))
        ops_group.permissions.set(ops_perms)
        self.stdout.write('  [OK] Grupo Fulfillment_Operators configurado (FulfillmentOrder).')

        self.stdout.write(self.style.SUCCESS('✅ Grupos RBAC configurados.'))
