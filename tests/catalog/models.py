# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal as D
from datetime import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.utils.translation import activate
from django.utils.text import slugify

from shop.models import Cart, CartItem

from catalog.models import (
    CatalogModel, Modifier, ModifierCondition, ModifierCode, CartModifierCode,
    ModifierModel, Category, Brand, Manufacturer, Tax, Product, Attribute,
    ProductAttributeValue)
from catalog import settings as scs

from ..utils import warning


def create_product(name, unit_price=100, **kwargs):
    filters = {
        'name': name,
        'slug': slugify(name),
        'upc': slugify(name),
        'unit_price': D(unit_price),
    }
    filters.update(kwargs)
    return Product.objects.language().create(**filters)


def create_categorization(model, name, **kwargs):
    filters = {
        'name': name,
        'slug': slugify(name),
    }
    filters.update(kwargs)
    return model.objects.language().create(**filters)


def create_category(name, **kwargs):
    return create_categorization(Category, name, **kwargs)


def create_brand(name, **kwargs):
    return create_categorization(Brand, name, **kwargs)


def create_manufacturer(name, **kwargs):
    return create_categorization(Manufacturer, name, **kwargs)


def create_modifier(name, values=[20, None], kind='standard'):
    kwargs = {
        'name': name,
        'code': slugify(name),
        'amount': D(values[0]),
    }
    if values[1] is not None:
        kwargs['percent'] = D(values[1])

    if hasattr(Modifier, 'KIND_%s' % kind.upper()):
        kwargs['kind'] = getattr(Modifier, 'KIND_%s' % kind.upper())

    return Modifier.objects.language().create(**kwargs)


class CatalogModelTestCase(TestCase):
    def setUp(self):
        TestCatalogModel = type(str('TestCatalogModel'), (CatalogModel, ),
                                {'__module__': __name__})
        self.model = TestCatalogModel(
            pk=1, active=True, date_added=datetime.now,
            last_modified=datetime.now)

    def test_get_absolute_url(self):
        self.assertIsNone(self.model.get_absolute_url())

    def test_get_name(self):
        self.assertEquals(self.model.get_name(), '1')

    def test_get_slug(self):
        self.assertEquals(self.model.get_slug(), '1')

    def test_as_dict(self):
        self.assertIsInstance(self.model.as_dict, dict)


