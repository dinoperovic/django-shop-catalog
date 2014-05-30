# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from hvad.forms import TranslatableModelForm

from shop_catalog.models import (
    Product, Attribute, ProductAttributeValue)
from shop_catalog.widgets import AttributeValueKindsMapSelect


class CatalogModelFormBase(TranslatableModelForm):
    """
    Catalog model form base.
    Objects that inherit from CatalogModel should have their form
    inherit from this one for some modified fields.
    """
    class Meta:
        model = None

    def __init__(self, *args, **kwargs):
        super(CatalogModelFormBase, self).__init__(*args, **kwargs)

        instance = getattr(self, 'instance', None)
        if instance is not None:
            self.fields['active'].help_text = _(
                'Is this %s active? You can hide it by unchecking this box.' %
                self.instance.__class__.__name__)


class ProductModelForm(CatalogModelFormBase):
    """
    Product model form.
    """
    class Meta:
        model = Product

    def __init__(self, *args, **kwargs):
        super(ProductModelForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = self.get_parent_queryset()

    def clean_parent(self):
        """
        If parent is set to a any value, checks that there aren't
        any other products with their parent set to this one.

        Makes sure parent is not set to 'self' or a 'variant'.
        """
        instance = getattr(self, 'instance', None)
        data = self.cleaned_data.get('parent')

        if data is not None:
            if instance is not None:
                if instance.is_group:
                    raise forms.ValidationError(
                        _('Other products have set this product as their '
                          'parent, you need to unassign or delete them before '
                          'you can change this value.'))
                if data == instance:
                    raise forms.ValidationError(
                        _('Cannot assign itself as a parent Product.'))

            if data.is_variant:
                raise forms.ValidationError(
                    _('Cannot assign "variant" as a parent Product.'))

        return data

    def get_parent_queryset(self):
        """
        Filters parents queryset to return only top level products
        and removes itself from a list.
        """
        instance = getattr(self, 'instance', None)
        queryset = Product.objects.top_level()
        pks = list(queryset.values_list('pk', flat=True))

        if instance is not None and instance.pk in pks:
            pks.remove(instance.pk)

        return queryset.filter(pk__in=pks)


class ProductAttributeValueModelForm(forms.ModelForm):
    """
    Attribute Value model form.
    Creates a custom form for managing multiple attribute values
    on an inline admin.
    """
    temp_data = ['empty', 'kinds', 'kinds_map']

    empty = forms.CharField(required=False, label=_('Value'))
    kinds = forms.CharField(
        widget=forms.Select(choices=Attribute.KIND_CHOICES))
    kinds_map = forms.CharField()

    class Meta:
        model = ProductAttributeValue
        labels = {'attribute': _('Attribute (Type)')}
        fields = (
            'attribute', 'empty', 'value_text', 'value_integer',
            'value_boolean', 'value_float', 'value_richtext', 'value_date',
            'value_option', 'value_file', 'value_image', 'kinds', 'kinds_map')

    def __init__(self, *args, **kwargs):
        super(ProductAttributeValueModelForm, self).__init__(*args, **kwargs)

        # Assign kinds_map custom widget and get it's choices.
        self.fields['kinds_map'].widget = AttributeValueKindsMapSelect(
            choices=self.get_kinds_map_choices())

        # Set javascript event trigger on attribute change.
        self.fields['attribute'].widget = forms.Select(
            choices=self.fields['attribute'].choices,
            attrs={'onchange': 'shopCatalogAttrValueOnChange(event);'})

    def clean(self):
        """
        Removes 'temp_data' from cleaned_data.
        """
        cleaned_data = super(ProductAttributeValueModelForm, self).clean()
        for item in self.temp_data:
            del cleaned_data[item]
        return cleaned_data

    def has_changed(self):
        """
        Removes 'temp_data' from changed_data so that form is not saved
        when nothing gets changed.
        """
        for item in self.temp_data:
            if item in self.changed_data:
                self.changed_data.remove(item)
        return super(ProductAttributeValueModelForm, self).has_changed()

    def get_kinds_map_choices(self):
        """
        Returns choices for a map of all attributes.
        """
        choices = ()
        for item in Attribute.objects.all():
            choices += (item.kind, item.pk),
        return choices
