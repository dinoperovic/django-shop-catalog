# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from shop.cart.cart_modifiers_base import BaseCartModifier

from catalog.models import Modifier


class ShopCatalogCartModifier(BaseCartModifier):
    def process_cart_item(self, cart_item, request):
        fields = self.get_extra_cart_item_price_field(cart_item, request)
        for field in fields:
            price = field[1]
            cart_item.current_total = cart_item.current_total + price
            cart_item.extra_price_fields.append(field)
        return cart_item

    def process_cart(self, cart, request):
        fields = self.get_extra_cart_price_field(cart, request)
        for field in fields:
            price = field[1]
            cart.current_total = cart.current_total + price
            cart.extra_price_fields.append(field)
        return cart

    def get_extra_cart_item_price_field(self, cart_item, request):
        fields = []
        for mod in cart_item.product.get_modifiers():
            field = mod.get_extra_cart_item_price_field(cart_item)
            if field:
                fields.append(field)
        return fields

    def get_extra_cart_price_field(self, cart, request):
        fields = []
        for mod in Modifier.get_cart_modifiers():
            field = mod.get_extra_cart_price_field(cart)
            if field:
                fields.append(field)
        return fields
