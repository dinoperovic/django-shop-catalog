# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template


register = template.Library()


@register.filter
def get(value, arg):
    """
    Returns the value from the dict. Used when key has to be a string.
    """
    return value.get(arg, None)


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
