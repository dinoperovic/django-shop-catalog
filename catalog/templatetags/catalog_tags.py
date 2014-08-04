# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from catalog.models import Attribute, Product


register = template.Library()


@register.assignment_tag
def get_attr_filters(products=None):
    """
    Returns all attributes for the given products. If no products are
    given it uses all active, top level products.
    """
    filters = {}

    if products is not None:
        variants = [x for y in products for x in y.variants.select_related()]
        attrs = [x for y in variants for x in y.attributes.select_related()]
        attrs = list(set(attrs))
    else:
        attrs = Attribute.objects.all()

    for attr in attrs:
        values = [x.value for x in attr.values.select_related()]

        filters[attr.get_slug()] = {
            'code': attr.get_slug(),
            'name': attr.get_name(),
            'values': values,
        }

    return filters


@register.assignment_tag
def get_price_steps(steps=5, products=None):
    """
    Return min and max price with the steps in between.
    """
    if products is None:
        products = Product.objects.active().top_level()

    if not products:
        return []

    min_price = products.order_by('unit_price')[0].get_unit_price()
    max_price = products.order_by('-unit_price')[0].get_unit_price()

    price_steps = [min_price]
    chunk = int(float((max_price - min_price) / (steps + 1)))

    for i in range(steps):
        price_steps.append(price_steps[-1] + chunk)
    price_steps.append(max_price)

    return price_steps
