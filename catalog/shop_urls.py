# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, url
from django.views.defaults import page_not_found
from django.views.generic import RedirectView

from catalog.urls import catalog_url
from catalog.views import ModifierCodeCreateView, ModifierCodeDeleteView


urlpatterns = patterns(
    '',
    # Disable products url since we are using 'catalog' which has
    # it's own urls for products.
    url(r'^products/', page_not_found),

    catalog_url('codes', ModifierCodeCreateView.as_view(),
                'cart_modifier_code_create'),
    catalog_url('codes', ModifierCodeDeleteView.as_view(),
                'cart_modifier_code_delete', 'delete'),

    # Redirect welcome to cart.
    url(r'^$', RedirectView.as_view(url='cart/'))
)
