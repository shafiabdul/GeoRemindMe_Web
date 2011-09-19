# coding=utf-8

"""
.. module:: helpers_acc
    :platform: appengine
    :synopsis: Helpers de los models_acc
"""


class UserSettingsHelper(object):
    def get_by_id(self, userid, async=False):
        try:
            userid = long(userid)
        except:
            return None
        import memcache
        settings = memcache.deserialize_instances(memcache.get('%ssettings_%s' % (memcache.version, userid)))
        if settings is None:
            from models_acc import UserSettings
            from models import User
            from google.appengine.ext import db
            key = db.Key.from_path(User.kind(), userid, UserSettings.kind(), 'settings_%s' % userid)
            settings = db.get(key)
            if settings is not None:
                memcache.set('%s%s' % (memcache.version, settings.key().name()), memcache.serialize_instances(settings), 300)
        return settings

    
class UserProfileHelper(object):
    def get_by_id(self, userid, async=False):
        try:
            userid = long(userid)
        except:
            return None
        import memcache
        profile = memcache.deserialize_instances(memcache.get('%sprofile_%s' % (memcache.version, userid)))
        if profile is None:
            from models_acc import UserProfile
            from models import User
            from google.appengine.ext import db
            key = db.Key.from_path(User.kind(), userid, UserProfile.kind(), 'profile_%s' % userid)
            profile = db.get(key)
            if profile is not None:
                memcache.set('%s%s' % (memcache.version, profile.key().name()), memcache.serialize_instances(profile), 300)
        return profile
        """
        if async:
            return db.get_async(key)
        return db.get(key)
        """

class UserCounterHelper(object):
    def get_by_id(self, userid, async=False):
        try:
            userid = long(userid)
        except:
            return None
        from models_acc import UserCounter
        from models import User
        from google.appengine.ext import db
        key = db.Key.from_path(User.kind(), userid, UserCounter.kind(), 'counters_%s' % userid)
        if async:
            return db.get_async(key)
        return db.get(key)


