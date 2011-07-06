"""
This file is part of GeoRemindMe.

GeoRemindMe is free software: you can redistribute it and/or modify
it under the terms of the Affero General Public License (AGPL) as published 
by Affero, as published by the Free Software Foundation, either version 3 
of the License, or (at your option) any later version.

GeoRemindMe is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  

You should have received a copy of the GNU Affero General Public License
along with GeoRemindMe.  If not, see <http://www.gnu.org/licenses/>.

"""

from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template, redirect_to

import facebookApp.watchers
#~ from facebookApp import 

urlpatterns = patterns('facebookApp.views',
    url(r'^$', 'login_panel'),
    url(r'^(?i)dashboard/$', 'dashboard'),
    url(r'^(?i)profile/$', 'profile_settings'),
    url(r'^(?i)profile/edit/$', 'edit_profile'),
    url(r'^(?i)user/(?P<username>[^/]*)$', 'public_profile'),
    url(r'^(?i)user/(?P<username>[^/]*)/followers/$', 'followers_panel'),
    url(r'^(?i)user/(?P<username>[^/]*)/followings/$', 'followings_panel'),
    url(r'^(?i)suggestions/$', 'user_suggestions'),
    url(r'^(?i)suggestions/add/$', 'add_suggestion'),
)
