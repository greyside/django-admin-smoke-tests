from django.contrib import admin
from django.core.exceptions import FieldError
from django.test import TestCase

from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

from .admin import (
    ChannelAdmin,
    FailPostAdmin,
    ForbiddenPostAdmin,
    ListFilter,
    PostAdmin,
)
from .models import Channel, FailPost, Post


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
                "False is not true : Field 'nonexistent_field' not found on "
                "test_project.main.models.FailPost \\(main.FailPostAdmin\\)",
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


class UnitTest(TestCase):
    maxDiff = None

    def test_strip(self):
        mixin = AdminSiteSmokeTestMixin()
        self.assertEqual(mixin.strip("search_fields", "scene"), "scene")
        self.assertEqual(mixin.strip("search_fields", "^scene"), "scene")
        self.assertEqual(mixin.strip("search_fields", "@scene"), "scene")
        self.assertEqual(mixin.strip("search_fields", "=scene"), "scene")
        self.assertEqual(mixin.strip("ordering", "scene"), "scene")
        self.assertEqual(mixin.strip("ordering", "-scene"), "scene")
        self.assertEqual(mixin.strip("foo", "-scene"), "-scene")

    def test_get_attr_set(self):
        from django_admin_smoke_tests.tests import (
            AdminSiteSmokeTest as OrigAdminSiteSmokeTest,
        )

        test_class = OrigAdminSiteSmokeTest()
        test_class.setUp()
        sites = admin.site._registry.items()
        self.assertSetEqual(
            test_class.get_attr_set(Channel, dict(sites)[Channel]),
            {
                "__str__",
                "slug",
                "title",
                "text",
                "rendered_text",
                "followers",
                "public",
                "enrollment",
                "forbidden_posts__title",
                "post__title",
            },
        )
        self.assertSetEqual(
            test_class.get_attr_set(Post, dict(sites)[Post]),
            {
                "time_diff",
                "author",
                "status",
                "id",
                "created",
                "modified",
                "channel",
                "text",
                "title",
                "slug",
                "published",
                "channel__followers__first_name",
                "author__first_name",
                ListFilter,
            },
        )

    def test_specified_fields_func(self):
        test_class = AdminSiteSmokeTest()
        test_class.setUp()
        sites = admin.site._registry.items()
        test_class.specified_fields_func(Channel, dict(sites)[Channel])
        test_class.specified_fields_func(Post, dict(sites)[Post])
