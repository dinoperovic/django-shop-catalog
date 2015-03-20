# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from itertools import chain
from decimal import Decimal
from datetime import datetime

from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible, force_str
from django.utils.text import slugify
from django.utils.module_loading import import_by_path

from shop.util.fields import CurrencyField
from shop.util.loader import get_model_string
from cms.models.fields import PlaceholderField
from hvad.models import TranslatableModel, TranslatedFields
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from filer.fields.image import FilerFileField, FilerImageField
from measurement.measures import Distance, Weight
from measurement.base import MeasureBase
from currencies.models import Currency
from currencies.utils import calculate_price

from catalog.fields import NullableCharField, UnderscoreField
from catalog.managers import (
    CatalogManager, ModifierCodeManager, ProductManager)
from catalog.utils.noconflict import classmaker
from catalog.utils import round_2
from catalog import settings as scs


@python_2_unicode_compatible
class CatalogModel(models.Model):
    """
    Defines common fields for catalog objects and abstracts some
    standard getter methods.

    When an object inherits from CatalogModel, it can define a
    CatalogManager as a manager for ease of getting "active" objects.
    """
    active = models.BooleanField(
        _('Active'), default=True, help_text=scs.ACTIVE_FIELD_HELP_TEXT)
    date_added = models.DateTimeField(_('Date added'), auto_now_add=True)
    last_modified = models.DateTimeField(_('Last modified'), auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_name()

    def get_absolute_url(self):
        return None

    def get_name(self):
        return force_str(self.pk)

    def get_slug(self):
        return slugify(unicode(self.get_name()))

    @property
    def as_dict(self):
        return dict(
            pk=force_str(self.pk),
            active=self.active,
            name=force_str(self.get_name()),
            slug=force_str(self.get_slug()),
            url=force_str(self.get_absolute_url()),
            date_added=force_str(self.date_added),
            last_modified=force_str(self.last_modified),
        )


class Modifier(TranslatableModel, CatalogModel):
    """
    Defines different amounts to be applied to a product or a category.
    """
    KIND_STANDARD = 'standard'
    KIND_DISCOUNT = 'discount'
    KIND_CART_MODIFIER = 'cart_modifier'
    KIND_CHOICES = (
        (KIND_STANDARD, _('Standard')),
        (KIND_DISCOUNT, _('Discount')),
        (KIND_CART_MODIFIER, _('Cart modifier')),
    )

    code = models.SlugField(
        _('Code'), max_length=128, unique=True,
        help_text=scs.SLUG_FIELD_HELP_TEXT)

    amount = CurrencyField(
        verbose_name=_('Amount'),
        help_text=_('Absolute amount that should be applied. '
                    'Can be negative.'))

    percent = models.DecimalField(
        _('Percent'), blank=True, null=True,
        max_digits=4, decimal_places=2,
        help_text=_('If percent is set, it will override the absolute '
                    'amount. Can be negative.'))

    kind = models.CharField(
        _('Kind'), max_length=128, choices=KIND_CHOICES, default=KIND_STANDARD,
        help_text=_('Select a modifier kind. If "Cart modifier" is selected, '
                    'modifier will be constant and affect entire cart.'))

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
    )

    objects = CatalogManager()

    class Meta:
        db_table = 'catalog_modifiers'
        verbose_name = _('Modifier')
        verbose_name_plural = _('Modifiers')

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.code

    def get_extra_cart_item_price_field(self, cart_item, request=None):
        """
        Returns extra price field for the given cart item.
        """
        if self.can_be_applied(cart_item=cart_item, request=request):
            return (self.get_name(), self.calculate_add_price(
                cart_item.current_total, cart_item.quantity))

    def get_extra_cart_price_field(self, cart, request=None):
        """
        Returns extra price field for entire cart.
        """
        if self.can_be_applied(cart=cart, request=request):
            return (self.get_name(), self.calculate_add_price(
                cart.current_total))

    def calculate_add_price(self, price, quantity=1):
        """
        Calculates and returns an amount to be added to the given price.
        """
        if self.percent:
            add_price = (self.percent / 100) * price
        else:
            add_price = self.amount * quantity
        return add_price

    def can_be_applied(self, cart_item=None, cart=None, request=None):
        """
        Checks if this modifier can be applied or not.
        """
        # Check that product is eligible if cart_item is specified.
        if cart_item and not self.is_eligible_product(cart_item.product):
            return False

        # Check that all conditions are met.
        for con in self.conditions.select_related().all():
            if not con.is_met(cart_item=cart_item, cart=cart, request=request):
                return False

        cart_id = cart_item.cart_id if cart_item else cart.id if cart else None
        return self.is_code_applied(cart_id)

    def is_code_applied(self, cart_id):
        """
        Check for codes on this modifier, and if they exist make sure
        that at least one is applied to the given cart. Codes have
        alerady been validated so we just have to make sure they are
        active and exist.
        """
        codes = self.codes.active()

        if codes.exists():
            cart_codes = CartModifierCode.objects.filter(cart_id=cart_id)
            cart_codes = list(set(cart_codes.values_list('code', flat=True)))
            if cart_codes:
                for code in cart_codes:
                    if codes.filter(code=code).exists():
                        return True

            # Codes exist but not one is applied, return False.
            return False

        # Codes don't exist, return True.
        return True

    def is_eligible_product(self, product):
        """
        Returns if modifier can be applied to a given product.
        """
        if self.kind == self.KIND_DISCOUNT:
            return product.is_discountable
        return self.kind != self.KIND_CART_MODIFIER

    @classmethod
    def get_cart_modifiers(cls):
        """
        Returns all active cart modifiers.
        """
        return cls.objects.active(kind=cls.KIND_CART_MODIFIER)


