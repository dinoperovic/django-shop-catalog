# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models.query import QuerySet

from hvad.manager import TranslationManager, TranslationQueryset


class CatalogQuerySet(QuerySet):
    """
    Defines "active" filter for getting active objects.
    """
    def active(self, **kwargs):
        return self.filter(active=True, **kwargs)


class CatalogTranslationQuerySet(TranslationQueryset, CatalogQuerySet):
    pass


class CatalogManager(TranslationManager):
    """
    Defines basic methods and should be used on CatalogModel
    inherited models.
    """
    queryset_class = CatalogTranslationQuerySet
    default_class = CatalogQuerySet

    def get_queryset(self):
        return self.default_class(self.model, using=self._db)

    def active(self, language_code=None, **kwargs):
        return self.get_queryset().active(**kwargs)

    # TODO: make slugs not unique, and handle getting them.
    # maybe add validation errors rather than making a constraint on
    # a database. get_by_slug could be removed since its not used often.
    # Could set unique_together (slug, id) on a translated model but not
    # on the base model. Reason to do so is that translated version of
    # a model could have the same slug, avoiding:
    # (en: iphone, hr: iphone-hr)
    def get_by_slug(self, slug, language_code=None):
        return self.language(language_code).active().get(slug=slug)


class ProductQuerySet(CatalogQuerySet):
    """
    Adds a Product specific QuerySet methods.
    """
    def top_level(self, **kwargs):
        return self.filter(parent_id=None, **kwargs)

    def filter_attrs(self, **kwargs):
        pks = [x.pk for x in self if x.filter_variants(**kwargs) is not None]
        return self.filter(pk__in=pks)


class ProductTranslationQuerySet(TranslationQueryset, ProductQuerySet):
    pass


class ProductManager(CatalogManager):
    """
    Adds a Product specific manager methods.
    """
    queryset_class = ProductTranslationQuerySet
    default_class = ProductQuerySet

    def top_level(self, language_code=None, **kwargs):
        return self.get_queryset().top_level(**kwargs)
