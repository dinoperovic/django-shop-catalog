# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^shop_catalog\.fields\.NullableCharField$'])
except ImportError:
    pass


class NullableCharField(models.CharField):
    """
    Nullable CharField.
    Enables blank and null char fields to be unique.
    """
    description = 'CharField that stores NULL but returns \'\''
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, models.CharField):
            return value
        return value or ''

    def get_prep_value(self, value):
        return value or None