class ModifierModel(models.Model):
    """
    Base model for a class that implements modifiers.
    """
    modifiers = models.ManyToManyField(
        Modifier, blank=True, null=True, verbose_name=_('Modifiers'),
        limit_choices_to=~Q(kind=Modifier.KIND_CART_MODIFIER))

    class Meta:
        abstract = True

    def get_modifiers(self):
        return self.modifiers.select_related().active()


def get_modifier_condition_choices():
    choices = ()
    for path in scs.MODIFIER_CONDITIONS:
        try:
            module = import_by_path(path)()
            choices += (path, module.get_name()),
        except ImportError:
            pass
    return choices


@python_2_unicode_compatible
class ModifierCondition(models.Model):
    """
    Inline model to modifier that holds the condition that have to
    be met in order to apply the modifier.
    """
    MODIFIER_CONDITION_CHOICES = get_modifier_condition_choices()

    modifier = models.ForeignKey(
        Modifier, related_name='conditions', verbose_name=_('Modifier'))
    path = models.CharField(
        _('Condition'), max_length=255, choices=MODIFIER_CONDITION_CHOICES)
    arg = models.DecimalField(
        _('Argument'), blank=True, null=True, max_digits=10, decimal_places=3)

    class Meta:
        db_table = 'catalog_modifier_conditions'
        verbose_name = _('Condition')
        verbose_name_plural = _('Conditions')

    def __str__(self):
        return '{} {}'.format(
            dict(self.MODIFIER_CONDITION_CHOICES).get(self.path),
            self.arg or '')

    def is_met(self, cart_item=None, cart=None, request=None):
        """
        Checks if condition is met and returns a boolean.
        """
        try:
            module = import_by_path(self.path)()
            if cart_item and not module.cart_item_condition(
                    cart_item, self.arg, request):
                return False
            if cart and not module.cart_condition(cart, self.arg, request):
                return False
        except ImportError:
            pass
        return True


@python_2_unicode_compatible
class ModifierCode(models.Model):
    modifier = models.ForeignKey(
        Modifier, related_name='codes', verbose_name=_('Modifier'))

    code = models.SlugField(
        _('Code'), max_length=30, unique=True,
        help_text=scs.SLUG_FIELD_HELP_TEXT)

    active = models.BooleanField(
        _('Active'), default=True, help_text=scs.ACTIVE_FIELD_HELP_TEXT)
    valid_from = models.DateTimeField(_('Valid from'), default=datetime.now)
    valid_until = models.DateTimeField(_('Valid until'), blank=True, null=True)

    objects = ModifierCodeManager()

    class Meta:
        db_table = 'catalog_modifier_codes'
        verbose_name = _('Code')
        verbose_name_plural = _('Codes')

    def __str__(self):
        return '{}'.format(self.code)


@python_2_unicode_compatible
class CartModifierCode(models.Model):
    cart = models.ForeignKey(get_model_string('Cart'), editable=False)
    code = models.CharField(_('Code'), max_length=30)

    class Meta:
        db_table = 'catalog_cart_modifier_codes'
        verbose_name = _('Cart modifier code')
        verbose_name_plural = _('Cart modifier codes')

    def __str__(self):
        return '{}'.format(self.code)


class CategoryBase(MPTTModel, CatalogModel, ModifierModel):
    """
    Base model for categorization, uses django-mptt for it's tree
    management.
    """
    parent = TreeForeignKey(
        'self', blank=True, null=True, related_name='children')

    class Meta:
        abstract = True

    def get_modifiers(self, distinct=True):
        """
        Fetches all modifiers from a tree and returns them.
        """
        mods = self.modifiers.select_related().active()
        for obj in self.get_ancestors():
            mods = mods | obj.modifiers.select_related().active()
        return mods.distinct() if distinct else mods

    @property
    def as_dict(self):
        data = super(CategoryBase, self).as_dict
        parent = force_str(self.parent_id) if self.parent is not None else None
        data.update(dict(
            parent=parent,
        ))
        return data


