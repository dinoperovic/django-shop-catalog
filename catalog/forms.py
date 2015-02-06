# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.forms.models import BaseInlineFormSet
from django.utils.translation import get_language
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_str

from hvad.forms import TranslatableModelForm

from catalog.models import (
    Modifier, ModifierCode, CartModifierCode, Category, Brand, Manufacturer,
    Product, Attribute, ProductAttributeValue, RelatedProduct)

from catalog.widgets import AttributeValueKindsMapSelect


class CatalogModelFormBase(TranslatableModelForm):
    """
    Objects that inherit from CatalogModel should have their form
    inherit from this one for some modified fields.
    """
    class Meta:
        model = None

    def clean(self):
        """
        Check that object with this slug on this language
        doesn't exists.
        """
        instance = getattr(self, 'instance', None)
        if instance is not None and instance.pk is None:
            slug = self.cleaned_data.get('slug', None)
            if slug is not None:
                language = getattr(self, 'language', get_language()[:2])
                try:
                    self._meta.model.objects.get_by_slug(slug, language)
                    raise forms.ValidationError(
                        _('%s with this slug already exists on this language.')
                        % self._meta.model.__name__)
                except self._meta.model.DoesNotExist:
                    pass
        return super(CatalogModelFormBase, self).clean()


class ModifierModelForm(CatalogModelFormBase):
    class Meta:
        model = Modifier


class CartModifierCodeModelForm(forms.ModelForm):
    class Meta:
        model = CartModifierCode

    def clean_code(self):
        instance = getattr(self, 'instance', None)
        code = self.cleaned_data.get('code')
        if instance is not None:
            if CartModifierCode.objects.filter(cart=instance.cart, code=code):
                raise forms.ValidationError(
                    _('Code is already applied to your cart.'))
            if not ModifierCode.objects.valid(code=code):
                raise forms.ValidationError(_('Code is invalid or expired.'))
        return code


class CategoryModelForm(CatalogModelFormBase):
    class Meta:
        model = Category


class BrandModelForm(CatalogModelFormBase):
    class Meta:
        model = Brand


class ManufacturerModelForm(CatalogModelFormBase):
    class Meta:
        model = Manufacturer


class ProductModelForm(CatalogModelFormBase):
    class Meta:
        model = Product

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


class ProductAttributeValueInlineFormSet(BaseInlineFormSet):
    """
    Custom formset for products attribute values.
    """
    def has_duplicates(self, instance, forms):
        """
        Returns if another variant with selected attributes
        already exists.
        """
        variation_exists = True
        variations = instance.parent.get_variations(
            exclude={'pk': instance.pk})

        for form in forms:
            key = form.cleaned_data['attribute'].code
            value = force_str(
                ProductAttributeValue.value_for(form.cleaned_data))

            # Check if this key, value pair already exists.
            if key in variations:
                if value in variations[key]['values']:
                    continue

            # One key, value pair does not exist in variations
            # so attribute pairs are valid.
            variation_exists = False
            break

        return variation_exists

    def clean(self):
        super(ProductAttributeValueInlineFormSet, self).clean()
        instance = getattr(self, 'instance', None)

        if any(self.errors) or instance is None:
            return

        # Filter out forms without attribute specified (empty).
        clean_forms = [x for x in self.forms if 'attribute' in x.cleaned_data]

        if instance.is_variant:
            # At least one attribute must be specified on a variant.
            if not clean_forms:
                raise forms.ValidationError(
                    _('If product is a "variant" attributes must be '
                      'specified.'))

            # Check for duplicates.
            if self.has_duplicates(instance, clean_forms):
                raise forms.ValidationError(
                    _('A "variant" for this parent with selected '
                      'attributes already exsists.'))

        # Check that product is not top level and has attributes.
        if instance.is_top_level and clean_forms:
            raise forms.ValidationError(
                _('Attributes can only be assigned to a "variant" '
                  'of a product.'))


class ProductAttributeValueModelForm(forms.ModelForm):
    """
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
            'attribute', 'empty', 'value_integer', 'value_boolean',
            'value_float', 'value_date', 'value_option', 'value_file',
            'value_image', 'kinds', 'kinds_map')

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
            if item in cleaned_data:
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


class RelatedProductModelForm(forms.ModelForm):
    """
    Related product model form.
    """
    class Meta:
        model = RelatedProduct

    def clean_product(self):
        """
        Custom product validation.
        """
        instance = getattr(self, 'instance', None)
        product = self.cleaned_data.get('product')

        if product is not None:
            if product.is_variant:
                raise forms.ValidationError(
                    _('You can\'t assign a "variant" product as a '
                      'related product, select a top level '
                      'product.'))

            if instance is not None:
                if instance.base_product_id == product.pk:
                    raise forms.ValidationError(
                        _('You can\'t assign a related product as '
                          'itself.'))

        return product


class RelatedProductInlineFormSet(BaseInlineFormSet):
    """
    Related Product custom formset.
    """
    def clean(self):
        super(RelatedProductInlineFormSet, self).clean()
        instance = getattr(self, 'instance', None)

        if any(self.errors) or instance is None:
            return

        # Filter out forms without product specified (empty).
        clean_forms = [x for x in self.forms if 'product' in x.cleaned_data]

        # Check that product is top level.
        if not instance.is_top_level and clean_forms:
            raise forms.ValidationError(
                _('Related products have to be specified on a top '
                  'level product. It\'s variants will inherit the '
                  'relations automatically.'))
