# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.conf.urls import url, patterns
from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from cms.admin.placeholderadmin import (
    PlaceholderAdminMixin, FrontendEditableAdminMixin)
from hvad.admin import TranslatableAdmin, TranslatableTabularInline
from mptt.admin import MPTTModelAdmin

from catalog.models import (
    Modifier, ModifierCondition, ModifierCode, Category, Brand, Manufacturer,
    Tax, Product, Attribute, ProductAttributeValue, AttributeOption,
    ProductMeasurement, Flag, ProductFlag, RelatedProduct)

from catalog.forms import (
    ModifierModelForm, CategoryModelForm, BrandModelForm,
    ManufacturerModelForm, ProductModelForm,
    ProductAttributeValueInlineFormSet, ProductAttributeValueModelForm,
    RelatedProductModelForm, RelatedProductInlineFormSet)

from catalog.filters import ProductParentListFilter
from catalog.utils import slug_num_suffix
from catalog import settings as scs


class ModifierConditionInline(admin.TabularInline):
    model = ModifierCondition
    extra = 0


class ModifierCodeInline(admin.TabularInline):
    model = ModifierCode
    extra = 0


class ModifierAdmin(TranslatableAdmin):
    form = ModifierModelForm
    list_display = (
        'get_name', 'code', 'amount', 'percent', 'kind', 'active',
        'all_translations')
    list_filter = ('date_added', 'last_modified', 'active', 'kind')

    readonly_fields = ('date_added', 'last_modified')

    def __init__(self, *args, **kwargs):
        super(ModifierAdmin, self).__init__(*args, **kwargs)
        self.prepopulated_fields = {'code': ('name', )}
        self.fieldsets = (
            (None, {
                'fields': ('name', 'code'),
            }),
            (None, {
                'fields': ('amount', 'percent'),
            }),
            (None, {
                'fields': ('kind', ),
            }),
            (None, {
                'fields': ('active', 'date_added', 'last_modified'),
            }),
        )
        self.inlines = self.get_inlines()

    def get_inlines(self):
        inlines = (ModifierConditionInline, )
        if scs.HAS_MODIFIER_CODES:
            inlines += ModifierCodeInline,
        return inlines

    def get_name(self, obj):
        return obj.get_name()
    get_name.short_description = _('Name')


class CategoryAdminBase(
        TranslatableAdmin, MPTTModelAdmin, FrontendEditableAdminMixin,
        PlaceholderAdminMixin, admin.ModelAdmin):
    list_display = ('get_name', 'get_slug', 'all_translations')
    list_filter = ('date_added', 'last_modified', 'active', 'parent')

    frontend_editable_fields = ()
    readonly_fields = ('date_added', 'last_modified')
    filter_horizontal = ('modifiers', )

    def __init__(self, *args, **kwargs):
        super(CategoryAdminBase, self).__init__(*args, **kwargs)
        self.prepopulated_fields = {'slug': ('name', )}

        self.fieldsets = (
            (None, {
                'fields': ('name', 'slug'),
            }),
            (None, {
                'fields': ('active', 'date_added', 'last_modified'),
            }),
            (None, {
                'fields': ('parent', ),
            }),
            (None, {
                'fields': ('featured_image', 'description'),
            }),
            (None, {
                'fields': ('modifiers', ),
            }),
        )

    def get_name(self, obj):
        dashes = '---' * obj.get_ancestors().count()
        return '{} {}'.format(dashes, obj.get_name())
    get_name.short_description = _('Name')

    def get_slug(self, obj):
        return obj.get_slug()
    get_slug.short_description = _('Slug')


class CategoryAdmin(CategoryAdminBase):
    form = CategoryModelForm


class BrandAdmin(CategoryAdminBase):
    form = BrandModelForm


class ManufacturerAdmin(CategoryAdminBase):
    form = ManufacturerModelForm


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    form = ProductAttributeValueModelForm
    formset = ProductAttributeValueInlineFormSet
    extra = 0


class TaxAdmin(admin.ModelAdmin):
    list_display = ('name', 'percent')


class ProductMeasurementInline(admin.TabularInline):
    model = ProductMeasurement
    extra = 0
    max_num = len(ProductMeasurement.KIND_CHOICES)


class ProductFlagInline(admin.TabularInline):
    model = ProductFlag
    extra = 0


class RelatedProductInline(admin.TabularInline):
    model = RelatedProduct
    fk_name = 'base_product'
    form = RelatedProductModelForm
    formset = RelatedProductInlineFormSet
    extra = 0
    raw_id_fields = ('product', )


