# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from cms.admin.placeholderadmin import (
    PlaceholderAdminMixin, FrontendEditableAdminMixin)
from hvad.admin import TranslatableAdmin

from shop_catalog.models import (
    Category, Brand, Manufacturer, Product, Attribute, ProductAttributeValue,
    AttributeOption)
from shop_catalog.forms import ProductModelForm, ProductAttributeValueModelForm
from shop_catalog.filters import ProductParentListFilter
from shop_catalog import settings as scs


class CategoryAdmin(
        TranslatableAdmin, FrontendEditableAdminMixin, PlaceholderAdminMixin,
        admin.ModelAdmin):
    frontend_editable_fields = ()
    readonly_fields = ('date_added', 'last_modified')


class BrandAdmin(
        TranslatableAdmin, FrontendEditableAdminMixin, PlaceholderAdminMixin,
        admin.ModelAdmin):
    frontend_editable_fields = ()
    readonly_fields = ('date_added', 'last_modified')


class ManufacturerAdmin(
        TranslatableAdmin, FrontendEditableAdminMixin, PlaceholderAdminMixin,
        admin.ModelAdmin):
    frontend_editable_fields = ()
    readonly_fields = ('date_added', 'last_modified')


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    form = ProductAttributeValueModelForm
    extra = 0


class ProductAdmin(
        TranslatableAdmin, FrontendEditableAdminMixin,
        PlaceholderAdminMixin, admin.ModelAdmin):
    form = ProductModelForm
    change_form_template = scs.PRODUCT_CHANGE_FORM_TEMPLATE

    list_display = ('get_name', 'get_slug', 'parent', 'unit_price')
    list_filter = (ProductParentListFilter,)

    frontend_editable_fields = ()
    readonly_fields = ('date_added', 'last_modified')

    inlines = (ProductAttributeValueInline, )

    def __init__(self, *args, **kwargs):
        super(ProductAdmin, self).__init__(*args, **kwargs)
        self.prepopulated_fields = {'slug': ('name', )}
        self.fieldsets = (
            (None, {
                'fields': (
                    'name', 'slug', 'active'),
            }),
            (None, {
                'fields': ('parent', ),
            }),
            (_('Categorization'), {
                'fields': ('category', 'brand', 'manufacturer'),
            }),
            (_('Price'), {
                'fields': ('unit_price', ),
            }),
            (_('Date information'), {
                'fields': ('date_added', 'last_modified'),
                'classes': ('collapse', ),
            }),
        )

    def get_name(self, obj):
        if obj.is_variant:
            return '{} > {}'.format(obj.parent.get_name(), obj.get_name())
        return obj.get_name()
    get_name.short_description = _('Name')

    def get_slug(self, obj):
        return obj.get_slug()
    get_slug.short_description = _('Slug')


class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption
    extra = 0


class AttributeAdmin(TranslatableAdmin):
    list_display = ('get_name', 'code', 'kind')
    list_filter = ('kind', )

    inlines = (AttributeOptionInline, )

    def __init__(self, *args, **kwargs):
        super(AttributeAdmin, self).__init__(*args, **kwargs)
        self.prepopulated_fields = {'code': ('name', )}
        self.fields = ('name', 'code', 'kind', 'template')

    def get_name(self, obj):
        return obj.get_name()
    get_name.short_description = _('Name')


admin.site.register(Category, CategoryAdmin)
admin.site.register(Brand, BrandAdmin)
admin.site.register(Manufacturer, ManufacturerAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Product, ProductAdmin)
