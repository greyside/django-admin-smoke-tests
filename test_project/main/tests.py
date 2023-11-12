import warnings
from unittest.mock import patch

import django
from assert_element import AssertElementMixin
from categories.models import Category
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldError
from django.test import TestCase
from django.test.utils import override_settings
from model_bakery import baker

from django_admin_smoke_tests.tests import (
    AdminSiteSmokeTestMixin,
    ModelAdminCreationException,
)

from .admin import (
    ChannelAdmin,
    FailPostAdmin,
    ForbiddenPostAdmin,
    ListFilter,
    PostAdmin,
)
from .models import (
    Channel,
    ExceptionChannel,
    FailPost,
    ForbiddenPost,
    HasPrimarySlug,
    HasPrimaryUUID,
    Post,
    ProxyChannel,
    expected_exception,
)


User = get_user_model()


class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_apps = ["auth"]
    exclude_modeladmins = [FailPostAdmin, "ForbiddenPostAdmin"]
    only_modeladmins = [ChannelAdmin, PostAdmin]


class FailAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_modeladmins = [ForbiddenPostAdmin, PostAdmin, "test_project.ChannelAdmin"]

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
            with self.assertRaisesRegex(
                Exception, "This exception should be tested for"
            ):
                super().changelist_view_func(model, model_admin)
        else:
            super().changelist_view_func(model, model_admin)


class ForbiddenAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    strict_mode = True
    fixtures = []
    exclude_modeladmins = [FailPostAdmin, PostAdmin, ChannelAdmin]
    print_responses = True


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
                "file",
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
                ("custom_summary", admin.DateFieldListFilter),
                ListFilter,
            },
        )


