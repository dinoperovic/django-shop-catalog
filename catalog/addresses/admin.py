# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.utils.translation import ugettext_lazy as _

from hvad.admin import TranslatableAdmin

from catalog.addresses.models import Region, Country, Address


class RegionAdmin(TranslatableAdmin):
    list_display = ('get_name', 'code')

    def get_name(self, obj):
        return obj.__str__()
    get_name.short_description = _('Name')


class CountryAdmin(TranslatableAdmin):
    list_display = ('get_name', 'code', 'region')
    list_filter = ('region', )

    def get_name(self, obj):
        return obj.__str__()
    get_name.short_description = _('Name')


class AddressAdmin(ModelAdmin):
    list_display = (
        'name', 'address', 'address2', 'zip_code', 'city', 'country',
        'user_shipping', 'user_billing')
    list_filter = ('country', )
    raw_id_fields = ('user_shipping', 'user_billing')


admin.site.register(Region, RegionAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Address, AddressAdmin)
