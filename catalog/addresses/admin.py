# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.options import ModelAdmin

from hvad.admin import TranslatableAdmin

from catalog.addresses.models import Country, Address


class CountryAdmin(TranslatableAdmin):
    pass


class AddressAdmin(ModelAdmin):
    list_display = (
        'name', 'address', 'address2', 'zip_code', 'city', 'country',
        'user_shipping', 'user_billing')
    raw_id_fields = ('user_shipping', 'user_billing')


admin.site.register(Address, AddressAdmin)
admin.site.register(Country, CountryAdmin)
