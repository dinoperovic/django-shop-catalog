# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


DATETIME_INPUT_FOMRAT = '%Y-%m-%d %H:%M:%S'
DATE_INPUT_FOMRAT = '%Y-%m-%d'

SLUG_FIELD_HELP_TEXT = _(
    'Can only contain the letters a-z, A-Z, digits, minus and underscores, '
    'and can\'t start with a digit.')

UNDERSCORE_FIELD_HELP_TEXT = _(
    'Can only contain the letters a-z, A-Z, digits and underscores, '
    'and can\'t start with a digit.')

ACTIVE_FIELD_HELP_TEXT = _(
    'Is this object active? You can hide it by unchecking this box.')

PRODUCT_CHANGE_FORM_TEMPLATE = (
    'admin/catalog/product_change_form.html')

ATTRIBUTE_TEMPLATE_CHOICES = getattr(
    settings, 'CATALOG_ATTRIBUTE_TEMPLATE_CHOICES', (
        ('radio', _('Radio')),
    ))

RELATED_PRODUCT_KIND_CHOICES = getattr(
    settings, 'CATALOG_RELATED_PRODUCT_KIND_CHOICES', (
        ('upsell', _('Upsell')),
        ('cross_sell', _('Cross sell')),
    ))

PRODUCTS_PER_PAGE = getattr(settings, 'CATALOG_PRODUCTS_PER_PAGE', 6)

# Toggles.
HAS_CATEGORIES = getattr(settings, 'CATALOG_HAS_CATEGORIES', True)
HAS_BRANDS = getattr(settings, 'CATALOG_HAS_BRANDS', True)
HAS_MANUFACTURERS = getattr(settings, 'CATALOG_HAS_MANUFACTURERS', True)
HAS_MODIFIER_CODES = getattr(settings, 'CATALOG_HAS_MODIFIER_CODES', True)

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
