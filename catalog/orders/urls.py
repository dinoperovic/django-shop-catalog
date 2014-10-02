# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import patterns, url

from shop.views.order import OrderListView, OrderDetailView


pats = [
    url(r'^orders/$',
        OrderListView.as_view(template_name='shop/order_list.html'),
        name='order_list'),
    url(r'^orders/(?P<pk>\d+)/$',
        OrderDetailView.as_view(template_name='shop/order_detail.html'),
        name='order_detail'),
]

urlpatterns = patterns('', *pats)
