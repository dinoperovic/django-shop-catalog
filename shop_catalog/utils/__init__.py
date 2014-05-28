# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist


def slug_num_suffix(slug, queryset, template='{slug}-{num}'):
    """ Returns next available suffix number in a given queryset. """
    num = 1
    while True:
        try:
            queryset.get(slug=template.format(slug=slug, num=num))
            num += 1
        except ObjectDoesNotExist:
            return num


def round_2(num):
    return Decimal(num).quantize(Decimal('0.00'))