class ProductAdmin(
        TranslatableAdmin, MPTTModelAdmin, FrontendEditableAdminMixin,
        PlaceholderAdminMixin, admin.ModelAdmin):
    form = ProductModelForm
    change_form_template = scs.PRODUCT_CHANGE_FORM_TEMPLATE

    list_display = (
        'get_name', 'get_slug', 'get_product_reference', 'get_unit_price',
        'get_discount_percent', 'get_price', 'get_quantity', 'is_discountable',
        'active', 'all_translations')
    list_filter = (
        'date_added', 'last_modified', 'active', 'is_discountable',
        ProductParentListFilter)

    frontend_editable_fields = ()
    mptt_level_indent = 0
    readonly_fields = ('date_added', 'last_modified')
    search_fields = ('upc', 'id', 'translations__name', 'translations__slug')
    raw_id_fields = ('parent', )
    filter_horizontal = ('modifiers', )

    inlines = (
        ProductFlagInline, ProductMeasurementInline,
        ProductAttributeValueInline, RelatedProductInline)

    def __init__(self, *args, **kwargs):
        super(ProductAdmin, self).__init__(*args, **kwargs)
        self.prepopulated_fields = {'slug': ('name', )}
        self.list_filter += self.get_categorization_list_filter()

        self.fieldsets = (
            (None, {
                'fields': ('upc', 'name', 'slug'),
            }),
            (None, {
                'fields': ('active', 'date_added', 'last_modified'),
            }),
            (None, {
                'fields': ('parent', ),
            }),
            (None, {
                'fields': ('featured_image', 'description'),
            }),
        )
        self.fieldsets += self.get_categorization_fieldset()
        self.fieldsets += (
            (_('Price'), {
                'fields': (
                    'unit_price', 'discount_percent', 'tax',
                    'is_discountable'),
            }),
            (None, {
                'fields': ('quantity', ),
            }),
            (None, {
                'fields': ('modifiers', ),
            }),
        )

    def get_urls(self):
        urls = super(ProductAdmin, self).get_urls()
        product_urls = patterns(
            '',
            url(r'^(?P<pk>\d+)/add_variant/$',
                self.admin_site.admin_view(self.add_variant),
                name='catalog_product_add_variant'),
        )
        return product_urls + urls

    def get_categorization_list_filter(self):
        list_filter = ()
        if scs.HAS_CATEGORIES:
            list_filter += 'category',
        if scs.HAS_BRANDS:
            list_filter += 'brand',
        if scs.HAS_MANUFACTURERS:
            list_filter += 'manufacturer',
        return list_filter

    def get_categorization_fieldset(self):
        fields = ()
        if scs.HAS_CATEGORIES:
            fields += 'category',
        if scs.HAS_BRANDS:
            fields += 'brand',
        if scs.HAS_MANUFACTURERS:
            fields += 'manufacturer',

        if fields:
            return (_('Categorization'), {
                'fields': fields,
                'description': _('If product is a variant, categorization '
                                 'will be inherited from it\'s parent and is '
                                 'not necessary to specify it again.')}),
        return ()

    def get_name(self, obj):
        if obj.is_variant:
            return '--- {}'.format(obj.get_name())
        return obj.get_name()
    get_name.short_description = _('Name')

    def get_slug(self, obj):
        return obj.get_slug()
    get_slug.short_description = _('Slug')

    def get_unit_price(self, obj):
        return obj.get_unit_price()
    get_unit_price.short_description = _('Unit price')

    def get_discount_percent(self, obj):
        return '{}%'.format(obj.get_discount_percent())
    get_discount_percent.short_description = _('Discount percent')

    def get_price(self, obj):
        return obj.get_price()
    get_price.short_description = _('Price')

    def get_product_reference(self, obj):
        return obj.get_product_reference()
    get_product_reference.short_description = _('Reference')

    def get_quantity(self, obj):
        return obj.quantity if obj.quantity is not None else _('~')
    get_quantity.short_description = _('Quantity')

    def add_variant(self, request, pk):
        """
        Redirects to product add view and prepopulates values for
        a variant product.
        """
        product = get_object_or_404(Product, pk=pk)
        if product.is_variant:
            product = product.parent

        num = slug_num_suffix(product.get_slug(), Product.objects.language())
        data = {
            'name': '{} #{}'.format(product.get_name(), num),
            'slug': '{}-{}'.format(product.get_slug(), num),
            'parent': product.pk,
        }
        return HttpResponseRedirect('{}?{}'.format(
            reverse('admin:catalog_product_add'), urlencode(data)))


class AttributeOptionInline(TranslatableTabularInline):
    model = AttributeOption
    extra = 0


class AttributeAdmin(TranslatableAdmin):
    list_display = ('get_name', 'code', 'kind', 'all_translations')
    list_filter = ('kind', )

    inlines = (AttributeOptionInline, )

    def __init__(self, *args, **kwargs):
        super(AttributeAdmin, self).__init__(*args, **kwargs)
        self.prepopulated_fields = {'code': ('name', )}
        self.fields = ('name', 'code', 'kind', 'template')

    def get_name(self, obj):
        return obj.get_name()
    get_name.short_description = _('Name')


class FlagAdmin(TranslatableAdmin):
    list_display = ('get_name', 'code', 'all_translations')

    def __init__(self, *args, **kwargs):
        super(FlagAdmin, self).__init__(*args, **kwargs)

    def get_name(self, obj):
        return obj.get_name()
    get_name.short_description = _('Name')


if scs.HAS_CATEGORIES:
    admin.site.register(Category, CategoryAdmin)
if scs.HAS_BRANDS:
    admin.site.register(Brand, BrandAdmin)
if scs.HAS_MANUFACTURERS:
    admin.site.register(Manufacturer, ManufacturerAdmin)

admin.site.register(Modifier, ModifierAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Tax, TaxAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Flag, FlagAdmin)
