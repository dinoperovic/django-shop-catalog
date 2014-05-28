# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.query import QuerySet

from hvad.manager import TranslationManager, TranslationQueryset


class CatalogQuerySet(QuerySet):
    """
    Catalog QuerySet class.
    Defines "active" filter for getting active objects.
    """
    def active(self, **kwargs):
        return self.filter(active=True, **kwargs)


class CatalogTranslationQuerySet(TranslationQueryset, CatalogQuerySet):
    pass


class CatalogManager(TranslationManager):
    """
    Catalog Manager class.
    Defines basic methods and should be used on CatalogModel
    inherited models.
    """
    queryset_class = CatalogTranslationQuerySet
    default_class = CatalogQuerySet

    def get_queryset(self):
        return self.default_class(self.model, using=self._db)

    def active(self, language_code=None, **kwargs):
        return self.get_queryset().active(**kwargs)

    def get_by_slug(self, slug, language_code=None):
        return self.language(language_code).active().get(slug=slug)


class ProductQuerySet(CatalogQuerySet):
    def top_level(self, **kwargs):
        return self.filter(parent_id=None, **kwargs)


class ProductManager(CatalogManager):
    default_class = ProductQuerySet

    def top_level(self, language_code=None, **kwargs):
        return self.get_queryset().top_level(**kwargs)
