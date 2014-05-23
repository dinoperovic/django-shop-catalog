# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _

from shop_catalog.models import Product


class ProductParentListFilter(SimpleListFilter):
    title = _('Parent')
    parameter_name = 'parent'

    def lookups(self, request, model_admin):
        lookups = ()

        for product in Product.objects.all():
            if product.is_group:
                lookups += (product.pk, product.get_name()),

        return lookups

    def queryset(self, request, queryset):
        if self.value():
            try:
                return queryset.get(pk=self.value()).variants.all()
            except Product.DoesNotExist:
                pass
        return queryset
