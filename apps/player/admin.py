from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import WatchHistory


@admin.register(WatchHistory)
class WatchHistoryAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'movie',
        'progress_display',
        'completed',
        'last_watched'
    )

    list_filter = (
        'completed',
        'last_watched',
        'created_at'
    )

    search_fields = (
        'user__username',
        'user__email',
        'movie__title'
    )

    readonly_fields = ('created_at', 'last_watched')

    ordering = ('-last_watched',)

    date_hierarchy = 'last_watched'

    fieldsets = (
        (None, {
            'fields': ('user', 'movie')
        }),
        (_('Progress'), {
            'fields': ('progress', 'duration', 'completed')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'last_watched'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'movie')

    def progress_display(self, obj):
        return f"{obj.get_progress_percentage()}%"

    progress_display.short_description = _('Progress')
