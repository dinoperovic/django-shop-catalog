# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from django.utils.translation import ugettext_lazy as _

from catalog.reviews.models import Review


class ReviewAdmin(ModelAdmin):
    pass


admin.site.register(Review, ReviewAdmin)
