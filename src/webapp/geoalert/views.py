# coding=utf-8

"""
.. module:: views
    :platform: appengine
    :synopsis: Views for GeoAlert
"""

from django.http import Http404, HttpResponseServerError
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.template import RequestContext

from models import *
from geouser.decorators import login_required
import memcache


#===============================================================================
# PERFIL DE EVENTOS
#===============================================================================
def suggestion_profile(request, slug, template='webapp/suggestionprofile.html'):
    """Devuelve el perfil de una sugerencia, comprueba la visibilidad de una funcion
        
            :param id: identificador de la sugerencia
            :type id: :class:`ìnteger`
    """
    suggestion = Suggestion.objects.get_by_slug_querier(slug, querier=request.user)
    if suggestion is None:
        raise Http404 
    from geovote.views import get_comments_event
    comments = get_comments_event(request, suggestion.id)
    from geovote.models import Vote, Comment
    return render_to_response(template, {
                                        'suggestion': suggestion,
                                        'comments': comments,
                                        'has_voted': Vote.objects.user_has_voted(request.user, suggestion.key()),
                                        'vote_counter': Vote.objects.get_vote_counter(suggestion.key()),
                                        'user_follower': suggestion.has_follower(request.user),
                                        'top_comments': Comment.objects.get_top_voted(suggestion, request.user)
                                        },
                               context_instance=RequestContext(request))

    
#===============================================================================
# FUNCIONES PARA AÑADIR, EDITAR, OBTENER Y MODIFICAR ALERTAS
#===============================================================================
@login_required
def add_alert(request, form, address):
    """ Añade una alerta
        
            :param form: formulario con los datos
            :type form: :class:`geoalert.forms.RemindForm`
            :param address: direccion obtenida de la posicion
            :type: :class:`string`
            
            :returns: :class:`geoalert.models.Alert`
    """
    alert = form.save(user = request.user, address = address)
    return alert


@login_required
def edit_alert(request, id, form, address):
    """ Edita una alerta
        
            :param form: formulario con los datos
            :type id: :class:`geoalert.forms.RemindForm`
            
            :returns: :class:`geoalert.models.Alert`
    """
    alert = form.save(user = request.user, address = address, id = id)
    return alert


@login_required
def get_alert(request, id, done = None, page = 1, query_id = None):
    """ Obtiene alertas
        
            :param id: identificador de la alerta
            :type id: :class:`integer`
            :param done: devolver solo las realizadas
            :type done: boolean
            :param page: pagina a devolver
            :type page: :class:`ìnteger`
            :param query_id: identificador de la busqueda
            :type query_id: :class:`integer`
            
            :returns: :class:`geoalert.models.Alert`
    """
    if id:
        return [Alert.objects.get_by_id_user(id, request.user)]
    if done is None:
        return Alert.objects.get_by_user(request.user, page, query_id)
    if done:
        return Alert.objects.get_by_user_done(request.user, page, query_id)
    else:
        return Alert.objects.get_by_user_undone(request.user, page, query_id)


@login_required    
def del_alert(request, id = None):
    """ Borra una alerta
        
            :param id: identificador de la alerta
            :type id: :class:`integer`
            
            :returns: True
            :raises: AttributeError
    """
    if id is None:
        raise AttributeError()
    alert = Alert.objects.get_by_id_user(id, request.user)
    if not alert:
            raise AttributeError()
    alert.delete()    
    return True

#===============================================================================
# AÑADIR PLACES
#===============================================================================
def _get_city(components):
    for i in components:
        if 'locality' in i['types']:
            return i['short_name']
            
