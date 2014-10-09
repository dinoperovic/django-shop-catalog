# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from catalog.models import Product


USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


@python_2_unicode_compatible
class Review(models.Model):
    """
    Model for product reviews.
    """
    RATING_CHOICES = tuple((x, x) for x in range(1, 6))

    product = models.ForeignKey(
        Product, related_name='reviews', verbose_name=_('Product'))
    user = models.ForeignKey(
        USER_MODEL, blank=True, null=True, verbose_name=_('User'))
    session_key = models.CharField(
        _('Session key'), max_length=255, blank=True)

    body = models.TextField(_('Body'), max_length=1024, blank=True)

    rating = models.PositiveIntegerField(
        _('Rating'), max_length=1,
        choices=RATING_CHOICES, default=RATING_CHOICES[0][0])

    date_added = models.DateTimeField(_('Date added'), auto_now_add=True)
    last_modified = models.DateTimeField(_('Last modified'), auto_now=True)

    class Meta:
        db_table = 'catalog_reviews_reviews'
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        unique_together = ('product', 'user')
        ordering = ('-date_added', )

    def __str__(self):
        return '{}...'.format(self.body[:13])

    def get_absolute_url(self):
        return reverse(
            'catalog_review_detail', args=[self.product.get_slug(), self.pk])
