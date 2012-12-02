# -*- coding: utf-8 -*-
from __future__ import absolute_import

import re
import webapp2
import logging

from soaringcoupons import model
from soaringcoupons.template import write_template
from soaringcoupons import webtopay

class UnconfiguredHandler(webapp2.RequestHandler):
    def get(self):
        write_template(self.response, 'unconfigured.html')

class MainHandler(webapp2.RequestHandler):
    def get(self):
        values = {'coupon_types': model.list_coupon_types()}
        write_template(self.response, 'index.html', values)


ERR_MISSING = u'Laukas yra privalomas'
ERR_INVALID_EMAIL = u'Nekorektiškas el. pašto adresas'

EMAIL_RE = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

class OrderHandler(webapp2.RequestHandler):
    def get(self, name):
        ct = model.get_coupon_type(name)
        self.show_form(ct)

    def post(self, name):
        ct = model.get_coupon_type(name)
        #errors = self.validate()
        #if errors:
        #    self.show_form(ct, errors)
        #    return

        order_id = model.order_gen_id()
        order = model.order_create(order_id, ct, test=self.app.config['debug'])

        data = self.prepare_webtopay_request(order, ct)
        logging.info('Starting payment transaction for %s' % data)
        url = webtopay.get_redirect_to_payment_url(data)
        self.response.out.write('Order: %s' % order.order_id)
        return
        #webapp2.redirect(url, abort=True)

    def show_form(self, ct, errors={}):
        values = {'request': self.request.params,
                  'coupon_type': ct,
                  'errors': errors}
        write_template(self.response, 'order.html', values)

    def validate(self):
        """ Validate form input
        """
        errors = {}

        # Validate required fields
        for field in ['name', 'surname', 'email']:
            if not self.request.get(field):
                errors[field] = ERR_MISSING

        # validate email
        if 'email' not in errors:
            if not EMAIL_RE.match(self.request.get('email')):
                errors['email'] = ERR_INVALID_EMAIL
        return errors

    def prepare_webtopay_request(self, order, ct):
        data = {}
        data['projectid'] = self.app.config['webtopay_project_id']
        data['sign_password'] = self.app.config['webtopay_password']
        data['cancelurl'] = webapp2.uri_for('wtp_cancel', _full=True)
        data['accepturl'] = webapp2.uri_for('wtp_accept', _full=True)
        data['callbackurl'] = webapp2.uri_for('wtp_callback', _full=True)
        data['orderid'] = order.order_id
        data['lang'] = 'LIT'
        data['amount'] = order.price * 100
        data['currency'] = 'LTL'
        data['country'] = 'LT'
        data['paytext'] = (u'%s. Užsakymas nr. [order_nr] svetainėje [site_name]' \
                           % (ct.description))
        data['test'] = order.test

        return data

class OrderCancelHandler(webapp2.RequestHandler):
    def get(self):
        pass

class OrderCallbackHandler(webapp2.RequestHandler):
    def get(self):
        params = webtopay.validate_and_parse_data(self.request.params)

        paid_amount = int(params['payamount']) / 100
        model.order_process(params['orderid'], params['p_email'],
                            paid_amount, params['paycurrency'],
                            payer_name=params['name'],
                            payer_surname=params['surename'],
                            payment_provider=params['payment'])

        self.response.out.write('OK')

class OrderAcceptHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('Payment accepted')
