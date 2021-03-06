# coding=utf-8

"""
.. module:: models
    :platform: appengine
    :synopsis: Modelo de voto y comentario
"""


from django.utils.translation import gettext_lazy as _
from google.appengine.ext import db

from georemindme.models_utils import Visibility
from georemindme import model_plus
from geouser.models import User


class CommentHelper(object):
    """ Helper de la clase comentario """
    def get_by_id(self, id):
        try:
            id = long(id)
        except:
            return None
        comment = Comment.get_by_id(id)
        if comment is not None:
            if comment.deleted:
                return None
            if comment._is_public():
                return comment
        return None
        
    def get_by_key(self, key):
        """
        Obtiene el evento con ese key
        """
        return Comment.get(key)
    
    def get_by_user(self, user, query_id = None, page=1, querier=None):
        """
        Obtiene una lista con todos los comentarios hechos por un usuario
        
            :param user: usuario a buscar
            :type user: :class:`geouser.models.User`
            :param query_id: identificador de la busqueda paginada
            :type query_id: :class:`long`
            :param page: pagina a buscar
            :type page: :class:`integer`
            
            :returns: [query_id, [:class:`geovote.models.Comment`]]
        """
        if querier is not None and not isinstance(querier, User):
            raise TypeError
        from georemindme.paging import PagedQuery
        from google.appengine.api import datastore
        q = datastore.Query('Comment', {'user =': user.key(), 'deleted =': False})
        q.Order(('created', datastore.Query.DESCENDING))
        p = PagedQuery(q, id = query_id, page_size=7)
        comments = p.fetch_page(page)
        from georemindme.funcs import prefetch_refpropsEntity
        prefetch = prefetch_refpropsEntity(comments, 'user', 'instance')
        return [p.id, [
          {'id': comment.key().id(),
           'username': prefetch[comment['user']].username,
           'has_voted':  Vote.objects.user_has_voted(querier, comment.key()) if querier is not None else None,
           'vote_counter': comment['votes'],
           'instance': prefetch[comment['instance']],
           'msg': comment['msg'],
           'created': comment['created'],
           } for comment in comments]
                ]
    
    def get_by_instance(self, instance, query_id=None, page=1, querier = None, async=False):
        """
        Obtiene una lista con todos los comentarios hechos en una instancia
        
            :param instance: objeto al que buscar los comentarios
            :type instance: :class:`db.Model`
            :param query_id: identificador de la busqueda paginada
            :type query_id: :class:`long`
            :param page: pagina a buscar
            :type page: :class:`integer`
            
            :returns: [query_id, [:class:`geovote.models.Comment`]]
        """
        if querier is not None and not querier.is_authenticated():
            querier = None
        if querier is not None and not isinstance(querier, User):
            raise TypeError
        if instance is None:
            return None
        from georemindme.paging import PagedQuery
        from google.appengine.api import datastore
        q = datastore.Query(kind='Comment', filters={'instance =': instance.key(), 'deleted =': False})
        q.Order(('created', datastore.Query.DESCENDING))
        p = PagedQuery(q, id = query_id, page_size=7)
        if async:
            from google.appengine.datastore import datastore_query
            q = Comment.all().filter('instance =', instance).filter('deleted =', False).order('-created')
            return p.id, q.run(config=datastore_query.QueryOptions(limit=7))
        comments = p.fetch_page(page)
        from georemindme.funcs import prefetch_refpropsEntity
        prefetch = prefetch_refpropsEntity(comments, 'user', 'instance')
        return [p.id, [
                      {'id': comment.key().id(),
                       'username': prefetch[comment['user']].username,
                       'has_voted':  Vote.objects.user_has_voted(querier, comment.key()) if querier is not None else None,
                       'vote_counter': comment['votes'],
                       'instance': prefetch[comment['instance']],
                       'msg': comment['msg'],
                       'created': comment['created'],
                       } for comment in comments]
                ]
        
    def load_comments_from_async(self, query_id, comments_async, querier):
        if querier is None:
            raise TypeError
        comments_objects = []
        for comment in comments_async:
            comments_objects.append(comment)
        comments_objects = model_plus.prefetch(comments_objects, Comment.user)            
        return [query_id, [{'id': comment.id,
                                    'created': comment.created,
                                    'modified': comment.modified, 
                                    'msg': comment.msg,
                                    'username': comment.user.username,
                                    'has_voted':  Vote.objects.user_has_voted(querier, comment.key()) if querier is not None else None,
                                    'vote_counter': comment.votes,
                                    } for comment in comments_objects]
                ]
    
    def get_by_id_user(self, id, user):
        try:
            id = long(id)
        except:
            return None
        if not isinstance(user, User):
            raise AttributeError()
        comment = Comment.get_by_id(int(id))
        if comment is not None:
            if comment.deleted:
                return None
            if Comment.user.get_value_for_datastore(comment) == user.key():
                return comment
        return None      
    
    def get_by_id_querier(self, id, querier):
        try:
            id = long(id)
        except:
            return None
        if not isinstance(querier, User):
            raise AttributeError()
        comment = Comment.get_by_id(id)
        if comment is not None:
            if comment.deleted:
                return None
            if Comment.user.get_value_for_datastore(comment) == querier.key():
                return comment
            elif comment._is_public(): # comentario publico
                return comment
            elif Comment.instance.user.get_value_for_datastore(comment) == querier.key():
            # comentario en un objeto publico
                return comment
            elif comment.instance._is_public(): # la instancia es publica, sus comentarios son publicos
                return comment
            elif comment.instance._is_shared() and comment.instance.user_invited(querier): # instancia compartida, usuario invitado
                return comment
        return None     
    
    def get_top_voted(self, instance, querier):
        if querier is None:
            raise TypeError
        if instance is not None:
            import memcache
            top = None #memcache.get(memcache.get('%stopcomments_%s' % (memcache.version, instance.key())))
            if top is None:
                from google.appengine.api import datastore
                top = datastore.Query('Comment', {'instance =': instance.key(), 'votes >': 0})
                top.Order(('votes', datastore.Query.DESCENDING))
                top = top.Get(3)
                if len(top) > 0:
                    from georemindme.funcs import prefetch_refpropsEntity
                    prefetch = prefetch_refpropsEntity(top, 'user')
                    return [
                                   {'id': comment.key().id(),
                                    'username': prefetch[comment['user']].username,
                                    'has_voted':  Vote.objects.user_has_voted(querier, comment.key()) if querier is not None else None,
                                    'vote_counter': comment['votes'],
                                    'msg': comment['msg'],
                                    'created': comment['created'],
                                    } for comment in top
                            ]
                    memcache.set('%stopcomments_%s' % (memcache.version, instance.key()), top, 300)
        return top
        

