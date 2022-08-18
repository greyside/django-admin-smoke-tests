import logging
from typing import List

import django
from django.contrib import admin, auth
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import transaction
from django.http.request import QueryDict
from django.test import TestCase
from django.test.client import RequestFactory
from model_bakery import baker


logger = logging.getLogger(__name__)


def model_path(model):
    return f"{model.__module__}.{model.__name__}"


def for_all_model_admins(fn):
    def test_deco(self):
        modeladmins = self.get_modeladmins()
        for model, model_admin in modeladmins:
            with self.subTest(f"{model_path(model)} {model_admin}"):
                fn(self, model, model_admin)

    return test_deco


def format_exception(e):
    return str(e).replace("\\n", "\\n\\t")


class AdminSiteSmokeTestMixin(object):
    modeladmins = None
    exclude_apps: List[str] = []
    exclude_modeladmins: List[str] = []
    fixtures = ["django_admin_smoke_tests"]

    single_attributes = ["date_hierarchy"]
    iter_attributes = [
        "filter_horizontal",
        "filter_vertical",
        "list_display",
        "list_display_links",
        "list_editable",
        "list_filter",
        "readonly_fields",
        "search_fields",
    ]
    iter_or_falsy_attributes = [
        "exclude",
        "fields",
        "ordering",
    ]

    strip_minus_attrs = ("ordering",)

    def get_modeladmins(self):
        if not self.modeladmins:
            modeladmins = admin.site._registry.items()
        else:
            modeladmins = self.modeladmins

        modeladmins = [
            (model, model_admin)
            for (model, model_admin) in modeladmins
            if (
                model_admin.__class__ not in self.exclude_modeladmins
                and model._meta.app_label not in self.exclude_apps
            )
        ]
        return modeladmins

    def create_superuser(self):
        return auth.get_user_model().objects.create_superuser(
            "testuser", "testuser@example.com", "foo"
        )

    def setUp(self):
        super().setUp()

        self.superuser = self.create_superuser()

        self.factory = RequestFactory()

        admin.autodiscover()

    def get_request(self, params=None):
        request = self.factory.get("/", params)

        request.user = self.superuser
        return request

    def create_models(self, model, model_admin, view_string, quantity=1):
        if quantity == 1:
            return baker.make(model)
        return baker.make(model, _quantity=quantity)

    def prepare_models(self, model, model_admin, view_string, quantity=1):
        try:
            return self.create_models(model, model_admin, view_string, quantity)
        except Exception as e:
            print(f"Not able to create {model} data for {view_string}:")
            print("\t%s" % str(e).replace("\n", "\n\t"))

    def post_request(self, post_data={}, params=None):
        request = self.factory.post("/", params, post_data=post_data)

        request.user = self.superuser
        request._dont_enforce_csrf_checks = True
        return request

    def strip_minus(self, attr, val):
        if attr in self.strip_minus_attrs and val[0] == "-":
            val = val[1:]
        return val

    def get_fieldsets(self, model, model_admin):
        request = self.get_request()
        return model_admin.get_fieldsets(request, obj=model())

    def get_attr_set(self, model, model_admin):
        attr_set = []

        for attr in self.iter_attributes:
            attr_set += [self.strip_minus(attr, a) for a in getattr(model_admin, attr)]

        for attr in self.iter_or_falsy_attributes:
            attrs = getattr(model_admin, attr, None)

            if isinstance(attrs, list) or isinstance(attrs, tuple):
                attr_set += [self.strip_minus(attr, a) for a in attrs]

        for fieldset in self.get_fieldsets(model, model_admin):
            for attr in fieldset[1]["fields"]:
                if isinstance(attr, list) or isinstance(attr, tuple):
                    attr_set += [self.strip_minus(fieldset, a) for a in attr]
                else:
                    attr_set.append(attr)

        attr_set = set(attr_set)

        for attr in self.single_attributes:
            val = getattr(model_admin, attr, None)

            if val:
                attr_set.add(self.strip_minus(attr, val))

        return attr_set

    @for_all_model_admins
    def test_specified_fields(self, model, model_admin):
        self.specified_fields_func(model, model_admin)

    def specified_fields_func(self, model, model_admin):
        attr_set = self.get_attr_set(model, model_admin)

        # FIXME: not all attributes can be used everywhere (e.g. you can't
        # use list_filter with a form field). This will have to be fixed
        # later.
        model_field_names = frozenset(model._meta.get_fields())
        form_field_names = frozenset(getattr(model_admin.form, "base_fields", []))

        model_instance = baker.make(model)

        for attr in attr_set:
            # for now we'll just check attributes, not strings
            if not isinstance(attr, str):
                continue

            # don't split attributes that start with underscores (such as
            # __str__)
            if attr[0] != "_":
                attr = attr.split("__")[0]

            has_model_field = attr in model_field_names
            has_form_field = attr in form_field_names
            has_model_class_attr = hasattr(model_instance.__class__, attr)
            has_admin_attr = hasattr(model_admin, attr)

            try:
                has_model_attr = hasattr(model_instance, attr)
            except (ValueError, ObjectDoesNotExist):
                has_model_attr = attr in model_instance.__dict__

            has_field_or_attr = (
                has_model_field
                or has_form_field
                or has_model_attr
                or has_admin_attr
                or has_model_class_attr
            )

            self.assertTrue(
                has_field_or_attr, f"{attr} not found on {model} ({model_admin})"
            )

    @for_all_model_admins
    def test_queryset(self, model, model_admin):
        self.queryset_func(model, model_admin)

    def queryset_func(self, model, model_admin):
        request = self.get_request()

        with transaction.atomic():
            self.prepare_models(model, model_admin, "queryset tests", quantity=5)

        # make sure no errors happen here
        if hasattr(model_admin, "get_queryset"):
            list(model_admin.get_queryset(request))

    @for_all_model_admins
    def test_get_absolute_url(self, model, model_admin):
        self.get_absolute_url_func(model, model_admin)

    def get_absolute_url_func(self, model, model_admin):
        if hasattr(model, "get_absolute_url"):
            # Use fixture data if it exists
            instance = model.objects.first()
            # Otherwise create a minimal instance
            if not instance:
                instance = model(pk=1)
            # make sure no errors happen here
            instance.get_absolute_url()

    @for_all_model_admins
    def test_changelist_view(self, model, model_admin):
        self.changelist_view_func(model, model_admin)

    def changelist_view_func(self, model, model_admin):
        request = self.get_request()

        with transaction.atomic():
            self.prepare_models(model, model_admin, "changelist view", quantity=5)

        # make sure no errors happen here
        try:
            response = model_admin.changelist_view(request)
            response.render()
            self.assertIn(response.status_code, [200, 302])
        except PermissionDenied as e:
            # this error is commonly raised by ModelAdmins that don't allow
            # changelist view
            logging.exception(
                e,
                f"PermissionDenied for {model_admin} on  {model_path(model)}, skipping smoke test",
            )

    @for_all_model_admins
    def test_changelist_view_search(self, model, model_admin):
        self.changelist_view_search_func(model, model_admin)

    def changelist_view_search_func(self, model, model_admin):
        request = self.get_request(params=QueryDict("q=test"))

        # make sure no errors happen here
        try:
            response = model_admin.changelist_view(request)
            response.render()
            self.assertIn(response.status_code, [200, 302])
        except PermissionDenied as e:
            # this error is commonly raised by ModelAdmins that don't allow
            # changelist view.
            logging.exception(
                e,
                f"PermissionDenied for {model_admin} on  {model_path(model)}, skipping smoke test",
            )

    @for_all_model_admins
    def test_add_view(self, model, model_admin):
        self.add_view_func(model, model_admin)

    def add_view_func(self, model, model_admin):
        request = self.get_request()

        # make sure no errors happen here
        try:
            response = model_admin.add_view(request)
            if isinstance(response, django.template.response.TemplateResponse):
                response.render()
            self.assertIn(response.status_code, [200, 302])
        except PermissionDenied as e:
            # this error is commonly raised by ModelAdmins that don't allow
            # adding.
            logging.exception(
                e,
                f"PermissionDenied for {model_admin} on  {model_path(model)}, skipping smoke test",
            )

    @for_all_model_admins
    def test_change_view(self, model, model_admin):
        self.change_view_func(model, model_admin)

    def change_view_func(self, model, model_admin):
        item = model.objects.last()
        if not item or model._meta.proxy:
            return
        pk = item.pk
        request = self.get_request()

        # make sure no errors happen here
        response = model_admin.change_view(request, object_id=str(pk))
        if isinstance(response, django.template.response.TemplateResponse):
            response.render()
        self.assertIn(response.status_code, [200, 302])

    @for_all_model_admins
    def test_change_post(self, model, model_admin):
        self.change_post_func(model, model_admin)

    def change_post_func(self, model, model_admin):
        item = model.objects.last()
        if not item:
            with transaction.atomic():
                item = self.prepare_models(model, model_admin, "change post view")
                if item is None:
                    return
        if model._meta.proxy:
            return
        pk = item.pk
        request = self.post_request()
        try:
            response = model_admin.change_view(request, object_id=str(pk))
            if isinstance(response, django.template.response.TemplateResponse):
                response.render()
            self.assertIn(response.status_code, [200, 302])

        except ValidationError as e:
            # This the form was sent, but did not pass it's validation
            logging.exception(
                e,
                f"Validation error for {model_admin} on  {model_path(model)}, skipping smoke test",
            )
        except PermissionDenied as e:
            # This error is commonly raised by ModelAdmin if the user doesn't have
            # permission to change the object
            logging.exception(
                e,
                f"PermissionDenied was encountered for {model_admin} on {model_path(model)}.",
            )


class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    pass
