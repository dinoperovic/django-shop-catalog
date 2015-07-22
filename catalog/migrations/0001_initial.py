# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import filer.fields.file
import datetime
import filer.fields.image
import mptt.fields
from decimal import Decimal
import shop.util.fields
import catalog.fields
import django.db.models.deletion
import cms.models.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '__latest__'),
        ('shop', '__first__'),
        ('filer', '__latest__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.SlugField(help_text="Can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit.", unique=True, max_length=128, verbose_name='Code')),
                ('kind', models.CharField(default='integer', help_text='Select data type. If you choose "Option" data type, specify the options below.', max_length=20, verbose_name='Type', choices=[('integer', 'Integer'), ('boolean', 'True / False'), ('float', 'Float'), ('date', 'Date'), ('option', 'Option'), ('file', 'File'), ('image', 'Image')])),
                ('template', models.CharField(choices=[('radio', 'Radio')], max_length=255, blank=True, help_text='You can select a template for rendering this attribute or leave it empty for the default (dropdown) look.', null=True, verbose_name='Template')),
            ],
            options={
                'ordering': ('code',),
                'db_table': 'catalog_attributes',
                'verbose_name': 'Attribute',
                'verbose_name_plural': 'Attributes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttributeOption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attribute', models.ForeignKey(related_name='options', verbose_name='Attribute', to='catalog.Attribute')),
            ],
            options={
                'db_table': 'catalog_attribute_options',
                'verbose_name': 'Option',
                'verbose_name_plural': 'Options',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttributeOptionTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('value', models.CharField(max_length=128, verbose_name='Value')),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='catalog.AttributeOption', null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'catalog_attribute_options_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Option Translation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttributeTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='catalog.Attribute', null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'catalog_attributes_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Attribute Translation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text='Is this object active? You can hide it by unchecking this box.', verbose_name='Active')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Date added')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('body', cms.models.fields.PlaceholderField(related_name='brand_body_set', slotname='catalog_brand_body', editable=False, to='cms.Placeholder', null=True)),
                ('featured_image', filer.fields.image.FilerImageField(verbose_name='Featured image', blank=True, to='filer.Image', null=True)),
            ],
            options={
                'db_table': 'catalog_brands',
                'verbose_name': 'Brand',
                'verbose_name_plural': 'Brands',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BrandTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', models.SlugField(help_text="Can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit.", max_length=128, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='catalog.Brand', null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'catalog_brands_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Brand Translation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CartModifierCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=30, verbose_name='Code')),
                ('cart', models.ForeignKey(editable=False, to='shop.Cart')),
            ],
            options={
                'db_table': 'catalog_cart_modifier_codes',
                'verbose_name': 'Cart modifier code',
                'verbose_name_plural': 'Cart modifier codes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text='Is this object active? You can hide it by unchecking this box.', verbose_name='Active')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Date added')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('body', cms.models.fields.PlaceholderField(related_name='category_body_set', slotname='catalog_category_body', editable=False, to='cms.Placeholder', null=True)),
                ('featured_image', filer.fields.image.FilerImageField(verbose_name='Featured image', blank=True, to='filer.Image', null=True)),
            ],
            options={
                'db_table': 'catalog_categories',
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CategoryTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', models.SlugField(help_text="Can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit.", max_length=128, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='catalog.Category', null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'catalog_categories_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Category Translation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', catalog.fields.UnderscoreField(help_text="Can only contain the letters a-z, A-Z, digits and underscores, and can't start with a digit.", unique=True, max_length=123, verbose_name='Code')),
            ],
            options={
                'db_table': 'catalog_flags',
                'verbose_name': 'Flag',
                'verbose_name_plural': 'Flags',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FlagTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='catalog.Flag', null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'catalog_flags_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Flag Translation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text='Is this object active? You can hide it by unchecking this box.', verbose_name='Active')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Date added')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('body', cms.models.fields.PlaceholderField(related_name='manufacturer_body_set', slotname='catalog_manufacturer_body', editable=False, to='cms.Placeholder', null=True)),
                ('featured_image', filer.fields.image.FilerImageField(verbose_name='Featured image', blank=True, to='filer.Image', null=True)),
            ],
            options={
                'db_table': 'catalog_manufacturers',
                'verbose_name': 'Manufacturer',
                'verbose_name_plural': 'Manufacturers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ManufacturerTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', models.SlugField(help_text="Can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit.", max_length=128, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='catalog.Manufacturer', null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'catalog_manufacturers_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Manufacturer Translation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Modifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text='Is this object active? You can hide it by unchecking this box.', verbose_name='Active')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Date added')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('code', models.SlugField(help_text="Can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit.", unique=True, max_length=128, verbose_name='Code')),
                ('amount', shop.util.fields.CurrencyField(default=Decimal('0.0'), help_text='Absolute amount that should be applied. Can be negative.', verbose_name='Amount', max_digits=30, decimal_places=2)),
                ('percent', models.DecimalField(decimal_places=2, max_digits=4, blank=True, help_text='If percent is set, it will override the absolute amount. Can be negative.', null=True, verbose_name='Percent')),
                ('kind', models.CharField(default='standard', help_text='Select a modifier kind. If "Cart modifier" is selected, modifier will be constant and affect entire cart.', max_length=128, verbose_name='Kind', choices=[('standard', 'Standard'), ('discount', 'Discount'), ('cart_modifier', 'Cart modifier')])),
            ],
            options={
                'db_table': 'catalog_modifiers',
                'verbose_name': 'Modifier',
                'verbose_name_plural': 'Modifiers',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModifierCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.SlugField(help_text="Can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit.", unique=True, max_length=30, verbose_name='Code')),
                ('active', models.BooleanField(default=True, help_text='Is this object active? You can hide it by unchecking this box.', verbose_name='Active')),
                ('valid_from', models.DateTimeField(default=datetime.datetime.now, verbose_name='Valid from')),
                ('valid_until', models.DateTimeField(null=True, verbose_name='Valid until', blank=True)),
                ('modifier', models.ForeignKey(related_name='codes', verbose_name='Modifier', to='catalog.Modifier')),
            ],
            options={
                'db_table': 'catalog_modifier_codes',
                'verbose_name': 'Code',
                'verbose_name_plural': 'Codes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModifierCondition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path', models.CharField(max_length=255, verbose_name='Condition', choices=[('catalog.modifier_conditions.PriceGreaterThanModifierCondition', 'Price greater than'), ('catalog.modifier_conditions.PriceLessThanModifierCondition', 'Price less than'), ('catalog.modifier_conditions.QuantityGreaterThanModifierCondition', 'Quantity greater than'), ('catalog.modifier_conditions.QuantityLessThanModifierCondition', 'Quantity less than'), ('catalog.modifier_conditions.WidthGreaterThanModifierCondition', 'Width greater than (m)'), ('catalog.modifier_conditions.WidthLessThanModifierCondition', 'Width less than (m)'), ('catalog.modifier_conditions.HeightGreaterThanModifierCondition', 'Height greater than (m)'), ('catalog.modifier_conditions.HeightLessThanModifierCondition', 'Height less than (m)'), ('catalog.modifier_conditions.DepthGreaterThanModifierCondition', 'Depth greater than (m)'), ('catalog.modifier_conditions.DepthLessThanModifierCondition', 'Depth less than (m)'), ('catalog.modifier_conditions.WeightGreaterThanModifierCondition', 'Weight greater than (g)'), ('catalog.modifier_conditions.WeightLessThanModifierCondition', 'Weight less than (g)')])),
                ('arg', models.DecimalField(null=True, verbose_name='Argument', max_digits=10, decimal_places=3, blank=True)),
                ('modifier', models.ForeignKey(related_name='conditions', verbose_name='Modifier', to='catalog.Modifier')),
            ],
            options={
                'db_table': 'catalog_modifier_conditions',
                'verbose_name': 'Condition',
                'verbose_name_plural': 'Conditions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ModifierTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='catalog.Modifier', null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'catalog_modifiers_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Modifier Translation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=True, help_text='Is this object active? You can hide it by unchecking this box.', verbose_name='Active')),
                ('date_added', models.DateTimeField(auto_now_add=True, verbose_name='Date added')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('upc', catalog.fields.NullableCharField(null=True, max_length=64, blank=True, help_text='Universal Product Code (UPC) is an identifier for a product which is not specific to a particular supplier. Eg. an ISBN for a book.', unique=True, verbose_name='UPC')),
                ('unit_price', shop.util.fields.CurrencyField(default=Decimal('0.0'), help_text='If Product is a "variant" and price is "0", unit price is inherited from it\'s parent.', verbose_name='Unit price', max_digits=30, decimal_places=2)),
                ('is_discountable', models.BooleanField(default=True, help_text='This flag indicates if this product can be used in an offer or not.', verbose_name='Is discountable?')),
                ('discount_percent', models.DecimalField(decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))], max_digits=4, blank=True, help_text='If Product is a "variant" and discount percent is not set, discount percent is inherited from it\'s parent. If you dont wan\'t this to happen, set discount percent to "0".', null=True, verbose_name='Discount percent')),
                ('quantity', models.PositiveIntegerField(help_text='Number of products available, if product is unavailable (out of stock) set this to "0". If left empty, product will be treated as if it\'s always available.', null=True, verbose_name='Quantity', blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
            ],
            options={
                'db_table': 'catalog_products',
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductAttributeValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value_integer', models.IntegerField(null=True, verbose_name='Integer', blank=True)),
                ('value_boolean', models.NullBooleanField(verbose_name='Boolean')),
                ('value_float', models.FloatField(null=True, verbose_name='Float', blank=True)),
                ('value_date', models.DateField(null=True, verbose_name='Date', blank=True)),
                ('attribute', models.ForeignKey(related_name='values', verbose_name='Attribute', to='catalog.Attribute')),
                ('product', models.ForeignKey(related_name='attribute_values', verbose_name='Product', to='catalog.Product')),
                ('value_file', filer.fields.file.FilerFileField(related_name='value_files', verbose_name='File', blank=True, to='filer.File', null=True)),
                ('value_image', filer.fields.image.FilerImageField(related_name='value_images', verbose_name='Image', blank=True, to='filer.Image', null=True)),
                ('value_option', models.ForeignKey(verbose_name='Option', blank=True, to='catalog.AttributeOption', null=True)),
            ],
            options={
                'db_table': 'catalog_product_attribute_values',
                'verbose_name': 'Attribute',
                'verbose_name_plural': 'Attributes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductFlag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_true', models.BooleanField(default=True, verbose_name='Is True?')),
                ('flag', models.ForeignKey(verbose_name='Flag', to='catalog.Flag')),
                ('product', models.ForeignKey(related_name='flags', verbose_name='Product', to='catalog.Product')),
            ],
            options={
                'db_table': 'catalog_product_flags',
                'verbose_name': 'Flag',
                'verbose_name_plural': 'Flags',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductMeasurement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(default='width', max_length=20, verbose_name='Kind', choices=[('width', 'Width'), ('height', 'Height'), ('depth', 'Depth'), ('weight', 'Weight')])),
                ('value', models.DecimalField(verbose_name='Value', max_digits=10, decimal_places=3)),
                ('unit', models.CharField(default=b'm', max_length=20, verbose_name='Unit', choices=[('Pm', 'Petametre'), ('km', 'Kilometre'), (b'british_yd', b'British yard (sears 1922)'), ('Em', 'Exametre'), (b'm', b'Meter'), (b'indian_yd', b'Indian yard'), (b'mi', b'Mile'), (b'british_chain_sears', b'British chain (sears 1922)'), ('Tm', 'Terametre'), ('pm', 'Picometre'), (b'link_benoit', b'Link (benoit)'), (b'sears_yd', b'Yard (sears)'), ('mm', 'Millimetre'), (b'british_yd', b'British yard'), (b'inch', b'Inches'), ('dm', 'Decimetre'), (b'british_ft', b'British foot (sears 1922)'), ('ym', 'Yoctometre'), ('Ym', 'Yottametre'), (b'chain_benoit', b'Chain (benoit)'), (b'survey_ft', b'U.s. foot'), ('am', 'Attometre'), (b'chain_sears', b'Chain (sears)'), ('cm', 'Centimetre'), ('um', 'Micrometre'), ('dam', 'Decametre'), (b'german_m', b'German legal metre'), ('zm', 'Zeptometre'), (b'british_ft', b'British foot'), ('nm', 'Nanometre'), (b'nm_uk', b'Nautical mile (uk)'), (b'gold_coast_ft', b'Gold coast foot'), (b'ft', b'Foot'), (b'clarke_ft', b"Clarke's foot"), ('Mm', 'Megametre'), (b'british_chain_sears_truncated', b'British chain (sears 1922 truncated)'), (b'yd', b'Yard'), ('Zm', 'Zetametre'), ('Gm', 'Gigametre'), ('fm', 'Femtometre'), (b'm', b'Metre'), (b'link_sears', b'Link (sears)'), (b'indian_yd', b'Yard (indian)'), (b'survey_ft', b'Us survey foot'), ('hm', 'Hectometre'), (b'nm', b'Nautical mile'), (b'clarke_link', b"Clarke's link"), (b'ft', b'Foot (international)'), (b'british_chain_benoit', b'British chain (benoit 1895 b)'), (b'lb', b'Pound'), ('yg', 'Yoctogram'), ('mg', 'Milligram'), ('dg', 'Decigram'), ('Pg', 'Petagram'), ('ug', 'Microgram'), ('fg', 'Femtogram'), ('Yg', 'Yottagram'), ('zg', 'Zeptogram'), (b'tonne', b'Metric ton'), ('Mg', 'Megagram'), (b'short_ton', b'Ton'), (b'oz', b'Ounce'), ('dag', 'Decagram'), ('ng', 'Nanogram'), (b'ug', b'Mcg'), (b'long_ton', b'Long ton'), ('Gg', 'Gigagram'), ('pg', 'Picogram'), (b'short_ton', b'Short ton'), ('Eg', 'Exagram'), ('ag', 'Attogram'), ('hg', 'Hectogram'), ('kg', 'Kilogram'), ('Zg', 'Zetagram'), ('cg', 'Centigram'), (b'tonne', b'Metric tonne'), (b'g', b'Gram'), ('Tg', 'Teragram')])),
                ('product', models.ForeignKey(related_name='measurements', verbose_name='Product', to='catalog.Product')),
            ],
            options={
                'db_table': 'catalog_product_measurements',
                'verbose_name': 'Measurement',
                'verbose_name_plural': 'Measurements',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProductTranslation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('language_code', models.CharField(max_length=15, verbose_name='Language', db_index=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('slug', models.SlugField(help_text="Can only contain the letters a-z, A-Z, digits, minus and underscores, and can't start with a digit.", max_length=128, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
                ('master', models.ForeignKey(related_name='translations', editable=False, to='catalog.Product', null=True)),
            ],
            options={
                'managed': True,
                'db_table': 'catalog_products_translation',
                'db_tablespace': '',
                'default_permissions': (),
                'verbose_name': 'Product Translation',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RelatedProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', catalog.fields.UnderscoreField(default='upsell', max_length=255, verbose_name='Kind', choices=[('upsell', 'Upsell'), ('cross_sell', 'Cross sell')])),
                ('base_product', models.ForeignKey(related_name='related_products', verbose_name='Base product', to='catalog.Product')),
                ('product', models.ForeignKey(verbose_name='Product', to='catalog.Product')),
            ],
            options={
                'db_table': 'catalog_related_products',
                'verbose_name': 'Related Product',
                'verbose_name_plural': 'Related Products',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tax',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128, verbose_name='Name')),
                ('percent', models.DecimalField(help_text='Tax percentage.', verbose_name='Percent', max_digits=4, decimal_places=2, validators=[django.core.validators.MinValueValidator(Decimal('0.00'))])),
            ],
            options={
                'db_table': 'catalog_taxes',
                'verbose_name': 'Tax',
                'verbose_name_plural': 'Taxes',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='relatedproduct',
            unique_together=set([('base_product', 'product', 'kind')]),
        ),
        migrations.AlterUniqueTogether(
            name='producttranslation',
            unique_together=set([('language_code', 'master'), ('slug', 'language_code')]),
        ),
        migrations.AlterUniqueTogether(
            name='productmeasurement',
            unique_together=set([('product', 'kind')]),
        ),
        migrations.AlterUniqueTogether(
            name='productflag',
            unique_together=set([('product', 'flag')]),
        ),
        migrations.AlterUniqueTogether(
            name='productattributevalue',
            unique_together=set([('attribute', 'product')]),
        ),
        migrations.AddField(
            model_name='product',
            name='attributes',
            field=models.ManyToManyField(related_name='attributes', verbose_name='Attributes', through='catalog.ProductAttributeValue', to='catalog.Attribute'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='body',
            field=cms.models.fields.PlaceholderField(related_name='product_body_set', slotname='catalog_product_body', editable=False, to='cms.Placeholder', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='brand',
            field=mptt.fields.TreeForeignKey(related_name='products', verbose_name='Brand', blank=True, to='catalog.Brand', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=mptt.fields.TreeForeignKey(related_name='products', verbose_name='Category', blank=True, to='catalog.Category', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='featured_image',
            field=filer.fields.image.FilerImageField(related_name='featured_images', verbose_name='Featured image', blank=True, to='filer.Image', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='manufacturer',
            field=mptt.fields.TreeForeignKey(related_name='products', verbose_name='Manufacturer', blank=True, to='catalog.Manufacturer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='media',
            field=cms.models.fields.PlaceholderField(related_name='product_media_set', slotname='catalog_product_media', editable=False, to='cms.Placeholder', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='modifiers',
            field=models.ManyToManyField(to='catalog.Modifier', null=True, verbose_name='Modifiers', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='variants', blank=True, to='catalog.Product', help_text='If this is a "variant" of a Product, select that Product.', null=True, verbose_name='Parent'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='product',
            name='tax',
            field=models.ForeignKey(related_name='products', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='catalog.Tax', help_text='Tax to be applied to this product. If not set and product is a variant, tax will be inherited from parent.', null=True, verbose_name='Tax'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='modifiertranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='manufacturertranslation',
            unique_together=set([('language_code', 'master'), ('slug', 'language_code')]),
        ),
        migrations.AddField(
            model_name='manufacturer',
            name='modifiers',
            field=models.ManyToManyField(to='catalog.Modifier', null=True, verbose_name='Modifiers', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='manufacturer',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='children', blank=True, to='catalog.Manufacturer', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='flagtranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='categorytranslation',
            unique_together=set([('language_code', 'master'), ('slug', 'language_code')]),
        ),
        migrations.AddField(
            model_name='category',
            name='modifiers',
            field=models.ManyToManyField(to='catalog.Modifier', null=True, verbose_name='Modifiers', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='category',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='children', blank=True, to='catalog.Category', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='brandtranslation',
            unique_together=set([('language_code', 'master'), ('slug', 'language_code')]),
        ),
        migrations.AddField(
            model_name='brand',
            name='modifiers',
            field=models.ManyToManyField(to='catalog.Modifier', null=True, verbose_name='Modifiers', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='brand',
            name='parent',
            field=mptt.fields.TreeForeignKey(related_name='children', blank=True, to='catalog.Brand', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='attributetranslation',
            unique_together=set([('language_code', 'master')]),
        ),
        migrations.AlterUniqueTogether(
            name='attributeoptiontranslation',
            unique_together=set([('language_code', 'master')]),
        ),
    ]
