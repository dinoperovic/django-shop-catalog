# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.utils.translation import ugettext_lazy as _

from shop.admin.orderadmin import (
    OrderItemInline, OrderExtraInfoInline, ExtraOrderPriceFieldInline,
    OrderPaymentInline)
from shop.admin.mixins import LocalizeDecimalFieldsMixin
from shop.order_signals import completed, shipped

from catalog.orders.models import Order


class OrderAdmin(LocalizeDecimalFieldsMixin, ModelAdmin):
    list_display = ('id', 'user', 'status', 'order_total', 'created')
    list_filter = ('status', 'user')
    search_fields = ('id', 'shipping_address_text', 'user__username')
    date_hierarchy = 'created'
    inlines = (
        OrderItemInline, OrderExtraInfoInline, ExtraOrderPriceFieldInline,
        OrderPaymentInline)

    readonly_fields = ('created', 'modified')
    raw_id_fields = ('user', )
    fieldsets = (
        (None, {
            'fields': (
                'user', 'status', 'order_total', 'order_subtotal',
                'created', 'modified'),
        }),
        (_('Currency'), {
            'fields': (
                'currency_name', 'currency_code', 'currency_symbol',
                'currency_factor', 'currency_order_subtotal',
                'currency_order_total')
        }),
        (_('Shipping'), {
            'fields': ('shipping_address_text', ),
        }),
        (_('Billing'), {
            'fields': ('billing_address_text', ),
        }),
    )

    def __init__(self, *args, **kwargs):
        super(OrderAdmin, self).__init__(*args, **kwargs)

    def save_model(self, request, order, form, change):
        try:
            instance = Order.objects.get(pk=order.pk)
        except Order.DoesNotExist:
            instance = None

        super(OrderAdmin, self).save_model(request, order, form, change)

        # Emmit shipped signal when status is changed to shipped.
        if instance and order.status == Order.SHIPPED \
                and instance.status != Order.SHIPPED:
            shipped.send(sender=self, order=order)

        if order.status == Order.CONFIRMED and order.is_paid():
            order.status = Order.COMPLETED
            order.save()
            completed.send(sender=self, order=order)

admin.site.register(Order, OrderAdmin)
