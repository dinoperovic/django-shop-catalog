# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, url
from django.views.defaults import page_not_found
from django.views.generic import RedirectView

from catalog.urls import catalog_url
from catalog.views import (
    CartModifierCodeCreateView, CartModifierCodeDeleteView)
from catalog import settings as scs


pats = []


if 'catalog.orders' in settings.INSTALLED_APPS:
    from catalog.orders.urls import pats as orders_pats
    pats.extend(orders_pats)


if scs.HAS_MODIFIER_CODES:
    pats.extend([
        catalog_url('codes', CartModifierCodeCreateView.as_view(),
                    'cart_modifier_code_create'),
        catalog_url('codes', CartModifierCodeDeleteView.as_view(),
                    'cart_modifier_code_delete', 'delete'),
    ])


pats.extend([
    # Disable products url since catalog has it's own urls for products.
    url(r'^products/', page_not_found),

    # Redirect welcome to cart.
    url(r'^$', RedirectView.as_view(url='cart/'))
])

urlpatterns = patterns('', *pats)