class UserTimelineHelper(object):
    def get_by_instance_user(self, instance, user):
        from models import User
        if not isinstance(user, User):
            raise TypeError
        from models_acc import UserTimelineBase
        return UserTimelineBase.all().filter('user =', user).filter('instance =', instance).run()

    def get_by_id(self, userid, query_id = None, querier=None):
        '''
        Obtiene la lista de ultimos timeline del usuario

            :param userid: id del usuario (user.id)
            :type userid: :class:`string`
            :param page: numero de pagina a mostrar
            :type param: int
            :param query_id: identificador de busqueda
            :type query_id: int
            :returns: lista de tuplas de la forma [query_id, [(id, username, avatar)]]
        '''
        try:
            userid = long(userid)
        except:
            return None
        from geovote.models import Vote, Comment
        from geoalert.models import Suggestion
        from geolist.models import List
        from models_acc import UserTimeline, UserTimelineSuggest
        from models import User
        from georemindme.paging import PagedQuery
        from google.appengine.ext import db
        query = UserTimeline.all().filter('user =', db.Key.from_path(User.kind(), userid)).order('-created')
        if query_id is not None:  # recuperamos los cursores anteriores
            query = query.with_cursor(start_cursor=query_id)
        timelines = query.fetch(10)
        query_id = query.cursor()
        from georemindme.funcs import prefetch_refprops
        timelines = prefetch_refprops(timelines, UserTimeline.user, UserTimeline.instance)
        instances = _load_ref_instances(timelines)
        if querier is None:
            from models_acc import UserTimelineSystem
            return [query_id, [{'id': timeline.id, 'created': timeline.created, 
                        'modified': timeline.modified,
                        'msg': timeline.msg, 'username':timeline.user.username, 
                        'msg_id': timeline.msg_id,
                        'instance': instances.get(UserTimeline.instance.get_value_for_datastore(timeline), timeline.instance),
                        'list': instances.get(UserTimelineSuggest.list.get_value_for_datastore(timeline), timeline.list) 
                                    if isinstance(timeline, UserTimelineSuggest) else None,
                        'has_voted':  Vote.objects.user_has_voted(db.Key.from_path(User.kind(), userid), timeline.instance.key()) if timeline.instance is not None else None,
                        'vote_counter': Vote.objects.get_vote_counter(timeline.instance.key()) if timeline.instance is not None else None,
                        'comments': Comment.objects.get_by_instance(timeline.instance),
                        'is_private': isinstance(timeline, UserTimelineSystem),
                        } 
                       for timeline in timelines]]
        elif querier.is_authenticated() and querier.are_friends(db.Key.from_path(User.kind(), userid)):
            return [query_id, [{'id': timeline.id, 'created': timeline.created, 
                        'modified': timeline.modified,
                        'msg': timeline.msg, 'username':timeline.user.username, 
                        'msg_id': timeline.msg_id,
                        'instance': instances.get(UserTimeline.instance.get_value_for_datastore(timeline), timeline.instance),
                        'list': instances.get(UserTimelineSuggest.list.get_value_for_datastore(timeline), timeline.list) 
                                    if isinstance(timeline, UserTimelineSuggest) else None,
                        'has_voted':  Vote.objects.user_has_voted(querier, timeline.instance.key()) if timeline.instance is not None else None,
                        'vote_counter': Vote.objects.get_vote_counter(timeline.instance.key()) if timeline.instance is not None else None,
                        'comments': Comment.objects.get_by_instance(timeline.instance, querier=querier),
                        'user_follower': timeline.instance.has_follower(querier) if isinstance(timeline.instance, Suggestion) and querier.is_authenticated() else None,
                        'is_private': False,
                        }
                        for timeline in timelines if timeline._is_shared() or timeline._is_public()]]
        return [query_id, [{'id': timeline.id, 'created': timeline.created, 
                        'modified': timeline.modified,
                        'msg': timeline.msg, 'username':timeline.user.username, 
                        'msg_id': timeline.msg_id,
                        'instance': instances.get(UserTimeline.instance.get_value_for_datastore(timeline), timeline.instance),
                        'list': instances.get(UserTimelineSuggest.list.get_value_for_datastore(timeline), timeline.list) 
                                    if isinstance(timeline, UserTimelineSuggest) else None,
                        'has_voted':  Vote.objects.user_has_voted(querier, timeline.instance.key()) if timeline.instance is not None and querier.is_authenticated()else None,
                        'vote_counter': Vote.objects.get_vote_counter(timeline.instance.key()) if timeline.instance is not None else None,
                        'comments': Comment.objects.get_by_instance(timeline.instance, querier=querier),
                        'user_follower': timeline.instance.has_follower(querier) if isinstance(timeline.instance, Suggestion) and querier.is_authenticated() else None,
                        'is_private': False,
                        }
                       for timeline in timelines if timeline._is_public()]]
        
def _load_ref_instances(timelines):
    """
    resuelve todas las referencias por lotes a las que estan apuntando el timeline
    
    Para luego construir el diccionario a devolver:
        'instance': instances.get(UserTimeline.instance.get_value_for_datastore(timeline), timeline.instance),
        'list': instances.get(UserTimelineSuggest.list.get_value_for_datastore(timeline), timeline.list) 
                    if isinstance(timeline, UserTimelineSuggest) else None,
    """
    from georemindme.funcs import prefetch_refprops
    from models import User
    from models_acc import UserTimelineSuggest, UserTimeline
    from geovote.models import Comment, Vote
    # cargo todas las referencias en instance
    instances = [t.instance for t in timelines if not isinstance(t.instance, User)]
    instances.extend(prefetch_refprops([t for t in timelines if isinstance(t, UserTimelineSuggest)], UserTimelineSuggest.list))
    instances.extend(prefetch_refprops([i for i in instances if isinstance(i, Comment) or isinstance(i, Vote)], 
                                       Comment.instance)
                     )
    instances.extend([i.instance for i in instances if isinstance(i, Comment) or isinstance(i, Vote)])
    instances.extend(prefetch_refprops(instances, UserTimeline.user, 
                                       ))
    instances = filter(None, instances)
    # devuelvo en un diccionario para luego crear el diccionario resultante
    instances = dict((i.key(), i) for i in instances)
    return instances