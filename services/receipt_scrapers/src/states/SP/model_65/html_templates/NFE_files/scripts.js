/// <reference path="jquery-2.0.0.js" />

/*	--------------------------------------------------
    :: Menu Principal
    -------------------------------------------------- */
$(function () {
    $(document).ready(function () { 
        $(".nav").setup_navigation() 
    });
    var e = { 48: "0", 49: "1", 50: "2", 51: "3", 52: "4", 53: "5", 54: "6", 55: "7", 56: "8", 57: "9", 59: ";", 65: "a", 66: "b", 67: "c", 68: "d", 69: "e", 70: "f", 71: "g", 72: "h", 73: "i", 74: "j", 75: "k", 76: "l", 77: "m", 78: "n", 79: "o", 80: "p", 81: "q", 82: "r", 83: "s", 84: "t", 85: "u", 86: "v", 87: "w", 88: "x", 89: "y", 90: "z", 96: "0", 97: "1", 98: "2", 99: "3", 100: "4", 101: "5", 102: "6", 103: "7", 104: "8", 105: "9" };

    $.fn.setup_navigation = function (t) {
        t = jQuery.extend({ menuHoverClass: "show-menu" }, t);

        $(this).attr("role", "menubar").find("li").attr("role", "menuitem");

        var n = $(this).find("> li > a");

        $(n).next("ul").attr("data-test", "true").attr({ "aria-hidden": "true", role: "menu" }).find("a").attr("tabIndex", -1);

        $(n).each(function () {
            if ($(this).next("ul").length > 0) { $(this).parent("li").attr("aria-haspopup", "true") }
        });

        $(n).hover(function () {
            $(this).closest("ul").attr("aria-hidden", "false").find("." + t.menuHoverClass).attr("aria-hidden", "true").removeClass(t.menuHoverClass).find("a").attr("tabIndex", -1); $(this).next("ul").attr("aria-hidden", "false").addClass(t.menuHoverClass).find("a").attr("tabIndex", 0)
        });
        $(n).focus(function () {
            $(this).closest("ul").find("." + t.menuHoverClass).attr("aria-hidden", "true").removeClass(t.menuHoverClass).find("a").attr("tabIndex", -1); $(this).next("ul").attr("aria-hidden", "false").addClass(t.menuHoverClass).find("a").attr("tabIndex", 0)
        }); $(n).keydown(function (n) {
            if (n.keyCode == 37) {
                n.preventDefault();
                if ($(this).parent("li").prev("li").length == 0) {
                    $(this).parents("ul").find("> li").last().find("a").first().focus()
                } else {
                    $(this).parent("li").prev("li").find("a").first().focus()
                }
            } else {
                if (n.keyCode == 38) {
                    n.preventDefault();
                    if ($(this).parent("li").find("ul").length > 0) { $(this).parent("li").find("ul").attr("aria-hidden", "false").addClass(t.menuHoverClass).find("a").attr("tabIndex", 0).last().focus() }
                } else { if (n.keyCode == 39) { n.preventDefault(); if ($(this).parent("li").next("li").length == 0) { $(this).parents("ul").find("> li").first().find("a").first().focus() } else { $(this).parent("li").next("li").find("a").first().focus() } } else { if (n.keyCode == 40) { n.preventDefault(); if ($(this).parent("li").find("ul").length > 0) { $(this).parent("li").find("ul").attr("aria-hidden", "false").addClass(t.menuHoverClass).find("a").attr("tabIndex", 0).first().focus() } } else { if (n.keyCode == 13 || n.keyCode == 32) { n.preventDefault(); $(this).parent("li").find("ul[aria-hidden=true]").attr("aria-hidden", "false").addClass(t.menuHoverClass).find("a").attr("tabIndex", 0).first().focus() } else { if (n.keyCode == 27) { n.preventDefault(); $("." + t.menuHoverClass).attr("aria-hidden", "true").removeClass(t.menuHoverClass).find("a").attr("tabIndex", -1) } else { $(this).parent("li").find("ul[aria-hidden=false] a").each(function () { if ($(this).text().substring(0, 1).toLowerCase() == e[n.keyCode]) { $(this).focus(); return false } }) } } } } }
            }
        });


        var r = $(n).parent("li").find("ul").find("a"); $(r).keydown(function (n) {
            if (n.keyCode == 38) {
                n.preventDefault();
                if ($(this).parent("li").prev("li").length == 0) {
                    $(this).parents("ul").parents("li").find("a").first().focus()
                } else { $(this).parent("li").prev("li").find("a").first().focus() }
            } else {
                if (n.keyCode == 40) {
                    n.preventDefault(); if ($(this).parent("li").next("li").length == 0) {
                        $(this).parents("ul").parents("li").find("a").first().focus()
                    } else { $(this).parent("li").next("li").find("a").first().focus() }
                } else {
                    if (n.keyCode == 27 || n.keyCode == 37) {
                        n.preventDefault(); $(this).parents("ul").first().prev("a").focus().parents("ul").first().find("." + t.menuHoverClass).attr("aria-hidden", "true").removeClass(t.menuHoverClass).find("a").attr("tabIndex", -1)
                    } else {
                        if (n.keyCode == 32) {
                            n.preventDefault(); window.location = $(this).attr("href")
                        } else {
                            var r = false; $(this).parent("li").nextAll("li").find("a").each(function () {
                                if ($(this).text().substring(0, 1).toLowerCase() == e[n.keyCode]) {
                                    $(this).focus(); r = true; return false
                                }
                            });

                            if (!r) {
                                $(this).parent("li").prevAll("li").find("a").each(function () {
                                    if ($(this).text().substring(0, 1).toLowerCase() == e[n.keyCode]) { $(this).focus(); return false }
                                })
                            }
                        }
                    }
                }
            }
        }); $(this).find("a").last().keydown(function (e) {
            if (e.keyCode == 9) {
                $("." + t.menuHoverClass).attr("aria-hidden", "true").removeClass(t.menuHoverClass).find("a").attr("tabIndex", -1)
            }
        }); $(document).click(function () { $("." + t.menuHoverClass).attr("aria-hidden", "true").removeClass(t.menuHoverClass).find("a").attr("tabIndex", -1) }); $(this).click(function (e) { e.stopPropagation() })
    }
})



