#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from setuptools import setup, find_packages


version = __import__('catalog').__version__
readme = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(
    name='django-shop-catalog',
    version=version,
    description='Catalog app for django SHOP',
    long_description=readme,
    author='Dino Perovic',
    author_email='dino.perovic@gmail.com',
    url='http://pypi.python.org/pypi/django-shop-catalog/',
    packages=find_packages(exclude=('tests', 'tests.*')),
    license='BSD',
    install_requires=(
        'django>=1.6,<1.8',
        'django-cms>=3.0.1',
        'django-shop>=0.2.0',
        'django-filer>=0.9.5',
        'django-mptt>=0.6.0',
        'django-hvad>=0.4.0',
        'measurement>=1.7.2',
        'django-currencies>=0.3.2',
    ),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ],
    test_suite='runtests.main',
    tests_require=(
        'django-nose==1.2',
    ),
)
