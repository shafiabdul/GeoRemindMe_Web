# coding=utf-8


from django.conf.urls.defaults import *

urlpatterns = patterns('geolist.views',
    (r'^(?i)list/(?P<id>[^/]*)/$', 'view_list', {}, 'view_list'),
)
