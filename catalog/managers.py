# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from django.db.models import Q
from django.db.models import Manager
from django.db.models.query import QuerySet
from django.utils.translation import get_language

from parler.managers import TranslatableManager, TranslatableQuerySet

from catalog.utils import round_2
from catalog import settings as scs


class CatalogQuerySet(QuerySet):
    """
    Defines "active" filter for getting active objects.
    """
    def active(self, **kwargs):
        return self.filter(active=True, **kwargs)


class CatalogTranslatableQuerySet(TranslatableQuerySet, CatalogQuerySet):
    pass


class CatalogManager(TranslatableManager):
    """
    Defines basic methods and should be used on CatalogModel
    inherited models.
    """
    queryset_class = CatalogTranslatableQuerySet

    def active(self, **kwargs):
        return self.all().active(**kwargs)

    def get_by_slug(self, slug, language=None):
        if not language:
            language = get_language()[:2]
        return self.translated(slug=slug).active().get()


class ModifierCodeQuerySet(CatalogQuerySet):
    def valid(self, **kwargs):
        at_datetime = kwargs.pop('at_datetime', datetime.now)
        qs = self.filter(
            Q(valid_from__lte=at_datetime) &
            (Q(valid_until__isnull=True) | Q(valid_until__gt=at_datetime)))
        return qs.filter(**kwargs)


class ModifierCodeManager(Manager):
    def get_queryset(self):
        return ModifierCodeQuerySet(self.model, using=self._db)

    def active(self, **kwargs):
        return self.get_queryset().active(**kwargs)

    def valid(self, **kwargs):
        return self.active().valid(**kwargs)


class ProductQuerySet(CatalogQuerySet):
    """
    Adds a Product specific QuerySet methods.
    """
    def top_level(self, **kwargs):
        return self.filter(parent_id=None, **kwargs)

    def filter_attrs(self, **kwargs):
        pks = [x.pk for x in self if x.filter_variants(**kwargs) is not None]
        return self.filter(pk__in=pks)

    def filter_price(self, price_from=None, price_to=None):
        filters = {}
        try:
            filters['unit_price__gte'] = round_2(float(price_from))
        except (TypeError, ValueError):
            pass
        try:
            filters['unit_price__lte'] = round_2(float(price_to))
        except (TypeError, ValueError):
            pass
        return self.filter(**filters)

    def filter_date(self, date_from=None, date_to=None):
        filters = {}
        try:
            filters['date_added__gte'] = datetime.strptime(
                date_from, scs.DATE_INPUT_FOMRAT)
        except (TypeError, ValueError):
            pass
        try:
            filters['date_added__lte'] = datetime.strptime(
                date_to, scs.DATE_INPUT_FOMRAT)
        except (TypeError, ValueError):
            pass
        return self.filter(**filters)


class ProductTranslationQuerySet(TranslatableQuerySet, ProductQuerySet):
    pass


class ProductManager(CatalogManager):
    """
    Adds a Product specific manager methods.
    """
    queryset_class = ProductTranslationQuerySet

    def top_level(self, language_code=None, **kwargs):
        return self.get_queryset().top_level(**kwargs)
