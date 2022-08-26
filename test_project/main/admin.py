# Django imports
from django.contrib import admin
from django.contrib.admin import SimpleListFilter

# App imports
from .models import (
    Channel,
    FailPost,
    ForbiddenPost,
    HasPrimarySlug,
    HasPrimaryUUID,
    Post,
)


class ChannelAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}

    search_fields = ["title", "slug", "=text", "post__title", "forbidden_posts__title"]


admin.site.register(Channel, ChannelAdmin)


class ListFilter(SimpleListFilter):
    title = "list_filter"
    parameter_name = "list_filter"

    def __init__(self, request, params, model, model_admin):
        super(ListFilter, self).__init__(request, params, model, model_admin)
        self.lookup_val = request.GET.getlist("a")

    def lookups(self, request, model_admin):
        return ()

    def queryset(self, request, queryset):
        return queryset


class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ["status"]
    list_display = (
        "title",
        "author",
        "status",
        "modified",
        "published",
    )
    list_filter = (
        "author",
        "status",
        "channel",
        "created",
        "modified",
        "published",
        ("custom_summary", admin.DateFieldListFilter),
        ListFilter,
    )
    readonly_fields = ["created", "modified", "time_diff"]
    ordering = (
        "title",
        "-id",
    )
    fieldsets = [
        ("Fielset", {"fields": ["created", ("slug", "title", "author", "status")]}),
    ]
    date_hierarchy = "created"

    search_fields = [
        "title",
        "text",
        "^author__first_name",
        "=channel__followers__first_name",
    ]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            db_field.default = request.user
        return super(PostAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs
        )


class FailPostAdmin(admin.ModelAdmin):
    """Admin, that should fail if it is not excluded from the smoke tests"""

    search_fields = ["nonexistent_field"]
    list_display = ["fail_field"]

    def fail_field(self, obj):
        raise Exception("This exception should be tested for")


class ForbiddenPostAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        False

    def has_change_permission(self, request, obj=None):
        False

    def has_delete_permission(self, request, obj=None):
        False

    def has_view_permission(self, request, obj=None):
        False


admin.site.register(Post, PostAdmin)
admin.site.register(FailPost, FailPostAdmin)
admin.site.register(ForbiddenPost, ForbiddenPostAdmin)


admin.site.register(HasPrimarySlug)


if HasPrimaryUUID:
    admin.site.register(HasPrimaryUUID)
