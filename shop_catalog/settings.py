# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


SLUG_FIELD_HELP_TEXT = _(
    'Can only contain the letters a-z, A-Z, digits, minus and underscores, '
    'and can\'t start with a digit.')

PRODUCT_CHANGE_FORM_TEMPLATE = (
    'admin/shop_catalog/product_change_form.html')

ATTRIBUTE_TEMPLATE_CHOICES = getattr(
    settings, 'SHOP_CATALOG_ATTRIBUTE_TEMPLATE_CHOICES', (
        ('radio', _('Radio')),
    ))

HAS_CATEGORIES = getattr(settings, 'SHOP_CATALOG_HAS_CATEGORIES', True)
HAS_BRANDS = getattr(settings, 'SHOP_CATALOG_HAS_BRANDS', True)
HAS_MANUFACTURERS = getattr(settings, 'SHOP_CATALOG_HAS_MANUFACTURERS', True)
