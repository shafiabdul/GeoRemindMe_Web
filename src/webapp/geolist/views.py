# coding=utf-8


from django.shortcuts import render_to_response
from django.shortcuts import Http404
from django.template import RequestContext
    
from geouser.decorators import login_required
from models import ListSuggestion, ListAlert, ListUser, List

#===============================================================================
# CREACION DE LISTAS
#===============================================================================
@login_required
def add_list_user(request, name, description = None, instances = []):
    '''
    Crea una nueva lista de usuarios
        
        :param name: nombre para la lista (el nombre es unico)
        :type name: :class:`string`
        :param description: descripcion de la lista (opcional)
        :type description: :class:`string`
        :param instances: lista de usuarios iniciales (opcional)
        :type instances: :class:`list`
        :returns: id de la lista creada o modificada si ya existia
    '''
    list = ListUser.insert_list(user=request.session['user'], name=name, description=description, instances=instances)
    return list.id

@login_required
def add_list_alert(request, name=None, description=None, instances=None):
    '''
    Crea una nueva lista de alertas
        
        :param name: nombre para la lista (el nombre es unico)
        :type name: :class:`string`
        :param description: descripcion de la lista (opcional)
        :type description: :class:`string`
        :param instances: lista de alertas iniciales (opcional)
        :type instances: :class:`list`
        :returns: id de la lista creada o modificada si ya existia
    '''
    list = ListAlert.insert_list(user=request.session['user'], name=name, description=description, instances=instances)
    return list.id

@login_required
def add_list_suggestion(request, id = None, name=None, description=None, instances=[], instances_del=[]):
    '''
    Modifica una lista de usuarios
        
        :param id: identificador de la lista
        :type id: :class:`integer`
        :param name: nombre para la lista (el nombre es unico)
        :type name: :class:`string`
        :param description: descripcion de la lista (opcional)
        :type description: :class:`string`
        :param instances: lista de alertas iniciales (opcional)
        :type instances: :class:`list`
        :returns: id de la lista modificada
    '''
    list = ListSuggestion.insert_list(user=request.user, id=id, name=name, description=description, instances=instances, instances_del=instances_del)
    return list
#===============================================================================
# Modificacion de listas
#===============================================================================
@login_required
def mod_list_user(request, id, name=None, description=None, instances_add=[], instances_del=[]):
    '''
    Modifica una lista de usuarios
        
        :param id: identificador de la lista
        :type id: :class:`integer`
        :param name: nombre para la lista (el nombre es unico)
        :type name: :class:`string`
        :param description: descripcion de la lista (opcional)
        :type description: :class:`string`
        :param instances: lista de alertas iniciales (opcional)
        :type instances: :class:`list`
        :returns: id de la lista modificada
    '''
    list = ListUser.objects.get_by_id_user(id, request.user)
    if list is not None:
        list.update(name=name, description=description, instances_add=instances_add, instances_del=instances_del)
        return True
    return False

@login_required
def mod_list_alert(request, id, name=None, description=None, instances_add=[], instances_del=[]):
    '''
    Modifica una lista de alertas
        
        :param id: identificador de la lista
        :type id: :class:`integer`
        :param name: nombre para la lista (el nombre es unico)
        :type name: :class:`string`
        :param description: descripcion de la lista (opcional)
        :type description: :class:`string`
        :param instances: lista de alertas iniciales (opcional)
        :type instances: :class:`list`
        :returns: id de la lista modificada
    '''
    list = ListAlert.objects.get_by_id_user(id, request.user)
    if list is not None:
        list.update(name=name, description=description, instances_add=instances_add, instances_del=instances_del)
        return True
    return False

#===============================================================================
# Obtiene listas
#===============================================================================
def get_list_id(request, id = None, user = None):
    '''
    Obtiene una lista por el identificador
        
        :param id: identificador de la lista
        :type id: :class:`integer`
        :returns: id de la lista modificada
    '''
    
    user = request.session.get('user', None)
    list = List.objects.get_by_id_user(id = id, user = user)
    return list

@login_required
def get_list_user_id(request, id = None, name = None):
    '''
    Obtiene una lista de usuarios
        
        :param id: identificador de la lista
        :type id: :class:`integer`
        :param name: nombre para la lista (el nombre es unico)
        :type name: :class:`string`
        :returns: id de la lista modificada
    '''
    user = request.session['user']

    list = ListUser.objects.get_by_id_user(id, user)

    return list

@login_required
def get_list_user_name(request, name):
    '''
    Obtiene una lista de usuarios
        
        :param id: identificador de la lista
        :type id: :class:`integer`
        :param name: nombre para la lista (el nombre es unico)
        :type name: :class:`string`
        :returns: id de la lista modificada
    '''
    user = request.session['user']
    list = ListUser.objects.get_by_name_user(name, user)
    
    return list


@login_required
def get_list_alert_id(request, id = None, name = None):
    '''
    Obtiene una lista de alertas
        
        :param id: identificador de la lista
        :type id: :class:`integer`
        :param name: nombre para la lista (el nombre es unico)
        :type name: :class:`string`
        :returns: id de la lista modificada
    '''
    user = request.session['user']
    list = ListAlert.objects.get_by_id_user(id, user)
    return list

