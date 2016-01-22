========================
django-admin-smoke-tests
========================

.. image:: https://travis-ci.org/greyside/django-admin-smoke-tests.svg?branch=master
    :target: https://travis-ci.org/greyside/django-admin-smoke-tests
.. image:: https://coveralls.io/repos/greyside/django-admin-smoke-tests/badge.png?branch=master
    :target: https://coveralls.io/r/greyside/django-admin-smoke-tests?branch=master

Run with ``./manage.py test django_admin_smoke_tests.tests``.

Or import into your own code:

.. code:: python

    from django.test import TestCase
    from django_admin_smoke_tests.tests import AdminSiteSmokeTestMixin

    class AdminSiteSmokeTest(AdminSiteSmokeTestMixin, TestCase):
        def setUp(self):
            super(AdminSiteSmokeTest, self).setUp()
            # custom setup goes here