/*	--------------------------------------------------
    :: Ajustes no web Controls
    -------------------------------------------------- */
$(function () {
    $(document).ready(function() {
        //Ajusta o asp.net MENU
        $("#Menu1").removeAttr("style");
        $("#Menu1").css("margin-top", "95px"); //Ajuste da altura do menu
    });
});



/*	--------------------------------------------------
    :: Tool Tip
    -------------------------------------------------- */
$(document).ready(function () {
    var a = $("[rel~=glossary]"),
        b = false,
        c = false,
        d = false;
    a.bind("mouseenter", function () {
        b = $(this);
        tip = b.attr("title");
        c = $('<div id="tooltip"></div>');
        if (!tip || tip == "") {
            return false
        }
        b.removeAttr("title");
        c.css("opacity", 0)
            .html(tip)
            .appendTo("body");
        var a = function () {
            if ($(window).width() < c
                .outerWidth() * 1.5) {
                c.css("max-width", $(window).width() / 2)
            } else {
                c.css("max-width", 340)
            }
            var a = b.offset()
                .left + b
                .outerWidth() / 2 - c
                .outerWidth() / 2,
                d = b.offset()
                    .top - c
                    .outerHeight() - 20;
            if (a < 0) {
                a = b.offset()
                    .left + b
                    .outerWidth() / 2 - 20;
                c.addClass("left")
            } else {
                c.removeClass("left")
            }
            if (a + c.outerWidth() > $(window)
                .width()) {
                a = b.offset()
                    .left - c
                    .outerWidth() + b
                    .outerWidth() / 2 + 20;
                c.addClass("right")
            } else {
                c.removeClass("right")
            }
            if (d < 0) {
                var d = b.offset()
                    .top + b
                    .outerHeight();
                c.addClass("top")
            } else {
                c.removeClass("top")
            }
            c.css({
                left: a,
                top: d
            })
                .animate({
                top: "+=10",
                opacity: 1
            }, 50)
        };
        a();
        $(window).resize(a);
        var d = function () {
            c.animate({
                top: "-=10",
                opacity: 0
            }, 50, function () {
                $(this).remove()
            });
            b.attr("title", tip)
        };
        b.bind("mouseleave", d);
        c.bind("click", d)
    })
});



