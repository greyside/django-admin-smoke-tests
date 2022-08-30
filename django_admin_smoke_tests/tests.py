import logging
import os
import warnings
from typing import List

from assert_element import AssertElementMixin
from django.contrib import admin, auth
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.utils import quote
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model
from django.db.models.fields.files import FieldFile
from django.http.request import QueryDict
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from model_bakery import baker

from django_admin_smoke_tests import baker_field_generators  # noqa


logger = logging.getLogger(__name__)


def model_path(model):
    return f"{model.__module__}.{model.__name__}"


def match_class(cls, data):
    return (
        cls.__name__ in data
        or model_path(cls) in data
        or cls in data
        or cls.__class__ in data
    )


def for_all_model_admins(fn):
    def test_deco(self):
        modeladmins = self.get_modeladmins()
        for model, model_admin in modeladmins:
            with self.subTest(f"{model_path(model)} {model_admin}"):
                fn(self, model, model_admin)

    return test_deco


def form_data(form, instance):
    data = {}
    for field in form.base_fields:
        try:
            value = getattr(instance, field, None)
        except ObjectDoesNotExist:
            value = None
        if isinstance(value, FieldFile):
            pass
        elif isinstance(value, Model):
            data[field] = value.pk
        elif value is not None:
            data[field] = value
    return data


class ModelAdminCreationException(Exception):
    def __init__(self, message, original_exception):
        self.original_exception = original_exception
        return super().__init__(message)