class ModifierTestCase(TestCase):
    def setUp(self):
        self.mod_1 = create_modifier('Mod 1', [0, -30], 'standard')
        self.mod_2 = create_modifier('Mod 2', [0, 30], 'discount')
        self.mod_3 = create_modifier('Mod 3', [-10, None], 'discount')
        self.mod_4 = create_modifier('Mod 4', [10, None], 'cart_modifier')

        self.prod_1 = create_product('Prod 1', 100, is_discountable=True)
        self.prod_2 = create_product('Prod 2', 200, is_discountable=False)
        self.prod_3 = create_product('Prod 3', 300, is_discountable=True)
        self.prod_4 = create_product('Prod 4', 400, is_discountable=True)

        self.cart_1 = Cart.objects.create()
        self.item_1 = self.cart_1.add_product(self.prod_1)
        self.cart_1.current_total = self.item_1.current_total = D(100)

        self.mc_1 = ModifierCode.objects.create(modifier=self.mod_1, code='a')
        CartModifierCode.objects.create(cart=self.cart_1, code='a')

        self.cart_2 = Cart.objects.create()
        self.mc_2 = ModifierCode.objects.create(modifier=self.mod_4, code='d')
        CartModifierCode.objects.create(cart=self.cart_2, code='d')

    def test_get_name(self):
        self.assertEquals(self.mod_1.get_name(), 'Mod 1')

    def test_get_slug(self):
        self.assertEquals(self.mod_1.get_slug(), self.mod_1.code)

    def test_get_extra_cart_item_price_field(self):
        field = self.mod_1.get_extra_cart_item_price_field(self.item_1)
        self.assertEquals(field, ('Mod 1', D(-30)))  # 30% of 100

    def test_get_extra_cart_price_field(self):
        field = self.mod_3.get_extra_cart_price_field(self.cart_1)
        self.assertEquals(field, ('Mod 3', D(-10)))

    def test_calculate_add_price(self):
        self.assertEquals(self.mod_1.calculate_add_price(D(100), 1), D(-30))
        self.assertEquals(self.mod_2.calculate_add_price(D(100), 1), D(30))
        self.assertEquals(self.mod_3.calculate_add_price(D(10), 2), D(-20))
        self.assertEquals(self.mod_4.calculate_add_price(D(100), 4), D(40))

    def test_can_be_applied(self):
        # The mod can't be applied because it's a CART_MODIFIER but cart
        # item is passed in.
        self.assertFalse(self.mod_4.can_be_applied(cart_item=self.item_1))
        self.assertTrue(self.mod_3.can_be_applied(cart_item=self.item_1))
        self.assertTrue(self.mod_2.can_be_applied(cart=self.cart_1))
        self.assertTrue(self.mod_1.can_be_applied(
            cart_item=self.item_1, cart=self.cart_1))

    def test_is_code_applied(self):
        self.assertTrue(self.mod_1.is_code_applied(self.cart_1.pk))
        self.assertTrue(self.mod_4.is_code_applied(self.cart_2.pk))

    def test_is_eligible_product(self):
        self.assertTrue(self.mod_1.is_eligible_product(self.prod_1))
        self.assertFalse(self.mod_2.is_eligible_product(self.prod_2))
        self.assertTrue(self.mod_3.is_eligible_product(self.prod_3))
        self.assertFalse(self.mod_4.is_eligible_product(self.prod_4))

    def test_get_cart_modifiers(self):
        mods = Modifier.get_cart_modifiers()
        self.assertEquals(len(mods), 1)
        self.assertEquals(mods[0].kind, 'cart_modifier')


class ModifierModelTestCase(TestCase):
    def setUp(self):
        # User product as a modifier model.
        self.prod = create_product('Prod 1')
        self.prod.modifiers.add(create_modifier('Mod 1'),
                                create_modifier('Mod 2'))

    def test_get_modifiers(self):
        self.assertEquals(len(self.prod.get_modifiers()), 2)


class ModifierConditionTestCase(TestCase):
    def setUp(self):
        self.prod_1 = create_product('Prod 1', 300)
        self.prod_2 = create_product('Prod 2', 10)

        self.mod_1 = create_modifier('Mod 1', [0, -30])
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

    def test_get_modifier_condition_choices(self):
        self.assertIsNotNone(ModifierCondition.MODIFIER_CONDITION_CHOICES)

    def test_is_met(self):
        self.assertTrue(self.cond_1.is_met(cart_item=self.item_1))
        self.assertFalse(self.cond_1.is_met(cart_item=self.item_2))
        self.assertFalse(self.cond_1.is_met(cart=self.cart_1))
        self.assertTrue(self.cond_2.is_met(cart=self.cart_1))


class CategoryBaseTestCase(TestCase):
    def setUp(self):
        self.cat_1 = Category.objects.language().create(
            name='Cat-1', slug='cat-1')
        self.cat_2 = Category.objects.language().create(
            name='Cat 2', slug='cat-2', parent=self.cat_1)

        mod = create_modifier('Mod 1')
        self.cat_1.modifiers.add(mod)
        self.cat_2.modifiers.add(mod)
        self.cat_2.modifiers.add(create_modifier('Mod 2'))

    def test_get_modifiers(self):
        self.assertEquals(len(self.cat_1.get_modifiers()), 1)
        self.assertEquals(len(self.cat_2.get_modifiers()), 2)


class CategoryTestCase(TestCase):
    def setUp(self):
        self.cat = Category.objects.language().create(name='Cat', slug='cat')

    def test_get_absolute_url(self):
        self.assertEquals(
            self.cat.get_absolute_url(),
            reverse('catalog_category_detail', args=['cat']))


class BrandTestCase(TestCase):
    def setUp(self):
        self.brand = Brand.objects.language().create(
            name='Brand', slug='brand')

    def test_get_absolute_url(self):
        self.assertEquals(
            self.brand.get_absolute_url(),
            reverse('catalog_brand_detail', args=['brand']))


