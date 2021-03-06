# coding=utf-8

from google.appengine.ext import db
from django.conf import settings

from georemindme import model_plus
from geouser.models import User
from georemindme.models_utils import Visibility
from geotags.models import Taggable
from georemindme.decorators import classproperty
from models_indexes import ListCounter
from signals import list_new, list_modified
try:
    import json as simplejson
except:
    from django.utils import simplejson


class List(db.polymodel.PolyModel, model_plus.Model):
    '''
        NO USAR ESTA LISTA, USAR LOS MODELOS ESPECIFICOS :D
    '''
    name = db.StringProperty(required=True)
    description = db.TextProperty()
    keys = db.ListProperty(db.Key)
    created = db.DateTimeProperty(auto_now_add = True)
    modified = db.DateTimeProperty(auto_now=True)
    active = db.BooleanProperty(default=True)
    _short_url = db.URLProperty(indexed=False)
    count = db.IntegerProperty(default=0)  # numero de sugerencias en la lista

    _counters = None
    _new = False

    @property
    def id(self):
        return int(self.key().id())
    
    @property
    def short_url(self):
        from os import environ
        if environ['HTTP_HOST'] == 'localhost:8080':
            return 'http://%s%s' % (environ['HTTP_HOST'], self.get_absolute_url())
        if self._short_url is None:
            self._get_short_url()
            if self._short_url is not None:
                self.put()
            else:
                from os import environ
                return 'http://%s%s' % (environ['HTTP_HOST'], self.get_absolute_url())
        return self._short_url

    @property
    def counters(self):
        if self._counters is None:
            self._counters = ListCounter.all().ancestor(self.key()).get()
            if self._counters is None:
                self._counters = ListCounter(parent=self)
                self._counters.put()
        return self._counters

    @classproperty
    def objects(self):
        return ListHelper()

    def _pre_put(self):
        self.count = len(self.keys)
        if not self.is_saved():
            self._get_short_url()
            self._new = True
            
    def put(self, from_comment=False):
        if self.is_saved():
            super(List, self).put()
            if from_comment:
                return self
            from watchers import modified_list, deleted_list
            if not self.active:
                list_deleted.send(sender=self)
            else:
                list_modified.send(sender=self)
        else:
            super(List, self).put()
            counter = ListCounter(parent=self)
            a = db.put_async(counter)
            from watchers import new_list
            list_new.send(sender=self)
            a.get_result()

    def delete(self):
        children = db.query_descendants(self).fetch(100)
        for c in children:
            c.delete()
        return db.delete_async(self)

    def to_dict(self, resolve=False, instances=None):
            dict = {'id': self.id,
                    'name': self.name,
                    'description': self.description,
                    'modified': self.modified if self.modified is not None else 0,
                    'created': self.created if self.created is not None else 0,
                    'tags': self.tags if hasattr(self, 'tags') else None,
                    'count': self.count,
                    'counters': self.counters.to_dict() if self.counters is not None else None,
                    'keys': [i.id() for i in self.keys],
                    'visibility': self._get_visibility(),
                    'get_absolute_url': self.get_absolute_url(),
                    'get_absolute_fburl': self.get_absolute_fburl(),
                    'short_url': self.short_url,
                    }
            if resolve:
                if instances is not None:
                    dict['instances'] = [instances[k] for k in self.keys]
                    dict['user'] = instances.get(ListSuggestion.user.get_value_for_datastore(self), self.user)
                else:
                    dict['instances'] = db.get(self.keys)
            else:
                dict['user'] = self.user.username
            return dict

    def to_json(self):
        from libs.jsonrpc.jsonencoder import JSONEncoder
        return simplejson.dumps(self.to_dict(), cls=JSONEncoder)

    def __str__(self):
        return unicode(self.name).encode('utf-8')

    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return '/list/%s/' % str(self.id)
    
    def get_absolute_fburl(self):
        return '/fb%s' % self.get_absolute_url()
    
    def _get_short_url(self):
        from libs.vavag import VavagRequest
        from os import environ
        try:
            # parche hasta conseguir que se cachee variable global
            client = VavagRequest(settings.SHORTENER_ACCESS['user'], settings.SHORTENER_ACCESS['key'])
            response =  client.set_pack('http://%s%s' % (environ['HTTP_HOST'], self.get_absolute_url()))
            self._short_url = response['packUrl']
        except Exception, e:
            import logging
            logging.error('ERROR EN VAVAG: %s' % e.message)
            self._short_url = None


