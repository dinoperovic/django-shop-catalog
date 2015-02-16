# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.core.urlresolvers import reverse

from .models import (
    create_product, create_category, create_brand, create_manufacturer)


class FilterProductsTestCase(TestCase):
    products_url = reverse('catalog_product_list')

    def setUp(self):
        cat_1 = create_category('Cat 1')
        bra_1 = create_brand('Bra 1')
        man_1 = create_manufacturer('Man 1')

        # Empty categorization
        create_category('Cat empty')
        create_brand('Bra empty')
        create_manufacturer('Man empty')

        create_product('P1', category=cat_1, brand=bra_1, manufacturer=man_1)
        create_product('P2', category=cat_1, brand=bra_1)
        create_product('P3', category=cat_1)

        self.resp_1 = self.get_products_response(
            category='cat-1', brand='bra-1', manufacturer='man-1')
        self.resp_2 = self.get_products_response(
            category='cat-1', brand='bra-empty')
        self.resp_3 = self.get_products_response(category='cat-non-existant')

    def get_products_response(self, **kwargs):
        return self.client.get(self.products_url, kwargs)

    def test_get_categorization_filters(self):
        self.assertEquals(len(self.resp_1.context['object_list']), 1)
        self.assertEquals(len(self.resp_2.context['object_list']), 0)

        # Category doesn't exists so return all.
        self.assertEquals(len(self.resp_3.context['object_list']), 3)

    def test_get_price_filters(self):
        pass

    def test_get_date_filters(self):
        pass

    def test_search_products(self):
        pass

    def test_sort_products(self):
        pass
