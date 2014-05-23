# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import Http404

from shop.views import ShopListView, ShopDetailView
from shop.views.product import ProductDetailView as ProductDetailViewBase

from shop_catalog.models import Category, Product


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
        try:
            obj = Category.objects.get_by_slug(slug)
        except Product.DoesNotExist:
            raise Http404

        return obj

    def get_context_data(self, **kwargs):
        context = super(CategoryDetailView, self).get_context_data(**kwargs)
        if self.object:
            context['object_list'] = Product.objects.active().filter(
                category_id=self.object.pk)
        return context


class ProductListView(ShopListView):
    template_name = 'shop/product_list.html'

    def get_queryset(self):
        return Product.objects.active()


class ProductDetailView(ProductDetailViewBase):
    model = Product
    template_name = 'shop/product_detail.html'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.get_queryset()

        slug = self.kwargs.get(self.slug_url_kwarg, None)
        try:
            obj = Product.objects.get_by_slug(slug)
        except Product.DoesNotExist:
            raise Http404

        return obj