/*	--------------------------------------------------
    :: Contraste
    -------------------------------------------------- */
function setActiveStyleSheet(a) {
    var b, c, d;
    for (b = 0; c = document.getElementsByTagName("link")[b]; b++) {
        if (c.getAttribute("rel")
            .indexOf("style") != -1 && c
            .getAttribute("title")) {
            c.disabled = true;
            if (c.getAttribute("title") == a) {
                c.disabled = false
            }
        }
    }
}
function getActiveStyleSheet() {
    var a, b;
    for (a = 0; b = document.getElementsByTagName("link")[a]; a++) {
        if (b.getAttribute("rel")
            .indexOf("style") != -1 && b
            .getAttribute("title") && !b
            .disabled) {
            return b.getAttribute("title");
        }
    }
    return null;
}

$(document).ready(function () {
    $(".contraste").click(function() {
        if (getActiveStyleSheet() == "default") {
            setActiveStyleSheet("contrast");
        } else {
            setActiveStyleSheet("default");
        }
    });
});



/*	--------------------------------------------------
    :: Tabindex Automático
    -------------------------------------------------- */
$(function () {
    var a = 1;
    $("input,select,button,a").each(function() {
        if (this.type != "hidden") {
            var b = $(this);
            b.attr("tabindex", a);
            a++;
        }
    });
});



/*	--------------------------------------------------
    :: Tamanho da Fonte
    -------------------------------------------------- */
$(document).ready(function () {
    var a = $("html").css("font-size");
    $(".resetFont").click(function () {
        $("html").css("font-size", a);
    });
    $(".increaseFont").click(function () {
        var a = $("html").css("font-size");
        var b = parseFloat(a, 11);
        var c = b * 1.2;
        $("html").css("font-size", c);
        return false;
    });
    $(".decreaseFont").click(function() {
        var a = $("html").css("font-size");
        var b = parseFloat(a, 11);
        var c = b * .8;
        $("html").css("font-size", c);
        return false;
    });
});



/*	--------------------------------------------------
    :: Show Hide
    -------------------------------------------------- */
$(document).ready(function () {
    $(".box-busca-avancada").hide();
    $(".btn-avancada").show();
    $(".btn-avancada").click(function () {
        $(".box-busca-avancada").toggle()
    })
});



/*	--------------------------------------------------
    :: Show Hide
    -------------------------------------------------- */
$(document).ready(function () {
    $(".box-tool-save").hide();
    $(".tool-save").show();
    $(".tool-save").click(function() {
        $(".box-tool-save").toggle();
    });
})



/*	--------------------------------------------------
    :: jQuery Tabs & Simple Tabs
    -------------------------------------------------- */
$(document).ready(function() {
    $(".abas").tabs();
});	

$(function () {
    $('.tabs').each(function() {
        var content = $(this).find('.tab-content'),
            tab     = $('> ul li', this);
        $('.content-main', content).eq(0).show();
        tab.click(function () {
            tab.removeClass('active');
            $(this).addClass('active');
            $('.content-main', content).hide().eq($(this).index()).show(); 
        });
    });
});


/*	--------------------------------------------------
    :: Modal
    -------------------------------------------------- */
