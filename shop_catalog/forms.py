# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils.translation import ugettext_lazy as _

from hvad.forms import TranslatableModelForm

from shop_catalog.models import Product, Attribute, ProductAttributeValue


class CatalogModelFormBase(TranslatableModelForm):
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
    class Meta:
        model = Product

    def __init__(self, *args, **kwargs):
        super(ProductModelForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = self.get_parent_queryset()

    def clean_parent(self):
        instance = getattr(self, 'instance', None)
        data = self.cleaned_data.get('parent')

        if instance is not None:
            if instance.is_group:
                raise forms.ValidationError(
                    _('Other products have set this product as their parent, '
                      'you need to unassign or delete them before you can '
                      'change this value.'))
            if data is not None and data == instance:
                raise forms.ValidationError(
                    _('Cannot assign itself as a parent Product.'))

        if data is not None and data.is_variant:
            raise forms.ValidationError(
                _('Cannot assign "variant" as a parent Product.'))

        return data

    def get_parent_queryset(self):
        instance = getattr(self, 'instance', None)
        queryset = Product.objects.top_level()
        pks = list(queryset.values_list('pk', flat=True))

        if instance is not None and instance.pk in pks:
            pks.remove(instance.pk)

        return queryset.filter(pk__in=pks)


class ProductAttributeValueModelForm(forms.ModelForm):
    temp_data = ['empty', 'kinds', 'kinds_map']

    empty = forms.CharField(required=False, label=_('Value'))
    kinds = forms.CharField(
        widget=forms.Select(choices=Attribute.KIND_CHOICES))
    kinds_map = forms.CharField()

    class Meta:
        model = ProductAttributeValue
        labels = {'attribute': _('Attribute (Type)')}
        fields = (
            'attribute',
            'empty',
            'value_text',
            'value_integer',
            'value_boolean',
            'value_float',
            'value_richtext',
            'value_date',
            'value_file',
            'value_image',
            'kinds',
            'kinds_map',
        )

    def __init__(self, *args, **kwargs):
        super(ProductAttributeValueModelForm, self).__init__(*args, **kwargs)

        self.fields['kinds_map'].widget = forms.Select(
            choices=self.get_kinds_map_choices())

        self.fields['attribute'].widget = forms.Select(
            choices=self.fields['attribute'].choices,
            attrs={'onchange': 'shopCatalogAttrValueOnChange(event);'})

    def clean(self):
        cleaned_data = super(ProductAttributeValueModelForm, self).clean()
        for item in self.temp_data:
            del cleaned_data[item]
        return cleaned_data

    def has_changed(self):
        for item in self.temp_data:
            if item in self.changed_data:
                self.changed_data.remove(item)
        return super(ProductAttributeValueModelForm, self).has_changed()

    def get_kinds_map_choices(self):
        choices = ()
        for item in Attribute.objects.all():
            choices += (item.kind, item.pk),
        return choices
