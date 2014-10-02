# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

from catalog import settings as scs


try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ['^catalog\.fields\.NullableCharField$'])
    add_introspection_rules([], ['^catalog\.fields\.UnderscoreField$'])
except ImportError:
    pass


class NullableCharField(models.CharField):
    """
    Enables blank and null char fields to be unique.
    """
    description = _('CharField that stores NULL but returns \'\'')
    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        if isinstance(value, models.CharField):
            return value
        return value or ''

    def get_prep_value(self, value):
        return value or None


class UnderscoreField(models.SlugField):
    """
    Slug field that doesn't allow dashes.
    """
    description = _('SlugField that doesn\'t allow dashes.')
    default_validators = [RegexValidator(
        r'^[a-zA-Z0-9_]+$', scs.UNDERSCORE_FIELD_HELP_TEXT, 'invalid')]
