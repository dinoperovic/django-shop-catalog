# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.utils.translation import ugettext_lazy as _

from catalog.addresses.models import Region, Country, Address


class RegionAdmin(ModelAdmin):
    list_display = ('name', 'code', 'get_number_of_countries', 'active')
    list_filter = ('active', )
    fieldsets = (
        (None, {
            'fields': ('code', 'name'),
        }),
        (None, {
            'fields': ('active', ),
        }),
    )

    def get_number_of_countries(self, obj):
        return obj.countries.all().count()
    get_number_of_countries.short_description = _('Number of countries')


class CountryAdmin(ModelAdmin):
    list_display = ('name', 'code', 'region', 'active')
    list_filter = ('region', 'active')
    fieldsets = (
        (None, {
            'fields': ('code', 'name'),
        }),
        (None, {
            'fields': ('active', ),
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
