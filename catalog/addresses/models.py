# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import RegexValidator
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from shop.addressmodel.models import USER_MODEL

from catalog import settings as scs


BASE_ADDRESS_TEMPLATE = _("""Name: %(name)s,
Address: %(address)s,
Zip-Code: %(zipcode)s,
City: %(city)s,
State: %(state)s,
Country: %(country)s""")

ADDRESS_TEMPLATE = getattr(
    settings, 'SHOP_ADDRESS_TEMPLATE', BASE_ADDRESS_TEMPLATE)


@python_2_unicode_compatible
class Region(models.Model):
    code = models.SlugField(
        _('Code'), max_length=128, unique=True, db_index=True)
    name = models.CharField(_('Name'), max_length=255)
    active = models.BooleanField(
        _('Active'), default=True, help_text=scs.ACTIVE_FIELD_HELP_TEXT)

    class Meta:
        db_table = 'catalog_addresses_regions'
        verbose_name = _('Region')
        verbose_name_plural = _('Regions')
        ordering = ('name', )

    def __str__(self):
        return '{}'.format(self.name)


@python_2_unicode_compatible
class Country(models.Model):
    region = models.ForeignKey(
        Region, related_name='countries', verbose_name=_('Region'),
        help_text=_('Select a region for this country. This is mostly used to '
                    'define shipping rates per region.'))

    code = models.SlugField(
        _('Code'), max_length=2, unique=True, db_index=True,
        help_text=_('A 2 letter country code.'))

    name = models.CharField(_('Name'), max_length=255)
    active = models.BooleanField(
        _('Active'), default=True, help_text=scs.ACTIVE_FIELD_HELP_TEXT)

    def __str__(self):
        return '{}'.format(self.name)

    class Meta:
        db_table = 'catalog_addresses_countries'
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ('name', )


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
        Country, verbose_name=_('Country'),
        limit_choices_to={'active': True, 'region__active': True})

    phone_number = models.CharField(
        _('Phone number'), max_length=16, blank=True, validators=[
            RegexValidator(r'^\+?1?\d{9,15}$',
                           _('Phone number must be entered in the '
                             'format: "+999999999". Up to 15 digits '
                             'allowed.'), 'invalid')])

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
            'phone_number': self.phone_number,
        }
