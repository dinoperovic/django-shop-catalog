django-shop-catalog
===================

Catalog app for django SHOP.

:Version: 0.0.1
:Source: https://github.com/dinoperovic/django-shop-catalog
:Dev Status: Alpha

Find starting templates in `django-shop-catalog-templates`_ repo.


Requirements
------------

.. code:: text

    django>=1.6,<1.8
    django-cms>=3.0.1
    django-shop>=0.2.0
    django-filer>=0.9.5
    django-mptt>=0.6.0
    django-hvad>=0.4.0
    measurement>=1.7.2
    django-currencies>=0.3.2


Installation
------------

Install with pip:

.. code:: bash

    pip install django-shop-catalog


Install from github using pip:

.. code:: bash

    pip install -e git://github.com/dinoperovic/django-shop-catalog.git@master#egg=django-shop-catalog


Getting Started
---------------

Setup `django-cms`_, `django-shop`_, `django-filer`_, `django-hvad`_ and `django-currencies`_.

Your ``INSTALLED_APPS`` should look something like this:

.. code:: python

    INSTALLED_APPS = [
        'djangocms_admin_style',
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.sites',
        'cms',
        'mptt',
        'menus',
        'south',
        'sekizai',
        'djangocms_text_ckeditor',
        'filer',
        'easy_thumbnails',
        'currencies',
        'hvad',
        'shop',
        'catalog',

        # Optional catalog apps.
        'catalog.orders',
        'catalog.addresses',
        'catalog.reviews',
    ]


Add to your ``settings.py``:

.. code:: python

    SHOP_PRODUCT_MODEL = 'catalog.models.Product'
    SHOP_CART_MODIFIERS = (
        'catalog.cart_modifiers.CatalogCartModifier',
    )

    # If you're using 'catalog.orders' app.
    SHOP_ORDER_MODEL = 'catalog.orders.models.Order'

    # If you're using 'catalog.addresses' app.
    SHOP_ADDRESS_MODEL = 'catalog.addresses.models.Address'


Add to your patterns in ``urls.py``:

.. code:: python

    urlpatterns = i18n_patterns('',
        url(r'^admin/', include(admin.site.urls)),
        url(r'^currencies/', include('currencies.urls')),

        # Include catalog shop_urls before django-shop urls.
        url(r'^shop/', include('catalog.shop_urls')),
        url(r'^shop/', include('shop.urls')),

        # You can include catalog urls here or use django-cms app hook.
        url(r'^catalog/', include('catalog.urls')),
        url(r'^', include('cms.urls')),
    )


Run:

.. code:: bash

    python manage.py syncdb --all
    python manage.py migrate --fake


Install `django-shop-catalog-templates`_ to get started quickly.


Notes
-----

If your're using ``catalog.addresses`` app, you can run this command
to have all countries and regions pulled from `geonames.org`_.

.. code:: bash

    python manage.py initcountries



.. _django-cms: https://github.com/divio/django-cms
.. _django-shop: https://github.com/divio/django-shop
.. _django-shop-catalog-templates: https://github.com/dinoperovic/django-shop-catalog-templates
.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django-hvad: https://github.com/kristianoellegaard/django-hvad
.. _django-currencies: https://github.com/panosl/django-currencies
.. _geonames.org http://geonames.org/