$.fx.speeds._default = 1000;
$(function() {
    $( ".box-modal" ).dialog({
        autoOpen: false,		// Não permite que a janela abra no automaticamente
        modal: true,			// Ativa modo MODAL
        closeOnEscape: false,	// Desativa o ESC
        resizable: false,		// Não permite redimensionar a janela
        draggable: false,		// Não permite arrastar a janela
        width: "900px",			// Trava a largura da modal
        closeText: "Fechar"
    });

    $( ".open-modal" ).click(function() {
        $( ".box-modal" ).dialog( "open" );
        return false;
    });
    
    $( ".close-modal" ).click(function() {
        $( ".box-modal" ).dialog( "close" );
        return false;
    });
});



/*	--------------------------------------------------
    :: Jquery Spinner
    -------------------------------------------------- */
jQuery().ready(function($) {
    $('.spinner').spinner({ min: 0, max: 1000 });
});

(function(j){var s="ui-state-active",l=j.ui.keyCode,C=l.UP,D=l.DOWN,t=l.RIGHT,E=l.LEFT,u=l.PAGE_UP,v=l.PAGE_DOWN,J=l.HOME,K=l.END,L=j.browser.msie,M=j.browser.mozilla?"DOMMouseScroll":"mousewheel",N=[C,D,t,E,u,v,J,K,l.BACKSPACE,l.DELETE,l.TAB],O;j.widget("ui.spinner",{options:{min:null,max:null,allowNull:false,group:"",point:".",prefix:"",suffix:"",places:null,defaultStep:1,largeStep:10,mouseWheel:true,increment:"slow",className:null,showOn:"always",width:16,upIconClass:"ui-icon-triangle-1-n",downIconClass:"ui-icon-triangle-1-s",
format:function(a,b){var d=/(\d+)(\d{3})/,g=(isNaN(a)?0:Math.abs(a)).toFixed(b)+"";for(g=g.replace(".",this.point);d.test(g)&&this.group;g=g.replace(d,"$1"+this.group+"$2"));return(a<0?"-":"")+this.prefix+g+this.suffix},parse:function(a){if(this.group==".")a=a.replace(".","");if(this.point!=".")a=a.replace(this.point,".");return parseFloat(a.replace(/[^0-9\-\.]/g,""))}},_create:function(){var a=this.element,b=a.attr("type");if(!a.is("input")||b!="text"&&b!="number")console.error("Invalid target for ui.spinner");
else{this._procOptions(true);this._createButtons(a);a.is(":enabled")||this.disable()}},_createButtons:function(a){function b(e){return e=="auto"?0:parseInt(e)}function d(e){for(var h=0;h<N.length;h++)if(N[h]==e)return true;return false}function g(e,h){if(F)return false;var m=String.fromCharCode(h||e),o=c.options;if(m>="0"&&m<="9"||m=="-")return false;if(c.places>0&&m==o.point||m==o.group)return false;return true}function i(e){function h(){w=0;e()}if(w){if(e===P)return;clearTimeout(w)}P=e;w=setTimeout(h,
100)}function p(){if(!f.disabled){var e=c.element[0],h=this===x?1:-1;e.focus();e.select();j(this).addClass(s);G=true;c._startSpin(h)}return false}function q(){if(G){j(this).removeClass(s);c._stopSpin();G=false}return false}var c=this,f=c.options,r=f.className,y=f.width,n=f.showOn,H=j.support.boxModel,Q=a.outerHeight(),R=c.oMargin=b(a.css("margin-right")),I=c.wrapper=a.css({width:(c.oWidth=H?a.width():a.outerWidth())-y,marginRight:R+y,textAlign:"right"}).after('<span class="ui-spinner ui-widget"></span>').next(),
z=c.btnContainer=j('<div class="ui-spinner-buttons"><div class="ui-spinner-up ui-spinner-button ui-state-default ui-corner-tr"><span class="ui-icon '+f.upIconClass+'">&nbsp;</span></div><div class="ui-spinner-down ui-spinner-button ui-state-default ui-corner-br"><span class="ui-icon '+f.downIconClass+'">&nbsp;</span></div></div>'),x,S,k,w,P,A,B,F,G,T=a[0].dir=="rtl";r&&I.addClass(r);I.append(z.css({height:Q,left:-y-R,top:a.offset().top-I.offset().top+"px"}));k=c.buttons=z.find(".ui-spinner-button");
k.css({width:y-(H?k.outerWidth()-k.width():0),height:Q/2-(H?k.outerHeight()-k.height():0)});x=k[0];S=k[1];r=k.find(".ui-icon");r.css({marginLeft:(k.innerWidth()-r.width())/2,marginTop:(k.innerHeight()-r.height())/2});z.width(k.outerWidth());n!="always"&&z.css("opacity",0);if(n=="hover"||n=="both")k.add(a).bind("mouseenter.uispinner",function(){i(function(){A=true;if(!c.focused||n=="hover")c.showButtons()})}).bind("mouseleave.uispinner",function(){i(function(){A=false;if(!c.focused||n=="hover")c.hideButtons()})});
k.hover(function(){c.buttons.removeClass("ui-state-hover");f.disabled||j(this).addClass("ui-state-hover")},function(){j(this).removeClass("ui-state-hover")}).mousedown(p).mouseup(q).mouseout(q);L&&k.dblclick(function(){if(!f.disabled){c._change();c._doSpin((this===x?1:-1)*f.step)}return false}).bind("selectstart",function(){return false});a.bind("keydown.uispinner",function(e){var h,m,o=e.keyCode;if(e.ctrl||e.alt)return true;if(d(o))F=true;if(B)return false;switch(o){case C:case u:h=1;m=o==u;break;
case D:case v:h=-1;m=o==v;break;case t:case E:h=o==t^T?1:-1;break;case J:e=c.options.min;e!=null&&c._setValue(e);return false;case K:e=c.options.max;e!=null&&c._setValue(e);return false}if(h){if(!B&&!f.disabled){keyDir=h;j(h>0?x:S).addClass(s);B=true;c._startSpin(h,m)}return false}}).bind("keyup.uispinner",function(e){if(e.ctrl||e.alt)return true;if(d(l))F=false;switch(e.keyCode){case C:case t:case u:case D:case E:case v:k.removeClass(s);c._stopSpin();return B=false}}).bind("keypress.uispinner",function(e){if(g(e.keyCode,
e.charCode))return false}).bind("change.uispinner",function(){c._change()}).bind("focus.uispinner",function(){function e(){c.element.select()}L?e():setTimeout(e,0);c.focused=true;O=c;if(!A&&(n=="focus"||n=="both"))c.showButtons()}).bind("blur.uispinner",function(){c.focused=false;if(!A&&(n=="focus"||n=="both"))c.hideButtons()})},_procOptions:function(a){var b=this.element,d=this.options,g=d.min,i=d.max,p=d.step,q=d.places,c=-1,f;if(d.increment=="slow")d.increment=[{count:1,mult:1,delay:250},{count:3,
mult:1,delay:100},{count:0,mult:1,delay:50}];else if(d.increment=="fast")d.increment=[{count:1,mult:1,delay:250},{count:19,mult:1,delay:100},{count:80,mult:1,delay:20},{count:100,mult:10,delay:20},{count:0,mult:100,delay:20}];if(g==null&&(f=b.attr("min"))!=null)g=parseFloat(f);if(i==null&&(f=b.attr("max"))!=null)i=parseFloat(f);if(!p&&(f=b.attr("step"))!=null)if(f!="any"){p=parseFloat(f);d.largeStep*=p}d.step=p=p||d.defaultStep;if(q==null&&(f=p+"").indexOf(".")!=-1)q=f.length-f.indexOf(".")-1;this.places=
q;if(i!=null&&g!=null){if(g>i)g=i;c=Math.max(Math.max(c,d.format(i,q,b).length),d.format(g,q,b).length)}if(a)this.inputMaxLength=b[0].maxLength;f=this.inputMaxLength;if(f>0){c=c>0?Math.min(f,c):f;f=Math.pow(10,c)-1;if(i==null||i>f)i=f;f=-(f+1)/10+1;if(g==null||g<f)g=f}c>0&&b.attr("maxlength",c);d.min=g;d.max=i;this._change();b.unbind(M+".uispinner");d.mouseWheel&&b.bind(M+".uispinner",this._mouseWheel)},_mouseWheel:function(a){var b=j.data(this,"spinner");if(!b.options.disabled&&b.focused&&O===b){b._change();
b._doSpin(((a.wheelDelta||-a.detail)>0?1:-1)*b.options.step);return false}},_setTimer:function(a,b,d){function g(){i._spin(b,d)}var i=this;i._stopSpin();i.timer=setInterval(g,a)},_stopSpin:function(){if(this.timer){clearInterval(this.timer);this.timer=0}},_startSpin:function(a,b){var d=this.options.increment;this._change();this._doSpin(a*(b?this.options.largeStep:this.options.step));if(d&&d.length>0){this.incCounter=this.counter=0;this._setTimer(d[0].delay,a,b)}},_spin:function(a,b){var d=this.options.increment,
g=d[this.incCounter];this._doSpin(a*g.mult*(b?this.options.largeStep:this.options.step));this.counter++;if(this.counter>g.count&&this.incCounter<d.length-1){this.counter=0;g=d[++this.incCounter];this._setTimer(g.delay,a,b)}},_doSpin:function(a){var b=this.curvalue;if(b==null)b=(a>0?this.options.min:this.options.max)||0;this._setValue(b+a)},_parseValue:function(){var a=this.element.val();return a?this.options.parse(a,this.element):null},_validate:function(a){var b=this.options,d=b.min,g=b.max;if(a==
null&&!b.allowNull)a=this.curvalue!=null?this.curvalue:d||g||0;return g!=null&&a>g?g:d!=null&&a<d?d:a},_change:function(){var a=this._parseValue();if(!this.selfChange){if(isNaN(a))a=this.curvalue;this._setValue(a,true)}},_setOption:function(a,b){j.Widget.prototype._setOption.call(this,a,b);this._procOptions()},increment:function(){this._doSpin(this.options.step)},decrement:function(){this._doSpin(-this.options.step)},showButtons:function(a){var b=this.btnContainer.stop();a?b.css("opacity",1):b.fadeTo("fast",
1)},hideButtons:function(a){var b=this.btnContainer.stop();a?b.css("opacity",0):b.fadeTo("fast",0);this.buttons.removeClass("ui-state-hover")},_setValue:function(a,b){this.curvalue=a=this._validate(a);this.element.val(a!=null?this.options.format(a,this.places,this.element):"");if(!b){this.selfChange=true;this.element.change();this.selfChange=false}},value:function(a){if(arguments.length){this._setValue(a);return this.element}return this.curvalue},enable:function(){this.buttons.removeClass("ui-state-disabled");
this.element[0].disabled=false;j.Widget.prototype.enable.call(this)},disable:function(){this.buttons.addClass("ui-state-disabled").removeClass("ui-state-hover");this.element[0].disabled=true;j.Widget.prototype.disable.call(this)},destroy:function(){this.wrapper.remove();this.element.unbind(".uispinner").css({width:this.oWidth,marginRight:this.oMargin});j.Widget.prototype.destroy.call(this)}})})(jQuery);



