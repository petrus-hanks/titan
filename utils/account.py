#!/usr/local/bin/python2.7
#coding:utf-8

import base64
import hashlib
import logging
from functools import wraps
from flask import g, url_for, redirect, request, render_template

from utils import code
from utils.mail import async_send_mail

logger = logging.getLogger(__name__)

def login_required(next=None, need=True, *args, **kwargs):
    def _login_required(f):
        @wraps(f)
        def _(*args, **kwargs):
            if (need and not g.current_user) or \
                    (not need and g.current_user):
                if next:
                    if next != 'account.login':
                        url = url_for(next)
                    else:
                        url = url_for(next, redirect=request.url)
                    return redirect(url)
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return _
    return _login_required

def send_forget_mail(user, stub):
    content = render_template('email.forget.html', user=user, stub=stub)
    async_send_mail(user.email, code.EMAIL_FORGET_TITLE, content)

def account_login(user):
    g.session['user_id'] = user.id
    g.session['user_token'] = user.token

def account_logout():
    g.session.clear()

def get_pubkey_finger(key):
    SIGN = 'AAAAB3NzaC1yc2EA'
    position = key.find(SIGN)
    if position == -1:
        return None
    key = base64.b64decode(key[position:].split(' ', 1)[0])
    fp_plain = hashlib.md5(key).hexdigest()
    return fp_plain

def get_fingerprint(finger):
    return ':'.join((a+b for a,b in zip(finger[::2], finger[1::2])))

