# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import loader, Context, TemplateDoesNotExist
from django.utils.translation import activate, get_language


class Notification(object):
    """
    Notification base class.
    """
    order = None
    request = None
    subject_template_name = None
    text_body_template_name = None
    html_body_template_name = None

    def __init__(self, order, **kwargs):
        self.order = order
        self.request = kwargs.get('request', None)

    def get_from_email(self):
        return getattr(
            settings, 'CATALOG_ORDERS_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)

    def get_recipients(self):
        return []

    def get_subject(self):
        subject = loader.render_to_string(
            self.subject_template_name, Context({'order': self.order}))
        return subject.join(subject.splitlines())

    def get_text_body(self):
        return loader.render_to_string(
            self.text_body_template_name, Context({'order': self.order}))

    def get_html_body(self):
        try:
            return loader.render_to_string(
                self.html_body_template_name, Context({'order': self.order}))
        except TemplateDoesNotExist:
            return None

    def get_message(self):
        recipients = self.get_recipients()
        if recipients:
            message = EmailMultiAlternatives(
                self.get_subject(), self.get_text_body(),
                self.get_from_email(), recipients)

            # Try to attach alternative html content.
            html_body = self.get_html_body()
            if html_body:
                message.attach_alternative(html_body, 'text/html')
            return message

    def send(self):
        message = self.get_message()
        if message:
            activate(self.order.language_code)
            message.send()
            activate(get_language())


class ClientNotification(Notification):
    subject_template_name = 'shop/notifications/client_subject.txt'
    text_body_template_name = 'shop/notifications/client_body.txt'
    html_body_template_name = 'shop/notifications/client_body.html'

    def get_recipients(self):
        emails = []
        if self.order.user and self.order.user.email:
            emails.append(self.order.user.email)
        if self.order.billing_email:
            emails.append(self.order.billing_email)
        if self.order.shipping_email:
            emails.append(self.order.shipping_email)
        return list(set(emails))


class OwnersNotification(Notification):
    subject_template_name = 'shop/notifications/owner_subject.txt'
    text_body_template_name = 'shop/notifications/owner_body.txt'
    html_body_template_name = 'shop/notifications/owner_body.html'

    def get_recipients(self):
        owners = getattr(settings, 'CATALOG_ORDERS_OWNERS', settings.MANAGERS)
        return [x[1] for x in owners]
