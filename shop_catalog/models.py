# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from itertools import chain
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify

from shop.util.fields import CurrencyField
from hvad.models import TranslatableModel, TranslatedFields
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey

from shop_catalog.managers import CatalogManager, ProductManager
from shop_catalog.utils.noconflict import classmaker
from shop_catalog import settings as scs


@python_2_unicode_compatible
class CatalogModel(models.Model):
    active = models.BooleanField(default=True, verbose_name=_('Active'))
    date_added = models.DateTimeField(_('Date added'), auto_now_add=True)
    last_modified = models.DateTimeField(_('Last modified'), auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_name()

    def get_name(self):
        return str(self.pk)

    def get_slug(self):
        return slugify(self.get_name())


class CategoryBase(MPTTModel, CatalogModel):
    parent = TreeForeignKey(
        'self', blank=True, null=True, related_name='children')

    class Meta:
        abstract = True


class Category(TranslatableModel, CategoryBase):
    __metaclass__ = classmaker()

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
        slug=models.SlugField(
            _('Slug'), max_length=128, unique=True,
            help_text=scs.SLUG_FIELD_HELP_TEXT),
    )

    objects = CatalogManager()

    class Meta:
        db_table = 'shop_catalog_categories'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')

    def get_absolute_url(self):
        return reverse('category_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


class Brand(TranslatableModel, CategoryBase):
    __metaclass__ = classmaker()

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
        slug=models.SlugField(
            _('Slug'), max_length=128, unique=True,
            help_text=scs.SLUG_FIELD_HELP_TEXT),
    )

    objects = CatalogManager()

    class Meta:
        db_table = 'shop_catalog_brands'
        verbose_name = _('Brand')
        verbose_name_plural = _('Brands')

    def get_absolute_url(self):
        return reverse('brand_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


class Manufacturer(TranslatableModel, CategoryBase):
    __metaclass__ = classmaker()

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
        slug=models.SlugField(
            _('Slug'), max_length=128, unique=True,
            help_text=scs.SLUG_FIELD_HELP_TEXT),
    )

    objects = CatalogManager()

    class Meta:
        db_table = 'shop_catalog_manufacturers'
        verbose_name = _('Manufacturer')
        verbose_name_plural = _('Manufacturers')

    def get_absolute_url(self):
        return reverse('manufacturer_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


@python_2_unicode_compatible
class ProductBase(MPTTModel, CatalogModel):
    attrs = None

    parent = TreeForeignKey(
        'self', blank=True, null=True, related_name='variants',
        verbose_name=_('Parent'),
        help_text=_('If this is a "variant" of a Product, select that '
                    'Product. Only top level products (without a parent) are '
                    'listed.'))

    unit_price = CurrencyField(
        verbose_name=_('Unit price'),
        help_text=_('If Product is a "variant" (parent is selected) and price '
                    'is "0", unit price is inherited from its parent.'))

    discount_percent = models.DecimalField(
        _('Discount percent'), blank=True, null=True,
        max_digits=4, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))])

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_name()

    def get_price(self):
        """ Checks if price is inherited and returns the correct price. """
        price = self.unit_price
        if self.is_price_inherited:
            price = self.parent.get_price()

        if self.is_discounted:
            price -= (self.discount_percent * price) / Decimal('100')

        return price

    def get_product_reference(self):
        return str(self.pk)

    @property
    def can_be_added_to_cart(self):
        """ Checks that product is active and doesn't have variants. """
        return self.active and not self.is_group

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
    def is_price_inherited(self):
        return self.is_variant and not self.unit_price

    @property
    def is_discounted(self):
        return not not self.discount_percent

    @property
    def as_json(self):
        return dict(
            pk=unicode(self.pk),
            parent=unicode(self.parent_id),
            name=unicode(self.get_name()),
            slug=unicode(self.get_slug()),
            unit_price=unicode(self.unit_price),
            price=unicode(self.get_price()),
            is_discounted=self.is_discounted,
            discount_percent=unicode(self.discount_percent or 0),
            can_be_added_to_cart=self.can_be_added_to_cart,
            attrs=self.get_attrs(),
        )

    def get_attrs(self):
        """
        If product is not a group (doesn't have variants) returns a
        formated list of dictionaries with product attributes.
        """
        attrs = []

        if not self.is_group:
            attr_values = self.attribute_values.select_related().all()

            for value in attr_values:
                attrs.append({
                    'name': value.attribute.get_name(),
                    'code': value.attribute.get_slug(),
                    'template': value.attribute.template,
                    'value': unicode(value.value),
                })

        return attrs

    def get_variations(self):
        """
        If product is a group product (has variants) returns a list of
        all it's variants attributes grouped by code in a dictionary with
        'name', 'code' and 'values' keys.
        """
        variations = {}

        if self.is_group:
            variants = self.variants.select_related().all()
            attr_values = list(chain(*[x.get_attrs() for x in variants]))

            for value in attr_values:
                if value['code'] not in variations:
                    variations[value['code']] = {
                        'name': value['name'],
                        'code': value['code'],
                        'template': value['template'],
                        'values': [],
                    }

                if value['value'] not in variations[value['code']]['values']:
                    variations[value['code']]['values'].append(value['value'])

        return variations.values()

    def get_variant(self, **kwargs):
        """
        Returns a variant which attributes match the given kwargs.
        """
        if not self.is_group:
            return None

        # Cast keys and values to unicode.
        kwargs = [(unicode(k), unicode(v)) for k, v in kwargs.iteritems()]

        # Loop throug variants and compare their attribute values to
        # kwargs. If they match, return that variant.
        for obj in self.variants.select_related().all():
            attrs = [(x['code'], x['value']) for x in obj.get_attrs()]
            if sorted(attrs) == sorted(kwargs):
                return obj

        # No variants match the given kwargs, return None.
        return None


