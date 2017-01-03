#!/usr/bin/env python
# -*- coding: utf-8 -*-

import django_admin_smoke_tests

from setuptools import setup

package_name = 'django_admin_smoke_tests'


def runtests():
    import os
    import sys

    import django
    from django.core.management import call_command

    os.environ['DJANGO_SETTINGS_MODULE'] = 'test_project.settings'
    if django.VERSION[0] == 1 and django.VERSION[1] >= 7:
        django.setup()
    call_command('test', 'test_project.main.tests')
    sys.exit()


setup(
    name='django-admin-smoke-tests',
    version=django_admin_smoke_tests.__version__,
    description="Runs some quick tests on your admin site objects to make sure \
there aren't non-existant fields listed, etc.",
    author='Seán Hayes',
    author_email='sean@seanhayes.name',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='django admin smoke test',
    url='https://github.com/SeanHayes/django-admin-smoke-tests',
    download_url='https://github.com/SeanHayes/django-admin-smoke-tests',
    license='BSD',
    install_requires=[
        'django>=1.6',
        'six',
    ],
    packages=[
        package_name,
    ],
    include_package_data=True,
    zip_safe=False,
    test_suite='setup.runtests',
)
