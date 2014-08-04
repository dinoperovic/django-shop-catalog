# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from catalog.models import Attribute, Product


register = template.Library()


@register.simple_tag(takes_context=True)
def query_transform(context, *args, **kwargs):
    """
    Appends or updates current query string. Can be used as pairs
    passing in every second arg as value so that key can be dynamic.
    It also supports the kwargs format.

    {% query_transform <key> <value> <key> <value> <key>=<value> %}
    """
    get = context['request'].GET.copy()
    if args:
        args_keys = [args[i] for i in range(len(args)) if i % 2 == 0]
        args_vals = [args[i] for i in range(len(args)) if i % 2 != 0]
        for i in range(len(args_vals)):
            get[args_keys[i]] = args_vals[i]
    for k, v in kwargs.items():
        get[k] = v
    return get.urlencode()


@register.assignment_tag(takes_context=True)
def get_attr_filters(context, products=None):
    """
    Returns all attributes for the given products. If no products are
    given it uses all active, top level products.
    """
    request = context.get('request')
    filters = {}

    if products is not None:
        variants = [x for y in products for x in y.variants.select_related()]
        attrs = [x for y in variants for x in y.attributes.select_related()]
        attrs = list(set(attrs))
    else:
        attrs = Attribute.objects.all()

    for attr in attrs:
        values = [{'value': x.value} for x in attr.values.select_related()]

        for val in values:
            get = request.GET.copy()
            get[attr.get_slug()] = val['value']
            val['query_string'] = get.urlencode()

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