class Category(TranslatableModel, CategoryBase):
    """
    A categorization layer inherited from CategoryBase.
    """
    __metaclass__ = classmaker()

    featured_image = FilerImageField(
        blank=True, null=True, verbose_name=_('Featured image'))

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
        slug=models.SlugField(
            _('Slug'), max_length=128, help_text=scs.SLUG_FIELD_HELP_TEXT),
        description=models.TextField(_('Description'), blank=True),
        meta={'unique_together': [('slug', 'language_code')]},
    )

    body = PlaceholderField(
        'catalog_category_body', related_name='category_body_set')

    objects = CatalogManager()

    class Meta:
        db_table = 'catalog_categories'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def get_absolute_url(self):
        return reverse('catalog_category_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


class Brand(TranslatableModel, CategoryBase):
    """
    A categorization layer inherited from CategoryBase.
    """
    __metaclass__ = classmaker()

    featured_image = FilerImageField(
        blank=True, null=True, verbose_name=_('Featured image'))

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
        slug=models.SlugField(
            _('Slug'), max_length=128, help_text=scs.SLUG_FIELD_HELP_TEXT),
        description=models.TextField(_('Description'), blank=True),
        meta={'unique_together': [('slug', 'language_code')]},
    )

    body = PlaceholderField(
        'catalog_brand_body', related_name='brand_body_set')

    objects = CatalogManager()

    class Meta:
        db_table = 'catalog_brands'
        verbose_name = _('Brand')
        verbose_name_plural = _('Brands')

    def get_absolute_url(self):
        return reverse('catalog_brand_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


class Manufacturer(TranslatableModel, CategoryBase):
    """
    A categorization layer inherited from CategoryBase.
    """
    __metaclass__ = classmaker()

    featured_image = FilerImageField(
        blank=True, null=True, verbose_name=_('Featured image'))

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
        slug=models.SlugField(
            _('Slug'), max_length=128, help_text=scs.SLUG_FIELD_HELP_TEXT),
        description=models.TextField(_('Description'), blank=True),
        meta={'unique_together': [('slug', 'language_code')]},
    )

    body = PlaceholderField(
        'catalog_manufacturer_body', related_name='manufacturer_body_set')

    objects = CatalogManager()

    class Meta:
        db_table = 'catalog_manufacturers'
        verbose_name = _('Manufacturer')
        verbose_name_plural = _('Manufacturers')

    def get_absolute_url(self):
        return reverse('catalog_manufacturer_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


@python_2_unicode_compatible
class Tax(models.Model):
    name = models.CharField(_('Name'), max_length=128)
    percent = models.DecimalField(
        _('Percent'), max_digits=4, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('Tax percentage.'))

    class Meta:
        db_table = 'catalog_taxes'
        verbose_name = _('Tax')
        verbose_name_plural = _('Taxes')

    def __str__(self):
        return '{}'.format(self.name)


@python_2_unicode_compatible
class ProductBase(MPTTModel, CatalogModel):
    """
    Base fields and calculations are defined here and all objects that
    can be added to cart must inherit from this model. Models that
    extend ProductBase must define 'attributes' M2M  relation to
    'Attribute' and through 'ProductAttributeValue' model.
    """
    upc = NullableCharField(
        _('UPC'), max_length=64, blank=True, null=True, unique=True,
        help_text=_('Universal Product Code (UPC) is an identifier for a '
                    'product which is not specific to a particular supplier. '
                    'Eg. an ISBN for a book.'))

    parent = TreeForeignKey(
        'self', blank=True, null=True, related_name='variants',
        verbose_name=_('Parent'),
        help_text=_('If this is a "variant" of a Product, select that '
                    'Product.'))

    unit_price = CurrencyField(
        verbose_name=_('Unit price'),
        help_text=_('If Product is a "variant" and price is "0", unit price '
                    'is inherited from it\'s parent.'))

    is_discountable = models.BooleanField(
        _('Is discountable?'), default=True,
        help_text=_('This flag indicates if this product can be used in an '
                    'offer or not.'))

    discount_percent = models.DecimalField(
        _('Discount percent'), blank=True, null=True,
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text=_('If Product is a "variant" and discount percent is not '
                    'set, discount percent is inherited from it\'s parent. '
                    'If you dont wan\'t this to happen, set discount percent '
                    'to "0".'))

    tax = models.ForeignKey(
        Tax, blank=True, null=True,
        related_name='products', on_delete=models.SET_NULL,
        verbose_name=_('Tax'),
        help_text=_('Tax to be applied to this product. If not set and '
                    'product is a variant, tax will be inherited from '
                    'parent.'))

    quantity = models.PositiveIntegerField(
        _('Quantity'), blank=True, null=True,
        help_text=_('Number of products available, if product is unavailable '
                    '(out of stock) set this to "0". If left empty, product '
                    'will be treated as if it\'s always available.'))

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_name()

    def get_price(self):
        price = self.get_unit_price()

        if self.is_discounted:
            discount = self.get_discount_percent()
            if discount:
                price -= (discount * price) / Decimal('100')

        if self.is_taxed:
            tax = self.get_tax_percent()
            price += (tax * price) / Decimal('100')

        return round_2(price)

    def get_unit_price(self):
        if self.is_price_inherited:
            return self.parent.get_unit_price()
        return round_2(self.unit_price)

    def get_discount_percent(self):
        if self.is_discount_inherited:
            return self.parent.get_discount_percent()
        return self.discount_percent or 0

    def get_tax_percent(self):
        if self.is_tax_inherited:
            return self.parent.get_tax_percent()
        return self.tax.percent if self.tax is not None else 0

    def get_product_reference(self):
        return self.upc or force_str(self.pk)

    def get_featured_image(self):
        """
        Returns a featured image for a product.
        This method should be overriden, by default returns None.
        """
        return None

    def get_extra_dict(self):
        """
        Returns a dict with extra values to be in as_dict property.
        This method should be overriden, by default returns None.
        """
        return None

    @property
    def can_be_added_to_cart(self):
        return self.active and self.is_available and not self.is_group

    @property
    def is_top_level(self):
        return self.parent_id is None

    @property
    def is_group(self):
        return self.is_top_level and self.variants.exists()

    @property
    def is_variant(self):
        return not self.is_top_level

    @property
    def is_available(self):
        return self.quantity is None or self.quantity > 0

    @property
    def is_discounted(self):
        if self.is_discount_inherited:
            return self.parent.is_discounted
        return not not self.discount_percent

    @property
    def is_taxed(self):
        if self.is_tax_inherited:
            return self.parent.is_taxed
        return self.tax is not None

    @property
    def is_price_inherited(self):
        return self.is_variant and not self.unit_price

    @property
    def is_discount_inherited(self):
        return self.is_variant and self.discount_percent is None

    @property
    def is_tax_inherited(self):
        return self.is_variant and self.tax is None

    @property
    def as_dict(self):
        """
        Returns a dicionary with product properties.
        """
        data = super(ProductBase, self).as_dict

        parent = force_str(self.parent_id) if self.is_variant else None
        quantity = force_str(self.quantity) if self.quantity else None

        featured_image = self.get_featured_image()
        featured_image = (
            force_str(featured_image.url) if featured_image else None)

        data.update(dict(
            upc=self.upc,
            parent=parent,
            unit_price=force_str(self.get_unit_price()),
            price=force_str(self.get_price()),
            is_price_inherited=self.is_price_inherited,
            quantity=quantity,
            is_available=self.is_available,
            is_discountable=self.is_discountable,
            is_discounted=self.is_discounted,
            is_discount_inherited=self.is_discount_inherited,
            is_taxed=self.is_taxed,
            is_tax_inherited=self.is_tax_inherited,
            discount_percent=force_str(self.get_discount_percent()),
            tax_percent=force_str(self.get_tax_percent()),
            can_be_added_to_cart=self.can_be_added_to_cart,
            featured_image=featured_image,
            attrs=self.get_attrs(),
        ))

        extra_dict = self.get_extra_dict()
        if extra_dict:
            data.update(extra_dict)
        return data

    @property
    def as_json(self):
        return json.dumps(self.as_dict)

    def get_attrs(self):
        """
        If product is not a group (doesn't have variants) returns a
        formated list of dictionaries with product attributes.
        """
        attrs = []

        if not self.is_group:
            attr_values = self.attribute_values.select_related().all()
            for value in attr_values:
                if value.value is not None:
                    attrs.append(value.as_dict)

        return attrs

    def get_variations(self, exclude={}):
        """
        If product is a group product (has variants) returns a list of
        all it's variants attributes grouped by code in a dictionary.
        """
        variations = {}

        if self.is_group:
            variants = self.variants.select_related().exclude(**exclude)
            attr_values = list(chain(*[x.get_attrs() for x in variants]))

            for value in attr_values:
                if value['code'] not in variations:
                    is_nullable = Attribute.is_nullable(value['code'], self)

                    variations[value['code']] = {
                        'name': value['name'],
                        'code': value['code'],
                        'type': value['type'],
                        'template': value['template'],
                        'is_nullable': is_nullable,
                        'values': [],
                    }

                if value['value'] not in variations[value['code']]['values']:
                    variations[value['code']]['values'].append(value['value'])

        return variations

    def get_variant(self, **kwargs):
        """
        Returns a variant which attributes match the given kwargs.
        """
        if not self.is_group:
            return None

        # Cast keys and values to str and filter out empty values.
        kwargs = [(force_str(k), force_str(v)) for k, v in kwargs.items() if v]

        # Loop through variants and compare their attribute values to
        # kwargs. If they match, return that variant.
        for obj in self.variants.select_related().all():
            attrs = [(x['code'], x['value']) for x in obj.get_attrs()]
            if sorted(attrs) == sorted(kwargs):
                return obj

        # No variants match the given kwargs, return None.
        return None

    def filter_variants(self, **kwargs):
        """
        Returns a list of variants filtered (attributes) by the
        given kwargs.
        """
        if not self.is_group:
            return None

        variants = []

        # Cast keys and values to str and filter out empty values.
        kwargs = [(force_str(k), force_str(v)) for k, v in kwargs.items()
                  if v is not None]

        # Loop through variants and compare their attribute values
        # to kwargs. Make sure that all kwargs are a part of attributes.
        for obj in self.variants.select_related().all():
            attrs = [(x['code'], x['value']) for x in obj.get_attrs()]
            if set(sorted(kwargs)).issubset(sorted(attrs)):
                variants.append(obj)

        # Return variants if any.
        return variants if any(variants) else None


class Product(TranslatableModel, ProductBase, ModifierModel):
    """
    Inherits from ProductBase and adds more specific fields like
    categorization etc.
    """
    __metaclass__ = classmaker()

    featured_image = FilerImageField(
        blank=True, null=True, related_name='featured_images',
        verbose_name=_('Featured image'))

    category = TreeForeignKey(
        Category, blank=True, null=True, related_name='products',
        verbose_name=_(u'Category'))
    brand = TreeForeignKey(
        Brand, blank=True, null=True, related_name='products',
        verbose_name=_(u'Brand'))
    manufacturer = TreeForeignKey(
        Manufacturer, blank=True, null=True, related_name='products',
        verbose_name=_(u'Manufacturer'))

    attributes = models.ManyToManyField(
        'Attribute', through='ProductAttributeValue',
        related_name='attributes', verbose_name=_('Attributes'))

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
        slug=models.SlugField(
            _('Slug'), max_length=128, help_text=scs.SLUG_FIELD_HELP_TEXT),
        description=models.TextField(_('Description'), blank=True),
        meta={'unique_together': [('slug', 'language_code')]},
    )

    media = PlaceholderField(
        'catalog_product_media', related_name='product_media_set')
    body = PlaceholderField(
        'catalog_product_body', related_name='product_body_set')

    objects = ProductManager()

    class Meta:
        db_table = 'catalog_products'
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def get_absolute_url(self):
        return reverse('catalog_product_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')

    def get_featured_image(self):
        if self.is_featured_image_inherited:
            return self.parent.get_featured_image()
        return self.featured_image

    def get_description(self):
        if self.is_description_inherited:
            return self.parent.get_description()
        return self.lazy_translation_getter('description')

    def get_extra_dict(self):
        data = dict(
            description=self.get_description(),
            is_description_inherited=self.is_description_inherited,
            is_featured_image_inherited=self.is_featured_image_inherited,
            is_media_inherited=self.is_media_inherited,
            is_body_inherited=self.is_body_inherited,
            measurements=self.get_measurements(),
            currencies=self.get_currencies(),
            flags=self.get_flags(),
            related_products=self.get_related_products(),
        )
        data.update(self.get_categorization())
        return data

    def get_modifiers(self, distinct=True):
        """
        Returns all modifiers from products gategorization.
        """
        mods = self.modifiers.select_related().active()

        if self.is_variant:
            mods = mods | self.parent.get_modifiers(distinct=False)
        else:
            if self.category:
                mods = mods | self.category.get_modifiers(distinct=False)
            if self.brand:
                mods = mods | self.brand.get_modifiers(distinct=False)
            if self.manufacturer:
                mods = mods | self.manufacturer.get_modifiers(distinct=False)

        return mods.distinct() if distinct else mods

    @property
    def is_description_inherited(self):
        return (self.is_variant and not
                self.lazy_translation_getter('description'))

    @property
    def is_featured_image_inherited(self):
        return self.is_variant and not self.featured_image

    @property
    def is_media_inherited(self):
        return self.is_variant and not self.media.get_plugins().exists()

    @property
    def is_body_inherited(self):
        return self.is_variant and not self.body.get_plugins().exists()

    def get_currencies(self):
        """
        Calculates prices for all currencies and returns them in a dict.
        """
        currencies = {}

        for currency in Currency.objects.filter(is_active=True):
            price = calculate_price(self.get_price(), currency.code)
            unit_price = calculate_price(self.get_unit_price(), currency.code)

            currencies[currency.code] = dict(
                code=force_str(currency.code),
                name=force_str(currency.name),
                symbol=force_str(currency.symbol),
                factor=force_str(currency.factor),
                is_base=currency.is_base,
                is_default=currency.is_default,
                price=force_str(price),
                unit_price=force_str(unit_price),
            )

        return dict(**currencies)

    def get_categorization(self):
        """
        Returns categorization dict, making sure to return a parents
        categorization if product is a variant.
        """
        if self.is_variant:
            return self.parent.get_categorization()

        category = self.category.as_dict if self.category else None
        brand = self.brand.as_dict if self.brand else None
        manufacturer = self.manufacturer.as_dict if self.manufacturer else None

        return dict(
            category=category,
            brand=brand,
            manufacturer=manufacturer,
        )

    def get_measurements(self):
        """
        Check if measure is inherited and returns correct dict of all
        product measurements.
        """
        measurements = self.measurements.select_related().all()

        if self.is_variant:
            kinds = measurements.values_list('kind', flat=True)
            parent_mesurements = self.parent.measurements.select_related()
            parent_mesurements = parent_mesurements.exclude(kind__in=kinds)
            measurements = measurements | parent_mesurements

        measurements_dict = {}
        for kind in dict(MeasurementBase.KIND_CHOICES).keys():
            try:
                measurements_dict[kind] = measurements.get(kind=kind).as_dict
            except ProductMeasurement.DoesNotExist:
                measurements_dict[kind] = None
        return measurements_dict

    def get_flags(self):
        """
        Checks for parent flags and returns correct list of dictionaries
        for product flags.
        """
        flags = self.flags.select_related().all()

        if self.is_variant:
            flag_ids = flags.values_list('flag_id', flat=True)
            parent_flags = self.parent.flags.select_related()
            parent_flags = parent_flags.exclude(flag_id__in=flag_ids)
            flags = flags | parent_flags
        return dict((x.get_code(), x.as_dict) for x in flags)

    def get_related_products(self):
        """
        Returns all related products for this product.
        """
        if self.is_variant:
            return self.parent.get_related_products()

        products_dict = dict(
            (x[0], {'name': force_str(x[1]), 'products': []})
            for x in scs.RELATED_PRODUCT_KIND_CHOICES)

        for obj in self.related_products.select_related().all():
            if obj.kind in products_dict:
                products_dict[obj.kind]['products'].append(
                    force_str(obj.product.pk))
        return products_dict


