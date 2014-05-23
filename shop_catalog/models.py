# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify

from shop.util.fields import CurrencyField
from hvad.models import TranslatableModel, TranslatedFields
from hvad.manager import TranslationManager
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey

from shop_catalog.utils.noconflict import classmaker
from shop_catalog import settings as scs


class CatalogManager(TranslationManager):
    def active(self, language_code=None):
        return self.language(language_code).filter(active=True)

    def get_by_slug(self, slug, language_code=None):
        return self.active(language_code).get(slug=slug)


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
    parent = TreeForeignKey(
        'self', blank=True, null=True, related_name='variants',
        verbose_name=_('Parent'),
        help_text=_('If this is a "variant" of a Product, select that '
                    'Product.'))

    unit_price = CurrencyField(verbose_name=_('Unit price'))

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_name()

    def get_price(self):
        return self.unit_price

    def get_product_reference(self):
        return str(self.pk)

    @property
    def can_be_added_to_cart(self):
        return self.active

    @property
    def is_top_level(self):
        return self.parent_id is None

    @property
    def is_group(self):
        return self.is_top_level and self.variants.exists()

    @property
    def is_variant(self):
        return not self.is_top_level


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

    objects = CatalogManager()

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
    KIND_CHOICES = (
        ('text', _('Text')),
        ('integer', _('Integer')),
        ('boolean', _('True / False')),
        ('float', _('Float')),
        ('richtext', _('Richtext')),
        ('date', _('Date')),
        ('file', _('File')),
        ('image', _('Image')),
    )

    code = models.SlugField(
        _('Code'), max_length=128, unique=True,
        help_text=scs.SLUG_FIELD_HELP_TEXT)

    kind = models.CharField(
        max_length=20, choices=KIND_CHOICES, default=KIND_CHOICES[0][0],
        verbose_name=_('Type'))

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


class AttributeValueBase(models.Model):
    attribute = models.ForeignKey(Attribute, verbose_name=_('Attribute'))

    value_text = models.CharField(
        _('Text'), max_length=255, blank=True, null=True)
    value_integer = models.IntegerField(_('Integer'), blank=True, null=True)
    value_boolean = models.NullBooleanField(_('Boolean'), blank=True)
    value_float = models.FloatField(_('Float'), blank=True, null=True)
    value_richtext = models.TextField(_('Richtext'), blank=True, null=True)
    value_date = models.DateField(_('Date'), blank=True, null=True)
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
