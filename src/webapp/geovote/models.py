# coding=utf-8

from google.appengine.ext import db

from georemindme.paging import *
from georemindme.models_utils import Visibility
from geouser.models import User
from watchers import *

class CommentHelper(object):
    
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
        q = Comment.all().filter('user =', user).filter('deleted =', False).order('-created')
        p = PagedQuery(q, id = query_id, page_size=7)
        comments = p.fetch_page(page)
        return [p.id,  [{'id': comment.id,
                        'created': comment.created,
                        'modified': comment.modified, 
                        'msg': comment.msg,
                        'username': comment.user.username,
                        'instance': comment.instance if comment.instance is not None else None,
                        'has_voted':  Vote.objects.user_has_voted(querier, comment.key()) if querier is not None else None,
                        'vote_counter': Vote.objects.get_vote_counter(comment.key()),
                        }
                       for comment in comments]]
    
    def get_by_instance(self, instance, query_id=None, page=1, querier = None):
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
        if querier is not None and not isinstance(querier, User):
            raise TypeError
        q = Comment.all().filter('instance =', instance).filter('deleted =', False).order('-created')
        p = PagedQuery(q, id = query_id, page_size=7)
        comments = p.fetch_page(page)
        return [p.id, [{'id': comment.id,
                        'created': comment.created,
                        'modified': comment.modified, 
                        'msg': comment.msg,
                        'username': comment.user.username,
                        'instance': comment.instance if comment.instance is not None else None,
                        'has_voted':  Vote.objects.user_has_voted(querier, comment.key()) if querier is not None else None,
                        'vote_counter': Vote.objects.get_vote_counter(comment.key()),
                        }
                       for comment in comments]]
    
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
            if comment.user.key() == user.key():
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
            if comment.user.key() == querier.key():
                return comment
            elif comment._is_public(): # comentario publico
                return comment
            elif comment.instance.user.key() == querier.key(): # comentario en un objeto publico
                return comment
            elif comment.instance._is_public(): # la instancia es publica, sus comentarios son publicos
                return comment
            elif comment.instance._is_shared() and comment.instance.user_invited(querier): # instancia compartida, usuario invitado
                return comment
        return None     
        

class Comment(Visibility):
    '''
    Se puede comentar cualquier objeto del modelo
    '''
    user = db.ReferenceProperty(User, collection_name='comments')
    instance = db.ReferenceProperty(None)
    created = db.DateTimeProperty(auto_now_add=True)
    modified = db.DateTimeProperty(auto_now = True)
    msg = db.TextProperty(required=True)
    deleted = db.BooleanProperty(default=False)
    
    objects = CommentHelper()
    """
    @classproperty
    def objects(self):
        return CommentHelper()
    """
    @property
    def id(self):
        return self.key().id()
    
    @classmethod
    def do_comment(cls, user, instance, msg):
        
        if msg is None or msg == '':
            raise TypeError('msg is empty')
        comment = Comment(user=user, instance=instance, msg=msg)
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
                'msg': self.msg
                }
        
    
from georemindme.models_utils import ShardedCounter
class VoteCounter(ShardedCounter):
    '''
        Contador sharded
        instance es el key del objeto al que apunta
    '''
    pass

class VoteHelper(object):
    def user_has_voted(self, user, instance_key):
        '''
        Comprueba que un usuario ya ha realizado un voto
        
            :param user: usuario que realiza el voto
            :type user: :class:`geouser.models.User`
            :param instance_key: key del objeto al que se vota
            :type instance_key: :class:`string`
            
            :returns: True si ya ha votado, False en caso contrario
        '''
        vote = db.GqlQuery('SELECT __key__ FROM Vote WHERE instance = :ins AND user = :user', ins=instance_key, user=user.key()).get()
        if vote is not None:
            return True
        return False
    
    def get_user_vote(self, user, instance_key):
        '''
        Obtiene el voto de un usuario a un objeto determinado
        
            :param user: usuario a buscar
            :type user: :class:`geouser.models.User`
            :param instance_key: clave del objeto al que hay que buscar el voto
            :type instance_key: :class:`db.Key`
            
            :returns: :class:`geovote.models.Vote` o None
        '''
        vote = Vote.all().filter('instance =', instance_key).filter('user =', user).get()
        return vote
    
    def get_vote_counter(self, instance_key):
        '''
        Obtiene el contador de votos de objeto determinado
        
            :param instance_key: clave del objeto al que hay que buscar el voto
            :type instance_key: :class:`db.Key`
            
            :returns: :class:`integer`
        '''
        return VoteCounter.get_count(instance_key)
        
    

class Vote(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='votes')
    instance = db.ReferenceProperty(None)
    created = db.DateTimeProperty(auto_now_add=True)
    count = db.IntegerProperty(default=0)
    
    objects = VoteHelper()
    
    @classmethod
    def do_vote(cls, user, instance, count=1):
        '''
        Añade un voto de un usuario a una instancia
        
            :param user: usuario que realiza la votacion
            :type user: :class:`geouser.models.User`
            :param instance: objeto al que se vota
            :type instance: :class:`object`
            :param count: valoracion del voto
            :type count: :class:`integer`
            
            :returns: True si se realizo el voto, False si ya se habia votado
        '''
        from signals import vote_new, vote_deleted
        count = int(count)
        vote = cls.objects.get_user_vote(user, instance.key())
        if vote is not None:
            if count < 0:
                VoteCounter.increase_counter(vote.instance.key(), -1)
                vote_deleted.send(sender=vote)
                vote.delete()
                return True
            return False
        vote = Vote(user=user, instance=instance, count=1)
        vote.put()
        vote_new.send(sender=vote)
        return True
    
    def put(self):
        if not self.is_saved():
            contador = VoteCounter.increase_counter(self.instance.key(), self.count)
        super(Vote, self).put()
        
    
