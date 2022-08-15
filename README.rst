========================
django-admin-smoke-tests
========================

.. image:: https://travis-ci.org/greyside/django-admin-smoke-tests.svg?branch=master
    :target: https://travis-ci.org/greyside/django-admin-smoke-tests
.. image:: https://coveralls.io/repos/greyside/django-admin-smoke-tests/badge.png?branch=master
    :target: https://coveralls.io/r/greyside/django-admin-smoke-tests?branch=master

Running smoke tests
-------------------

Run with ``./manage.py test django_admin_smoke_tests.tests``.

You don't have to add anything ``INSTALLED_APPS``

Usage in your tests
-------------------

If you want to customize smoke testing, create testing file (e.g. ``tests/test_admin_smoke.py``) and add following starting code:

.. code:: python

    from django.test import TestCase
    from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        def setUp(self):
            super().setUp()
            # custom setup goes here

If you want to use admin smoke tests as part of your tests with data from fixtures,
you can override the ``fixtures`` attribute:

.. code:: python

    from django.test import TestCase
    from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        fixtures = ['testing_data']

And you can also exclude certain (e.g. external) apps or model admins with class attributes:

.. code:: python

    exclude_apps = ['constance',]
    exclude_modeladmins = [apps.admin.ModelAdmin]