class ListSuggestion(List, Visibility, Taggable):
    '''
    Lista agrupando sugerencias, que no tienen porque ser sugerencias
    creadas por el mismo usuario que crea la lista.
    Tiene control de visibilidad
    '''

    user = db.ReferenceProperty(User)

    @classproperty
    def objects(self):
        return ListSuggestionHelper()

    def _user_is_follower(self, user_key):
        '''
        Busca si un usuario ya sigue a una lista

            :param user_key: key del usuario a buscar
            :type user_key: :class:`db.Key`
            :returns: True si el usuario ya sigue la lista. False si no.
        '''
        if not self.is_saved():
            return db.NotSavedError()
        from models_indexes import ListFollowersIndex
        index = ListFollowersIndex.all().ancestor(self.key()).filter('keys =', user_key).get()
        if index is not None:
            return True
        return False

    def notify_followers(self):
        '''
        Crea un timelineSystem por cada usuario que sigue
        a esta lista
        '''
        from models_indexes import ListFollowersIndex
        if not self._is_private():
            if ListFollowersIndex.all().ancestor(self.key()).count() == 0:
                return True
            timelines = []
            for list in ListFollowersIndex.all().ancestor(self.key()):
                for key in list.users:
                    timelines.append(UserTimelineSystem(parent=key, user=key, msg_id=351, instance=self))
            db.put(timelines)
            return True

    @classmethod
    def insert_list(cls, user, id=None, name=None, description = None, instances=[], instances_del=[], tags = None, vis='public'):
        """
        Crea una nueva lista, en el caso de que exista una con ese nombre,
        se añaden las alertas

            :param user: usuario
            :type user: :class:`geouser.models.User`
            :param name: nombre de la lista
            :type name: :class:`string`
            :param description: descripcion de la lista
            :type description: :class:`string`
            :param instances: objetos a añadir a la lista
            :type instances: :class:`geoalert.models.Alert`
            :param vis: Visibilidad de la lista
            :type vis: :class:`string`
        """
        list = None
        if id is not None:
            list = cls.objects.get_by_id_user(id, user)
            if list is None:
                list = user.listsuggestion_set.filter('name =', name).get()
            if list is not None:  # la lista con ese nombre ya existe, la editamos
                list.update(name=name, 
                            description=description,
                            instances=instances, 
                            instances_del=instances_del,
                            tags=tags, 
                            vis=vis
                            )
                return list
            return False
        keys= set([db.Key.from_path('Event', int(instance)) for instance in instances])
        list = ListSuggestion(name=name, 
                              user=user, 
                              description=description, 
                              keys=[k for k in keys], 
                              _vis=vis if vis is not None else 'public'
                              )
        if tags is not None:
            list._tags_setter(tags, commit=False)
        list.put()
        followers = ListFollowersIndex(parent=list.key(), keys=[list.user.key()])
        followers.put()
        return list

    def update(self, name=None, description=None, instances=[], instances_del=[], tags=None, vis='public'):
        """
        Actualiza una lista de alertas

            :param user: usuario
            :type user: :class:`geouser.models.User`
            :param name: nombre de la lista
            :type name: :class:`string`
            :param description: descripcion de la lista
            :type description: :class:`string`
            :param instances: objetos a añadir a la lista
            :type instances: :class:`geoalert.models.Alert`
            :param vis: Visibilidad de la lista
            :type vis: :class:`string`
        """
        if name is not None or name == '':
            self.name = name
        if description is not None:
            self.description = description
        for deleted in instances_del:
            try:
                self.keys.remove(db.Key.from_path('Event', int(deleted)))
            except:
                pass
        keys = self.keys
        keys.extend([db.Key.from_path('Event', int(instance)) for instance in instances])
        keys = set(keys)
        self.keys = [k for k in keys]
        if vis is not None:
            self._vis = vis
        if tags is not None:
            self._tags_setter(tags, commit=False)
        self.put()

    def del_follower(self, user):
        """
        Borra un usuario de la lista

            :param user_key: key del usuario a buscar
            :type user_key: :class:`db.Key`
            :returns: True si se borro el usuario. False si hubo algun error o no existia
        """
        if self.__class.user.get_value_for_datastore(self) == user.key():
            return False
        def _tx(index_key, user_key):
            index = db.get(index_key)
            index.keys.remove(user_key)
            index.count -= 1
            index.put()
        user_key = user.key()
        if not self._user_is_follower(user_key):
            return False
        from models_indexes import ListFollowersIndex
        index = ListFollowersIndex.all().ancestor(self.key()).filter('keys =', user_key).get()
        db.run_in_transaction(_tx, index.key(), user_key)
        list_following_deleted.send(sender=self, user=db.get(user_key))
        return True

    def add_follower(self, user):
        """
        Añade un usuario a los seguidores de una lista

            :param user: Usuario que quiere apuntarse a una sugerencia
            :type user: :class:`geouser.models.User`

            :returns: True si se añadio, False en caso contrario
        """
        if self.__class__.user.get_value_for_datastore(self) == user.key():
            return False
        def _tx(list_key, user_key):
            # TODO : cambiar a contador con sharding
            from models_indexes import ListFollowersIndex
            if ListFollowersIndex.all().ancestor(list_key).filter('keys =', user_key).get() is not None:
                return False  # el usuario ya sigue la lista
            # indice con personas que siguen la sugerencia
            index = ListFollowersIndex.all().ancestor(list_key).filter('count <', 80).get()
            if index is None:
                index = ListFollowersIndex(parent=list_key)
            index.keys.append(user_key)
            index.count += 1
            index.put()
            return True
        if self._user_is_follower(user.key()):
            return True
        if self._is_private():
            return False
        elif self._is_shared():
            if self.user_invited(user) is None:
                return False
        tx = db.run_in_transaction(_tx, list_key = self.key(), user_key = user.key())
        if not tx:
            return True
        self.user_invited(user, set_status=1)  # FIXME : mejor manera de cambiar estado invitacion
        list_following_new.send(sender=self, user=user)
        return True

    def has_follower(self, user):
        if not user.is_authenticated():
            return False
        if ListFollowersIndex.all(keys_only=True).ancestor(self.key()).filter('keys =', user.key()).get() is not None:
            return True
        return False

    def delete(self):
        list_deleted.send(sender=self)
        super(ListSuggestion, self).delete()


