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

PRODUCT_URL = getattr(
    settings, 'SHOP_CATALOG_PRODUCT_URL', 'products')
CATEGORY_URL = getattr(
    settings, 'SHOP_CATALOG_CATEGORY_URL', 'categories')
BRAND_URL = getattr(
    settings, 'SHOP_CATALOG_BRAND_URL', 'brands')
MANUFACTURER_URL = getattr(
    settings, 'SHOP_CATALOG_MANUFACTURER_URL', 'manufacturers')

MEASUREMENT_UNITS = getattr(settings, 'SHOP_CATALOG_MEASUREMENT_UNITS', [])

MODIFIER_CONDITIONS = getattr(settings, 'SHOP_CATALOG_MODIFIER_CONDITIONS', [
    'shop_catalog.modifier_conditions.PriceGreaterThanModifierCondition',
    'shop_catalog.modifier_conditions.PriceLessThanModifierCondition',
    'shop_catalog.modifier_conditions.QuantityGreaterThanModifierCondition',
    'shop_catalog.modifier_conditions.QuantityLessThanModifierCondition',
    'shop_catalog.modifier_conditions.WidthGreaterThanModifierCondition',
    'shop_catalog.modifier_conditions.WidthLessThanModifierCondition',
    'shop_catalog.modifier_conditions.HeightGreaterThanModifierCondition',
    'shop_catalog.modifier_conditions.HeightLessThanModifierCondition',
    'shop_catalog.modifier_conditions.DepthGreaterThanModifierCondition',
    'shop_catalog.modifier_conditions.DepthLessThanModifierCondition',
    'shop_catalog.modifier_conditions.WeightGreaterThanModifierCondition',
    'shop_catalog.modifier_conditions.WeightLessThanModifierCondition',
])
