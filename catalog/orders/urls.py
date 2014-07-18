# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, url
from django.views.defaults import page_not_found
from django.views.generic import RedirectView

from shop.views.order import OrderListView, OrderDetailView


urlpatterns = patterns(
    '',
    url(r'^orders/$',
        OrderListView.as_view(template_name='shop/order_list.html'),
        name='order_list'),
    url(r'^orders/(?P<pk>\d+)/$',
        OrderDetailView.as_view(template_name='shop/order_detail.html'),
        name='order_detail'),

    # Disable products url since we are using 'catalog' which has
    # it's own urls for products.
    url(r'^products/', page_not_found),

    # Redirect welcome to cart.
    url(r'^$', RedirectView.as_view(url='cart/'))
)