class ListRequested(ListSuggestion):
    @classproperty
    def objects(self):
        return ListRequestedHelper()

    @classmethod
    def insert_list(cls, user, id=None, name=None, description = None, instances=[], instances_del=[], tags=None, vis='public'):
        """
        Crea una nueva lista, en el caso de que exista una con ese nombre,
        se añaden las alertas

            :param user: usuario
            :type user: :class:`geouser.models.User`
            :param name: nombre de la lista
            :type name: :class:`string`
            :param description: descripcion de la lista
            :type description: :class:`string`
            :param instances: objetos a añadir a la lista
            :type instances: :class:`geoalert.models.Alert`
            :param vis: Visibilidad de la lista
            :type vis: :class:`string`
        """
        from geoalert.models import Suggestion
        list = None
        if id is not None:
            list = cls.objects.get_by_id_user(id, user)
        if list is None:
            list = user.listsuggestion_set.filter('name =', name).get()
        if list is not None:  # la lista con ese nombre ya existe, la editamos
            if isinstance(list, ListRequested):
                list.update(name=name, 
                            description=description, 
                            instances=instances, 
                            instances_del=instances_del, 
                            tags=tags,
                            vis=vis 
                            )
                return list
        # TODO: debe haber una forma mejor de quitar repetidos, estamos atados a python2.5 :(, los Sets
        keys= set([db.Key.from_path('Event', int(instance)) for instance in instances])
        list = ListRequested(name=name, 
                             user=user, 
                             description=description, 
                             keys=[k for k in keys], 
                             _vis=vis if vis is not None else 'public'
                             )
        if tags is not None:
            list._tags_setter(tags, commit=False)    
        list.put()
        return list

    def update(self, querier, name=None, description=None, instances=[], instances_del=[], tags=None, vis='public'):
        '''
        Actualiza una lista de alertas

            :param user: usuario
            :type user: :class:`geouser.models.User`
            :param name: nombre de la lista
            :type name: :class:`string`
            :param description: descripcion de la lista
            :type description: :class:`string`
            :param instances: objetos a añadir a la lista
            :type instances: :class:`geoalert.models.Alert`
            :param vis: Visibilidad de la lista
            :type vis: :class:`string`
        '''
        from geoalert.models import Suggestion
        if querier.key() == self.user.key():
            if name is not None or name == '':
                self.name = name
            if description is not None:
                self.description = description
            for deleted in instances_del:
                try:
                    self.keys.remove(db.Key.from_path('Event', int(deleted)))
                except:
                    pass
        else:
            if self.is_shared():
                invitation = self.user_invited(querier)
                if invitation is None or not invitation.is_accepted():
                    from georemindme.exceptions import ForbiddenAccess
                    raise ForbiddenAccess
            elif self.is_private():
                from georemindme.exceptions import ForbiddenAccess
                raise ForbiddenAccess
        keys = self.keys
        keys.extend([db.Key.from_path('Event', int(instance)) for instance in instances])
        keys = set(keys)
        self.keys = [k for k in keys]
        if vis is not None:
            self._vis = vis
        if tags is not None:
            self._tags_setter(tags, commit=False)
        self.put(querier=querier)


