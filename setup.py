#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re

from setuptools import setup

import django_admin_smoke_tests


package_name = "django_admin_smoke_tests"


def runtests():
    import os
    import sys

    import django
    from django.core.management import call_command

    os.environ["DJANGO_SETTINGS_MODULE"] = "test_project.settings"
    django.setup()
    call_command("test", "test_project")
    sys.exit()


def parse_requirements(file_name):
    requirements = []
    for line in open(file_name, "r").read().split("\n"):
        if re.match(r"(\s*#)|(\s*$)", line):
            continue
        if re.match(r"\s*-e\s+", line):
            requirements.append(re.sub(r"\s*-e\s+.*#egg=(.*)$", r"\1", line))
        elif re.match(r"(\s*git)|(\s*hg)", line):
            pass
        else:
            requirements.append(line)
    return requirements


setup(
    name="django-admin-smoke-tests",
    version=django_admin_smoke_tests.__version__,
    description="Runs some quick tests on your admin site objects to make sure \
there aren't non-existant fields listed, etc.",
    author="Seán Hayes",
    author_email="sean@seanhayes.name",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="django admin smoke test",
    url="https://github.com/SeanHayes/django-admin-smoke-tests",
    download_url="https://github.com/SeanHayes/django-admin-smoke-tests",
    license="BSD",
    install_requires=parse_requirements("requirements.txt"),
    packages=[
        package_name,
    ],
    include_package_data=True,
    zip_safe=False,
    test_suite="setup.runtests",
)