class AdminSiteSmokeTestMixin(AssertElementMixin):
    modeladmins = None
    exclude_apps: List[str] = []
    exclude_modeladmins: List[str] = []
    recipes_prefix = None
    strict_mode = False
    print_responses = False

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

    @classmethod
    def get_modeladmins(cls):
        modeladmins = cls.modeladmins or admin.site._registry.items()

        modeladmins = [
            (model, model_admin)
            for (model, model_admin) in modeladmins
            if (
                not match_class(model_admin.__class__, cls.exclude_modeladmins)
                and model._meta.app_label not in cls.exclude_apps
            )
        ]

        only_modeladmins = getattr(cls, "only_modeladmins", [])
        only_apps = getattr(cls, "only_apps", [])
        if only_modeladmins != [] or only_apps != []:
            modeladmins = [
                (model, model_admin)
                for (model, model_admin) in modeladmins
                if match_class(model_admin.__class__, only_modeladmins)
                or model._meta.app_label in only_apps
            ]

            missing_apps = []
            for app in only_apps:
                if not any(app == m._meta.app_label for m, _ in modeladmins):
                    missing_apps.append(app)
            if missing_apps:
                warnings.warn(
                    "Not all apps in only_apps were found, "
                    f"using only apps {missing_apps}",
                    UserWarning,
                )

            missing_modeladmins = []
            for model_admin in only_modeladmins:
                if not any(
                    match_class(m.__class__, [model_admin]) for _, m in modeladmins
                ):
                    missing_modeladmins.append(model_admin)
            if missing_modeladmins:
                warnings.warn(
                    "Not all modeladmins in only_modeladmins were found, "
                    f"using only modeladmin {missing_modeladmins}",
                    UserWarning,
                )

        return modeladmins

    def create_superuser(self):
        try:
            return auth.get_user_model().objects.get(username="superuser")
        except ObjectDoesNotExist:
            return auth.get_user_model().objects.create_superuser(
                "superuser", "testuser@example.com", "foo"
            )

    @classmethod
    def setUpTestData(cls):
        """Load initial data for the TestCase"""
        cls.prepare_all_models()

    def does_print_responses(self):
        yes_answers = ("y", "yes", "t", "true", "on", "1")
        if os.environ.get("SMOKE_TESTS_PRINT_RESPONSES", "0").lower() in yes_answers:
            return True
        return self.print_responses

    def print_response(self, response, model, model_admin, view_name):
        if self.does_print_responses():
            with open(
                f"response_{model.__name__ if model else ''}_{model_admin}_{view_name}.html",
                "w",
            ) as f:
                f.write(response.content.decode("utf-8"))

    def setUp(self):
        super().setUp()

        self.superuser = self.create_superuser()

        self.factory = RequestFactory()

        admin.autodiscover()

    def get_url(self, model, model_admin):
        return "/"

    def get_request(self, model, model_admin, params=None):
        request = self.factory.get(self.get_url(model, model_admin), params)
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        setattr(request, "_messages", FallbackStorage(request))

        request.user = self.superuser
        return request

    @classmethod
    def create_models(cls, model, model_admin, quantity=1):
        """Create models with model_bakery"""
        basic_options = {
            "_quantity": quantity,
            "_create_files": True,
            "_refresh_after_create": True,
        }

        options_list = []
        if cls.recipes_prefix:
            options_list += [
                (
                    "make_recipe",
                    (f"{cls.recipes_prefix}.{model.__name__}",),
                    {**basic_options, "_fill_optional": True},
                ),
                (
                    "make_recipe",
                    (f"{cls.recipes_prefix}.{model.__name__}",),
                    basic_options,
                ),
            ]
        options_list += [
            ("make", (model,), {**basic_options, "_fill_optional": True}),
            ("make", (model,), basic_options),
        ]

        for function_name, args, kwargs in options_list:
            try:
                models = getattr(baker, function_name)(*args, **kwargs)
                return models
            except (AttributeError, TypeError, ValueError):
                pass
        return baker.make(model)  # Last try, will let the errors propagate

    @classmethod
    def prepare_models(cls, model, model_admin, quantity=1):
        """Prepare models by model_bakery, if it is not possible, return None"""
        with override_settings(MPTT_ALLOW_TESTING_GENERATORS=True):
            try:
                return cls.create_models(model, model_admin, quantity)
            except Exception as e:
                warning_string = f"Not able to create {model_path(model)} data for {model_admin} creation."
                logging.exception(e, warning_string)
                warnings.warn(warning_string)
                if cls.strict_mode:
                    raise ModelAdminCreationException(
                        "Above exception occured while trying to create model "
                        f"{model_path(model)} data for {model_admin} ModelAdmin.",
                        e,
                    ) from e

    @classmethod
    def prepare_all_models(cls):
        """Prepare all models for all modeladmins"""
        for model, model_admin in cls.get_modeladmins():
            cls.prepare_models(model, model_admin, quantity=5)

    def post_request(self, model, model_admin, post_data={}, **params):
        request = self.factory.post(
            self.get_url(model, model_admin), post_data, **params
        )
        middleware = SessionMiddleware(request)
        middleware.process_request(request)
        setattr(request, "_messages", FallbackStorage(request))

        request.user = self.superuser
        request._dont_enforce_csrf_checks = True
        return request

    def strip(self, attr, val):
        if attr in self.strip_minus_attrs and val[0] == "-":
            val = val[1:]

        if attr == "search_fields":
            for ch in ["^", "=", "@"]:
                val = val.lstrip(ch)
        return val

    def get_fieldsets(self, model, model_admin):
        request = self.get_request(model, model_admin)
        return model_admin.get_fieldsets(request, obj=model())

    def get_attr_set(self, model, model_admin):
        attr_set = []

        for attr in self.iter_attributes:
            attr_set += [self.strip(attr, a) for a in getattr(model_admin, attr)]

        for attr in self.iter_or_falsy_attributes:
            attrs = getattr(model_admin, attr, None)

            if isinstance(attrs, list) or isinstance(attrs, tuple):
                attr_set += [self.strip(attr, a) for a in attrs]

        for fieldset in self.get_fieldsets(model, model_admin):
            for attr in fieldset[1]["fields"]:
                if isinstance(attr, list) or isinstance(attr, tuple):
                    attr_set += [self.strip(fieldset, a) for a in attr]
                else:
                    attr_set.append(attr)

        attr_set = set(attr_set)

        for attr in self.single_attributes:
            val = getattr(model_admin, attr, None)

            if val:
                attr_set.add(self.strip(attr, val))

        return attr_set

    def has_attr(self, model_instance, model, model_admin, attr):
        # FIXME: not all attributes can be used everywhere (e.g. you can't
        # use list_filter with a form field). This will have to be fixed
        # later.
        model_field_names = frozenset(model._meta.get_fields())
        form_field_names = frozenset(getattr(model_admin.form, "base_fields", []))

        has_model_field = attr in model_field_names
        has_form_field = attr in form_field_names
        has_model_class_attr = hasattr(model_instance.__class__, attr)
        has_admin_attr = hasattr(model_admin, attr)

        try:
            has_model_attr = hasattr(model_instance, attr)
        except (ValueError, ObjectDoesNotExist):
            has_model_attr = attr in model_instance.__dict__

        return (
            has_model_field
            or has_form_field
            or has_model_attr
            or has_admin_attr
            or has_model_class_attr
        )

    @for_all_model_admins
    def test_specified_fields(self, model, model_admin):
        self.specified_fields_func(model, model_admin)

    def specified_fields_func(self, model, model_admin, instance=None):
        attr_set = self.get_attr_set(model, model_admin)

        if not instance:
            instance = self.get_instance(model, model_admin)
        if not instance:
            return

        for attr in attr_set:
            # for now we'll just check attributes, not strings
            if not isinstance(attr, str):
                continue

            # don't split attributes that start with underscores (such as
            # __str__)
            if attr[0] != "_":
                attr = attr.split("__")[0]

            attr_variants = [attr, f"{attr}_set"]
            self.assertTrue(
                any(
                    self.has_attr(instance, model, model_admin, att)
                    for att in attr_variants
                ),
                f"Field '{attr}' not found on {model_path(model)} ({model_admin})",
            )

    @for_all_model_admins
    def test_queryset(self, model, model_admin):
        self.queryset_func(model, model_admin)

    def queryset_func(self, model, model_admin):
        request = self.get_request(model, model_admin)

        # make sure no errors happen here
        if hasattr(model_admin, "get_queryset"):
            list(model_admin.get_queryset(request))

    @for_all_model_admins
    def test_get_absolute_url(self, model, model_admin):
        self.get_absolute_url_func(model, model_admin)

    def get_absolute_url_func(self, model, model_admin, instance=None):
        if hasattr(model, "get_absolute_url"):
            # Use fixture data if it exists
            if not instance:
                instance = self.get_instance(model, model_admin, warn=False)
            # Otherwise create a minimal instance
            if not instance:
                instance = model(pk=1)
            # make sure no errors happen here
            instance.get_absolute_url()

    @for_all_model_admins
    def test_changelist_view(self, model, model_admin):
        self.changelist_view_func(model, model_admin)

    def changelist_view_func(self, model, model_admin):
        """Run the changelist_view method on the model admin."""
        request = self.get_request(model, model_admin)

        self.client.force_login(self.superuser)
        if not hasattr(
            model_admin, "has_view_permission"  # Django <= 2.0
        ) or model_admin.has_view_permission(request):
            # make sure no errors happen here
            url = reverse(
                f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
            )
            response = self.client.get(url, follow=True)

            self.changelist_view_asserts(model, model_admin, response, "changelist")
            return response

    def changelist_view_asserts(self, model, model_admin, response, view_name):
        if view_name is not None:
            self.print_response(response, model, model_admin, view_name)
        self.assertIn(response.status_code, [200])
        self.assertElementContains(
            response,
            "h1[id=site-name]",
            f"<h1 id='site-name'><a href='{reverse('admin:index')}'>"
            f"{response.context_data['site_header']}"
            "</a></h1>",
        )
        self.assertElementContains(
            response,
            "div[id=content] h1",
            f"<h1>Select {model._meta.verbose_name} to change</h1>",
        )

    @for_all_model_admins
    def test_changelist_filters_view(self, model, model_admin):
        """Try to get various values for list_filter and call the view with them"""
        self.changelist_filters_view_func(model, model_admin)

    def changelist_filters_view_func(self, model, model_admin):
        request = self.get_request(model, model_admin)

        self.client.force_login(self.superuser)
        if not hasattr(
            model_admin, "has_view_permission"  # Django <= 2.0
        ) or model_admin.has_view_permission(request):
            for filter in model_admin.list_filter:
                if isinstance(filter, tuple):
                    filter = filter[0]
                if isinstance(filter, str):
                    key = filter
                    value = model.objects.values(filter).first()[filter]
                    filters = [(key, value)]
                elif issubclass(filter, SimpleListFilter):
                    filter_instance = filter(request, [], model, model_admin)
                    key = filter_instance.parameter_name
                    filters = [
                        (key, lookup[0]) for lookup in filter_instance.lookup_choices
                    ]
                for key, value in filters:
                    response = self.client.get(
                        reverse(
                            f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
                        )
                        + f"?{key}={value}",
                        follow=True,
                    )
                    self.changelist_view_asserts(
                        model, model_admin, response, "changelist_filters"
                    )

    @for_all_model_admins
    def test_changelist_view_search(self, model, model_admin):
        self.changelist_view_search_func(model, model_admin)

    def changelist_view_search_func(self, model, model_admin):
        request = self.get_request(model, model_admin, params=QueryDict("q=test"))

        self.client.force_login(self.superuser)
        if model_admin.has_change_permission(request):
            # make sure no errors happen here
            response = self.client.get(
                reverse(
                    f"admin:{model._meta.app_label}_{model._meta.model_name}_changelist"
                )
                + "?q=test",
                follow=True,
            )
            self.changelist_view_asserts(model, model_admin, response, None)
            self.changelist_view_search_asserts(
                model, model_admin, response, "changelist_view_search"
            )
            return response

    def changelist_view_search_asserts(self, model, model_admin, response, view_name):
        """Additional asserts for search test"""
        self.print_response(response, model, model_admin, view_name)
        if hasattr(model_admin, "search_fields") and len(model_admin.search_fields) > 0:
            self.assertElementContains(
                response,
                "input[type=text]",
                '<input type="text" size="40" name="q" value="test" id="searchbar" autofocus="">',
            )

    @for_all_model_admins
    def test_add_view(self, model, model_admin):
        self.add_view_func(model, model_admin)

    def add_view_func(self, model, model_admin):
        request = self.get_request(model, model_admin)

        self.client.force_login(self.superuser)
        if model_admin.has_add_permission(request):
            # make sure no errors happen here
            response = self.client.get(
                reverse(f"admin:{model._meta.app_label}_{model._meta.model_name}_add"),
                follow=True,
            )
            self.add_view_asserts(model, model_admin, response)
            return response

    def add_view_asserts(self, model, model_admin, response):
        self.print_response(response, model, model_admin, "add_view")
        self.assertIn(response.status_code, [200])
        self.assertElementContains(
            response,
            "h1[id=site-name]",
            f"<h1 id='site-name'><a href='{reverse('admin:index')}'>"
            f"{response.context_data['site_header']}"
            "</a></h1>",
        )
        self.assertElementContains(
            response,
            "div[id=content] h1",
            f"<h1>Add {model._meta.verbose_name}</h1>",
        )

    @for_all_model_admins
    def test_change_view(self, model, model_admin):
        self.change_view_func(model, model_admin)

    def change_view_func(self, model, model_admin, instance=None):
        if not instance:
            instance = self.get_instance(model, model_admin)
        if not instance:
            return
        request = self.get_request(model, model_admin)

        self.client.force_login(self.superuser)
        if model_admin.has_change_permission(request):
            url = reverse(
                f"admin:{model._meta.app_label}_{model._meta.model_name}_change",
                args=(quote(instance.pk),),
            )
            response = self.client.get(url, follow=True)
            self.change_view_asserts(model, model_admin, response, "change_view")
            return response

    def change_view_asserts(self, model, model_admin, response, view_name):
        self.assertIn(response.status_code, [200])
        self.print_response(response, model, model_admin, view_name)
        self.assertElementContains(
            response,
            "h1[id=site-name]",
            f"<h1 id='site-name'><a href='{reverse('admin:index')}'>"
            f"{response.context_data['site_header']}"
            "</a></h1>",
        )
        self.assertElementContains(
            response,
            "div[id=content] h1",
            f"<h1>Change {model._meta.verbose_name}</h1>",
        )

    @for_all_model_admins
    def test_change_post(self, model, model_admin):
        self.change_post_func(model, model_admin)

    def get_instance(self, model, model_admin, warn=True):
        if model._meta.proxy:
            return
        instance = model.objects.last()
        if not instance and warn:
            warn_message = f"No {model_path(model)} data created to test {model_admin}."
            if self.strict_mode:
                raise AssertionError(warn_message)
            warnings.warn(warn_message)
        return instance

    def change_post_func(self, model, model_admin, instance=None):
        if not instance:
            instance = self.get_instance(model, model_admin)
        if not instance:
            return

        # Get form and use it to create POST data
        request = self.post_request(model, model_admin)
        form = model_admin.get_form(request)
        self.client.force_login(self.superuser)
        if model_admin.has_change_permission(request):
            url = reverse(
                f"admin:{model._meta.app_label}_{model._meta.model_name}_change",
                args=(quote(instance.pk),),
            )
            data = form_data(form, instance)
            data.update({"_continue": "Save and continue editing"})
            response = self.client.post(url, data=data, follow=True)
            self.change_view_asserts(model, model_admin, response, "change_view_post")
            return response

    def test_index_page(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin:index"))
        self.index_page_asserts(response)

    def index_page_asserts(self, response):
        self.print_response(response, None, None, "index_page")
        self.assertIn(response.status_code, [200])
        self.assertElementContains(
            response,
            "h1[id=site-name]",
            f"<h1 id='site-name'><a href='{reverse('admin:index')}'>"
            f"{response.context_data['site_header']}"
            "</a></h1>",
        )


class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
    pass
