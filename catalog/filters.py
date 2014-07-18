# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Q
from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _

from catalog.models import Product


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
            queryset = queryset.filter(
                Q(pk=self.value()) | Q(parent_id=self.value()))

        return queryset
