# coding=utf-8

from geouser.models import User
from models import *
from models_indexes import ListFollowersIndex

class ListHelper(object):
    _klass = List

    def get_all_public(self, query_id=None, page=1):
        '''
        Devuelve todas las listas publicas ¡PAGINADA!

            :param page: numero de pagina a mostrar
            :type param: int
            :param query_id: identificador de busqueda
            :type query_id: int
        '''
        q = self._klass.all().filter('_vis =', 'public').filter('active =', True).order('-modified')
        from georemindme.paging import PagedQuery
        p = PagedQuery(q, id = query_id)
        from georemindme.funcs import prefetch_refprops
        lists = prefetch_refprops(p.fetch_page(page), self._klass.user)
        return [p.id, lists]

    def get_by_id(self, id):
        '''
        Devuelve la lista publica con ese ID

            :param id: identificador de la lista
            :type id: :class:`Integer`
            :returns: None o :class:`geolist.models.List`
        '''
        try:
            id = int(id)
        except:
            raise TypeError
        list = self._klass.get_by_id(id)
        return list

    def get_by_name_user(self, name, user):
        list = self._klass.all().filter('user =', user).filter('name =', name).filter('active =', True).get()
        return list

    def get_by_id_querier(self, id, querier):
        '''
        Devuelve la lista publica con ese ID

            :param id: identificador de la lista
            :type id: :class:`Integer`
            :returns: None o :class:`geolist.models.List`
        '''
        if not isinstance(querier, User):
            raise TypeError()
        list = self.get_by_id(id)
        if list is None:
            return None
        if list.user.key() == querier.key():
            return list
        if hasattr(list, '_vis'):
            if list._is_public():
                return list
            elif list._is_shared() and list.user_invited(querier):
                return list
        return None

    def get_by_id_user(self, id, user):
        '''
        Devuelve la lista con ese ID y el usuario como dueño.

            :param id: identificador de la lista
            :type id: :class:`Integer`
            :param user: usuario
            :type user: :class:`geouser.models.User`
            :returns: None o :class:`geolist.models.List`
        '''
        list = self.get_by_id(id)
        if list is not None:
            if not list.active:
                return None
            if list.user.key() == user.key():
                return list
        return None

    def get_list_user_following(self, user, resolve=False, async=False):
        '''
        Devuelve las listas a las que sigue el usuario

            :param user: usuario del que buscar las listas
            :type user: :class:`geouser.models.User`
        '''
        from google.appengine.api import datastore
        q = datastore.Query('ListFollowersIndex', {'keys =': user.key()}, keys_only=True)
        if async:
            indexes = db.GqlQuery('SELECT __key__ FROM ListFollowersIndex WHERE keys = :1', user.key())
            return indexes.run()
        c = indexes.Count()
        indexes = q.Get(c)
        from georemindme.funcs import fetch_parentsKeys
        lists = fetch_parentsKeys(indexes)
        return [list.to_dict(resolve=resolve) for list in lists if list.active]
    
    def load_list_user_following_by_async(self, lists_async, resolve=False):
        from georemindme.funcs import fetch_parentsKeys
        lists = fetch_parentsKeys(lists_async)
        return filter(lambda x: x.active, lists)
        # return [list.to_dict(resolve=resolve) for list in lists if list.active]

    def get_shared_list(self, user):
        '''
        Devuelve las listas que el usuario tiene invitacion

            :param user: usuario del que buscar las listas
            :type user: :class:`geouser.models.User`
        '''
        lists = [inv.list for inv in user.toinvitations_set if inv.status == 1]
        return lists

    def get_by_user(self, user, querier, page = 1, query_id = None, all=False):
        """
        Obtiene las listas de un usuario
        """
        if not isinstance(user, User) or not isinstance(querier, User):
            raise TypeError()
        if user.id == querier.id:
            q = self._klass.gql('WHERE user = :1 AND active = True ORDER BY modified DESC', user)
        else:
            q = self._klass.gql('WHERE user = :1  AND active = True AND _vis = :2 ORDER BY modified DESC', user, 'public')
        if not all:
            from georemindme.paging import PagedQuery
            p = PagedQuery(q, id = query_id)
            from georemindme.funcs import prefetch_refprops
            lists = prefetch_refprops(p.fetch_page(page), self._klass.user)
            return [p.id, lists]
        else:
            return q.run()
        
    def get_by_tag_querier(self, tagInstance, querier, page=1, query_id=None):
        from georemindme.paging import PagedQuery
        if not isinstance(querier, User):
            raise TypeError()
        from geotags.models import Tag
        if not isinstance(tagInstance, Tag):
            raise TypeError
        lists = self._klass.all().filter('_tags_list =', tagInstance.key())
        p = PagedQuery(lists, id = query_id)
        return_list = []
        from georemindme.funcs import prefetch_refprops
        lists = prefetch_refprops(p.fetch_page(page), self._klass.user)
        for list in lists:
            if list.user.key() == querier.key():
                return_list.append(list)
            elif hasattr(list, '_vis'):
                if list._is_public():
                    return_list.append(list)
                elif list._is_shared() and list.user_invited(querier):
                    return_list.append(list)
        if len(return_list) != 0:
            return [p.id, return_list]
        return None


class ListSuggestionHelper(ListHelper):
    _klass = ListSuggestion

    def get_by_suggestion(self, suggestion, querier):
        if querier is None:
            raise TypeError()
        lists = self._klass.all().filter('keys =', suggestion.key()).filter('active =', True)
        lists_loaded = []
        from georemindme.funcs import prefetch_refprops
        lists = prefetch_refprops(lists, self._klass.user)
        for list in lists:
            if not querier.is_authenticated():
                if list._is_public():
                    lists_loaded.append(list)
            else:
                if list.user.key() == querier.key():
                    lists_loaded.append(list)
                elif list._is_public():
                    lists_loaded.append(list)
                elif list._is_shared() and list.user_invited(querier):
                    lists_loaded.append(list)
        return lists_loaded

class ListRequestedHelper(ListSuggestionHelper):
    _klass = ListRequested

    def get_by_id_querier(self, id, querier):
        '''
        Devuelve la lista publica con ese ID

            :param id: identificador de la lista
            :type id: :class:`Integer`
            :returns: None o :class:`geolist.models.List`
        '''
        if not isinstance(querier, User):
            raise TypeError()
        list = self.get_by_id(id)
        if list is None or not isinstance(list, ListRequested):
            return None
        if list.user.key() == querier.key():
            return list
        if list._is_public():
            return list
        elif list._is_shared() and list.user_invited(querier):
            return list
        return None


class ListAlertHelper(ListHelper):
    _klass = ListAlert


class ListUserHelper(ListHelper):
    _klass = ListUser
