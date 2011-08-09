# coding=utf-8

import logging

from signals import *
from exceptions import *

from geouser.models_acc import UserTimelineSystem, UserTimeline


def new_list(sender, **kwargs):
    if isinstance(sender, ListAlert):
        timeline = UserTimelineSystem(user=sender.user.key(), msg_id=250, instance=sender)
    elif isinstance(sender, ListUser):
        timeline = UserTimelineSystem(user=sender.user.key(), msg_id=150, instance=sender)
    elif isinstance(sender, ListSuggestion):
        timelinePublic = UserTimeline(user = sender.user, instance = sender, msg_id=350, _vis=sender._get_visibility())
        timelinePublic.put()
        timeline = UserTimelineSystem(user=sender.user, msg_id=350, instance=sender)
    elif isinstance(sender, ListRequested):
        timelinePublic = UserTimeline(user = sender.user, instance = sender, msg_id=360, _vis=sender._get_visibility())
        timelinePublic.put()
        timeline = UserTimelineSystem(user=sender.user, msg_id=360, instance=sender)
    else:
        return
    timeline.put()
list_new.connect(new_list)


def modified_list(sender, **kwargs):
    """
    if isinstance(sender, ListAlert):
        timeline = UserTimelineSystem(user=sender.user.key(), msg_id=251, instance=sender)
    elif isinstance(sender, ListUser):
        timeline = UserTimelineSystem(user=sender.user.key(), msg_id=151, instance=sender)
    elif isinstance(sender, ListSuggestion):
        timelinePublic = UserTimeline(user = sender.user, instance = sender, msg_id=351, _vis=sender._get_visibility())
        timelinePublic.put()
        timeline = UserTimelineSystem(user=sender.user.key(), msg_id=351, instance=sender)
        from georemindme.tasks import NotificationHandler
        NotificationHandler().list_followers_notify(sender)
    else:
        return
    timeline.put()
    """
    if isinstance(sender, ListRequested):
        timeline = UserTimelineSystem(user=kwargs['querier'], msg=351, _vis=sender._get_visibility())
        from georemindme.tasks import NotificationHandler
        NotificationHandler().list_followers_notify(sender)
        timeline.put()
        if kwargs['querier'].key() != sender.user.key():
            from geouser.models_utils import _Notification
            notification = _Notification(owner=sender.user, timeline=timeline)
            notification.put()
list_modified.connect(modified_list)


def deleted_list(sender, **kwargs):
    from geouser.models_acc import UserTimelineBase
    query = UserTimelineBase.all().filter('instance =', sender.key())
    for q in query:
        q.delete()
list_deleted.connect(deleted_list)


def new_following_list(sender, **kwargs):
    sender.counters.set_followers(+1)
    timeline = UserTimelineSystem(user = kwargs['user'], instance = sender, msg_id=353, visible=False)
    timeline.put()
    if kwargs['user'].key() != sender.user.key():
        from geouser.models_utils import _Notification
        notification = _Notification(owner=sender.user, timeline=timeline)
        notification.put()
list_following_new.connect(new_following_list)


def deleted_following_list(sender, **kwargs):
    sender.counters.set_followers(-1)
    timeline = UserTimelineSystem(user = kwargs['user'], instance = sender, msg_id=354, visible=False)
    timeline.put()
list_following_deleted.connect(deleted_following_list)


from models import *