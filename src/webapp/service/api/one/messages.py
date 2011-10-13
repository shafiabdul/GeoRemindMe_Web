# coding=utf-8


from protorpc import messages

    
class LoginResponse(messages.Message):
    """
            Respuesta correcta a una peticion de login,
        se iniciara una sesion nueva.
        
            Devuelve: 
                session: :class:`String` identificador unico de una sesion
                expires: :class:'integer' tiempo (en segundos) que dura la sesion
    """
    session = messages.StringField(1)
    expires = messages.IntegerField(2)


class Timeline(messages.Message):
    """
            Estructura que contiene la informacion devuelta
        de un solo timeline
        
            msg: :class:`string` mensaje (opcional)
            msg_id: :class:`integer` numero de tipo de mensaje
            instance_id: :class:`integer` identificador del objeto al
                que se refiere el timeline
            instance_name: :class:`string' nombre del objeto al
                que se refiere el timeline
            url: :class:`string` url del objeto (opcional)
            user: :class:'string' nombre del usuario dueño del timeline
            created :class:`integer` tiempo en segundos desde que se creo
                el timeline
    """
    msg = messages.StringField(1)
    msg_id = messages.IntegerField(2)
    instance_id = messages.IntegerField(3)
    instance_name = messages.StringField(4)
    url = messages.StringField(5)
    user = messages.StringField(6)
    created = messages.IntegerField(7)
    

class Timelines(messages.Message):
    """
        Contendra todos los timelines que se esten devolviendo en la consulta
        
            timelines: :class:`Timeline` lista con los timelines
            query_id: :class:`string` identificador para continuar con la consulta
    """
    timelines = messages.MessageField(Timeline, 1, repeated=True)
    query_id = messages.StringField(2)
    

class List(messages.Message):
    """
        Informacion sobre una lista
        
            id: :class:`integer` identificador de la lista
            name: :class:`string` nombre de la lista
    """
    id = messages.IntegerField(1)
    name = messages.StringField(2)
    

class Comment(messages.Message):
    """
        Contiene un comentario
        
            id: :class:`integer` identificador del comentario
            username: :class:`string` nombre del usuario
            message: :class:`string` mensaje 
            created: :class:`integer` tiempo en segundos desde que se creo
                el comentario
    """
    id = messages.IntegerField(1)
    username = messages.StringField(2)
    message = messages.StringField(3)
    created = messages.IntegerField(4)
    
    
class Suggestion(messages.Message):
    """
        Contiene una sugerencia
        
            name: :class:`string` nombre de la sugerencia
            description: :class:`string`
            poi_lat: :class:`float`
            poi_lon: :class:`float`
            poi_id: :class:`integer`
            google_places_reference: :class:`string`
            created: :class:`integer` tiempo en segundos desde que se creo
                la sugerencia
            modified: :class:`integer` tiempo en segundos desde que se modifico
                por ultima vez la sugerencia
            username: :class:`string`
            id: :class:`integer`
            lists: :class:`List` contiene las listas a las que pertenece la sugerencia
            comments: :class:'Comment` contiene todos los comentarios de la sugerencia
            has_voted: :class:boolean` True si el usuario ha votado
            vote_counter: :class:`integer`
            user_follower: :class:`boolean` True si el usuario ya sigue la sugerencia
            top_comments: :class:`Comment` lista con los comentarios mas votados 
    """
    name = messages.StringField(1, required=True)
    description = messages.StringField(2)
    poi_lat = messages.FloatField(3)
    poi_lon = messages.FloatField(4)
    poi_id = messages.IntegerField(5)
    google_places_reference = messages.StringField(6)
    created = messages.IntegerField(7)
    modified = messages.IntegerField(8)
    username = messages.StringField(9)
    id = messages.IntegerField(10)
    lists = messages.MessageField(List, 11, repeated=True)
    comments = messages.MessageField(Comment, 13, repeated=True)
    has_voted = messages.BooleanField(14)
    vote_counter = messages.IntegerField(15)
    user_follower = messages.BooleanField(16)
    top_comments = messages.MessageField(Comment, 17, repeated=True)
    

class Suggestions(messages.Message):
    """
        Contendra una lista de sugerencias que se esten devolviendo en la consulta
        
            suggestions: :class:`Timeline` lista con los timelines
            query_id: :class:`string` identificador para continuar con la consulta
    """
    query_id = messages.StringField(1)
    suggestions = messages.MessageField(Suggestion, 2, repeated=True)
    

class Site(messages.Message):
    """
        Informacion de un sitio a devolver con el autocompletado
        
            name: :class:`string` nombre devuelto por Places
            address: :class:`string` direccion devuelta por Places
            lat: :class:`float`
            lon: :class:`float`
    """
    name = messages.StringField(1, required=True)
    address = messages.StringField(2)
    lat = messages.FloatField(3)
    lon = messages.FloatField(4)
    
    
class Sites(messages.Message):
    """
        Coleccion de sitios devueltos por Places
    """
    sites = messages.MessageField(Site, 1, repeated=True)


class Place(messages.Message):
    """
        Informacion de un sitio:
        
            name: :class:`string` nombre de la sugerencia
            address: :class:`string`
            city: :class:`string`
            poi_lat: :class:`float`
            poi_lon: :class:`float`
            google_places_reference: :class:`string`
            id: :class:`integer`
            vote_counter: :class:`integer`
            suggestions: :class:`Suggestions` lista con los suggerencias
    """ 
    id = messages.IntegerField(1)
    name = messages.StringField(2)
    address = messages.StringField(3)
    city = messages.StringField(4)
    suggestions = messages.MessageField(Suggestions, 5)
    poi_lat = messages.FloatField(6)
    poi_lon = messages.FloatField(7)
    vote_counter = messages.IntegerField(8)
    google_places_reference = messages.StringField(9)
    