@python_2_unicode_compatible
class Attribute(TranslatableModel):
    """
    Used to define different types of attributes to be assigned on a
    Product variant. Eg. For a t-shirt attributes could be size, color,
    pattern etc.
    """
    KIND_OPTION = 'option'
    KIND_FILE = 'file'
    KIND_IMAGE = 'image'
    KIND_INTEGER = 'integer'
    KIND_BOOLEAN = 'boolean'
    KIND_FLOAT = 'float'
    KIND_DATE = 'date'
    KIND_CHOICES = (
        (KIND_INTEGER, _('Integer')),
        (KIND_BOOLEAN, _('True / False')),
        (KIND_FLOAT, _('Float')),
        (KIND_DATE, _('Date')),
        (KIND_OPTION, _('Option')),
        (KIND_FILE, _('File')),
        (KIND_IMAGE, _('Image')),
    )

    code = models.SlugField(
        _('Code'), max_length=128, unique=True,
        help_text=scs.SLUG_FIELD_HELP_TEXT)

    kind = models.CharField(
        max_length=20, choices=KIND_CHOICES, default=KIND_CHOICES[0][0],
        verbose_name=_('Type'),
        help_text=_('Select data type. If you choose "Option" data type, '
                    'specify the options below.'))

    template = models.CharField(
        _('Template'), max_length=255, blank=True, null=True,
        choices=scs.ATTRIBUTE_TEMPLATE_CHOICES,
        help_text=_('You can select a template for rendering this attribute '
                    'or leave it empty for the default (dropdown) look.'))

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
    )

    class Meta:
        db_table = 'catalog_attributes'
        ordering = ('code', )
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')

    def __str__(self):
        return '{} ({})'.format(
            self.get_slug(), dict(self.KIND_CHOICES)[self.kind])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.code

    @property
    def type(self):
        return self.kind

    @property
    def is_option(self):
        return self.kind == self.KIND_OPTION

    @property
    def is_file(self):
        return self.kind in (self.KIND_FILE, self.KIND_IMAGE)

    @property
    def as_dict(self):
        template = force_str(self.template) if self.template else None
        return dict(
            code=force_str(self.get_slug()),
            name=force_str(self.get_name()),
            type=force_str(self.kind),
            template=template,
        )

    def get_values(self):
        return list(set([x.value for x in self.values.select_related().all()]))

    @classmethod
    def is_nullable(cls, attr_code, obj):
        """
        If any of 'obj.variants' miss the given attribute means that
        this attribute can be null and returns True.

        If all 'obj.variants' have defined this attribute, then it's
        required and returns False.
        """
        if obj.is_group:
            for variant in obj.variants.select_related().all():
                if attr_code not in [x['code'] for x in variant.get_attrs()]:
                    return True
            return False

    @classmethod
    def template_for(cls, attr_code):
        """
        Returns an attribute template for attribute with a given code.
        """
        try:
            return cls.objects.get(code=attr_code).template
        except cls.DoesNotExist:
            return None

    @classmethod
    def filter_dict(cls, dictionary):
        """
        Filters the given dictionary, removes items where key is not
        an attribute code.
        """
        codes = [x.code for x in cls.objects.all()]
        return dict((k, v) for k, v in dictionary.items() if k in codes and v)


