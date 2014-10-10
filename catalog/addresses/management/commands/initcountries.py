# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from urllib2 import urlopen

from django.utils.encoding import smart_str
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

    def handle(self, *args, **options):
        print 'Querying database at {}.'.format(COUNTRIES_API_URL)

        api = urlopen(COUNTRIES_API_URL)
        data = json.loads(api.read()).get('geonames', None)
        if data is not None:
            self.data = dict((x['countryCode'], x) for x in data)
        else:
            raise CommandError('Error fetching %s.' % COUNTRIES_API_URL)

        codes = list(args) if len(args) else self.data.keys()
        codes = [x for x in codes if x in self.data]

        created_countries = []
        created_regions = []

        for code in codes:
            country = self.data.get(code)

            try:
                region = Region.objects.get(code=country['continent'])
            except Region.DoesNotExist:
                print 'Creating region: \'{}\' ({}).'.\
                    format(country['continent'],
                           self.get_unicode(country['continentName']))
                region = Region.objects.create(code=country['continent'],
                                               name=country['continentName'])
                created_regions.append(country['continent'])

            if not Country.objects.filter(code=code):
                print 'Creating country: \'{}\' ({}).'.\
                    format(code, self.get_unicode(country['countryName']))

                Country.objects.create(code=code, name=country['countryName'],
                                       region=region)
                created_countries.append(code)

        print 'Done! Created {} countries, and {} regions.'.\
            format(len(created_countries), len(created_regions))

    def get_unicode(self, string):
        try:
            return '{}'.format(smart_str(string))
        except UnicodeDecodeError:
            return 'Don\'t want to deal with unicode errors right now, sry!'
