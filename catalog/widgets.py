# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.utils.encoding import force_text

from catalog.models import Attribute, AttributeOption


class AttributeValueKindsMapSelect(forms.Select):
    """
    A custom Select widget for generating 'data-choices' attribute when
    selected attributes kind is Attribute.KIND_OPTION.
    """
    def render_option(self, selected_choices, option_value, option_label):
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                selected_choices.remove(option_value)
        else:
            selected_html = ''

        if option_value == Attribute.KIND_OPTION:
            opts = AttributeOption.objects.language().filter(
                attribute__id=option_label).values_list('value', flat=True)
            choices = mark_safe(' data-choices="{0}"'.format(','.join(opts)))
        else:
            choices = ''

        return format_html('<option value="{0}"{1}{2}>{3}</option>',
                           option_value,
                           selected_html,
                           choices,
                           force_text(option_label))
