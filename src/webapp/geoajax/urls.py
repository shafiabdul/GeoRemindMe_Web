# coding=utf-8


from django.conf.urls.defaults import *

urlpatterns = patterns('geoajax.views',
    (r'^delete/reminder/$', 'delete_reminder'),
    (r'^delete/following/$', 'delete_following'),
    (r'^delete/suggestion/$', 'delete_suggestion'),
    (r'^add/following/$', 'add_following'),
    (r'^add/reminder/$', 'add_reminder'),
    (r'^add/following/$', 'add_following'),
    (r'^add/suggestion/$', 'add_suggestion'),
    (r'^get/reminder/$', 'get_reminder'),
    (r'^get/followers/$', 'get_followers'),
    (r'^get/followings/$', 'get_followings'),
    (r'^get/timeline/$', 'get_timeline'),
    (r'^get/chronology/$', 'get_chronology'),
    (r'^get/suggestion/$', 'get_suggestion'),
    (r'^vote/suggestion/$', 'do_vote_suggestion'),
    (r'^contacts/google/$', 'get_contacts_google'),
    (r'^contacts/facebook/$', 'get_friends_facebook'),
    (r'^contacts/twitter/$', 'get_friends_twitter'),
	(r'^login/$', 'login'),
	(r'^register/$', 'register'),
	(r'^exists/$', 'exists'),
	(r'^contact/$', 'contact'),
	(r'^keep-up-to-date/$', 'keepuptodate'),
    (r'^searchconfgoogle/$', 'mod_searchconfig_google')

)
