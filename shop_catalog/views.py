# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.http import Http404, HttpResponse

from shop.views import ShopView, ShopListView, ShopDetailView
from shop.views.product import ProductDetailView as ProductDetailViewBase

from shop_catalog.models import Category, Product
from shop_catalog.utils.shortcuts import get_by_slug_or_404


class CategoryListView(ShopListView):
    template_name = 'shop/category_list.html'

    def get_queryset(self):
        return Category.objects.active()


class CategoryDetailView(ShopDetailView):
    model = Category
    template_name = 'shop/category_detail.html'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg, None)
        return get_by_slug_or_404(Category, slug)

    def get_context_data(self, **kwargs):
        context = super(CategoryDetailView, self).get_context_data(**kwargs)
        if self.object:
            context['object_list'] = Product.objects.active(
                category_id=self.object.pk)
        return context


class ProductListView(ShopListView):
    template_name = 'shop/product_list.html'

    def get_queryset(self):
        return Product.objects.active().top_level()


class ProductDetailView(ProductDetailViewBase):
    model = Product
    template_name = 'shop/product_detail.html'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg, None)
        return get_by_slug_or_404(Product, slug)


class ProductVariantsJSONView(ShopView):
    """
    If GET kwargs not specified, returns all product variants.
    Otherwise tries to match kwargs with a variant by it's attributes or
    returns None (raises Http404 if request is not ajax).
    """
    def get(self, request, slug, *args, **kwargs):
        product = get_by_slug_or_404(Product, slug)
        attrs = dict(request.GET.items())

        response = None
        if attrs:
            variant = product.get_variant(**attrs)
            if variant is not None:
                response = variant.as_json
        else:
            variants = product.variants.select_related().all()
            if variants:
                response = [x.as_json for x in variants]

        if response is None and not request.is_ajax():
            raise Http404

        return HttpResponse(
            json.dumps(response), content_type='application/json')
