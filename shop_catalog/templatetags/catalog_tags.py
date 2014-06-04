# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from shop_catalog.utils import round_2 as r2


register = template.Library()


@register.filter
def round_2(value):
    return r2(value)
