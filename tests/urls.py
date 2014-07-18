# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.conf.urls.i18n import i18n_patterns


urlpatterns = i18n_patterns(
    '',
    url(r'^catalog/', include('catalog.urls')),
    url(r'^shop/', include('shop.urls')),
)
