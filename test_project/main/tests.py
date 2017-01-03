import django

from django.test import TestCase

from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin,\
    ModelAdminCheckException, for_all_model_admins
from .admin import ChannelAdmin, FailPostAdmin, ForbiddenPostAdmin, PostAdmin


class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_apps = ['auth']
    exclude_modeladmins = [FailPostAdmin, ForbiddenPostAdmin]


class FailAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_modeladmins = [ForbiddenPostAdmin, PostAdmin, ChannelAdmin]

    @for_all_model_admins
    def test_specified_fields(self, model, model_admin):
        with self.assertRaises(ModelAdminCheckException):
            super(FailAdminSiteSmokeTest, self).test_specified_fields()

    @for_all_model_admins
    def test_changelist_view_search(self, model, model_admin):
        with self.assertRaises(ModelAdminCheckException):
            super(FailAdminSiteSmokeTest, self).test_changelist_view_search()

    if django.VERSION >= (1, 8):
        @for_all_model_admins
        def test_changelist_view(self, model, model_admin):
            with self.assertRaises(ModelAdminCheckException):
                super(FailAdminSiteSmokeTest, self).test_changelist_view()


class ForbiddenAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    fixtures = []
    exclude_modeladmins = [FailPostAdmin, PostAdmin, ChannelAdmin]
