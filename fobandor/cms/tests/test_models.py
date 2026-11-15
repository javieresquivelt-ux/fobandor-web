import pytest

from fobandor.cms.models import ServiceCategory, OfficialSocialLink, CompanyProfile


@pytest.mark.django_db
def test_service_category_creation():
    cat = ServiceCategory.objects.create(
        slug='test-web', title_es='Web', title_en='Web', order=1)
    assert str(cat) == 'Web'
    assert cat.is_active is True


@pytest.mark.django_db
def test_official_social_link_creation():
    link = OfficialSocialLink.objects.create(
        platform='instagram',
        url='https://www.instagram.com/fobandor.ai',
        handle='@fobandor.ai',
        order=1)
    assert 'Instagram' in str(link)


@pytest.mark.django_db
def test_company_profile_singleton():
    p1 = CompanyProfile.load()
    p2 = CompanyProfile.load()
    assert p1.pk == p2.pk == 1


@pytest.mark.django_db
def test_seed_initial_content_idempotent():
    from django.core.management import call_command
    call_command('seed_initial_content', verbosity=0)
    count_before = ServiceCategory.objects.count()
    call_command('seed_initial_content', verbosity=0)
    count_after = ServiceCategory.objects.count()
    assert count_before == count_after == 4
