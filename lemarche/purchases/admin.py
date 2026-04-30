from django.contrib import admin
from django.utils import timezone

from lemarche.purchases import constants as purchases_constants
from lemarche.purchases.models import SlugMappingCache
from lemarche.utils.admin.admin_site import admin_site


class SourceFilter(admin.SimpleListFilter):
    title = "Source"
    parameter_name = "source"

    def lookups(self, request, model_admin):
        return purchases_constants.SLUG_MAPPING_SOURCE_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(source=self.value())
        return queryset


class KindFilter(admin.SimpleListFilter):
    title = "Type"
    parameter_name = "kind"

    def lookups(self, request, model_admin):
        return purchases_constants.SLUG_MAPPING_KIND_CHOICES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(kind=self.value())
        return queryset


def validate_mappings(modeladmin, request, queryset):
    """Valide les correspondances sélectionnées et les rend disponibles pour tous les utilisateurs."""
    updated = queryset.update(
        source=purchases_constants.SLUG_MAPPING_SOURCE_ADMIN_VALIDATED,
        validated_by=request.user,
        validated_at=timezone.now(),
    )
    modeladmin.message_user(request, f"{updated} correspondance(s) validée(s) avec succès.")


validate_mappings.short_description = "✅ Valider les correspondances sélectionnées"


def reject_mappings(modeladmin, request, queryset):
    """Supprime les correspondances sélectionnées."""
    count, _ = queryset.delete()
    modeladmin.message_user(request, f"{count} correspondance(s) supprimée(s).")


reject_mappings.short_description = "❌ Supprimer les correspondances sélectionnées"


@admin.register(SlugMappingCache, site=admin_site)
class SlugMappingCacheAdmin(admin.ModelAdmin):
    list_display = [
        "raw_value",
        "kind",
        "resolved_slug",
        "confidence_display",
        "source",
        "usage_count",
        "proposed_by",
        "validated_by",
        "created_at",
    ]
    list_filter = [SourceFilter, KindFilter]
    search_fields = ["raw_value", "resolved_slug"]
    search_help_text = "Cherche sur : valeur saisie, slug résolu"
    readonly_fields = [
        "raw_value",
        "kind",
        "resolved_slug",
        "confidence",
        "source",
        "usage_count",
        "proposed_by",
        "validated_by",
        "validated_at",
        "created_at",
        "updated_at",
    ]
    actions = [validate_mappings, reject_mappings]
    ordering = ["-usage_count", "raw_value"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def confidence_display(self, obj):
        """Affiche le score de confiance en pourcentage."""
        return f"{obj.confidence * 100:.0f}%"

    confidence_display.short_description = "Confiance"
    confidence_display.admin_order_field = "confidence"