class Comment(Visibility):
    """ Se puede comentar cualquier objeto del modelo """
    user = db.ReferenceProperty(User, collection_name='comments')
    instance = db.ReferenceProperty(None)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now = True)
    msg = db.TextProperty(required=True)
    deleted = db.BooleanProperty(default=False)
    votes = db.IntegerProperty(default=0)
    
    objects = CommentHelper()

    @property
    def id(self):
        return int(self.key().id())
    
    def set_votes(self, count):
        def _tx(count):
            obj = Comment.get(self.key())
            obj.votes += count
            if obj.votes < 0:
                obj.votes = 0
            obj.put()
            return obj.votes
        return db.run_in_transaction(_tx, count)
    
    @classmethod
    def do_comment(cls, user, instance, msg):
        
        if msg is None or msg == '':
            raise TypeError('msg is empty')
        comment = Comment(user=user, instance=instance, msg=msg, _vis=instance._vis if hasattr(instance, '_vis') else 'private')
        comment.put()
        if getattr(instance, 'counter', None) is not None:
            instance.counter.set_comments()
        from signals import comment_new
        comment_new.send(sender=comment)
        return comment
    
    def to_dict(self):
        return {'id': self.id if self.is_saved() else -1,
                'instance': self.instance.id,
                'created': self.created,
                'modified': self.modified,
                'msg': self.msg,
                'user': self.user,
                }
        
    def delete(self, force=False):
        from signals import comment_deleted
        if force:
            comment_deleted.send(self)
            super(Comment, self).deleted()
        else:
            self.deleted = True
            self.put()
            comment_deleted.send(self)
            
    def __str__(self):
        return unicode(self.msg).encode('utf-8')

    def __unicode__(self):
        return self.msg
            

