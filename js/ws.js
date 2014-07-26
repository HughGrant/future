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
		$('#allTabs').show();
		return false;
	} else if (msg.indexOf('id:') !== -1) {
		var aid = msg.split(':')[1];
		copytr.attr('aid', aid);
		alert('Aid Got' + aid);
		return false;
	}
	alert(message);
}

$(function(){
    $('#quit').click(function () {
        if (ws.readyState === 1) {
			ws.send('quit');
		} else {
			console.log('WebSocket error or aid not exist');
		}
    });

    $('#add_more_object').click(function () {
        // var inputs = $(this).parents('form').find('input');
        // $.each(inputs, function(i, obj) {
        //     $(obj).after(obj.outerHTML);
        // });
        var inputs = $(this).parents('form').find('div[class="form-group"]');
        var html = '<hr>';
        $.each(inputs, function(i, obj) {
            if (i < 4) {
                html += obj.outerHTML;
            };
        });
        var p = $(this).parents('form').find('div[class="form-group"]:eq(3)');
        p.after(html);
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
        })
        return false;
    });

    $(document).on('click', '.uniChange', function () {
        var pid = get_pid(this);
        var uni = $(this);
        var action = uni.attr('action');
        $('#uniForm input[name=pid]').val(pid);
        $('#uniForm input[name=action]').val(action);
        $('#uniModal h4').html(uni.text());
        $('#uniModal').modal();
    });

    $('#uniForm').submit( function () {
		var info = $(this).serializeObject();
        $.post(info.action, info, function (data) {
            $('#uniModal').modal("hide");
            alert(data);
        });
        return false;
    });

	$(document).on('click', '.deleteProduct', function () {
		var pid = get_pid(this);
		var tr = $(this).parents('tr');
		$.post('/delete_product', {'pid':pid}, function (data) {
			if (data.ok) {
				tr.remove();
			} else {
				alert('delete product error');
			}
		});
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

	$(document).on('click', '.copyProduct', function () {
		if (!logged) {
			alert('Need to Login');
			return false;
		}

		var aid = get_aid(this);
		var keywords = get_kws(this);
		var pname = get_pname(this);
		var cmd = 'cp<>' + aid + '<>' + keywords;
		$.post('/check_product_name', {'product_name':pname}, function (count) {
			if (parseInt(count) > 0) {
				if (ws.readyState === 1 && aid) {
					ws.send(cmd);
				} else {
					console.log('WebSocket error or aid not exist');
				}
			} else {
				alert('collect names first');
			}
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

	$(document).on('click', '.uploadProduct', function () {
		if (!logged) {
			alert('Need to Login');
			return false;
		}
		var pid = get_pid(this);
		$.post('/check_keyword', {'pid':pid}, function (data) {
			if (ws.readyState !== 1) {
				alert('WebSocket error');
				return false;
			}
			if (parseInt(data) > 0) {
				ws.send('up ' + pid);
			} else {
				// collect key words
				ws.send('ck ' + keywords);
			}
		});
	});

	$(document).on('click', '.productID', function () {
		if (get_aid(this)) {
			alert('Already have aid');
			return false;
		}

		if (!logged) {
			alert('Need to Login');
			return false;
		}

		var product_name = get_pname(this);
		var product_id = get_pid(this);
		copytr = $(this).parents('tr');

		if (ws.readyState === 1) {
			ws.send('id<>' + product_name + '<>' + product_id);
		} else {
			alert('WebSocket error');
		}
	});

	$(document).on('click', '.logBtn', function () {
		var email = $(this).attr('email');
		var password = $(this).attr('password');
		var cmd = ['login', email, password].join('<>');
		if (ws.readyState === 1) {
            $.post('/set_db', {'email':email});
			ws.send(cmd);
            $(this).siblings('.logBtn').not(this).remove();
		} else{
			console.log('WebSocket error')
		}
	});
});