@python_2_unicode_compatible
class AttributeValueBase(models.Model):
    """
    Used to define values on a Product with relation to Attribute.
    """
    attribute = models.ForeignKey(
        Attribute, related_name='values', verbose_name=_('Attribute'))

    value_integer = models.IntegerField(_('Integer'), blank=True, null=True)
    value_boolean = models.NullBooleanField(_('Boolean'), blank=True)
    value_float = models.FloatField(_('Float'), blank=True, null=True)
    value_date = models.DateField(_('Date'), blank=True, null=True)
    value_option = models.ForeignKey(
        'AttributeOption', blank=True, null=True, verbose_name=_('Option'))

    value_file = FilerFileField(
        blank=True, null=True, related_name='value_files',
        verbose_name=_('File'))
    value_image = FilerImageField(
        blank=True, null=True, related_name='value_images',
        verbose_name=_('Image'))

    class Meta:
        abstract = True

    def __str__(self):
        return '{}: {}'.format(self.attribute.get_name(), self.value)

    @property
    def value(self):
        value = getattr(self, 'value_%s' % self.attribute.kind, None)
        if self.attribute.is_option:
            value = value.get_value() if value else None
        elif self.attribute.is_file:
            value = value.url if value else None
        return value

    @property
    def as_dict(self):
        data = self.attribute.as_dict
        data.update({'value': force_str(self.value)})
        return data

    @classmethod
    def value_for(cls, data):
        """
        Creates a temp object and return it's correct value.
        """
        field_names = [x.name for x in cls._meta.fields]
        for x in data.keys():
            if x not in field_names:
                del data[x]
        obj = cls(**data)
        return obj.value


