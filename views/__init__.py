#!/usr/bin/python
# encoding: UTF-8

from views.account import account
from views.organization import organization

def init_views(app):
    app.register_blueprint(account, url_prefix='/account')
    app.register_blueprint(organization, url_prefix='/organization')