class UnitTestMixin(AssertElementMixin, TestCase):
    def setUp(self):
        self.test_class = AdminSiteSmokeTest()
        self.test_class.setUp()
        self.test_class.client = self.client
        self.sites = admin.site._registry.items()

    def test_has_attr(self):
        self.assertTrue(
            self.test_class.has_attr(
                Channel(), Channel, dict(self.sites)[Channel], "slug"
            )
        )
        self.assertTrue(
            self.test_class.has_attr(Post(), Post, dict(self.sites)[Post], "title")
        )
        self.assertFalse(
            self.test_class.has_attr(
                Post(), Post, dict(self.sites)[Post], "nonexistent_field"
            )
        )
        self.assertFalse(
            self.test_class.has_attr(
                Post, Post, dict(self.sites)[Post], "nonexistent_field"
            )
        )
        self.assertFalse(
            self.test_class.has_attr(
                None, Post, dict(self.sites)[Post], "nonexistent_field"
            )
        )
        self.assertTrue(
            self.test_class.has_attr(
                Post(author_id=12345), Post, dict(self.sites)[Post], "author"
            )
        )

    def test_specified_fields_func(self):
        self.test_class.specified_fields_func(
            Channel, dict(self.sites)[Channel], baker.make("Channel")
        )
        self.test_class.specified_fields_func(
            Post, dict(self.sites)[Post], baker.make("Post")
        )

    def test_prepare_models(self):
        channels = self.test_class.prepare_models(Channel, ChannelAdmin)
        self.assertTrue(isinstance(channels[0], Channel))

    def test_prepare_models_failure(self):
        class MyAdminSiteSmokeTest(AdminSiteSmokeTest):
            recipes_prefix = "foo"

        test_class = MyAdminSiteSmokeTest()
        with self.assertWarnsRegex(
            Warning,
            "Not able to create test_project.main.models.ExceptionChannel data.",
        ):
            test_class.prepare_models(ExceptionChannel, ChannelAdmin)

    def test_prepare_models_error(self):
        class MyAdminSiteSmokeTest(AdminSiteSmokeTest):
            recipes_prefix = "foo"
            strict_mode = True

        test_class = MyAdminSiteSmokeTest()
        with self.assertRaisesRegex(
            ModelAdminCreationException,
            "Above exception occured while trying to create model "
            "test_project.main.models.ExceptionChannel data",
        ) as e:
            test_class.prepare_models(ExceptionChannel, ChannelAdmin)
        self.assertEquals(e.exception.original_exception, expected_exception)

    def test_prepare_models_recipe(self):
        class MyAdminSiteSmokeTest(AdminSiteSmokeTest):
            recipes_prefix = "test_project.main"

        test_class = MyAdminSiteSmokeTest()
        channels = test_class.prepare_models(Channel, ChannelAdmin)
        self.assertTrue(isinstance(channels[0], Channel))
        self.assertEquals(channels[0].text, "Created by recipe")

    def test_get_absolute_url(self):
        self.test_class.get_absolute_url_func(
            Channel, dict(self.sites)[Channel], baker.make("Channel")
        )
        self.test_class.get_absolute_url_func(
            Post, dict(self.sites)[Post], baker.make("Post")
        )

    def test_change_view_func(self):
        self.test_class.change_view_func(
            Channel, dict(self.sites)[Channel], baker.make("Channel")
        )
        with patch.dict(
            "os.environ", {"SMOKE_TESTS_PRINT_RESPONSES": "True"}
        ):  # Just to test the print_response env var
            self.test_class.change_view_func(
                Post, dict(self.sites)[Post], baker.make("Post")
            )

    def test_change_view_func_encode_url(self):
        """
        Test with UUID PK that doesn't encode well in URLs.
        The _5B sekvention makes problems if not correctly encoded.
        """
        has_primary_slug = baker.make(
            "HasPrimarySlug", pk="zk5TAeSTSeHY1PNmIaujuk_p7qxxS4ixkNGqC_5Bttfk81_0D6"
        )
        self.test_class.change_view_func(
            HasPrimarySlug,
            dict(self.sites)[HasPrimarySlug],
            has_primary_slug,
        )

    def test_change_post_func_exception(self):
        self.test_class.strict_mode = True
        with self.assertRaisesRegex(
            AssertionError,
            "No test_project.main.models.Channel data created to test main.ChannelAdmin.",
        ):
            self.test_class.change_post_func(Channel, dict(self.sites)[Channel])

    def test_change_post_func(self):
        channel = baker.make("Channel", title="Foo title")
        response = self.test_class.change_post_func(
            Channel, dict(self.sites)[Channel], channel
        )
        self.assertElementContains(
            response,
            "input[id=id_title]",
            '<input type="text" name="title" value="Foo title" class="vTextField" '
            'maxlength="140" required="" id="id_title">',
        )

        post = baker.make("Post", title="Foo post", author_id=123456)
        response = self.test_class.change_post_func(Post, dict(self.sites)[Post], post)
        self.assertElementContains(
            response,
            "input[id=id_title]",
            '<input type="text" name="title" value="Foo post" class="vTextField" '
            'maxlength="140" required="" id="id_title">',
        )
        post.delete()  # to prevent error during tearDown

    @override_settings(MPTT_ALLOW_TESTING_GENERATORS=True)
    def test_changelist_view_search_func_no_site_header(self):
        """
        Test that site_header defaults correctly
        The django-categories has for some reason empty context_data but the H1
        we are testing for still has to defaults to "Django administration".
        """
        baker.make("Category", name="Foo title")
        response = self.test_class.changelist_view_search_func(
            Category, dict(self.sites)[Category]
        )
        with open("response.html", "w") as f:
            f.write(response.content.decode("utf-8"))
        self.assertEquals(hasattr(response, "context_data"), False)
        autofocus_string = "" if django.VERSION >= (4, 2) else ' autofocus=""'
        self.assertElementContains(
            response,
            "input[id=searchbar]",
            f'<input type="text" size="40" name="q" value="test" id="searchbar" {autofocus_string}>',
        )
        self.assertElementContains(
            response,
            "h1[id=site-name]",
            '<h1 id="site-name"><a href="/admin/">Django administration</a></h1>',
        )

    def test_change_post_func_encode_url(self):
        """
        Test with UUID PK that doesn't encode well in URLs.
        The _5B sekvention makes problems if not correctly encoded.
        """
        has_primary_slug = baker.make(
            "HasPrimarySlug", pk="zk5TAeSTSeHY1PNmIaujuk_p7qxxS4ixkNGqC_5Bttfk81_0D6"
        )
        self.test_class.change_post_func(
            HasPrimarySlug,
            dict(self.sites)[HasPrimarySlug],
            has_primary_slug,
        )

    def test_changelist_filters_view_func(self):
        self.test_class.changelist_filters_view_func(Channel, dict(self.sites)[Channel])
        baker.make("Post", title="Foo post")
        self.test_class.changelist_filters_view_func(Post, dict(self.sites)[Post])

        class FooFilter:
            pass

        class MyPostAdmin(PostAdmin):
            list_filter = (FooFilter,)

        with self.assertRaisesRegex(
            Exception,
            "Unknown filter type: <class "
            "'test_project.main.tests.UnitTestMixin.test_changelist_filters_view_func.<locals>.FooFilter'>",
        ):
            self.test_class.changelist_filters_view_func(
                Post, MyPostAdmin(Post, self.sites)
            )

    def test_get_instance(self):
        channel = baker.make("Channel")
        self.assertEquals(
            self.test_class.get_instance(Channel, dict(self.sites)[Channel]),
            channel,
        )

    def test_get_instance_superuser(self):
        self.assertEquals(
            self.test_class.get_instance(User, dict(self.sites)[User]),
            None,
        )