from georemindme.models_utils import ShardedCounter
class VoteCounter(ShardedCounter):
    """
        Contador sharded
        instance es el key del objeto al que apunta
    """
    pass


class VoteHelper(object):
    """ Helper de la clase Vote """
    def user_has_voted(self, user, instance_key):
        """
        Comprueba que un usuario ya ha realizado un voto
        
            :param user: usuario que realiza el voto
            :type user: :class:`geouser.models.User`
            :param instance_key: key del objeto al que se vota
            :type instance_key: :class:`string`
            
            :returns: True si ya ha votado, False en caso contrario
        """
        if user is None:
            return None
        if isinstance(user, db.Key):
            vote = Vote.all(keys_only=True).filter('instance = ', instance_key).filter('user =', user).get()
        else:
            if not user.is_authenticated():
                return False
            vote = Vote.all(keys_only=True).filter('instance = ', instance_key).filter('user =', user).get()
        if vote is not None:
            return True
        return False
    
    def get_user_vote(self, user, instance_key):
        """
        Obtiene el voto de un usuario a un objeto determinado
        
            :param user: usuario a buscar
            :type user: :class:`geouser.models.User`
            :param instance_key: clave del objeto al que hay que buscar el voto
            :type instance_key: :class:`db.Key`
            
            :returns: :class:`geovote.models.Vote` o None
        """
        from google.appengine.api import datastore
        vote = datastore.Query('Vote', {'instance =': instance_key, 'user =': user.key()})
        vote = vote.Get(1)
        return vote[0] if any(vote) else None
    
    def get_vote_counter(self, instance_key):
        """
        Obtiene el contador de votos de objeto determinado
        
            :param instance_key: clave del objeto al que hay que buscar el voto
            :type instance_key: :class:`db.Key`
            
            :returns: :class:`integer`
        """
        return VoteCounter.get_count(instance_key)
        

class Vote(model_plus.Model):
    """ Se podria votar cualquier objeto """
    user = db.ReferenceProperty(User, collection_name='votes')
    instance = db.ReferenceProperty(None)
    created = db.DateTimeProperty(auto_now_add=True)
    count = db.IntegerProperty(default=0)
    
    objects = VoteHelper()
    
    @property
    def id(self):
        return int(self.key().id())
    
    @classmethod
    def do_vote(cls, user, instance, count=1):
        """
        Añade un voto de un usuario a una instancia
        
            :param user: usuario que realiza la votacion
            :type user: :class:`geouser.models.User`
            :param instance: objeto al que se vota
            :type instance: :class:`object`
            :param count: valoracion del voto
            :type count: :class:`integer`
            
            :returns: True si se realizo el voto, False si ya se habia votado
        """
        from signals import vote_new, vote_deleted
        count = int(count)
        vote = cls.objects.get_user_vote(user, instance.key())
        if vote is not None:
            if count < 0:
                vote = Vote.from_entity(vote)
                vote_deleted.send(sender=vote)
                vote.delete()
                return True
            return False
        vote = Vote(parent=instance, user=user, instance=instance, count=1)
        vote.put()
        vote_new.send(sender=vote)
        return True
    
    def to_dict(self):
        return {'id': self.id if self.is_saved() else -1,
                'instance': self.instance.id,
                'created': self.created,
                'user': self.user,
                'count': self.count,
                }
    
    def put(self):
        if not self.is_saved():
            if hasattr(self.instance, 'set_votes'):
                self.instance.set_votes(self.count)
            else:
                contador = VoteCounter.increase_counter(self.instance.key(), self.count)
        super(Vote, self).put()
        
    def delete(self):
        if hasattr(self.instance, 'set_votes'):
                self.instance.set_votes(-1)
        else:
            VoteCounter.increase_counter(self.instance.key(), -1)
        vote_deleted.send(self)
        super(Vote, self).delete()


from watchers import *
