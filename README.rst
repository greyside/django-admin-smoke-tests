========================
django-admin-smoke-tests
========================

.. image:: https://travis-ci.org/greyside/django-admin-smoke-tests.svg?branch=master
    :target: https://travis-ci.org/greyside/django-admin-smoke-tests
.. image:: https://coveralls.io/repos/greyside/django-admin-smoke-tests/badge.png?branch=master
    :target: https://coveralls.io/r/greyside/django-admin-smoke-tests?branch=master

Run with ``./manage.py test django_admin_smoke_tests.tests``.

You don't have to add anything ``INSTALLED_APPS``

Usage in your tests
-------------------

Import into your own code:

.. code:: python

    from django.test import TestCase
    from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        def setUp(self):
            super(AdminSiteSmokeTest, self).setUp()
            # custom setup goes here

If you want to use admin smoke tests as part of your tests with data from fixtures,
you can do following:

.. code:: python

    from django.test import TestCase
    from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        fixtures = ['data']

And you can exclude certain (external) apps or model admins with::

    exclude_apps = ['constance',]
    exclude_modeladmins = [apps.admin.ModelAdmin]
