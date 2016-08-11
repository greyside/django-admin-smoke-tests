from .admin import FailPostAdmin
from django.test import TestCase
from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin,\
    ModelAdminCheckException, for_all_model_admins


class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    exclude_apps = ['auth']
    exclude_modeladmins = [FailPostAdmin]


class FailAdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    @for_all_model_admins
    def test_specified_fields(self, model, model_admin):
        with self.assertRaises(ModelAdminCheckException):
            super().test_specified_fields()

    @for_all_model_admins
    def test_changelist_view_search(self, model, model_admin):
        with self.assertRaises(ModelAdminCheckException):
            super().test_changelist_view_search()

    @for_all_model_admins
    def test_changelist_view(self, model, model_admin):
        with self.assertRaises(ModelAdminCheckException):
            super().test_changelist_view()