/*	--------------------------------------------------
    :: Collapse Expand
    -------------------------------------------------- */
$("html").addClass("js");
$(function() {
    $(".accordion h3.expand").toggle();
    $("html").removeClass("js");
});

//TODO : Remover
//(function(e){e.fn.expandAll=function(t){var n=e.extend({},e.fn.expandAll.defaults,t);return this.each(function(t){function d(t){for(var n=0,r=arguments.length;n<r;n++){var i=arguments[n],s=e(i);if(s.scrollTop()>0){return i}else{s.scrollTop(1);var o=s.scrollTop()>0;s.scrollTop(0);if(o){return i}}}return[]}var r=e(this),i,s,u,a,f,l,c;n.switchPosition=="before"?(e.fn.findSibling=e.fn.prev,e.fn.insrt=e.fn.before):(e.fn.findSibling=e.fn.next,e.fn.insrt=e.fn.after);if(this.id.length){f="#"+this.id}else if(this.className.length){f=this.tagName.toLowerCase()+"."+this.className.split(" ").join(".")}else{f=this.tagName.toLowerCase()}if(n.ref&&r.find(n.ref).length){n.switchPosition=="before"?i=r.find("'"+n.ref+":first'"):i=r.find("'"+n.ref+":last'")}else{return}if(n.cllpsLength&&r.closest(f).find(n.cllpsEl).text().length<n.cllpsLength){r.closest(f).find(n.cllpsEl).addClass("dont_touch");return}n.initTxt=="show"?(l=n.expTxt,c=""):(l=n.cllpsTxt,c="open");if(n.state=="hidden"){r.find(n.cllpsEl+":not(.shown, .dont_touch)").hide().findSibling().find("> a.open").removeClass("open").data("state",0)}else{r.find(n.cllpsEl).show().findSibling().find("> a").addClass("open").data("state",1)}n.oneSwitch?i.insrt('<p class="switch"><a href="#" class="'+c+'">'+l+"</a></p>"):i.insrt('<p class="switch"><a href="#" class="">'+n.expTxt+'</a> | <a href="#" class="open">'+n.cllpsTxt+"</a></p>");s=i.findSibling("p").find("a");u=r.closest(f).find(n.cllpsEl).not(".dont_touch");a=n.trigger?r.closest(f).find(n.trigger+" > a"):r.closest(f).find(".expand > a");if(n.child){r.find(n.cllpsEl+".shown").show().findSibling().find("> a").addClass("open").text(n.cllpsTxt);window.$vrbls={kt1:n.expTxt,kt2:n.cllpsTxt}}var h;typeof d=="function"?h=d("html","body"):h="html, body";s.click(function(){var t=e(this),r=t.closest(f).find(n.cllpsEl+":first"),i=r.offset().top-n.offset;if(n.parent){var s=t.parent().nextAll().children("p.switch").find("a");kidTxt1=$vrbls.kt1,kidTxt2=$vrbls.kt2,kidTxt=t.text()==n.expTxt?kidTxt2:kidTxt1;s.text(kidTxt);if(t.text()==n.expTxt){s.addClass("open")}else{s.removeClass("open")}}if(t.text()==n.expTxt){if(n.oneSwitch){t.text(n.cllpsTxt).attr("class","open")}a.addClass("open").data("state",1);u[n.showMethod](n.speed)}else{if(n.oneSwitch){t.text(n.expTxt).attr("class","")}a.removeClass("open").data("state",0);if(n.speed==0||n.instantHide){u.hide()}else{u[n.hideMethod](n.speed)}if(n.scroll&&i<e(window).scrollTop()){e(h).animate({scrollTop:i},600)}}return false});if(n.localLinks){var p=e(f).find(n.localLinks);if(p.length){e(p).click(function(){var t=e(this.hash);t=t.length&&t||e("[name="+this.hash.slice(1)+"]");if(t.length){var n=t.offset().top;e(h).animate({scrollTop:n},600);return false}})}}})};e.fn.expandAll.defaults={state:"hidden",initTxt:"show",expTxt:"[Expand All]",cllpsTxt:"[Collapse All]",oneSwitch:true,ref:".expand",switchPosition:"before",scroll:false,offset:20,showMethod:"slideDown",hideMethod:"slideUp",speed:600,cllpsEl:".collapse",trigger:".expand",localLinks:null,parent:false,child:false,cllpsLength:null,instantHide:false};e.fn.toggler=function(t){var n=e.extend({},e.fn.toggler.defaults,t);var r=e(this);r.wrapInner('<a style="display:block" href="#" />');if(n.initShow){e(n.initShow).addClass("shown")}r.next(n.cllpsEl+":not(.shown)").hide();return this.each(function(){var t;n.container?t=n.container:t="html";if(r.next(".shown").length){r.closest(t).find(".shown").show().prev().find("a").addClass("open")}e(this).click(function(){e(this).find("a").toggleClass("open").end().next(n.cllpsEl)[n.method](n.speed);return false})})};e.fn.toggler.defaults={cllpsEl:".collapse",method:"slideToggle",speed:"slow",container:"",initShow:".shown"};e.fn.fadeToggle=function(e,t){return this.animate({opacity:"toggle"},e,function(){if(jQuery.browser.msie){this.style.removeAttribute("filter")}if(jQuery.isFunction(t)){t()}})};e.fn.slideFadeToggle=function(e,t,n){return this.animate({opacity:"toggle",height:"toggle"},e,t,function(){if(jQuery.browser.msie){this.style.removeAttribute("filter")}if(jQuery.isFunction(n)){n()}})};e.fn.slideFadeDown=function(e,t){return this.animate({opacity:"show",height:"show"},e,function(){if(jQuery.browser.msie){this.style.removeAttribute("filter")}if(jQuery.isFunction(t)){t()}})};e.fn.slideFadeUp=function(e,t){return this.animate({opacity:"hide",height:"hide"},e,function(){if(jQuery.browser.msie){this.style.removeAttribute("filter")}if(jQuery.isFunction(t)){t()}})}})(jQuery)



