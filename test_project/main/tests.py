from django.core.exceptions import FieldError
from django.test import TestCase

from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

from .admin import ChannelAdmin, FailPostAdmin, ForbiddenPostAdmin, PostAdmin
from .models import Channel, FailPost


class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_apps = ["auth"]
    exclude_modeladmins = [FailPostAdmin, ForbiddenPostAdmin]


class FailAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_modeladmins = [ForbiddenPostAdmin, PostAdmin, ChannelAdmin]

    def setUp(self):
        FailPost.objects.create(
            channel=Channel.objects.create(),
            author_id=1,
        )
        super(FailAdminSiteSmokeTest, self).setUp()

    def specified_fields_func(self, model, model_admin):
        if model_admin.__class__ == FailPostAdmin:
            with self.assertRaisesRegex(
                AssertionError,
                "False is not true : nonexistent_field not found on "
                "<class 'test_project.main.models.FailPost'> \\(main.FailPostAdmin\\)",
            ):
                super().specified_fields_func(model, model_admin)
        else:
            super().specified_fields_func(model, model_admin)

    def changelist_view_search_func(self, model, model_admin):
        if model_admin.__class__ == FailPostAdmin:
            with self.assertRaisesRegex(
                FieldError,
                "Cannot resolve keyword 'nonexistent_field' into field. Choices are: author.*",
            ):
                super().changelist_view_search_func(model, model_admin)
        else:
            super().changelist_view_search_func(model, model_admin)

    def changelist_view_func(self, model, model_admin):
        if model_admin.__class__ == FailPostAdmin:
            with self.assertRaisesRegex(Exception, ""):
                super().changelist_view_func(model, model_admin)
        else:
            super().changelist_view_func(model, model_admin)


class ForbiddenAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_modeladmins = [FailPostAdmin, PostAdmin, ChannelAdmin]
