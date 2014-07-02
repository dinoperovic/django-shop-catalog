# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

from django.utils.translation import ugettext_lazy as _


class ModifierConditionBase(object):
    """
    An interface for writing a custom condition.
    """
    name = None

    def get_name(self):
        """
        Returns the name of a modifier.
        """
        return self.name

    def cart_item_condition(self, cart_item, arg=None, request=None):
        """
        Returns boolean if condition is met per item.
        """
        return True

    def cart_condition(self, cart, arg=None, request=None):
        """
        Returns boolean if condition is met on entire cart.
        """
        return True


class PriceGreaterThanModifierCondition(ModifierConditionBase):
    name = _('Price greater than')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        return cart_item.product.get_price() > arg

    def cart_condition(self, cart, arg=None, request=None):
        arg = arg or 0
        return cart.current_total > arg


class PriceLessThanModifierCondition(ModifierConditionBase):
    name = _('Price less than')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        return cart_item.product.get_price() < arg

    def cart_condition(self, cart, arg=None, request=None):
        arg = arg or 0
        return cart.current_total < arg


class QuantityGreaterThanModifierCondition(ModifierConditionBase):
    name = _('Quantity greater than')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        return cart_item.quantity > arg


class QuantityLessThanModifierCondition(ModifierConditionBase):
    name = _('Quantity less than')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        return cart_item.quantity < arg


class WidthGreaterThanModifierCondition(ModifierConditionBase):
    name = _('Width greater than (m)')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        measurement = cart_item.product.get_measurements()['width']
        if measurement:
            return Decimal(measurement.get('standard_value', 0)) > arg
        return False


class WidthLessThanModifierCondition(ModifierConditionBase):
    name = _('Width less than (m)')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        measurement = cart_item.product.get_measurements()['width']
        if measurement:
            return Decimal(measurement.get('standard_value', 0)) < arg
        return False


class HeightGreaterThanModifierCondition(ModifierConditionBase):
    name = _('Height greater than (m)')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        measurement = cart_item.product.get_measurements()['height']
        if measurement:
            return Decimal(measurement.get('standard_value', 0)) > arg
        return False


class HeightLessThanModifierCondition(ModifierConditionBase):
    name = _('Height less than (m)')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        measurement = cart_item.product.get_measurements()['height']
        if measurement:
            return Decimal(measurement.get('standard_value', 0)) < arg
        return False


class DepthGreaterThanModifierCondition(ModifierConditionBase):
    name = _('Depth greater than (m)')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        measurement = cart_item.product.get_measurements()['depth']
        if measurement:
            return Decimal(measurement.get('standard_value', 0)) > arg
        return False


class DepthLessThanModifierCondition(ModifierConditionBase):
    name = _('Depth less than (m)')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        measurement = cart_item.product.get_measurements()['depth']
        if measurement:
            return Decimal(measurement.get('standard_value', 0)) < arg
        return False


class WeightGreaterThanModifierCondition(ModifierConditionBase):
    name = _('Weight greater than (g)')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        measurement = cart_item.product.get_measurements()['weight']
        if measurement:
            return Decimal(measurement.get('standard_value', 0)) > arg
        return False


class WeightLessThanModifierCondition(ModifierConditionBase):
    name = _('Weight less than (g)')

    def cart_item_condition(self, cart_item, arg=None, request=None):
        arg = arg or 0
        measurement = cart_item.product.get_measurements()['weight']
        if measurement:
            return Decimal(measurement.get('standard_value', 0)) < arg
        return False
