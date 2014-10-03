# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.views.generic import (
    ListView, DetailView, CreateView, DeleteView, UpdateView)

from catalog.models import Product
from catalog.reviews.models import Review
from catalog.utils.shortcuts import get_by_slug_or_404


class ProductMixin(object):
    product = None

    def dispatch(self, request, *args, **kwargs):
        self.product = get_by_slug_or_404(Product, kwargs.get('slug', None))
        return super(ProductMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Updates context to add a product object instance.
        """
        context = {'product': self.product}
        context.update(kwargs)
        return super(ProductMixin, self).get_context_data(**context)


class OwnerRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        """
        Raise permission error if object is not owned by user/session.
        """
        self.object = self.get_object()
        user = getattr(request, 'user', None)
        if (user and user == self.object.user or
                self.object.session_key == request.session.session_key):
            return super(OwnerRequiredMixin, self).dispatch(
                request, *args, **kwargs)
        raise PermissionDenied()


class ReviewListView(ProductMixin, ListView):
    model = Review
    template_name = 'shop/reviews/review_list.html'

    def get_queryset(self):
        qs = super(ReviewListView, self).get_queryset()
        return qs.filter(product=self.product)


class ReviewDetailView(ProductMixin, DetailView):
    model = Review
    template_name = 'shop/reviews/review_detail.html'


class ReviewCreateView(ProductMixin, CreateView):
    model = Review
    fields = ['body', 'rating']
    template_name = 'shop/reviews/review_create.html'

    def get(self, request, *args, **kwargs):
        """
        If review already written for this user/session redirect to
        update view for that review.
        """
        user = getattr(request, 'user', None)
        product = get_by_slug_or_404(Product, kwargs.get('slug', None))
        filters = {'product': product}

        if user and user.is_authenticated():
            filters['user'] = user
        else:
            filters['session_key'] = request.session.session_key

        if len(filters) > 1:
            try:
                review = Review.objects.get(**filters)
                return HttpResponseRedirect(reverse_lazy(
                    'catalog_review_update',
                    args=[product.get_slug(), review.pk]))
            except Review.DoesNotExist:
                pass

        return super(ReviewCreateView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        """
        Force product and user values into a form after it's validated
        and save review_id to session.
        """
        product = get_by_slug_or_404(Product, self.kwargs.get('slug', None))
        form.instance.product = product

        user = getattr(self.request, 'user', None)
        form.instance.user = user if user and user.is_authenticated() else None
        form.instance.session_key = self.request.session.session_key

        return super(ReviewCreateView, self).form_valid(form)


class ReviewUpdateView(OwnerRequiredMixin, ProductMixin, UpdateView):
    model = Review
    fields = ['body', 'rating']
    template_name = 'shop/reviews/review_update.html'


class ReviewDeleteView(OwnerRequiredMixin, ProductMixin, DeleteView):
    model = Review
    template_name = 'shop/reviews/review_delete.html'

    def get_success_url(self):
        return reverse_lazy(
            'catalog_review_list', args=[self.object.product.get_slug()])
