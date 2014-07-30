# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from urllib2 import urlopen

from django.core.management.base import CommandError, BaseCommand

from catalog.addresses.models import Region, Country


COUNTRIES_API_URL = \
    'http://api.geonames.org/countryInfoJSON?username=dinoperovic'


class Command(BaseCommand):
    help = 'Create countries and regions automatically from api.geonames.org.'
    args = '<code code code code...>'
    data = None

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        print 'Querying database at %s.' % COUNTRIES_API_URL
        api = urlopen(COUNTRIES_API_URL)
        data = json.loads(api.read()).get('geonames', None)
        if data is not None:
            self.data = dict((x['countryCode'], x) for x in data)
        else:
            raise CommandError('Error fetching %s' % COUNTRIES_API_URL)
        print 'Creating countries and regions.'

    def handle(self, *args, **options):
        if len(args):
            for code in list(args):
                self.create_country(code)
        else:
            for code in self.data.keys():
                self.create_country(code)

    def create_country(self, code):
        if code in self.data:
            country = self.data.get(code)

            try:
                region = Region.objects.get(
                    code=country['continent'])
            except Region.DoesNotExist:
                region = Region.objects.create(
                    code=country['continent'], name=country['continentName'])

        if not Country.objects.filter(code=code):
            Country.objects.create(
                code=code, name=country['countryName'], region=region)
