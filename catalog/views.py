# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.http import Http404, HttpResponse

from shop.views import ShopView, ShopListView, ShopDetailView
from shop.views.product import ProductDetailView as ProductDetailViewBase

from catalog.models import (
    Category, Brand, Manufacturer, Product, Attribute)
from catalog.utils.shortcuts import get_by_slug_or_404


class CategoryListViewBase(ShopListView):
    model = None

    def get_queryset(self):
        return self.model.objects.active()


class CategoryListView(CategoryListViewBase):
    model = Category
    template_name = 'shop/category_list.html'


class BrandListView(CategoryListViewBase):
    model = Brand
    template_name = 'shop/brand_list.html'


class ManufacturerListView(CategoryListViewBase):
    model = Manufacturer
    template_name = 'shop/manufacturer_list.html'


class CategoryDetailViewBase(ShopDetailView):
    model = None

    def get_queryset(self):
        return self.model.objects.language().active()

    def get_context_data(self, **kwargs):
        """
        Adds a list of products into the context.
        """
        context = {'object_list': []}

        if self.object:
            context_object_name = self.get_context_object_name(self.object)
            if hasattr(Product, context_object_name):
                filters = {'{}_id'.format(context_object_name): self.object.pk}
                products = Product.objects.active(**filters).top_level()

                # Filter products by attributes.
                attrs = Attribute.filter_dict(self.request.GET)
                if any(attrs):
                    products = products.filter_attrs(**attrs)

                context['object_list'] = products

        context.update(kwargs)
        return super(CategoryDetailViewBase, self).get_context_data(**context)


class CategoryDetailView(CategoryDetailViewBase):
    model = Category
    template_name = 'shop/category_detail.html'


class BrandDetailView(CategoryDetailViewBase):
    model = Brand
    template_name = 'shop/brand_detail.html'


class ManufacturerDetailView(CategoryDetailViewBase):
    model = Manufacturer
    template_name = 'shop/manufacturer_detail.html'


class ProductListView(ShopListView):
    model = Product
    template_name = 'shop/product_list.html'

    def get_queryset(self):
        queryset = self.model.objects.active().top_level()
        attrs = Attribute.filter_dict(self.request.GET)
        return queryset.filter_attrs(**attrs) if any(attrs) else queryset


class ProductDetailView(ProductDetailViewBase):
    model = Product
    template_name = 'shop/product_detail.html'

    def get_queryset(self):
        return self.model.objects.language().active()


class ProductVariantsJSONView(ShopView):
    """
    If GET kwargs not specified, returns all product variants.
    Otherwise tries to match kwargs with a variant by or returns None
    (raises Http404 if request is not ajax).
    """
    def get(self, request, slug, *args, **kwargs):
        product = get_by_slug_or_404(Product, slug)
        attrs = dict(request.GET.items())

        response = None
        if attrs:
            variant = product.get_variant(**attrs)
            if variant is not None:
                response = variant.as_dict
        else:
            variants = product.variants.select_related().all()
            if variants:
                response = [x.as_dict for x in variants]

        if response is None and not request.is_ajax():
            raise Http404

        return HttpResponse(
            json.dumps(response), content_type='application/json')