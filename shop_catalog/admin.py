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
from hvad.admin import TranslatableAdmin

from shop_catalog.models import (
    Category, Brand, Manufacturer, Product, Attribute, ProductAttributeValue,
    AttributeOption)
from shop_catalog.forms import ProductModelForm, ProductAttributeValueModelForm
from shop_catalog.filters import ProductParentListFilter
from shop_catalog.utils import slug_num_suffix
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
                'fields': ('unit_price', 'discount_percent'),
            }),
            (_('Date information'), {
                'fields': ('date_added', 'last_modified'),
                'classes': ('collapse', ),
            }),
        )

    def get_urls(self):
        urls = super(ProductAdmin, self).get_urls()
        product_urls = patterns(
            '',
            url(r'^(?P<pk>\d+)/add_variant/$',
                self.admin_site.admin_view(self.add_variant),
                name='shop_catalog_product_add_variant'),
        )
        return product_urls + urls

    def get_name(self, obj):
        if obj.is_variant:
            return '{} > {}'.format(obj.parent.get_name(), obj.get_name())
        return obj.get_name()
    get_name.short_description = _('Name')

    def get_slug(self, obj):
        return obj.get_slug()
    get_slug.short_description = _('Slug')

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
            reverse('admin:shop_catalog_product_add'), urlencode(data)))


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
