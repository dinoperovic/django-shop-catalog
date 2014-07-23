# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from shop.addressmodel.models import USER_MODEL
from hvad.models import TranslatableModel, TranslatedFields


BASE_ADDRESS_TEMPLATE = _("""Name: %(name)s,
Address: %(address)s,
Zip-Code: %(zipcode)s,
City: %(city)s,
State: %(state)s,
Country: %(country)s""")

ADDRESS_TEMPLATE = getattr(
    settings, 'SHOP_ADDRESS_TEMPLATE', BASE_ADDRESS_TEMPLATE)


@python_2_unicode_compatible
class Country(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(_('Name'), max_length=255),
    )

    def __str__(self):
        return self.lazy_translation_getter('name')

    class Meta:
        db_table = 'catalog_addresses_countries'
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')


@python_2_unicode_compatible
class Address(models.Model):
    user_shipping = models.OneToOneField(
        USER_MODEL, blank=True, null=True,
        related_name='catalog_shipping_address',
        verbose_name=_('User shipping'))

    user_billing = models.OneToOneField(
        USER_MODEL, blank=True, null=True,
        related_name='catalog_billing_address',
        verbose_name=_('User billing'))

    name = models.CharField(_('Name'), max_length=255)
    email = models.EmailField(_('Email'), max_length=255)
    address = models.CharField(_('Address'), max_length=255)
    address2 = models.CharField(_('Address 2'), max_length=255, blank=True)
    zip_code = models.CharField(_('Zip Code'), max_length=20)
    city = models.CharField(_('City'), max_length=20)
    state = models.CharField(_('State'), max_length=255)
    country = models.ForeignKey(
        Country, verbose_name=_('Country'))

    class Meta:
        db_table = 'catalog_addresses_addresses'
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')

    def __str__(self):
        return '{} ({}, {})'.format(self.name, self.zip_code, self.city)

    def clone(self):
        new_kwargs = dict([(fld.name, getattr(self, fld.name))
                           for fld in self._meta.fields if fld.name != 'id'])
        return self.__class__.objects.create(**new_kwargs)

    def as_text(self):
        return ADDRESS_TEMPLATE % {
            'name': self.name,
            'email': self.email,
            'address': '%s\n%s' % (self.address, self.address2),
            'zipcode': self.zip_code,
            'city': self.city,
            'state': self.state,
            'country': self.country,
        }
