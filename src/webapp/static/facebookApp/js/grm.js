GRM = { common : {} };

GRM.common.extend = function(m, e){
    var e = e || this;
    for (var x in m) e[x] = m[x];
    return e;
};

GRM.common.get = function(s){
    if (typeof(s) == "string")
        return $(s);
    
    return s;
};

/*
    <span class="like-dislike" value="{{obj.instance.id}}" {% if obj.has_voted %}like="true"{%endif%} type="suggestion">
        <span class="dislike">
            <span class="hoverlink">Ya no me gusta</span> 
            <span class="text like-text increase">{{obj.vote_counter}}</span> personas
        </span>

        <span class="like">
            Me gusta
        </span>
    </span>
    
    $('.like-dislike').remember({like_class: "xxx", dislike_class: "xxx", progress_class: "xxx"});
*/
GRM.like = function(settings) {
    
    settings = jQuery.extend({
        like_class: null,
        dislike_class: null,
        progress_class: null        
    }, settings);
       
    return this.each(function(){

        // get init state
        var state = (typeof $(this).attr('like') != "undefined" );

        // auto-init classes
        if (state && settings.dislike_class)
            $(this).addClass(settings.dislike_class);
        if (!state && settings.like_class)
            $(this).addClass(settings.like_class);

        // auto-init show/hide
        if (state)
            $(this).find('.like').hide();
        else
            $(this).find('.dislike').hide();


        // counter incremental
        var inc = $(this).find('.increase');
        $.each(inc, function(index,item){
            $(item).text(parseInt($(item).text())+1);
        });
        
        $(this).click(function() {
            
            var type = $(this).attr('type'), id = $(this).attr('value'), vote = (typeof $(this).attr('like') != "undefined" )?-1:1;
            
            if (settings.progress_class)
                $(this).addClass(settings.progress_class);
            
            $.ajax({
                    type: "POST",
                    url: "/ajax/vote/"+type+"/",
                    data: {
                        instance_id:id,
                        puntuation: vote
                    },
                    context: $(this),
                    success: function(){
                        
                        // disliking
                        if (typeof $(this).attr('like') != "undefined" ) {
                            // send vote -1
                            $(this).find('.dislike').hide();
                            $(this).find('.like').show();
                            $(this).removeAttr("like");
                            
                            if (settings.dislike_class)
                                $(this).removeClass(settings.dislike_class);
                            
                            if (settings.like_class)
                                $(this).addClass(settings.like_class);
                                
                        }
                        
                        // liking
                        else {
                            // send vote +1
                            $(this).find('.like').hide();
                            $(this).find('.dislike').show();
                            $(this).attr("like","true");
                            
                            if (settings.like_class)
                                $(this).removeClass(settings.like_class);
                            
                            if (settings.dislike_class)
                                $(this).addClass(settings.dislike_class);
                            }
                        
                    },
                    complete: function()
                    {
                        if (settings.progress_class)
                            $(this).removeClass(settings.progress_class);
                    }
                });
        });
    });
};

/*
    <span title="Guardar en favoritos"  class="remember-forget" value="{{obj.instance.id}}" {%if obj.user_follower%}remember="true"{%endif%}>
        <span class="remember">Guardar</span>
        <span class="forget">Guardado</span>
    </span>
    
    $('.remember-forget').remember({remember_class: "xxx", forget_class: "xxx", progress_class: "xxx"});
*/
GRM.remember = function(settings) {
    
    settings = jQuery.extend({
        remember_class: null,
        forget_class: null,
        progress_class: null        
    }, settings);
       
    return this.each(function(){

        // get init state
        var state = (typeof $(this).attr('remember') != "undefined" );

        // auto-init classes
        if (state && settings.forget_class)
            $(this).addClass(settings.forget_class);
        if (!state && settings.remember_class)
            $(this).addClass(settings.remember_class);

        // auto-init show/hide
        if (state)
            $(this).find('.remember').hide();
        else
            $(this).find('.forget').hide();

        $(this).click(function() {
            
            var id = $(this).attr('value'), url = (typeof $(this).attr('remember') != "undefined" )?"/ajax/delete/suggestion/follower/":"/ajax/add/suggestion/follower/";
            
            if (settings.progress_class)
                $(this).addClass(settings.progress_class);
            
            $.ajax({
                    type: "POST",
                    url: url,
                    data: {
                        eventid:id
                    },
                    context: $(this),
                    success: function(){
                        
                        // disliking
                        if (typeof $(this).attr('remember') != "undefined" ) {
                            // send vote -1
                            $(this).find('.forget').hide();
                            $(this).find('.remember').show();
                            $(this).removeAttr("remember");
                            
                            if (settings.forget_class)
                                $(this).removeClass(settings.forget_class);
                            
                            if (settings.remember_class)
                                $(this).addClass(settings.remember_class);
                                
                        }
                        
                        // liking
                        else {
                            // send vote +1
                            $(this).find('.remember').hide();
                            $(this).find('.forget').show();
                            $(this).attr("remember","true");
                            
                            if (settings.remember_class)
                                $(this).removeClass(settings.remember_class);
                            
                            if (settings.forget_class)
                                $(this).addClass(settings.forget_class);
                            }
                        
                    },
                    complete: function()
                    {
                        if (settings.progress_class)
                            $(this).removeClass(settings.progress_class);
                    }
                });
        });
    });
};