class ProductAttributeValue(AttributeValueBase):
    """
    Through model for Product M2M relation to Attribute.
    """
    product = models.ForeignKey(
        Product, related_name='attribute_values', verbose_name=_('Product'))

    class Meta:
        db_table = 'catalog_product_attribute_values'
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')
        unique_together = ('attribute', 'product')


@python_2_unicode_compatible
class AttributeOption(TranslatableModel):
    """
    Option values for Attribute used when kind is Attribute.KIND_OPTION.
    """
    attribute = models.ForeignKey(
        Attribute, related_name='options', verbose_name=_('Attribute'))

    translations = TranslatedFields(
        value=models.CharField(_('Value'), max_length=128),
    )

    class Meta:
        db_table = 'catalog_attribute_options'
        verbose_name = _('Option')
        verbose_name_plural = _('Options')

    def __str__(self):
        return self.get_value()

    def get_value(self):
        return self.lazy_translation_getter('value')


def get_measure_alias(measure):
    """
    Adds prefixes to SI aliases and returns them in a dict.
    """
    SI_ALIAS = {}
    for unit in measure.SI_UNITS:
        alias = dict((v, k) for k, v in measure.ALIAS.items())[unit]
        for prefix_alias, prefix_unit in MeasureBase.SI_PREFIXES.items():
            SI_ALIAS['{}{}'.format(prefix_alias, alias)] = '{}{}'.\
                format(prefix_unit, unit)
    aliases = dict(measure.ALIAS.items() + SI_ALIAS.items())

    # Only return keys that are specified in MEASUREMENT_UNITS setting.
    if scs.MEASUREMENT_UNITS:
        for key, value in aliases.copy().items():
            if (value not in scs.MEASUREMENT_UNITS and
                    value != measure.STANDARD_UNIT):
                del aliases[key]
    return aliases


