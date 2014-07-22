# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

SLUG_FIELD_HELP_TEXT = _(
    'Can only contain the letters a-z, A-Z, digits, minus and underscores, '
    'and can\'t start with a digit.')

PRODUCT_CHANGE_FORM_TEMPLATE = (
    'admin/catalog/product_change_form.html')

ATTRIBUTE_TEMPLATE_CHOICES = getattr(
    settings, 'CATALOG_ATTRIBUTE_TEMPLATE_CHOICES', (
        ('radio', _('Radio')),
    ))

HAS_CATEGORIES = getattr(settings, 'CATALOG_HAS_CATEGORIES', True)
HAS_BRANDS = getattr(settings, 'CATALOG_HAS_BRANDS', True)
HAS_MANUFACTURERS = getattr(settings, 'CATALOG_HAS_MANUFACTURERS', True)

PRODUCT_URL = getattr(
    settings, 'CATALOG_PRODUCT_URL', 'products')
CATEGORY_URL = getattr(
    settings, 'CATALOG_CATEGORY_URL', 'categories')
BRAND_URL = getattr(
    settings, 'CATALOG_BRAND_URL', 'brands')
MANUFACTURER_URL = getattr(
    settings, 'CATALOG_MANUFACTURER_URL', 'manufacturers')

MEASUREMENT_UNITS = getattr(settings, 'CATALOG_MEASUREMENT_UNITS', [])

MODIFIER_CONDITIONS = getattr(settings, 'CATALOG_MODIFIER_CONDITIONS', [
    'catalog.modifier_conditions.PriceGreaterThanModifierCondition',
    'catalog.modifier_conditions.PriceLessThanModifierCondition',
    'catalog.modifier_conditions.QuantityGreaterThanModifierCondition',
    'catalog.modifier_conditions.QuantityLessThanModifierCondition',
    'catalog.modifier_conditions.WidthGreaterThanModifierCondition',
    'catalog.modifier_conditions.WidthLessThanModifierCondition',
    'catalog.modifier_conditions.HeightGreaterThanModifierCondition',
    'catalog.modifier_conditions.HeightLessThanModifierCondition',
    'catalog.modifier_conditions.DepthGreaterThanModifierCondition',
    'catalog.modifier_conditions.DepthLessThanModifierCondition',
    'catalog.modifier_conditions.WeightGreaterThanModifierCondition',
    'catalog.modifier_conditions.WeightLessThanModifierCondition',
])
