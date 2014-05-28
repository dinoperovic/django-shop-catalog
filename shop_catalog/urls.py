# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, url

from shop_catalog.views import (
    ProductListView, ProductDetailView,
    CategoryListView, CategoryDetailView,
    ProductVariantsJSONView)
from shop_catalog import settings as scs


# List of url patterns.
pats = []

if scs.HAS_CATEGORIES:
    pats.extend([
        url(r'^categories/$', CategoryListView.as_view(),
            name='category_list'),
        url(r'^categories/(?P<slug>[0-9A-Za-z-_.//]+)/$',
            CategoryDetailView.as_view(), name='category_detail'),
    ])

if scs.HAS_BRANDS:
    pats.extend([])

if scs.HAS_MANUFACTURERS:
    pats.extend([])

# Main patterns.
pats.extend([
    url(r'^$', ProductListView.as_view(), name='product_list'),
    url(r'^(?P<slug>[0-9A-Za-z-_.//]+)/variants/$',
        ProductVariantsJSONView.as_view(),
        name='product_variants'),
    url(r'^(?P<slug>[0-9A-Za-z-_.//]+)/$', ProductDetailView.as_view(),
        name='product_detail'),
])

urlpatterns = patterns('', *pats)