@login_required
def get_list_alert_name(request, name):
    '''
    Obtiene una lista de usuarios
        
        :param id: identificador de la lista
        :type id: :class:`integer`
        :param name: nombre para la lista (el nombre es unico)
        :type name: :class:`string`
        :returns: id de la lista modificada
    '''
    user = request.session['user']
    list = ListAlert.objects.get_by_name_user(name, user)
    
    return list

@login_required
def del_list(request, id):
    '''
    Borra una lista
        
        :param id: identificador de la lista
        :type id: :class:`integer`
        :returns: True si se borro la lista
    '''
    list = List.objects.get_by_id_user(id, user = request.user)
    if list is not None:
        if list.user.key() == request.user.key():
            list.active = False
            list.put()
            return True
    return False

@login_required
def get_all_list_user(request, query_id=None, page=1):
    '''
    Devuelve todas las listas de usuarios del usuario ¡PAGINADA!
    
        :param page: numero de pagina a mostrar
        :type param: int
        :param query_id: identificador de busqueda
        :type query_id: int
        :returns: [query_id, [:class:`geolist.models.`]
    '''
    user = request.session['user']
    lists = ListUser.objects.get_by_user(user, query_id=query_id, page=page)
    
    return lists

@login_required
def get_all_list_alert(request, query_id=None, page=1):
    '''
    Devuelve todas las listas de alertas del usuario ¡PAGINADA!
    
        :param page: numero de pagina a mostrar
        :type param: int
        :param query_id: identificador de busqueda
        :type query_id: int
        :returns: [query_id, [:class:`geolist.models.`]
    '''
    user = request.session['user']
    lists = ListAlert.objects.get_by_user(user, query_id=query_id, page=page)
    
    return lists

@login_required
def get_list_suggestion(request, list_id=None, user_id=None, query_id=None, page=1):
    '''
    Devuelve todas las listas de sugerencias del usuario ¡PAGINADA!
    
        :param page: numero de pagina a mostrar
        :type param: int
        :param query_id: identificador de busqueda
        :type query_id: int
        :returns: [query_id, [:class:`geolist.models.ListSuggestion`]
    '''
    if list_id is None:
        if user_id is not None:
            from geouser.models import User
            user = User.objects.get_by_id(user_id)
            if user is None:
                raise Http404
            lists = ListSuggestion.objects.get_by_user(user, query_id=query_id, page=page, querier=request.user)
            return lists
        else:
            lists = ListSuggestion.objects.get_by_user(query_id=query_id, page=page, querier=request.user)
            return lists
    else:
        list = ListSuggestion.objects.get_by_id_querier(list_id, querier=request.user)
        return list


@login_required
def follow_list_suggestion(request, id):
    '''
    Añade a un usuario como seguir de una lista de sugerencias
    
        :param id: identificador de la lista
        :type id: :class:`integer`
        
        :returns: True si se añadio, False si no tiene permisos
    '''
    user = request.session['user']
    list = ListSuggestion.objects.get_by_id(id)
    follow = list.add_follower(user)
    
    return follow

def get_all_public_list_suggestion(request, query_id=None, page=1):
    '''
    Devuelve todas las listas de sugerencias publicas ¡PAGINADA!
    
        :param page: numero de pagina a mostrar
        :type param: int
        :param query_id: identificador de busqueda
        :type query_id: int
        :returns: [query_id, [:class:`geolist.models.ListSuggestion`]
    '''
    lists = ListSuggestion.objects.get_all_public(query_id=query_id, page=page)
    
    return lists

@login_required
def get_all_shared_list_suggestion(request):
    '''
    Devuelve todas las listas de sugerencias compartidas con el usuario
    
        :returns: [:class:`geolist.models.ListSuggestion`]
    '''
    lists = ListSuggestion.objects.get_shared_list(request.user)
    
    return lists


@login_required
def view_list(request, id, template='webapp/view_list.html'):
    def load_suggestions_async(suggestions):
        suggestions_loaded = []
        for suggestion in suggestions:
            suggestions_loaded.append({
                                    'instance': suggestion,
                                    'has_voted':  Vote.objects.user_has_voted(request.user, suggestion.key()) if request.user.is_authenticated() else False,
                                    'vote_counter': Vote.objects.get_vote_counter(suggestion.key())
                                   }
                                  )
            if len(suggestions_loaded) > 7:
                    break
        return suggestions_loaded
    list = ListSuggestion.objects.get_by_id_querier(id, request.user)
    if list is None:
        raise Http404
    from google.appengine.ext import db
    from geoalert.models import Event
    suggestions_async = db.get(list.keys)
    from geovote.models import Vote
    from geovote.views import get_comments_list
    from geovote.models import Comment
    has_voted = Vote.objects.user_has_voted(request.user, list.key())
    vote_counter = Vote.objects.get_vote_counter(list.key())
    query_id, comments_async = get_comments_list(request, list.id, async=True)
    top_comments = Comment.objects.get_top_voted(list, request.user)
    user_follower = list.has_follower(request.user)
    return render_to_response(template, {'list': list, 
                                         'has_voted': has_voted,
                                         'vote_counter': vote_counter,
                                         'user_follower': user_follower,
                                         'suggestions':load_suggestions_async(suggestions_async),
                                         'comments': Comment.objects.load_comments_from_async(query_id, comments_async, request.user),
                                         'top_comments': top_comments
                                         },
                              context_instance=RequestContext(request)
                              )