class ManufacturerTestCase(TestCase):
    def setUp(self):
        self.man = Manufacturer.objects.language().create(
            name='Man', slug='man')

    def test_get_absolute_url(self):
        self.assertEquals(
            self.man.get_absolute_url(),
            reverse('catalog_manufacturer_detail', args=['man']))


class ProductBaseTestCase(TestCase):
    def setUp(self):
        self.tax = Tax.objects.create(name='PDV', percent=D(20))

        self.prod_1 = create_product('Prod 1', 300, upc=None)
        self.prod_2 = create_product('Prod 2', 100, discount_percent=D(10))
        self.prod_3 = create_product('Prod 3', 500, tax=self.tax)
        self.prod_4 = create_product('Prod 4', 80, quantity=0)
        self.prod_1_var_1 = create_product('Prod 1-1', 300, parent=self.prod_1)
        self.prod_2_var_1 = create_product('Prod 2-1', 0, parent=self.prod_2)
        self.prod_3_var_1 = create_product('Prod 3-1', 200, parent=self.prod_3)

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
        self.assertEquals(self.prod_2_var_1.get_price(), D(90))

    def test_get_unit_price(self):
        self.assertEquals(self.prod_1_var_1.get_unit_price(), D(300))
        self.assertEquals(self.prod_2_var_1.get_unit_price(), D(100))

    def test_get_discount_percent(self):
        self.assertEquals(self.prod_1_var_1.get_discount_percent(), D(0))
        self.assertEquals(self.prod_2_var_1.get_discount_percent(), D(10))
        self.assertEquals(self.prod_2.get_discount_percent(), D(10))

    def test_get_tax_percent(self):
        self.assertEquals(self.prod_1.get_tax_percent(), D(0))
        self.assertEquals(self.prod_3_var_1.get_tax_percent(), D(20))
        self.assertEquals(self.prod_3.get_tax_percent(), D(20))

    def test_get_product_reference(self):
        self.assertEquals(self.prod_1.get_product_reference(), '1')
        self.assertEquals(self.prod_2.get_product_reference(), 'prod-2')

    def test_can_be_added_to_cart(self):
        self.assertFalse(self.prod_1.can_be_added_to_cart)
        self.assertFalse(self.prod_4.can_be_added_to_cart)
        self.assertTrue(self.prod_1_var_1.can_be_added_to_cart)

    def test_is_top_level(self):
        self.assertTrue(self.prod_1.is_top_level)
        self.assertFalse(self.prod_1_var_1.is_top_level)

    def test_is_group(self):
        self.assertTrue(self.prod_1.is_group)
        self.assertFalse(self.prod_4.is_group)
        self.assertFalse(self.prod_1_var_1.is_group)

    def test_is_variant(self):
        self.assertFalse(self.prod_1.is_variant)
        self.assertTrue(self.prod_1_var_1.is_variant)

    def test_is_available(self):
        self.assertTrue(self.prod_1.is_available)
        self.assertFalse(self.prod_4.is_available)

    def test_is_discounted(self):
        self.assertFalse(self.prod_1.is_discounted)
        self.assertFalse(self.prod_1_var_1.is_discounted)
        self.assertTrue(self.prod_2.is_discounted)

    def test_is_taxed(self):
        self.assertTrue(self.prod_3.is_taxed)
        self.assertFalse(self.prod_4.is_taxed)

    def test_is_price_inherited(self):
        self.assertFalse(self.prod_1.is_price_inherited)
        self.assertTrue(self.prod_2_var_1.is_price_inherited)

    def test_is_discount_inherited(self):
        self.assertFalse(self.prod_1.is_discount_inherited)
        self.assertTrue(self.prod_2_var_1.is_discount_inherited)

    def test_is_tax_inherited(self):
        self.assertFalse(self.prod_1.is_tax_inherited)
        self.assertTrue(self.prod_3_var_1.is_tax_inherited)

    def test_is_dict(self):
        self.assertIsInstance(self.prod_1.as_dict, dict)

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
