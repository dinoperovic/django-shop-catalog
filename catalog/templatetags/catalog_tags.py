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
        data = attr.as_dict
        data.update({'values': attr.get_values()})
        filters[attr.get_slug()] = data

    return filters


@register.assignment_tag
def get_price_steps(steps=5, products=None):
    """
    Return min and max price with the steps in between.
    """
    if products is None:
        products = Product.objects.active().top_level()
    elif products:
        pks = list(products.values_list('pk', flat=True))
        products = Product.objects.language().filter(pk__in=pks)
    else:
        return []

    products = products.order_by('unit_price')
    min_price, max_price = (products[0].get_unit_price(),
                            products.reverse()[0].get_unit_price())

    price_steps = [min_price]
    chunk = int(float((max_price - min_price) / (steps + 1)))

    for i in range(steps):
        price_steps.append(price_steps[-1] + chunk)
    price_steps.append(max_price)

    steps_count = list(set(price_steps))
    return price_steps if len(steps_count) > 1 else []
