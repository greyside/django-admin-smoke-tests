# Django imports
from django.contrib import admin
import django

# App imports
from .models import Channel, HasPrimarySlug, HasPrimaryUUID, Post, FailPost


class ChannelAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}

admin.site.register(Channel, ChannelAdmin)


class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ['status']
    list_display = ('title', 'author', 'status', 'modified', 'published',)
    list_filter = ('author', 'status', 'channel', 'created', 'modified',
        'published',)
    readonly_fields = ['created', 'modified', 'time_diff']
    ordering = ('title', '-id',)

    search_fields = ['title', 'text']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'author':
            db_field.default = request.user
        return super(PostAdmin, self).formfield_for_foreignkey(db_field,
            request, **kwargs)


class FailPostAdmin(admin.ModelAdmin):
    search_fields = ['nonexistent_field']

    if django.VERSION >= (1, 8):
        list_display = ['nonexistent_field']

    def has_add_permission(self, request):
        False


admin.site.register(Post, PostAdmin)
admin.site.register(FailPost, FailPostAdmin)


admin.site.register(HasPrimarySlug)


if HasPrimaryUUID:
    admin.site.register(HasPrimaryUUID)