def search_place(pos, radius=500, types=None, language=None, name=None, sensor=False):
    """ Busca lugares cercano a la posicion usando la API de Google Places
        
            :param pos: posicion a buscar
            :type pos: :class:`db.GeoPt`
            :param radius: radio a buscar
            :type radius: :class:`integer`
            :param types: lista de tipos de sitios (opcional)
            :type types: list
            :param language: idioma de los resultados (opcional)
            :type language: string
            :param name: Nombre que buscar (opcional)
            :type name: string
            :param sensor: indicar si la posicion se obtiene con GPS, etc.
            :type sensor: boolean
            
            :returns: dict
    """
    def _add_urls_to_results(search):
        gets = list()
        length = len(search['results'])
        for i in xrange(length):
            gets.append(Place.all().filter('google_places_id =', search['results'][i]['id']).run())    
        for i in xrange(length):
            place = gets[i]
            try:
                place = place.next()
                search['results'][i].update({'_url': place.get_absolute_url()})
            except StopIteration:
                # no existe, devolvemos una url 'generica'
                search['results'][i].update({'_url': '/place/gref/%s' % search['results'][i]['reference']})
        return search
    from mapsServices.places.GPRequest import GPRequest
    search = GPRequest().do_search(pos, radius, types, language, name, sensor)
    return _add_urls_to_results(search)

@login_required
def add_from_google_reference(request, reference):
    """ Añade un lugar a partir de una referencia
        
            :param reference: clave de referencia
            :type reference: :class:`string`

    """
    place = Place.objects.get_by_google_reference(reference)
    if place is not None:  # ya existe, hacemos una redireccion permanente
        return redirect(place.get_absolute_url(), permanent=True)
    try:
        place = Place.insert_or_update_google(google_places_reference=reference,
                                              user = request.user
                                              )
    except Exception, e:
        return render_to_response('webapp/placeerror.html', {'error': e},
                                  context_instance=RequestContext(request))
    
    return redirect(place.get_absolute_url(), permanent=True)


@login_required
def add_from_foursquare_id(request, venueid):
    place = Place.objects.get_by_foursquare_id(venueid)
    if place is not None:
        return redirect(place.get_absolute_url(), permanent=True)
    try:
        place = Place.insert_or_update_foursquare(foursquare_id=venueid,
                                                  user = request.user
                                                  )
    except Exception, e:
        return render_to_response('webapp/placeerror.html', {'error': e},
                                  context_instance=RequestContext(request))
    return redirect(place.get_absolute_url(), permanent=True)


def view_place(request, slug, template='webapp/place.html'):
    """ Devuelve la vista con informacion de un lugar
       
           :param slug: slug identificativo del lugar
           :type slug: string
    """
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
    slug = slug.lower()
    place = Place.objects.get_by_slug(slug)
    if place is None:
        raise Http404
    from geovote.models import Vote
    if request.user.is_authenticated():
        has_voted = Vote.objects.user_has_voted(request.user, place.key())
    else:
        has_voted = False
    query_id, suggestions_async = Suggestion.objects.get_by_place(place, 
                                                  querier=request.user if request.user.is_authenticated() else None,
                                                  async = True
                                                  )
    vote_counter = Vote.objects.get_vote_counter(place.key())
    
    from mapsServices.places.GPRequest import GPRequest
    try:
        search = GPRequest().retrieve_reference(place.google_places_reference)
    except: 
        return render_to_response(template, {'place': place,
                                             'has_voted': has_voted,
                                             'vote_counter': vote_counter,
                                             'suggestions': [query_id, load_suggestions_async(suggestions_async)],
                                              },
                                  context_instance=RequestContext(request)
                                  )
    
    place.update(name=search['result']['name'],
                        address=search['result']['formatted_address'], 
                        city=_get_city(search['result']['address_components']),
                        location=db.GeoPt(search['result']['geometry']['location']['lat'], search['result']['geometry']['location']['lng']),
                        google_places_reference=search['result']['reference'],
                        google_places_id=search['result']['id']
                        )
    return render_to_response(template, {'place': place, 
                                         'google': search['result'],
                                         'has_voted': has_voted,
                                         'vote_counter': vote_counter,
                                         'suggestions': [query_id, load_suggestions_async(suggestions_async)],
                                         },
                              context_instance=RequestContext(request)
                              )
        

#===============================================================================
# FUNCIONES PARA AÑADIR, EDITAR, OBTENER Y MODIFICAR RECOMENDACIONES
#===============================================================================
@login_required
def user_suggestions(request, template='webapp/suggestions.html'):
    from geolist.models import ListSuggestion
    lists = ListSuggestion.objects.get_by_user(user=request.user, querier=request.user, all=True)
    counters = request.user.counters_async()
    suggestions = get_suggestion(request, id=None,
                                wanted_user=request.user,
                                page = 1, query_id = None
                                )
    
    return  render_to_response(template, {'suggestions': suggestions,
                                          'counters': counters.next(),
                                          'lists': [l for l in lists]
                                          }, context_instance=RequestContext(request)
                               )


