#!/usr/local/bin/python2.7
#coding:utf-8

import logging

from flask import url_for, request, redirect, \
        g, abort

from utils import code
from utils.jagare import get_jagare
from utils.token import create_token
from utils.helper import MethodView, Obj
from utils.account import login_required
from utils.organization import member_required
from utils.gists import gist_require, get_url, render_tree

from query.gists import create_gist, update_gist, delete_gist

logger = logging.getLogger(__name__)

class Create(MethodView):
    decorators = [member_required(admin=False), login_required('account.login')]
    def get(self, organization, member):
        return self.render_template(
                    organization=organization, \
                    member=member, \
                )

    def post(self, organization, member):
        summary = request.form.get('summary')
        filenames = request.form.getlist('filename')
        codes = request.form.getlist('code')
        private = create_token(20) if request.form.get('private') else None
        data = {}
        if len(filenames) != len(codes):
            raise abort(400)
        for filename, content in zip(filenames, codes):
            if not filename and not content:
                continue
            if not filename or not content:
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_WITHOUT_FILENAME if not filename else code.GIST_WITHOUT_CONTENT, \
                            filenames=filenames, \
                            codes=codes, \
                        )
            if data.get(filename):
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_FILENAME_EXISTS, \
                            filenames=filenames, \
                            codes=codes, \
                        )
            data[filename] = content
        gist, err = create_gist(organization, g.current_user, summary, data=data, private=private, watchers=1)
        if err:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.GIST_CREATE_FAILED, \
                        filenames=filenames, \
                        codes=codes, \
                    )
        return redirect(get_url(organization, gist))

class Delete(MethodView):
    decorators = [gist_require(owner=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist):
        delete_gist(g.current_user, gist, organization)
        return redirect(url_for('organization.view', git=organization.git))

class Edit(MethodView):
    decorators = [gist_require(owner=True), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist):
        jagare = get_jagare(gist.id, gist.parent)
        error, tree = jagare.ls_tree(gist.get_real_path())
        if not error:
            tree, meta = tree['content'], tree['meta']
            tree = render_tree(jagare, tree, gist, organization, False)
        return self.render_template(
                    organization=organization, \
                    member=member, \
                    error=error, \
                    tree=tree, \
                    gist=gist, \
                )

    def post(self, organization, member, gist):
        summary = request.form.get('summary')
        filenames = request.form.getlist('filename')
        codes = request.form.getlist('code')
        data = {}
        if len(filenames) != len(codes):
            raise abort(400)
        for filename, content in zip(filenames, codes):
            if not filename and not content:
                continue
            if not filename or not content:
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_WITHOUT_FILENAME if not filename else code.GIST_WITHOUT_CONTENT, \
                            tree=self.gen_tree(filenames, codes), \
                            gist=gist,
                        )
            if data.get(filename):
                return self.render_template(
                            organization=organization, \
                            member=member, \
                            error=code.GIST_FILENAME_EXISTS, \
                            tree=self.gen_tree(filenames, codes), \
                            gist=gist,
                        )
            data[filename] = content
        jagare = get_jagare(gist.id, gist.parent)
        error, tree = jagare.ls_tree(gist.get_real_path())
        if error:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.REPOS_LS_TREE_FAILED, \
                        tree=self.gen_tree(filenames, codes), \
                        gist=gist,
                    )
        data = self.diff(tree, data)
        _, error = update_gist(g.current_user, gist, data, summary)
        if error:
            return self.render_template(
                        organization=organization, \
                        member=member, \
                        error=code.GIST_UPDATE_FAILED, \
                        tree=self.gen_tree(filenames, codes), \
                        gist=gist,
                    )
        return redirect(gist.meta.view)

    def diff(self, tree, data):
        tree, meta = tree['content'], tree['meta']
        for d in tree:
            name = d['name']
            if data.get(name, None) is None:
                # set delete flag
                data[d['path']] = ''
                continue
        return data

    def gen_tree(self, filenames, codes):
        for filename, content in zip(filenames, codes):
            d = Obj()
            d.name = filename
            d.content = lambda: content
            yield d

class Fork(MethodView):
    decorators = [gist_require(), member_required(admin=False), login_required('account.login')]
    def get(self, organization, member, gist):
        private = create_token(20) if gist.private else None
        fork_gist, err = create_gist(organization, g.current_user, gist.summary, parent=gist, private=private, watchers=1)
        if err:
            return redirect(gist.meta.view)
        return redirect(get_url(organization, fork_gist))

