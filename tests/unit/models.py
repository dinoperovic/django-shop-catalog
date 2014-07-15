# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal as D

from django.test import TestCase
from django.utils.translation import activate

from shop.models import Cart, CartItem

from shop_catalog.models import (
    Modifier, ModifierCondition, Product, Attribute, ProductAttributeValue)
from shop_catalog import settings as scs

from tests.utils import warning


class ModifierTestCase(TestCase):
    def setUp(self):
        self.mod_1 = Modifier.objects.create(
            percent=D(-30), kind=Modifier.KIND_STANDARD)
        self.mod_2 = Modifier.objects.create(
            percent=D(30), kind=Modifier.KIND_DISCOUNT)
        self.mod_3 = Modifier.objects.create(
            amount=D(-10), kind=Modifier.KIND_DISCOUNT)
        self.mod_4 = Modifier.objects.create(
            amount=D(10), kind=Modifier.KIND_CART_MODIFIER)

        self.prod_1 = Product.objects.create(
            unit_price=D(100), is_discountable=True)
        self.prod_2 = Product.objects.create(
            unit_price=D(200), is_discountable=False)
        self.prod_3 = Product.objects.create(
            unit_price=D(300), is_discountable=True)
        self.prod_4 = Product.objects.create(
            unit_price=D(400), is_discountable=True)

    def test_calculate_add_price(self):
        self.assertEquals(self.mod_1.calculate_add_price(D(100), 1), D(-30))
        self.assertEquals(self.mod_2.calculate_add_price(D(100), 1), D(30))
        self.assertEquals(self.mod_3.calculate_add_price(D(10), 2), D(-10))
        self.assertEquals(self.mod_4.calculate_add_price(D(100), 4), D(40))

    def test_is_eligible_product(self):
        self.assertTrue(self.mod_1.is_eligible_product(self.prod_1))
        self.assertFalse(self.mod_2.is_eligible_product(self.prod_2))
        self.assertTrue(self.mod_3.is_eligible_product(self.prod_3))
        self.assertFalse(self.mod_4.is_eligible_product(self.prod_4))


class ModifierConditionTestCase(TestCase):
    def setUp(self):
        self.prod_1 = Product.objects.create(unit_price=D(300))
        self.prod_2 = Product.objects.create(unit_price=D(10))
        self.mod_1 = Modifier.objects.create(percent=D(-30))
        self.cond_1 = ModifierCondition.objects.create(
            modifier=self.mod_1, path=scs.MODIFIER_CONDITIONS[0], arg=D(200))
        self.cond_2 = ModifierCondition.objects.create(
            modifier=self.mod_1, path=scs.MODIFIER_CONDITIONS[0], arg=D(50))

        self.cart_1 = Cart.objects.create()
        self.cart_1.current_total = D(100)
        self.item_1 = CartItem.objects.create(
            cart=self.cart_1, quantity=1, product=self.prod_1)
        self.item_2 = CartItem.objects.create(
            cart=self.cart_1, quantity=1, product=self.prod_2)

    def test_is_met(self):
        self.assertTrue(self.cond_1.is_met(cart_item=self.item_1))
        self.assertFalse(self.cond_1.is_met(cart_item=self.item_2))
        self.assertFalse(self.cond_1.is_met(cart=self.cart_1))
        self.assertTrue(self.cond_2.is_met(cart=self.cart_1))


class ProductTestCase(TestCase):
    def setUp(self):
        self.prod_1 = Product.objects.create(unit_price=D(300))
        self.prod_2 = Product.objects.create(
            unit_price=D(100), discount_percent=D(10))
        self.prod_1_var_1 = Product.objects.create(parent=self.prod_1)
        self.prod_2_var_1 = Product.objects.create(
            parent=self.prod_2, unit_price=D(200))

        self.attr_1 = Attribute.objects.create(
            code='attr_1', kind=Attribute.KIND_INTEGER)
        self.attr_1_val_1 = ProductAttributeValue.objects.create(
            attribute=self.attr_1, product=self.prod_1_var_1, value_integer=10)
        self.attr_2 = Attribute.objects.create(
            code='attr_2', kind=Attribute.KIND_BOOLEAN)
        self.attr_2_val_1 = ProductAttributeValue.objects.create(
            attribute=self.attr_2, product=self.prod_1_var_1,
            value_boolean=True)

    def test_get_price(self):
        self.assertEquals(self.prod_1.get_price(), D(300))
        self.assertEquals(self.prod_2.get_price(), D(90))
        self.assertEquals(self.prod_1_var_1.get_price(), D(300))
        self.assertEquals(self.prod_2_var_1.get_price(), D(180))

    def test_get_unit_price(self):
        self.assertEquals(self.prod_1_var_1.get_unit_price(), D(300))
        self.assertEquals(self.prod_2_var_1.get_unit_price(), D(200))

    def test_get_attrs(self):
        self.assertEquals(self.prod_1_var_1.get_attrs()[0]['value'], '10')
        self.assertTrue(self.prod_1_var_1.get_attrs()[1]['value'])

    def test_get_variations(self):
        self.assertEquals(len(self.prod_1.get_variations()), 2)

    def test_get_variant(self):
        self.assertTrue(self.prod_1.get_variant(attr_1=10, attr_2=True))
        self.assertFalse(self.prod_1.get_variant(attr_1=20, attr_2=True))
        self.assertFalse(self.prod_1.get_variant(attr_1=20, attr_2=False))

    def test_filter_variants(self):
        self.assertTrue(self.prod_1.filter_variants(attr_1=10, attr_2=True))
        self.assertFalse(self.prod_1.filter_variants(attr_1=10, attr_2=False))
        self.assertTrue(self.prod_1.filter_variants(attr_2=True))
        self.assertFalse(self.prod_1.filter_variants(attr_1=20, attr_2=False))