@login_required
def add_suggestion(request, template='webapp/add_suggestion.html'):
    """ Añade una sugerencia
        
            :param form: formulario con los datos
            :type form: :class:`geoalert.forms.RemindForm`
            :param address: direccion obtenida de la posicion
            :type: :class:`string`
            
            :returns: :class:`geoalert.models.Suggestion`
    """
    from forms import SuggestionForm
    f = SuggestionForm();
    return  render_to_response(template, {'f': f,},
                               context_instance=RequestContext(request)
                               )
@login_required
def save_suggestion(request, form):
    """ Añade una sugerencia
    :param form: formulario con los datos
    :type form: :class:`geoalert.forms.RemindForm`
    :param address: direccion obtenida de la posicion
    :type: :class:`string`
    :returns: :class:`geoalert.models.Suggestion`
    """
    sug = form.save(user = request.user)
    return sug

@login_required
def add_suggestion_invitation(request, eventid, userid):
    """Envia una invitacion a un usuario
    
        :param eventid: identificador del evento
        :type eventid: :class:`Integer`
        :param userid: identificador del usuario
        :type userid: :class:`Integer`
        
        :returns: :class:`Boolean`
    """
    user_to = User.objects.get_by_id(userid)
    if user_to is None:
        raise Http404
    event = Suggestion.objects.get_by_id(eventid, request.user, request.user)
    if event is None:
        raise Http404
    
    return event.send_invitation(request.user, user_to)

@login_required
def edit_suggestion(request, suggestion_id, form, template='webapp/add_suggestion.html'):
    """ Edita una sugerencia
        
            :param form: formulario con los datos
            :type id: :class:`geoalert.forms.SuggestionForm`
            
            :returns: :class:`geoalert.models.Suggestion`
    """
    from geoalert.forms import SuggestionForm
    s = Suggestion.objects.get_by_id(suggestion_id)
    return  render_to_response(template, {
                                                        'eventid':suggestion_id,
                                                        'name': s.name,
                                                        'poi_id': s.poi.id,
                                                        'poi_reference': s.poi.google_places_reference,
                                                        'starts': s.date_starts,
                                                        'ends': s.date_ends,
                                                        'description': s.description, 
                                                        'visibility': s._vis,
                                                        'poi_location': s.poi.location,
                                                        'poi_name': s.poi.name,
                                                        'poi_address': s.poi.address,
                                                        }, context_instance=RequestContext(request)
                               )


@login_required
def get_suggestion(request, id, wanted_user=None, page = 1, query_id = None):
    """ Obtiene sugerencias
        
            :param id: identificador de la sugerencia
            :type id: :class:`integer`
            :param done: devolver solo las realizadas
            :type done: boolean
            :param page: pagina a devolver
            :type page: :class:`ìnteger`
            :param query_id: identificador de la busqueda
            :type query_id: :class:`integer`
            
            :returns: :class:`geoalert.models.Suggestion`
    """
    if id:
        return [Suggestion.objects.get_by_id_user(id, wanted_user, request.user)]
    else:
        return Suggestion.objects.get_by_user(wanted_user, request.user, page, query_id)


@login_required
def add_suggestion_follower(request, id):
    suggestion = Suggestion.objects.get_by_id_querier(id, request.user)
    if suggestion is not None:
        suggestion.add_follower(request.user)
        return True
    return False


@login_required
def del_suggestion_follower(request, id):
    suggestion = Suggestion.objects.get_by_id_querier(id, request.user)
    if suggestion is not None:
        suggestion.del_follower(request.user)
        return True
    return False


@login_required    
def del_suggestion(request, id = None):
    """ Borra una sugerencia
        
            :param id: identificador de la alerta
            :type id: :class:`integer`
            
            :returns: True
            :raises: AttributeError
    """
    if id is None:
        raise AttributeError()
    sug = Suggestion.objects.get_by_id_user(id, request.user, request.user)
    if not sug:
        raise AttributeError()
    sug.delete()    
    return True

