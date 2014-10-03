# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.conf.urls import patterns, url
from django.utils.text import slugify

from shop.views import ShopTemplateView

from catalog.views import (
    ProductListView, ProductDetailView,
    CategoryListView, CategoryDetailView,
    BrandListView, BrandDetailView,
    ManufacturerListView, ManufacturerDetailView,
    ProductVariantsJSONView)
from catalog import settings as scs


def catalog_url(url_string, view, name, extra_url=None):
    """
    Url wrapper function that gets an url attribute from settings
    if it exists and prepends it to the url. If it doesn't exist, the
    given string is used as a base url. It also prefixes the name with
    the string 'catalog_'.
    """
    url_string = getattr(scs, '{}_URL'.format(url_string.upper()), url_string)
    url_string = slugify(url_string)

    if extra_url is not None:
        url_string = '{}/{}'.format(url_string, extra_url)
    url_string = url_string.strip('/')

    if url_string:
        url_string = '{}/'.format(url_string)
    url_string = r'^{}$'.format(url_string)

    return url(url_string, view, name='catalog_{}'.format(name))


pats = []

if scs.HAS_CATEGORIES:
    pats.extend([
        catalog_url('category', CategoryListView.as_view(), 'category_list'),
        catalog_url('category', CategoryDetailView.as_view(),
                    'category_detail', '(?P<slug>[0-9A-Za-z-_.//]+)'),
    ])

if scs.HAS_BRANDS:
    pats.extend([
        catalog_url('brand', BrandListView.as_view(), 'brand_list'),
        catalog_url('brand', BrandDetailView.as_view(), 'brand_detail',
                    '(?P<slug>[0-9A-Za-z-_.//]+)'),
    ])

if scs.HAS_MANUFACTURERS:
    pats.extend([
        catalog_url('manufacturer', ManufacturerListView.as_view(),
                    'manufacturer_list'),
        catalog_url('manufacturer', ManufacturerDetailView.as_view(),
                    'manufacturer_detail', '(?P<slug>[0-9A-Za-z-_.//]+)'),
    ])


if 'catalog.reviews' in settings.INSTALLED_APPS:
    from catalog.reviews.urls import pats as reviews_pats
    pats.extend(reviews_pats)


# Main patterns.
pats.extend([
    catalog_url('product', ProductListView.as_view(), 'product_list'),
    catalog_url('product', ProductVariantsJSONView.as_view(),
                'product_variants', '(?P<slug>[0-9A-Za-z-_.//]+)/variants/'),
    catalog_url('product', ProductDetailView.as_view(), 'product_detail',
                '(?P<slug>[0-9A-Za-z-_.//]+)'),

    url(r'^$', ShopTemplateView.as_view(
        template_name='shop/welcome.html'), name='shop_welcome'),
])

urlpatterns = patterns('', *pats)
