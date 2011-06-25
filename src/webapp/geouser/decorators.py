# coding=utf-8

from django.http import HttpResponseRedirect

"""
.. module:: decorators
    :platform: appengine
    :synopsis: login_required decorator
    It is used to check if a user is logged in or not
"""

def login_required(func):
    def _wrapper(*args, **kwargs):
        request = args[0]  # request es el primer parametro que pasamos
        #raise Exception(session._session)
        if request.user.is_authenticated():
            return func(*args, **kwargs)
        from views import login
        return login(args[0])
    return _wrapper

def admin_required(func):
    def _wrapper(*args, **kwargs):
        session = args[0].session  # request es el primer parametro que pasamos
        user = session.get('user')
        if user and user.is_authenticated() and user.is_admin():
            return func(*args, **kwargs)
        from views import login
        return login(args[0])
    return _wrapper