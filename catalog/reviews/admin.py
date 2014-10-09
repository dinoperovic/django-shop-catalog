# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.options import ModelAdmin

from catalog.reviews.models import Review


class ReviewAdmin(ModelAdmin):
    list_display = ('__str__', 'rating', 'product', 'user')
    search_fields = ('body', 'product__pk', 'user__username')
    list_filter = ('rating', 'product', 'user')
    raw_id_fields = ('product', 'user')

    fieldsets = (
        (None, {
            'fields': ('product', 'user', ),
        }),
        (None, {
            'fields': ('body', 'rating'),
        }),
    )


admin.site.register(Review, ReviewAdmin)
