# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from itertools import chain
from decimal import Decimal

from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify
from django.utils.module_loading import import_by_path

from shop.util.fields import CurrencyField
from cms.models.fields import PlaceholderField
from hvad.models import TranslatableModel, TranslatedFields
from mptt.models import MPTTModel
from mptt.fields import TreeForeignKey
from filer.fields.image import FilerFileField, FilerImageField
from measurement.measures import Distance, Weight
from measurement.base import MeasureBase

from shop_catalog.fields import NullableCharField
from shop_catalog.managers import CatalogManager, ProductManager
from shop_catalog.utils.noconflict import classmaker
from shop_catalog.utils import round_2
from shop_catalog import settings as scs


@python_2_unicode_compatible
class CatalogModel(models.Model):
    """
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
        db_table = 'shop_catalog_modifiers'
        verbose_name = _('Modifier')
        verbose_name_plural = _('Modifiers')

    def get_name(self):
        return self.lazy_translation_getter('name')

    def get_extra_cart_item_price_field(self, cart_item, request=None):
        """
        Returns extra price field for the given cart item.
        """
        if self.is_eligible_product(cart_item.product):
            for condition in self.conditions.select_related().all():
                if not condition.is_met(cart_item=cart_item, request=request):
                    return None
            return (self.get_name(), self.calculate_add_price(
                cart_item.current_total, cart_item.quantity))

    def get_extra_cart_price_field(self, cart, request=None):
        """
        Returns extra price field for entire cart.
        """
        for condition in self.conditions.select_related().all():
            if not condition.is_met(cart=cart, request=request):
                return None
        return (self.get_name(), self.calculate_add_price(cart.current_total))

    def calculate_add_price(self, price, quantity=1):
        """
        Calculates and returns an amount to be added to the given price.
        """
        if self.percent:
            add_price = (self.percent / 100) * price
        else:
            add_price = self.amount * quantity
        return add_price if price + add_price > 0 else price * -1

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
        db_table = 'shop_catalog_modifier_conditions'
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
        parent = str(self.parent_id) if self.parent is not None else None
        data = dict(
            parent=parent,
        )
        return dict(data.items() + super(CategoryBase, self).as_dict.items())


class Category(TranslatableModel, CategoryBase):
    """
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
            measurements=self.get_measurements(),
        )
        return dict(data.items() + self.get_categorization().items())

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

    @classmethod
    def filter_dict(cls, dictionary):
        """
        Filters the given dictionary, removes items where key is not
        an attribute code.
        """
        codes = [x.code for x in cls.objects.all()]
        return dict((k, v) for k, v in dictionary.items() if k in codes)


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
            value = value.get_value()
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
        db_table = 'shop_catalog_attribute_options'
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
        return dict([(x[0], str(x[1])) for x in values if x[1] is not None])


class ProductMeasurement(MeasurementBase):
    """
    Through model for product measurements.
    """
    product = models.ForeignKey(
        Product, related_name='measurements', verbose_name=_('Product'))

    class Meta:
        db_table = 'shop_catalog_product_measurements'
        verbose_name = _('Measurement')
        verbose_name_plural = _('Measurements')
        unique_together = ('product', 'kind')
