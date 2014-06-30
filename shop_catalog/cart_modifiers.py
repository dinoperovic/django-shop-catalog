# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from shop.cart.cart_modifiers_base import BaseCartModifier


class ShopCatalogCartModifier(BaseCartModifier):
    def process_cart_item(self, cart_item, request):
        fields = self.get_extra_cart_item_price_field(cart_item, request)
        for field in fields:
            price = field[1]
            cart_item.current_total = cart_item.current_total + price
            cart_item.extra_price_fields.append(field)
        return cart_item

    def get_extra_cart_item_price_field(self, cart_item, request):
        fields = []
        for modifier in cart_item._product_cache.get_modifiers():
            price = modifier.calculate_price(cart_item.current_total)
            fields.append((modifier.get_name(), price))
        return fields
