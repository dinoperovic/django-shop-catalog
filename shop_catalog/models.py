# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from itertools import chain
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from django.core.urlresolvers import reverse
from django.contrib.gis.measure import D
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify

from shop.util.fields import CurrencyField
from cms.models.fields import PlaceholderField
from hvad.models import TranslatableModel, TranslatedFields
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from filer.fields.image import FilerFileField, FilerImageField

from shop_catalog.fields import NullableCharField
from shop_catalog.managers import CatalogManager, ProductManager
from shop_catalog.utils.noconflict import classmaker
from shop_catalog.utils import round_2
from shop_catalog import settings as scs


@python_2_unicode_compatible
class CatalogModel(models.Model):
    """
    Catalog model.
    Defines common fields for catalog objects and abstracts some
    standard getter methods.

    When an object inherits from CatalogModel, it can define a
    CatalogManager as a manager for ease of getting "active" objects.
    """
    active = models.BooleanField(default=True, verbose_name=_('Active'))
    date_added = models.DateTimeField(_('Date added'), auto_now_add=True)
    last_modified = models.DateTimeField(_('Last modified'), auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.get_name()

    def get_absolute_url(self):
        return None

    def get_name(self):
        return str(self.pk)

    def get_slug(self):
        return slugify(self.get_name())

    @property
    def as_dict(self):
        return dict(
            pk=str(self.pk),
            active=self.active,
            name=str(self.get_name()),
            slug=str(self.get_slug()),
            url=str(self.get_absolute_url()),
            date_added=str(self.date_added),
            last_modified=str(self.last_modified),
        )


class CategoryBase(MPTTModel, CatalogModel):
    """
    Category base model.
    Base model for categorization, uses django-mptt for it's tree
    management.
    """
    parent = TreeForeignKey(
        'self', blank=True, null=True, related_name='children')

    class Meta:
        abstract = True

    @property
    def as_dict(self):
        parent = str(self.parent_id) if self.parent is not None else None
        data = dict(
            parent=parent,
        )
        return dict(data.items() + super(CategoryBase, self).as_dict.items())


class Category(TranslatableModel, CategoryBase):
    """
    Category model.
    A categorization layer inherited from CategoryBase.
    """
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
        return reverse('catalog_category_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


class Brand(TranslatableModel, CategoryBase):
    """
    Brand model.
    A categorization layer inherited from CategoryBase.
    """
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
        return reverse('catalog_brand_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


class Manufacturer(TranslatableModel, CategoryBase):
    """
    Manufacturer model.
    A categorization layer inherited from CategoryBase.
    """
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
        return reverse('catalog_manufacturer_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')


@python_2_unicode_compatible
class ProductBase(MPTTModel, CatalogModel):
    """
    Product base model.
    Base fields and calculations are defined here and all objects that
    can be added to cart must inherit from this model.
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
                    'Product. Only top level products (without a parent) are '
                    'listed.'))

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

        return round_2(price)

    def get_unit_price(self):
        if self.is_price_inherited:
            return self.parent.get_unit_price()
        return round_2(self.unit_price)

    def get_discount_percent(self):
        if self.is_discount_inherited:
            return self.parent.get_discount_percent()
        return self.discount_percent or 0

    def get_product_reference(self):
        return self.upc or str(self.pk)

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
    def is_available(self):
        return self.quantity is None or self.quantity > 0

    @property
    def is_discounted(self):
        if self.is_discount_inherited:
            return self.parent.is_discounted
        return not not self.discount_percent

    @property
    def is_price_inherited(self):
        return self.is_variant and not self.unit_price

    @property
    def is_discount_inherited(self):
        return self.is_variant and self.discount_percent is None

    @property
    def as_dict(self):
        """
        Returns a dicionary with product properties.
        """
        parent = str(self.parent_id) if self.is_variant else None
        quantity = str(self.quantity) if self.quantity else None

        featured_image = self.get_featured_image()
        featured_image = str(featured_image.url) if featured_image else None

        data = dict(
            upc=self.upc,
            parent=parent,
            unit_price=str(self.get_unit_price()),
            price=str(self.get_price()),
            is_price_inherited=self.is_price_inherited,
            quantity=quantity,
            is_available=self.is_available,
            is_discountable=self.is_discountable,
            is_discounted=self.is_discounted,
            is_discount_inherited=self.is_discount_inherited,
            discount_percent=str(self.get_discount_percent()),
            can_be_added_to_cart=self.can_be_added_to_cart,
            featured_image=featured_image,
            attrs=self.get_attrs(),
        )

        extra_dict = self.get_extra_dict()
        if extra_dict:
            data = dict(data.items() + extra_dict.items())

        return dict(data.items() + super(ProductBase, self).as_dict.items())

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

    def get_variations(self):
        """
        If product is a group product (has variants) returns a list of
        all it's variants attributes grouped by code in a dictionary.
        """
        variations = {}

        if self.is_group:
            variants = self.variants.select_related().all()
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

        return variations.values()

    def get_variant(self, **kwargs):
        """
        Returns a variant which attributes match the given kwargs.
        """
        if not self.is_group:
            return None

        # Cast keys and values to str and filter out empty values.
        kwargs = [(str(k), str(v)) for k, v in kwargs.items() if v]

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
        kwargs = [(str(k), str(v)) for k, v in kwargs.items() if v]

        # Loop through variants and compare their attribute values
        # to kwargs. Make sure that all kwargs are a part of attributes.
        for obj in self.variants.select_related().all():
            attrs = [(x['code'], x['value']) for x in obj.get_attrs()]
            if set(kwargs).issubset(attrs):
                variants.append(obj)

        # Return variants if any.
        return variants if any(variants) else None


class Product(TranslatableModel, ProductBase):
    """
    Product model.
    Inherits from ProductBase and adds more specific fields like
    categorization etc.
    """
    __metaclass__ = classmaker()

    featured_image = FilerImageField(
        blank=True, null=True, related_name='featured_images',
        verbose_name=_('Featured image'))

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

    media = PlaceholderField(
        'shop_catalog_product_media', related_name='product_media_set')
    body = PlaceholderField(
        'shop_catalog_product_body', related_name='product_body_set')

    objects = ProductManager()

    class Meta:
        db_table = 'shop_catalog_products'
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def get_absolute_url(self):
        return reverse('catalog_product_detail', args=[self.get_slug()])

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_slug(self):
        return self.lazy_translation_getter('slug')

    def get_featured_image(self):
        return self.featured_image

    def get_extra_dict(self):
        data = dict(
            is_media_inherited=self.is_media_inherited,
            is_body_inherited=self.is_body_inherited,
        )
        return dict(data.items() + self.get_categorization().items())

    @property
    def is_media_inherited(self):
        return self.is_variant and not self.media.get_plugins().exists()

    @property
    def is_body_inherited(self):
        return self.is_variant and not self.body.get_plugins().exists()

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


@python_2_unicode_compatible
class Attribute(TranslatableModel):
    """
    Attribute model.
    Used to define different types of attributes to be assigned on a
    Product variant. Eg. For a t-shirt attributes could be size, color,
    pattern etc.
    """
    KIND_OPTION = 'option'
    KIND_FILE = 'file'
    KIND_IMAGE = 'image'
    KIND_CHOICES = (
        ('text', _('Text')),
        ('integer', _('Integer')),
        ('boolean', _('True / False')),
        ('float', _('Float')),
        ('richtext', _('Richtext')),
        ('date', _('Date')),
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

    @property
    def is_file(self):
        return self.kind in (self.KIND_FILE, self.KIND_IMAGE)

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


@python_2_unicode_compatible
class AttributeValueBase(models.Model):
    """
    Attribute Value base model.
    Used to define values on a Product with relation to Attribute.
    """
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
            value = value.value
        elif self.attribute.is_file:
            value = value.url if value else None
        return value

    @property
    def as_dict(self):
        template = (
            str(self.attribute.template) if self.attribute.template else None)

        return dict(
            code=str(self.attribute.get_slug()),
            name=str(self.attribute.get_name()),
            type=str(self.attribute.kind),
            template=template,
            value=str(self.value),
        )


class ProductAttributeValue(AttributeValueBase):
    """
    Product Attribute Value model.
    Through model for Product M2M relation to Attribute.
    """
    product = models.ForeignKey(
        Product, related_name='attribute_values', verbose_name=_('Product'))

    class Meta:
        db_table = 'shop_catalog_product_attribute_values'
        verbose_name = _('Attribute')
        verbose_name_plural = _('Attributes')
        unique_together = ('attribute', 'product')


@python_2_unicode_compatible
class AttributeOption(models.Model):
    """
    Attribute Option model.
    Option values for Attribute used when kind is Attribute.KIND_OPTION.
    """
    attribute = models.ForeignKey(
        Attribute, related_name='options', verbose_name=_('Attribute'))
    value = models.CharField(_('Value'), max_length=128)

    class Meta:
        db_table = 'shop_catalog_attribute_options'
        verbose_name = _('Option')
        verbose_name_plural = _('Options')

    def __str__(self):
        return self.value


@python_2_unicode_compatible
class MeasureBase(models.Model):
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
    UNIT_CHOICES = tuple((v, k.capitalize()) for k, v in D.ALIAS.items())

    kind = models.CharField(
        _('Measure'), max_length=20,
        choices=KIND_CHOICES, default=KIND_CHOICES[0][0])
    value = models.DecimalField(
        _('Value'), max_digits=10, decimal_places=3)
    unit = models.CharField(
        _('Unit'), max_length=20,
        choices=UNIT_CHOICES, default=D.STANDARD_UNIT)

    class Meta:
        abstract = True

    def __str__(self):
        return self.distance

    @property
    def distance(self):
        return D(**{self.unit: self.value})


class ProductMeasure(MeasureBase):
    product = models.ForeignKey(
        Product, related_name='measures', verbose_name=_('Product'))

    class Meta:
        db_table = 'shop_catalog_product_measures'
        verbose_name = _('Measure')
        verbose_name_plural = _('Measures')
        unique_together = ('product', 'kind')
