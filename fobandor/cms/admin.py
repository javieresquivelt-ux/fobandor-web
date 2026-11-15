from django.contrib import admin

from .models import (
    ServiceCategory, ServiceItem, Project,
    CompanyProfile, OfficialSocialLink, ContactInquiry,
)


class ServiceItemInline(admin.TabularInline):
    model = ServiceItem
    extra = 1
    fields = ('title_es', 'title_en', 'order', 'is_active')


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('title_es', 'slug', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title_es', 'title_en', 'slug')
    prepopulated_fields = {'slug': ('title_es',)}
    inlines = [ServiceItemInline]
    fieldsets = (
        ('Español', {'fields': ('slug', 'title_es', 'icon', 'order', 'is_active')}),
        ('English', {'fields': ('title_en',)}),
    )


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title_es', 'category', 'is_featured', 'order', 'created_at')
    list_filter = ('category', 'is_featured')
    search_fields = ('title_es', 'title_en', 'client_name', 'tags')
    list_editable = ('order', 'is_featured')
    fieldsets = (
        ('Español', {'fields': ('title_es', 'desc_es')}),
        ('English', {'fields': ('title_en', 'desc_en')}),
        ('Metadata', {'fields': ('category', 'client_name', 'image', 'url',
                                 'is_featured', 'order', 'tags')}),
    )


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Español', {'fields': ('mission_es', 'vision_es', 'values_es')}),
        ('English', {'fields': ('mission_en', 'vision_en', 'values_en')}),
        ('Datos Generales', {'fields': ('founded_year', 'location', 'website_url')}),
    )

    def has_add_permission(self, request):
        """Bloquea agregar si ya existe el registro singleton."""
        return not CompanyProfile.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OfficialSocialLink)
class OfficialSocialLinkAdmin(admin.ModelAdmin):
    list_display = ('platform', 'handle', 'url', 'is_active', 'order')
    list_editable = ('is_active', 'order')


@admin.register(ContactInquiry)
class ContactInquiryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'service_interest', 'status', 'created_at')
    list_filter = ('status', 'service_interest')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('name', 'email', 'phone', 'message',
                       'service_interest', 'created_at')

    def has_add_permission(self, request):
        return False
