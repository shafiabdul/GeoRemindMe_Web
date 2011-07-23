# coding=utf-8

from google.appengine.ext import db
from django.utils.translation import ugettext as _


class _Do_later_ft(db.Model):
    instance_key = db.ReferenceProperty(None)
    created = db.DateTimeProperty(auto_now_add=True)
    last_try = db.DateTimeProperty(auto_now=True)
    
    @classmethod
    def try_again(cls):
        """
            Reintenta añadir a fusion tables los objetos 
            que fallaron, deben implementar el metodo insert_ft()
        """
        queries = cls.all()
        
        for q in queries:
            try:
                instance = db.get(q.instance_key)
                instance.insert_ft()
                q.delete()
            except:
                q.put()

SHARDS = 5
class ShardedCounter(db.Model):
    '''
        Contador sharded
        instance es el key del objeto al que apunta
    '''
    instance = db.TextProperty(required=True)
    count = db.IntegerProperty(required=True, default=0)
    
    @classmethod
    def get_count(cls, instance):
        '''
            Returns the value of the counter, is counters is not in memcache, 
            counts all the sharded counters
        ''' 
        from google.appengine.api import memcache
        instance=str(instance)
        total = memcache.get(instance)
        if not total:
            total = 0
            counters = cls.gql('WHERE instance = :1', instance)
            for counter in counters:
                total += counter.count
            memcache.add(instance, str(total), 60)
        return int(total)
    
    @classmethod
    def increase_counter(cls, instance, count):
        '''
            Increment the counter of given key
        '''
        from google.appengine.api import memcache
        instance=str(instance)
        def increase():
            import random
            index = random.randint(0, SHARDS-1)#select a random shard to increases
            shard_key = instance + str(index)#creates key_name
            counter = cls.get_by_key_name(shard_key)
            if not counter:#if counter doesn't exist, create a new one
                counter = cls(key_name=shard_key, instance=instance)
            counter.count += count
            counter.put()
        db.run_in_transaction(increase)
        if count > 0:
            memcache.incr(instance, initial_value=0)
        else:
            memcache.decr(instance, initial_value=0)
    
VISIBILITY_CHOICES = (
          ('public', _('Public')),
          ('private', _('Private')),
          ('shared', _('Shared')),
                      )

class Visibility(db.Model):
    """Metodos comunes heredados por todas las Clases que necesiten visibilidad"""
    _vis = db.StringProperty(required = True, choices = ('public', 'private', 'shared'), default = 'public')
    
    def _get_visibility(self):
        return self._vis
    
    def _is_public(self):
        if self._vis == 'public':
            return True
        return False
    
    def _is_private(self):
        if self._vis == 'private':
            return True
        return False
    
    def _is_shared(self):
        if self._vis == 'shared':
            return True
        return False

#  from http://blog.notdot.net/2010/04/Pre--and-post--put-hooks-for-Datastore-models

class HookedModel(db.Model):
    def _pre_put(self):
        pass
    
    def put(self, **kwargs):
        self.put_async().get_result()
        return self._post_put_sync()
        
    def _post_put(self):
        pass
    
    def _post_put_sync(self):
        pass
    
    def _pre_delete(self):
        pass
    
    def delete(self):
        return self.delete_async().get_result()
    
    def _post_delete(self):
        pass
    
    def put_async(self,**kwargs):
        return db.put_async(self)
    
    def delete_async(self):
        return db.delete_async(self)

old_async_put = db.put_async
def hokked_put_async(models, **kwargs):
    if type(models) != type(list()):
        models = [models]
    for model in models:
        if isinstance(model, HookedModel):
            model._pre_put()
    async = old_async_put(models, **kwargs)
    get_result = async.get_result
    def get_result_with_callback():
        for model in models:
            if isinstance(model, HookedModel):
                model._post_put()
        return get_result()
    async.get_result = get_result_with_callback
    return async
db.put_async = hokked_put_async

old_async_delete = db.delete_async
def hokked_delete_async(models):
    if type(models) != type(list()):
        models = [models]
    for model in models:
        if isinstance(model, HookedModel):
            model._pre_delete()
    async = old_async_delete(models)
    get_result = async.get_result
    def get_result_with_callback():
        for model in models:
            if isinstance(model, HookedModel):
                model._post_delete()
        return get_result()
    async.get_result = get_result_with_callback
    return async
db.delete_async = hokked_delete_async