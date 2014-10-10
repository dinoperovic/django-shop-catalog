# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from shop.views.order import OrderListView, OrderDetailView


# Pats are automatically inserted into urlpatterns in catalog urls.py
# so urlpatterns are not specified here.
pats = [
    url(r'^orders/$',
        OrderListView.as_view(template_name='shop/order_list.html'),
        name='order_list'),
    url(r'^orders/(?P<pk>\d+)/$',
        OrderDetailView.as_view(template_name='shop/order_detail.html'),
        name='order_detail'),
]
