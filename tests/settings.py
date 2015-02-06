# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def root_path(*args):
    return os.path.join(ROOT_DIR, *args)


LANGUAGE_CODE = 'en'
LANGUAGES = [
    ('en', 'English'),
    ('it', 'Italian'),
    ('hr', 'Croatian'),
]

DEBUG = True
TEMPLATE_DEBUG = True

FIXTURE_DIRS = (
    root_path('tests', 'fixtures'),
)

USE_TZ = True

ROOT_URLCONF = 'tests.urls'

SECRET_KEY = 'secretkey'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

STATIC_URL = '/static/'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.request',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'cms',
    'mptt',
    'filer',
    'hvad',
    'shop',
    'shop.addressmodel',
    'catalog',
    'currencies',
)

SHOP_PRODUCT_MODEL = 'catalog.models.Product'

SHOP_CART_MODIFIERS = (
    'catalog.cart_modifiers.ShopCatalogCartModifier',
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
