# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from catalog.urls import catalog_url
from catalog.reviews.views import (
    ReviewListView, ReviewDetailView, ReviewCreateView, ReviewUpdateView,
    ReviewDeleteView)


# Pats are automatically inserted into urlpatterns in catalog urls.py
# so urlpatterns are not specified here.
pats = [
    catalog_url('product', ReviewListView.as_view(),
                'review_list',
                '(?P<slug>[0-9A-Za-z-_.//]+)/reviews/'),

    catalog_url('product', ReviewDetailView.as_view(),
                'review_detail',
                '(?P<slug>[0-9A-Za-z-_.//]+)/reviews/(?P<pk>[\d+])/'),

    catalog_url('product', ReviewCreateView.as_view(),
                'review_create',
                '(?P<slug>[0-9A-Za-z-_.//]+)/reviews/create/'),

    catalog_url('product', ReviewUpdateView.as_view(),
                'review_update',
                '(?P<slug>[0-9A-Za-z-_.//]+)/reviews/(?P<pk>[\d+])/update/'),

    catalog_url('product', ReviewDeleteView.as_view(),
                'review_delete',
                '(?P<slug>[0-9A-Za-z-_.//]+)/reviews/(?P<pk>[\d+])/delete/'),
]
