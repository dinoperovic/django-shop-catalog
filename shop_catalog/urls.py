# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, url

from shop.views import ShopTemplateView

from shop_catalog.views import (
    ProductListView, ProductDetailView,
    CategoryListView, CategoryDetailView,
    BrandListView, BrandDetailView,
    ManufacturerListView, ManufacturerDetailView,
    ProductVariantsJSONView)
from shop_catalog import settings as scs


# List of url patterns.
pats = []

if scs.HAS_CATEGORIES:
    pats.extend([
        url(r'^categories/$', CategoryListView.as_view(),
            name='catalog_category_list'),
        url(r'^categories/(?P<slug>[0-9A-Za-z-_.//]+)/$',
            CategoryDetailView.as_view(), name='catalog_category_detail'),
    ])

if scs.HAS_BRANDS:
    pats.extend([
        url(r'^brands/$', BrandListView.as_view(),
            name='catalog_brand_list'),
        url(r'^brands/(?P<slug>[0-9A-Za-z-_.//]+)/$',
            BrandDetailView.as_view(), name='catalog_brand_detail'),
    ])

if scs.HAS_MANUFACTURERS:
    pats.extend([
        url(r'^manufacturers/$', ManufacturerListView.as_view(),
            name='catalog_manufacturer_list'),
        url(r'^manufacturers/(?P<slug>[0-9A-Za-z-_.//]+)/$',
            ManufacturerDetailView.as_view(),
            name='catalog_manufacturer_detail'),
    ])

# Main patterns.
pats.extend([
    url(r'^products/$', ProductListView.as_view(),
        name='catalog_product_list'),
    url(r'^products/(?P<slug>[0-9A-Za-z-_.//]+)/variants/$',
        ProductVariantsJSONView.as_view(),
        name='catalog_product_variants'),
    url(r'^products/(?P<slug>[0-9A-Za-z-_.//]+)/$',
        ProductDetailView.as_view(),
        name='catalog_product_detail'),

    url(r'^$', ShopTemplateView.as_view(
        template_name='shop/welcome.html'), name='shop_welcome'),
])

urlpatterns = patterns('', *pats)