@python_2_unicode_compatible
class MeasurementBase(models.Model):
    """
    A base model used for setting measurements to objects.
    """
    KIND_WIDTH = 'width'
    KIND_HEIGHT = 'height'
    KIND_DEPTH = 'depth'
    KIND_WEIGHT = 'weight'
    KIND_CHOICES = (
        (KIND_WIDTH, _('Width')),
        (KIND_HEIGHT, _('Height')),
        (KIND_DEPTH, _('Depth')),
        (KIND_WEIGHT, _('Weight')),
    )

    aliases = [get_measure_alias(Distance), get_measure_alias(Weight)]
    UNIT_CHOICES = tuple(
        (v, k.capitalize()) for x in aliases for k, v in x.items())

    kind = models.CharField(
        _('Kind'), max_length=20,
        choices=KIND_CHOICES, default=KIND_CHOICES[0][0])
    value = models.DecimalField(
        _('Value'), max_digits=10, decimal_places=3)
    unit = models.CharField(
        _('Unit'), max_length=20,
        choices=UNIT_CHOICES, default=Distance.STANDARD_UNIT)

    class Meta:
        abstract = True

    def __str__(self):
        return '{}'.format(self.distance or self.weight)

    @property
    def distance(self):
        if self.unit in get_measure_alias(Distance).values():
            return Distance(**{self.unit: self.value})
        return None

    @property
    def weight(self):
        if self.unit in get_measure_alias(Weight).values():
            return Weight(**{self.unit: self.value})
        return None

    @property
    def as_dict(self):
        values = []
        measure = self.distance or self.weight

        if measure:
            # Add standard and original units to dict.
            values.append(('standard_unit', measure.STANDARD_UNIT))
            values.append(('standard_value',
                           getattr(measure, measure.STANDARD_UNIT, None)))
            values.append(('original_unit', self.unit))
            values.append(('original_value',
                           getattr(measure, self.unit, None)))

            # Add all values to dict.
            for unit in get_measure_alias(measure).values():
                values.append((unit, getattr(measure, unit, None)))

        # Cast all values to strings, remove null's and return the dict.
        return dict([(x[0], force_str(x[1])) for x in values
                    if x[1] is not None])