jQuery.fn.like = GRM.like;
jQuery.fn.remember = GRM.remember;

GRM.init = function() {
        $(".like-dislike").like();
        $(".remember-forget").remember();
    }

//$(document).ready(GRM.init);

function initRemovable(){

    $(".removable").hide();
    $(".removable").parent().hover(
        function(){$(this).find(".removable:first").show()},
        function(){$(this).find(".removable:first").hide()}
    )
    $(".removable").click(function(){
        var id=$(this).attr('value');
        var type=$(this).attr('type');
        
        if(type=="suggestion"){
            data={eventid:id};
        }else if (type=="comment"){
            data={comment_id:id};
        }
        var elem=$(this)
        $.ajax({
            type: "POST",
            url: "/ajax/delete/"+type+"/",
            data: data,
            dataType:'json',
            success: function(msg){
                if(msg==true){

                    if (type=="comment"){
                        //Eliminamos el comentario
                        var preElem=elem.parent().prev();
                        var posElem=elem.parent().next();
                        //parentTree=elem.parentsUntil('.suggestion-element');
                        if(preElem.size()==0 && posElem.size()==0){
                            //Si al borrar el comentario ya no quedan más elementos
                            //Ocultamos la caja de comentarios
                            elem.parent().parent().next().addClass('hidden');
                            
                        }
                        elem.parent().remove()
                        
                    }else if(type=="suggestion")
                        elem.parent().parent().remove()
                }
            },
            error:function(){
            }
            
        });
    });
}

function loadPage(dict){
            var page=dict['page'];
            var container=dict['container']
            var url=dict['url']
            var template=dict['template']
            var data=dict["data"]
            
            if ( typeof loadPage.currentPage == 'undefined' ) {
            // It has not... perform the initilization
                loadPage.currentPage=1
            }
            if (page=='next')
                loadPage.currentPage++;
            else if(page=='prev' && loadPage.currentPage>1)
                loadPage.currentPage--;
            else
                loadPage.currentPage=page;
            
            page=loadPage.currentPage;
            data['page']=page;
            
            $.ajax({
                type: 'POST',
                url: url,
                data:data,
                success: function(data){
                    
                    $(container).empty()
                    $.each(data[1], function(index,suggestion){
                        $(template).tmpl( {element:suggestion} ).appendTo(container);
                    });
                    
                    //Ocultamos los botones de siguiente y anterior si es necesario
                    if(page>1)
                        $('#prev-page').removeClass('hidden')
                    else
                        $('#prev-page').addClass('hidden')
                    
                    return page;
                }
            });
        }

//Creamos nuestro propio namespace       
//~ if (typeof GRM == "undefined" || !GRM ) {
    //~ window.GRM = {};
//~ };

/*
 *  Esta función hace una petición AJAX y carga una plantilla con los
 *  datos recibidos.
 * 
 *  Ejemplo de llamada:
 *  GRM.loadPage({
 *               page:page,
 *               container:'#suggestion-list',
 *               url:'/ajax/get/suggestion/',
 *               template: "#suggestionTemplate",
 *               data:{
 *                       'query_id':{{suggestions.0}},
 *                   }                
 *           });
 */
 //~ jQuery.extend({
     //~ loadPage : function(dict){
        //~ var page=dict['page'];
        //~ var container=dict['container']
        //~ var url=dict['url']
        //~ var template=dict['template']
        //~ var data=dict["data"]
        //~ console.log(dict)
        //~ 
        //~ if ( typeof GRM.loadPage.currentPage == 'undefined' ) {
            //~ // Creamos una variable estática
            //~ GRM.loadPage.currentPage=1
        //~ }
        //~ if (page=='next')
            //~ GRM.loadPage.currentPage++;
        //~ else if(page=='prev' && loadPage.currentPage>1)
            //~ GRM.loadPage.currentPage--;
        //~ else
            //~ GRM.loadPage.currentPage=page;
        //~ 
        //~ page=GRM.loadPage.currentPage;
        //~ data['page']=page;
        //~ 
        //~ $.ajax({
            //~ type: 'POST',
            //~ url: url,
            //~ data:data,
            //~ success: function(data){
                //~ 
                //~ $(container).empty()
                //~ $.each(data[1], function(index,suggestion){
                    //~ $(template).tmpl( {suggestion} ).appendTo(container);
                //~ });
                //~ 
                //~ //Ocultamos los botones de siguiente y anterior si es necesario
                //~ if(page>1)
                    //~ $('#prev-page').removeClass('hidden')
                //~ else
                    //~ $('#prev-page').addClass('hidden')
                //~ 
                //~ return page;
            //~ }
        //~ });
    //~ }
//~ });
