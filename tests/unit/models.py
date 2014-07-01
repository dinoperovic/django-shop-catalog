# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal as D

from django.test import TestCase
from django.utils.translation import activate

from shop_catalog.models import Modifier


class ModifierTestCase(TestCase):
    def setUp(self):
        self.mod_1 = Modifier.objects.create(percent=D(-30))
        self.mod_2 = Modifier.objects.create(percent=D(30))
        self.mod_3 = Modifier.objects.create(amount=D(-10))
        self.mod_4 = Modifier.objects.create(amount=D(10))

    def test_calculate_add_price(self):
        self.assertEquals(self.mod_1.calculate_add_price(D(100), 1), D(-30))
        self.assertEquals(self.mod_2.calculate_add_price(D(100), 1), D(30))
        self.assertEquals(self.mod_3.calculate_add_price(D(10), 2), D(-10))
        self.assertEquals(self.mod_4.calculate_add_price(D(100), 4), D(40))


class ProductTestCase(TestCase):
    def setUp(self):
        pass
