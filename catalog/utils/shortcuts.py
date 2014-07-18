# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import Http404


def get_by_slug_or_404(model, slug):
    try:
        return model.objects.get_by_slug(slug=slug)
    except model.DoesNotExist:
        raise Http404