class Product(TranslatableModel, ProductBase):
    __metaclass__ = classmaker()

    category = TreeForeignKey(
        Category, blank=True, null=True, related_name='products')
    brand = TreeForeignKey(
        Brand, blank=True, null=True, related_name='products')
    manufacturer = TreeForeignKey(
        Manufacturer, blank=True, null=True, related_name='products')

    attributes = models.ManyToManyField(
        'Attribute', through='ProductAttributeValue',
        related_name='attributes', verbose_name=_('Attributes'))

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128),
        slug=models.SlugField(
            _('Slug'), max_length=128, unique=True,
            help_text=scs.SLUG_FIELD_HELP_TEXT),
    )

    objects = ProductManager()

    class Meta:
        db_table = 'shop_catalog_products'
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


@python_2_unicode_compatible
class Attribute(TranslatableModel):
    KIND_OPTION = 'option'
    KIND_CHOICES = (
        ('text', _('Text')),
        ('integer', _('Integer')),
        ('boolean', _('True / False')),
        ('float', _('Float')),
        ('richtext', _('Richtext')),
        ('date', _('Date')),
        (KIND_OPTION, _('Option')),
        ('file', _('File')),
        ('image', _('Image')),
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
        help_text=_('You can select a template for rendering this "Attribute" '
                    'or leave it empty for the default (dropdown) look.'))

    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=128)
    )

    class Meta:
        db_table = 'shop_catalog_attributes'
        ordering = ('code', )
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')

    def __str__(self):
        return '{} ({})'.format(
            self.get_name(), dict(self.KIND_CHOICES)[self.kind])

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


class AttributeValueBase(models.Model):
    attribute = models.ForeignKey(
        Attribute, related_name='values', verbose_name=_('Attribute'))

    value_text = models.CharField(
        _('Text'), max_length=255, blank=True, null=True)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True)
    value_boolean = models.NullBooleanField(_('Boolean'), blank=True)
    value_float = models.FloatField(_('Float'), blank=True, null=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_date = models.DateField(_('Date'), blank=True, null=True)
    value_option = models.ForeignKey(
        'AttributeOption', blank=True, null=True, verbose_name=_('Option'))
    value_file = models.FileField(
        _('File'), upload_to='shop_catalog/', max_length=255,
        blank=True, null=True)
    value_image = models.ImageField(
        _('Image'), upload_to='shop_catalog/', max_length=255,
        blank=True, null=True)

    class Meta:
        abstract = True

    def __str__(self):
        return '{}: {}'.format(self.attribute.get_name(), self.value)

    @property
    def value(self):
        return getattr(self, 'value_%s' % self.attribute.kind, None)


class ProductAttributeValue(AttributeValueBase):
    product = models.ForeignKey(
        Product, related_name='attribute_values', verbose_name=_('Product'))

    class Meta:
        db_table = 'shop_catalog_product_attribute_values'
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')
        unique_together = ('attribute', 'product')


@python_2_unicode_compatible
class AttributeOption(models.Model):
    attribute = models.ForeignKey(
        Attribute, related_name='options', verbose_name=_('Attribute'))
    value = models.CharField(_('Value'), max_length=128)

    class Meta:
        db_table = 'shop_catalog_attribute_options'
        verbose_name = _('Option')
        verbose_name_plural = _('Options')

    def __str__(self):
        return self.value
