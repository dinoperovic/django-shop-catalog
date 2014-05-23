# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, url

from shop_catalog.views import (
    ProductListView, ProductDetailView,
    CategoryListView, CategoryDetailView)

urlpatterns = patterns(
    '',
    url(r'^categories/$', CategoryListView.as_view(), name='category_list'),
    url(r'^categories/(?P<slug>[0-9A-Za-z-_.//]+)/$',
        CategoryDetailView.as_view(), name='category_detail'),

    url(r'^$', ProductListView.as_view(), name='product_list'),
    url(r'^(?P<slug>[0-9A-Za-z-_.//]+)/$', ProductDetailView.as_view(),
        name='product_detail'),
)
