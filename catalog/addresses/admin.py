# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.options import ModelAdmin

from catalog.addresses.models import Region, Country, Address


class RegionAdmin(ModelAdmin):
    list_display = ('name', 'code')


class CountryAdmin(ModelAdmin):
    list_display = ('name', 'code', 'region')
    list_filter = ('region', )
    fieldsets = (
        (None, {
            'fields': ('code', 'name'),
        }),
        (None, {
            'fields': ('region', ),
        }),
    )


class AddressAdmin(ModelAdmin):
    list_display = (
        'name', 'address', 'address2', 'zip_code', 'city', 'country',
        'user_shipping', 'user_billing')
    list_filter = ('country', )
    raw_id_fields = ('user_shipping', 'user_billing')


admin.site.register(Region, RegionAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Address, AddressAdmin)