/*	--------------------------------------------------
    :: Placeholder
    -------------------------------------------------- */

//TODO : Remover
//$('input[placeholder], textarea[placeholder]').placeholder(); 

(function(b){function d(a){this.input=a;a.attr("type")=="password"&&this.handlePassword();b(a[0].form).submit(function(){if(a.hasClass("placeholder")&&a[0].value==a.attr("placeholder"))a[0].value=""})}d.prototype={show:function(a){if(this.input[0].value===""||a&&this.valueIsPlaceholder()){if(this.isPassword)try{this.input[0].setAttribute("type","text")}catch(b){this.input.before(this.fakePassword.show()).hide()}this.input.addClass("placeholder");this.input[0].value=this.input.attr("placeholder")}},
hide:function(){if(this.valueIsPlaceholder()&&this.input.hasClass("placeholder")&&(this.input.removeClass("placeholder"),this.input[0].value="",this.isPassword)){try{this.input[0].setAttribute("type","password")}catch(a){}this.input.show();this.input[0].focus()}},valueIsPlaceholder:function(){return this.input[0].value==this.input.attr("placeholder")},handlePassword:function(){var a=this.input;a.attr("realType","password");this.isPassword=!0;if(b.browser.msie&&a[0].outerHTML){var c=b(a[0].outerHTML.replace(/type=(['"])?password\1/gi,
"type=$1text$1"));this.fakePassword=c.val(a.attr("placeholder")).addClass("placeholder").focus(function(){a.trigger("focus");b(this).hide()});b(a[0].form).submit(function(){c.remove();a.show()})}}};var e=!!("placeholder"in document.createElement("input"));b.fn.placeholder=function(){return e?this:this.each(function(){var a=b(this),c=new d(a);c.show(!0);a.focus(function(){c.hide()});a.blur(function(){c.show(!1)});b.browser.msie&&(b(window).load(function(){a.val()&&a.removeClass("placeholder");c.show(!0)}),
a.focus(function(){if(this.value==""){var a=this.createTextRange();a.collapse(!0);a.moveStart("character",0);a.select()}}))})}})(jQuery);

function printdiv(printpage) {
    var headstr = "<html><head><title></title></head><body>";
    var footstr = "</body>";
    var newstr = document.all.item(printpage).innerHTML;
    var oldstr = document.body.innerHTML;
    document.body.innerHTML = headstr + newstr + footstr;
    window.print();
    document.body.innerHTML = oldstr;
    return false;
}

function habilitarConfirmaRecusa(idTextBox) {
    var texto = $("#" + idTextBox + "").val();
    texto = $.trim(texto);
    if (texto.length > 0)
        $("#btnEnviarJust").button("enable");
    else
        $("#btnEnviarJust").button("disable");
}


