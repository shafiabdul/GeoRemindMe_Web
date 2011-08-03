# coding=utf-8


from django.conf.urls.defaults import *

urlpatterns = patterns('geoajax.views',
    (r'^delete/reminder/$', 'delete_reminder'),
    (r'^delete/following/$', 'delete_following'),
    (r'^delete/suggestion/$', 'delete_suggestion'),
    (r'^delete/suggestion/follower/$', 'delete_suggestion_follower'),
    (r'^delete/suggestion/list/$', 'delete_list_suggestion'),
    (r'^delete/comment/$', 'delete_comment'),
    (r'^add/following/$', 'add_following'),
    (r'^add/reminder/$', 'add_reminder'),
    (r'^add/following/$', 'add_following'),
    (r'^add/suggestion/$', 'add_suggestion'),
    (r'^add/suggestion/invitation/$', 'add_suggestion_invitation'),
    (r'^add/suggestion/follower/$', 'add_suggestion_follower'),
    (r'^add/suggestion/list/$', 'add_list_suggestion',{},'add_suggestion_list'),
    (r'^add/comment/event/$', 'do_comment_event'),
    (r'^get/reminder/$', 'get_reminder'),
    (r'^get/followers/$', 'get_followers'),
    (r'^get/followings/$', 'get_followings'),
    (r'^get/friends/$', 'get_friends'),
    (r'^get/timeline/$', 'get_profile_timeline'),
    (r'^get/activity/$', 'get_activity_timeline',{},'get_activity_timeline'),
    (r'^get/notifications/$', 'get_notifications_timeline'),
    (r'^get/suggestion/$', 'get_suggestion'),
    (r'^get/suggestion/list/$', 'get_list_suggestion'),
    (r'^get/place/near$', 'get_place_near'),
    (r'^vote/suggestion/$', 'do_vote_suggestion'),
    (r'^vote/comment/$', 'do_vote_comment'),
    (r'^contacts/google/$', 'get_contacts_google'),
    (r'^contacts/facebook/$', 'get_friends_facebook'),
    (r'^contacts/twitter/$', 'get_friends_twitter'),
    (r'^contacts/block/$', 'block_contacts'),
	(r'^login/$', 'login'),
	(r'^register/$', 'register'),
	(r'^exists/$', 'exists'),
	(r'^contact/$', 'contact'),
	(r'^keep-up-to-date/$', 'keepuptodate'),
    (r'^searchconfgoogle/$', 'mod_searchconfig_google')

)
