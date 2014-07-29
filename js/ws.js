var ws = new WebSocket('ws://127.0.0.1:9000')
var logged = false;
var product_id = null;
var copytr = null;

function get_pid (ele) {
	return $(ele).parents('tr').attr('pid');
}

$.fn.serializeObject = function()
{
   var o = {};
   var a = this.serializeArray();
   $.each(a, function() {
       if (o[this.name]) {
           if (!o[this.name].push) {
               o[this.name] = [o[this.name]];
           }
           o[this.name].push(this.value || '');
       } else {
           o[this.name] = this.value || '';
       }
   });
   return o;
};

ws.onmessage = function (message) {
	var msg = message.data;
	console.log(msg);
	if (msg == 'login success') {
		logged = true;
	}
    alert(msg);
}

$(function(){
    $('#quit').click(function () {
        $(this).siblings('.logBtn').not(this).show();
        if (ws.readyState === 1) {
			ws.send('quit');
		} else {
			console.log('WebSocket error or aid not exist');
		}
    });

    $(document).on('click', '.createOrder', function () {
        var pid = get_pid(this);
        $('input[name=customer_id]').val(pid); 
        $('a[href="#order"').tab('show');
    });


    $(document).on('click', '.uniDelete', function () {
        var _id = get_pid(this);
        var ele = $(this);
        var action = ele.attr('action');
        var collection = ele.attr('collection');
        var tr = ele.parents('tr');
        data = {'_id':_id, 'collection':collection} 
        $.post(action, data).done(function (msg) {
            if (msg == 'success') {
                tr.remove()
            }
        });
    });

    $(document).on('click', '.uniOrder', function () {
        var pid = get_pid(this);
        var uni = $(this);
        var action = uni.attr('action');
        var data ={'pid':pid}
         
        $.post(action, data, function (msg) {
            alert(msg);
        });
    });

    $(document).on('submit', '.uniCreate', function () {
        var form = $(this);
        var action = form.attr('action');
        var data = form.serializeObject();
        var tableId = form.attr('tid');
        $.post(action, data).done(function (html) {
            $('#'+tableId).prepend(html);
            form[0].reset();
        }).fail(function (msg) {
            console.log(msg);
            alert(msg.responseText);
        });
        return false;
    });

    $(document).on('click', '.uniChange', function () {
        var pid = get_pid(this);
        var uni = $(this);
        var prop_name = uni.attr('prop_name');
        $('#uniForm input[name=pid]').val(pid);
        $('#uniForm input[name=prop_name]').val(prop_name);
        $('#uniModal h4').html(uni.text());
        $('#uniModal').modal();
    });

    $('#uniForm').submit(function () {
		var info = $(this).serializeObject();
        $.post('/common_alter', info, function (data) {
            $('#uniModal').modal("hide");
            alert(data);
        });
        return false;
    });

	$(document).on('click', '.uniws', function () {
        var action = $(this).attr('action');
        var pid = get_pid(this);
        if (ws.readyState === 1 && pid) {
            console.log(pid);
			ws.send(action + '<>' + pid);
		} else {
			console.log('WebSocket error or aid not exist');
		}
    });

	$(document).on('click', '.showPanel', function () {
        var replace_id = '#' + $(this).attr('replace_id');
        var action = '/' + $(this).attr('action');

        $.post(action).done(function (html) {
            $(replace_id).html(html);
        });
    });

	$(document).on('click', '.showKeyword', function () {
        var pid = get_pid(this);
        var action = $(this).attr('action');
		$.post(action, {'pid':pid}, function (html) {
			$('#kwt').html(html);
			$('a[href="#profile"]').tab('show');
		});
	});

    $(document).on('click', '.selectKeyword', function () {
        var kw = $(this).text();
        $.post('/list_keywords', {'keyword':kw}, function (html) {
            $('#kwt').html(html);
        })
    });

    $(document).on('click', '.selectCategory', function () {
        var cn = $(this).text();
        $.post('/list_products', {'category_name':cn}, function (html) {
            $('#productTable').html(html);
        })
    });

	$(document).on('click', '.uniws', function () {
		if (!logged) {
			alert('Need to Login');
			return false;
		}

		var pid = get_pid(this);
        var cmd = $(this).attr('action') + '<>' + pid;
        
		if (ws.readyState === 1) {
            ws.send(cmd);
		} else {
			alert('WebSocket error:' + cmd);
		}
	});

	$(document).on('click', '.logBtn', function () {
		var email = $(this).attr('email');
		var password = $(this).attr('password');
		var cmd = ['login', email, password].join('<>');
        $(this).siblings('.logBtn').not(this).hide();
        $.post('/set_db', {'email':email}, function () {
		    $('#allTabs').show();
            if (ws.readyState === 1) {
                ws.send(cmd);
            } else {
                console.log('WebSocket error')
            }
        });
		
	});
});
