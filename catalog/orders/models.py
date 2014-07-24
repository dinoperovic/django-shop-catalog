# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

from django.db import models
from django.utils.translation import get_language, ugettext_lazy as _
from django.dispatch import receiver

from shop.models_bases import BaseOrder
from shop.models_bases.managers import OrderManager as BaseOrderManager
from shop.order_signals import confirmed, completed, shipped, cancelled

from catalog.orders.notifications import ClientNotification, OwnersNotification
from catalog.utils import round_2


@receiver([confirmed, completed, shipped, cancelled])
def notify_client(sender, **kwargs):
    notification = ClientNotification(kwargs.get('order'))
    notification.send()


@receiver([confirmed, completed, cancelled])
def notify_owners(sender, **kwargs):
    notification = OwnersNotification(kwargs.get('order'))
    notification.send()


class OrderManager(BaseOrderManager):
    def create_order_object(self, cart, request):
        """
        Override order creation to fill out new fields.
        """
        order = super(OrderManager, self).create_order_object(cart, request)

        if 'LANGUAGE_CODE' in request:
            order.language_code = request.LANGUAGE_CODE
        else:
            order.language_code = get_language()[:2]

        currency = request.session.get('currency', None)
        if currency:
            order.currency_code = currency.code
            order.currency_name = currency.name
            order.currency_symbol = currency.symbol
            order.currency_factor = currency.factor
        return order


class Order(BaseOrder):
    language_code = models.CharField(
        _('Language code'), max_length=10, blank=True, null=True)

    shipping_name = models.CharField(
        _('Name'), max_length=255, blank=True, null=True)
    shipping_email = models.EmailField(
        _('Email'), max_length=255, blank=True, null=True)
    shipping_phone_number = models.CharField(
        _('Phone number'), max_length=16, blank=True, null=True)

    billing_name = models.CharField(
        _('Name'), max_length=255, blank=True, null=True)
    billing_email = models.EmailField(
        _('Email'), max_length=255, blank=True, null=True)
    billing_phone_number = models.CharField(
        _('Phone number'), max_length=16, blank=True, null=True)

    currency_code = models.CharField(
        _('Code'), max_length=3, blank=True, null=True)
    currency_name = models.CharField(
        _('Name'), max_length=35, blank=True, null=True)
    currency_symbol = models.CharField(
        _('Symbol'), max_length=4, blank=True, null=True)
    currency_factor = models.DecimalField(
        _('Factor'), max_digits=30, decimal_places=10, default=Decimal(1))

    objects = OrderManager()

    class Meta:
        abstract = False
        db_table = 'catalog_orders_orders'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def set_billing_address(self, billing_address):
        self.billing_name = getattr(billing_address, 'name', None)
        self.billing_email = getattr(billing_address, 'email', None)
        self.billing_phone_number = getattr(
            billing_address, 'phone_number', None)
        super(Order, self).set_billing_address(billing_address)

    def set_shipping_address(self, shipping_address):
        self.shipping_name = getattr(shipping_address, 'name', None)
        self.shipping_email = getattr(shipping_address, 'email', None)
        self.shipping_phone_number = getattr(
            shipping_address, 'phone_number', None)
        super(Order, self).set_shipping_address(shipping_address)

    def get_name(self):
        return self.billing_name or self.shipping_name or ''

    def get_items(self):
        items = self.items.all()
        for item in items:
            item.currency_unit_price = self.calculate_currency(item.unit_price)
            item.currency_line_total = self.calculate_currency(item.line_total)
            item.currency_line_subtotal = \
                self.calculate_currency(item.line_subtotal)

            fields = []
            for field in item.extraorderitempricefield_set.all():
                field.currency_value = self.calculate_currency(field.value)
                fields.append(field)
            item.extra_price_fields = fields
        return items

    @property
    def extra_price_fields(self):
        fields = []
        for field in self.extraorderpricefield_set.all():
            field.currency_value = self.calculate_currency(field.value)
            fields.append(field)
        return fields

    def currency_order_subtotal(self):
        return self.calculate_currency(self.order_subtotal)
    currency_order_subtotal.short_description = _('Order subtotal')

    def currency_order_total(self):
        return self.calculate_currency(self.order_total)
    currency_order_total.short_description = _('Order Total')

    def calculate_currency(self, price):
        return round_2(price * self.currency_factor)