class ListAlert(List):
    '''
    Lista agrupando alertas, las alertas nunca son visibles por otros
    usuarios
    '''
    user = db.ReferenceProperty(User)

    @classproperty
    def objects(self):
        return ListAlertHelper()

    @classmethod
    def insert_list(cls, user, name, description = None, instances=[]):
        """
        Crea una nueva lista, en el caso de que exista una con ese nombre,
        se añaden las alertas

            :param user: usuario
            :type user: :class:`geouser.models.User`
            :param name: nombre de la lista
            :type name: :class:`string`
            :param description: descripcion de la lista
            :type description: :class:`string`
            :param instances: objetos a añadir a la lista
            :type instances: :class:`geoalert.models.Alert`
        """
        from geoalert.models import Alert
        list = user.listalert_set.filter('name =', name).get()
        if list is not None:  # la lista con ese nombre ya existe, la editamos
            if description is not None:
                list.description = description
            keys = list.keys
            keys.extend([db.Key.from_path('Event', int(instance)) for instance in instances])
            keys = set(keys)
            list.keys = [k for k in keys]
            list.put()
            return list
        keys= set([db.Key.from_path('Event', int(instance)) for instance in instances])
        list = ListAlert(name=name, user=user, description=description, keys=[k for k in keys])
        list.put()
        return list

    def update(self, name=None, description=None, instances_add=[], instances_del=[]):
        '''
        Actualiza una lista de alertas

            :param user: usuario
            :type user: :class:`geouser.models.User`
            :param name: nombre de la lista
            :type name: :class:`string`
            :param description: descripcion de la lista
            :type description: :class:`string`
            :param instances: objetos a añadir a la lista
            :type instances: :class:`geoalert.models.Alert`
        '''
        if name is not None:
            self.name = name
        if description is not None:
                self.description = description
        for instance in instances_del:
            try:
                self.keys.remove(instance.key())
            except ValueError:
                pass
        keys = set(self.keys)
        keys |= set([instance.key() for instance in instances_add])
        self.keys = [k for k in keys]
        self.put()


class ListUser(List):
    '''
    Lista agrupando usuarios, para mejor gestion del usuario, no es publica
    '''
    user = db.ReferenceProperty(User)

    @classproperty
    def objects(self):
        return ListUserHelper()

    @classmethod
    def insert_list(cls, user, name, description=None, instances=[]):
        '''
        Crea una nueva lista de usuarios, en el caso de que exista una con ese nombre,
        se añaden los usuarios

            :param user: usuario
            :type user: :class:`geouser.models.User`
            :param name: nombre de la lista
            :type name: :class:`string`
            :param description: descripcion de la lista
            :type description: :class:`string`
            :param instances: objetos a añadir a la lista
            :type instances: :class:`geouser.models.User`
        '''
        list = user.listuser_set.filter('name =', name).get()
        if list is not None:
            if  description is not None:
                list.description = description
            keys = set(list.keys)
            keys |= set([instance.key() for instance in instances])
            list.keys = [k for k in keys]
            list.put()
            return list
        keys= set([instance.key() for instance in instances])
        list = ListUser(name=name, user=user, description=description, keys=[k for k in keys])
        list.put()
        return list

    def update(self, name=None, description=None, instances_add=[], instances_del=[]):
        '''
        Actualiza una lista de usuarios

            :param user: usuario
            :type user: :class:`geouser.models.User`
            :param name: nombre de la lista
            :type name: :class:`string`
            :param description: descripcion de la lista
            :type description: :class:`string`
            :param instances: objetos a añadir a la lista
            :type instances: :class:`geouser.models.User`
        '''
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        for instance in instances_del:
            try:
                self.keys.remove(instance.key())
            except ValueError:
                pass
        keys = set(self.keys)
        keys |= set([instance.key() for instance in instances_add])
        self.keys = [k for k in keys]
        self.put()

class _Deleted_List(db.Model):
    # TODO: crear deleted list
    pass


from watchers import *
from helpers import *