class UnitTestMixinNoInstances(TestCase):
    maxDiff = None

    def setUp(self):
        self.sites = admin.site._registry.items()

        class MyAdminSiteSmokeTest(AdminSiteSmokeTest):
            modeladmins = []
            superuser_username = "superuser1"
            only_modeladmins = [ChannelAdmin, "PostAdmin"]

            def prepare_models(self, model, model_admin, quantity=1):
                return

        self.test_class = MyAdminSiteSmokeTest()
        self.test_class.setUp()

    def test_get_absolute_url(self):
        self.test_class.get_absolute_url_func(Channel, dict(self.sites)[Channel])
        self.test_class.get_absolute_url_func(Post, dict(self.sites)[Post])

    def test_specified_fields_func(self):
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Channel data created to test main.ChannelAdmin.",
        ):
            self.test_class.specified_fields_func(Channel, dict(self.sites)[Channel])
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Post data created to test main.PostAdmin.",
        ):
            self.test_class.specified_fields_func(Post, dict(self.sites)[Post])

    def test_change_view_func(self):
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Channel data created to test main.ChannelAdmin.",
        ):
            self.test_class.change_view_func(Channel, dict(self.sites)[Channel])
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Post data created to test main.PostAdmin.",
        ):
            self.test_class.change_view_func(Post, dict(self.sites)[Post])

    def test_change_post_func(self):
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Channel data created to test main.ChannelAdmin.",
        ):
            self.test_class.change_post_func(Channel, dict(self.sites)[Channel])
        with warnings.catch_warnings(record=True) as w:
            self.test_class.change_post_func(ProxyChannel, dict(self.sites)[Channel])
            self.assertEqual(w, [])
        with self.assertWarnsRegex(
            Warning,
            "No test_project.main.models.Post data created to test main.PostAdmin.",
        ):
            self.test_class.change_post_func(Post, dict(self.sites)[Post])

    def test_get_modeladmins(self):
        class OnlySmokeTest(AdminSiteSmokeTestMixin, TestCase):
            only_apps = ["main", "foo_app"]
            only_modeladmins = ["foo_modeladmin", PostAdmin]

        with warnings.catch_warnings(record=True) as w:
            OnlySmokeTest().get_modeladmins()
            self.assertEqual(len(w), 2)
            self.assertEqual(
                str(w[0].message),
                "Not all apps in only_apps were found, using only apps ['foo_app']",
            )
            self.assertEqual(
                str(w[1].message),
                "Not all modeladmins in only_modeladmins were found, "
                "using only modeladmin ['foo_modeladmin']",
            )
        modeladmins = OnlySmokeTest.get_modeladmins()
        self.assertEqual(len(modeladmins), 6)
        print(modeladmins)
        model_list = list(zip(*modeladmins))[0]
        self.assertSetEqual(
            set(model_list),
            {Channel, Post, FailPost, ForbiddenPost, HasPrimarySlug, HasPrimaryUUID},
        )
