# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from shop.cart.cart_modifiers_base import BaseCartModifier

from catalog.models import Modifier


class CatalogCartModifier(BaseCartModifier):
    def process_cart_item(self, cart_item, request):
        """
        Loops through extra cart item fields and updates the
        total value of the cart item.
        """
        fields = self.get_extra_cart_item_price_field(cart_item, request)
        for field in fields:
            price = field[1]
            new_total = cart_item.current_total + price
            cart_item.current_total = new_total if new_total > 0 else 0
            cart_item.extra_price_fields.append(field)
        return cart_item

    def process_cart(self, cart, request):
        """
        Loops through extra cart fields and updates the
        total value of the cart.
        """
        fields = self.get_extra_cart_price_field(cart, request)
        for field in fields:
            price = field[1]
            new_total = cart.current_total + price
            cart.current_total = new_total if new_total > 0 else 0
            cart.extra_price_fields.append(field)
        return cart

    def get_extra_cart_item_price_field(self, cart_item, request):
        """
        Returns all modifiers for the cart item.
        """
        fields = []
        for mod in cart_item.product.get_modifiers():
            field = mod.get_extra_cart_item_price_field(cart_item)
            if field:
                fields.append(field)
        return fields

    def get_extra_cart_price_field(self, cart, request):
        """
        Returns all cart modifiers.
        """
        fields = []
        for mod in Modifier.get_cart_modifiers():
            field = mod.get_extra_cart_price_field(cart)
            if field:
                fields.append(field)
        return fields
