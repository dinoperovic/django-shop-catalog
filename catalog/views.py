# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import operator

from django.db.models import Q
from django.http import Http404, HttpResponse
from django.views.generic import CreateView, View
from django.views.generic.list import MultipleObjectMixin
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect

from shop.views import ShopView, ShopListView, ShopDetailView
from shop.views.product import ProductDetailView as ProductDetailViewBase
from shop.util.cart import get_or_create_cart

from catalog.models import (
    CartModifierCode, Category, Brand, Manufacturer, Product, Attribute)
from catalog.forms import CartModifierCodeModelForm
from catalog.utils.shortcuts import get_by_slug_or_404
from catalog.utils import calculate_base_price
from catalog import settings as scs


def get_categorization_filters(request):
    """
    Returns filter dictionary for categorization objects.
    """
    filters = {}
    category = request.GET.get('category', None)
    brand = request.GET.get('brand', None)
    manufacturer = request.GET.get('manufacturer', None)

    for slug, model in [(category, Category), (brand, Brand),
                        (manufacturer, Manufacturer)]:
        if slug:
            try:
                pk = model.objects.get_by_slug(slug).pk
                filters = {'{}_id'.format(model.__name__.lower()): pk}
            except model.DoesNotExist:
                pass
    return filters


def get_price_filters(request):
    """
    Return prices formated into a base currency.
    """
    price_from = request.GET.get('price-from', None)
    price_to = request.GET.get('price-to', None)
    currency = \
        request.GET.get('currency', request.session.get('currency', None))
    if currency and price_from:
        price_from = calculate_base_price(price_from, currency)
    if currency and price_to:
        price_to = calculate_base_price(price_to, currency)
    return price_from, price_to


def get_date_filters(request):
    """
    Return date filters.
    """
    date_from = request.GET.get('date-from', None)
    date_to = request.GET.get('date-to', None)
    return date_from, date_to


def search_products(queryset, request):
    """
    Simple product serach by name and slug.
    """
    query = request.GET.get('search', None)
    if query:
        keywords = [x for x in query.split(' ') if x]
        pks = list(queryset.values_list('pk', flat=True))
        queryset = Product.objects.language().filter(
            Q(pk__in=pks) &
            (reduce(operator.or_, (Q(upc=x) for x in keywords)) |
             reduce(operator.or_, (Q(slug__icontains=x) for x in keywords)) |
             reduce(operator.or_, (Q(name__icontains=x) for x in keywords))))
    return queryset


def sort_products(queryset, request):
    """
    Sort products.
    """
    sort = request.GET.get('sort', None)
    if sort and len(queryset) and hasattr(queryset[0], sort.lstrip('-')):
        pks = list(queryset.values_list('pk', flat=True))
        queryset = Product.objects.language().filter(pk__in=pks).order_by(sort)
    return queryset


def filter_products(queryset, request):
    """
    A helper function that applies filters to the given product queryset.
    """
    cat_filters = get_categorization_filters(request)
    if cat_filters:
        queryset = queryset.filter(**cat_filters)

    price_from, price_to = get_price_filters(request)
    if price_from or price_to:
        queryset = queryset.filter_price(price_from, price_to)

    date_from, date_to = get_date_filters(request)
    if date_from or date_to:
        queryset = queryset.filter_date(date_from, date_to)

    attrs = Attribute.filter_dict(request.GET)
    if attrs:
        queryset = queryset.filter_attrs(**attrs)

    queryset = search_products(queryset, request)
    queryset = sort_products(queryset, request)

    return queryset


class CartModifierCodeCreateView(CreateView):
    model = CartModifierCode
    form_class = CartModifierCodeModelForm
    template_name = 'shop/cart_modifier_code_create.html'
    success_url = reverse_lazy('catalog_cart_modifier_code_create')

    def get_success_url(self):
        return self.request.GET.get('next', self.success_url)

    def get_form_kwargs(self):
        kwargs = super(CartModifierCodeCreateView, self).get_form_kwargs()
        cart = get_or_create_cart(self.request, True)
        instance = CartModifierCode(cart=cart)
        kwargs.update({'instance': instance})
        return kwargs

    def get_context_data(self, **kwargs):
        context = {'object_list': []}
        cart = get_or_create_cart(self.request, True)
        context['object_list'] = CartModifierCode.objects.filter(cart=cart)
        context.update(kwargs)
        return super(CartModifierCodeCreateView, self).\
            get_context_data(**context)


class CartModifierCodeDeleteView(View):
    """
    This view deletes all CartModifierCode's for the currenct cart.
    """
    success_url = reverse_lazy('catalog_cart_modifier_code_create')

    def get_success_url(self):
        return self.request.GET.get('next', self.success_url)

    def get(self, *args, **kwargs):
        self.delete_cart_modifier_codes()
        return redirect(self.get_success_url())

    def post(self, *args, **kwargs):
        self.delete_cart_modifier_codes()
        return redirect(self.get_success_url())

    def delete_cart_modifier_codes(self, codes=None):
        cart = get_or_create_cart(self.request)
        filters = {}
        if codes:
            filters['code__in'] = codes
        cart.cartmodifiercode_set.filter(**filters).delete()


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


class CategoryDetailViewBase(ShopDetailView, MultipleObjectMixin):
    model = None
    object_list = []
    paginate_by = scs.PRODUCTS_PER_PAGE

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

                # Add all children to filters, this should maybe go in
                # a method like 'get_products()' on categorization models.
                pks = [x.pk for x in
                       self.object.get_descendants(include_self=True)]
                filters = {'{}_id__in'.format(context_object_name): pks}

                products = Product.objects.active(**filters).top_level()
                products = filter_products(products, self.request)
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
    paginate_by = scs.PRODUCTS_PER_PAGE

    def get_queryset(self):
        queryset = self.model.objects.active().top_level()
        return filter_products(queryset, self.request)


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
