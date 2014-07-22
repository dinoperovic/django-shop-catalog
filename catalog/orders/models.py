# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

from django.db import models
from django.utils.translation import get_language, ugettext_lazy as _
from django.dispatch import receiver

from shop.models_bases import BaseOrder
from shop.models_bases.managers import OrderManager as BaseOrderManager
from shop.util.fields import CurrencyField
from shop.order_signals import confirmed, completed, shipped, cancelled

from catalog.orders.notifications import ClientNotification, OwnersNotification
from catalog.utils import round_2


@receiver(confirmed)
@receiver(completed)
@receiver(shipped)
@receiver(cancelled)
def notify_client(sender, **kwargs):
    notification = ClientNotification(kwargs.get('order'))
    notification.send()


@receiver(confirmed)
@receiver(completed)
@receiver(cancelled)
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

    currency_code = models.CharField(
        _('Code'), max_length=3, blank=True, null=True)
    currency_name = models.CharField(
        _('Name'), max_length=35, blank=True, null=True)
    currency_symbol = models.CharField(
        _('Symbol'), max_length=4, blank=True, null=True)
    currency_factor = models.DecimalField(
        _('Factor'), max_digits=30, decimal_places=10, default=Decimal(1))

    currency_order_subtotal = CurrencyField(verbose_name=_('Order subtotal'))
    currency_order_total = CurrencyField(verbose_name=_('Order Total'))

    objects = OrderManager()

    class Meta:
        abstract = False
        db_table = 'catalog_orders_orders'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')

    def save(self, *args, **kwargs):
        self.calculate_currency()
        super(Order, self).save(*args, **kwargs)

    def calculate_currency(self):
        self.currency_order_subtotal = round_2(
            self.order_subtotal * self.currency_factor)
        self.currency_order_total = round_2(
            self.order_total * self.currency_factor)