class ProductMeasurement(MeasurementBase):
    """
    Through model for product measurements.
    """
    product = models.ForeignKey(
        Product, related_name='measurements', verbose_name=_('Product'))

    class Meta:
        db_table = 'catalog_product_measurements'
        verbose_name = _('Measurement')
        verbose_name_plural = _('Measurements')
        unique_together = ('product', 'kind')


@python_2_unicode_compatible
class Flag(TranslatableModel):
    """
    Flags model to specify custom bool options on an object.
    """
    code = UnderscoreField(
        _('Code'), max_length=123, unique=True,
        help_text=scs.UNDERSCORE_FIELD_HELP_TEXT)

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
    )

    class Meta:
        db_table = 'catalog_flags'
        verbose_name = _('Flag')
        verbose_name_plural = _('Flags')

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_code(self):
        return self.code


@python_2_unicode_compatible
class ProductFlag(models.Model):
    """
    Through model for product flag relation.
    """
    product = models.ForeignKey(
        Product, related_name='flags', verbose_name=_('Product'))
    flag = models.ForeignKey(Flag, verbose_name=_('Flag'))
    is_true = models.BooleanField(_('Is True?'), default=True)

    class Meta:
        db_table = 'catalog_product_flags'
        verbose_name = _('Flag')
        verbose_name_plural = _('Flags')
        unique_together = ('product', 'flag')

    def __str__(self):
        return self.flag.get_name()

    def get_code(self):
        return self.flag.code

    @property
    def as_dict(self):
        return dict(
            name=force_str(self.__str__()),
            code=force_str(self.get_code()),
            is_true=self.is_true,
        )


@python_2_unicode_compatible
class RelatedProduct(models.Model):
    """
    Product relations model.
    """
    base_product = models.ForeignKey(
        Product, related_name='related_products',
        verbose_name=_('Base product'))

    product = models.ForeignKey(
        Product, verbose_name=_('Product'))

    kind = UnderscoreField(
        _('Kind'), max_length=255,
        choices=scs.RELATED_PRODUCT_KIND_CHOICES,
        default=scs.RELATED_PRODUCT_KIND_CHOICES[0][0])

    class Meta:
        db_table = 'catalog_related_products'
        verbose_name = _('Related Product')
        verbose_name_plural = _('Related Products')
        unique_together = ('base_product', 'product', 'kind')

    def __str__(self):
        return self.product.get_name()

    @property
    def as_dict(self):
        return dict(
            product=force_str(self.product_id),
            kind=force_str(self.kind),
        )
