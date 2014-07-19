var ws = new WebSocket('ws://127.0.0.1:9000')
var logged = false;
var product_id = null;
var copytr = null;

function get_pid (ele) {
	return $(ele).parents('tr').attr('pid');
}

function get_kws (ele) {
	return $(ele).parents('tr').attr('kws');
}

function get_pname (ele) {
	return $(ele).parents('tr').attr('pname');
}

function get_aid (ele) {
	return $(ele).parents('tr').attr('aid');
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
	console.log(message);
	var msg = message.data;

	if (msg == 'login success') {
		logged = true;
		$('#logForm').hide();
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
	$('#logForm').submit(function () {
		var ap = $(this).serializeObject();
		$.post('/set_account', ap, function (html) {
			if (html) {
				$('#logBtnGroup').append(html);
			} else {
				alert('Already exist');
			}
		});
		return false;
	});
    // create a customer info with shipping address
    $('#customerInfoForm').submit(function () {
		var info = $(this).serializeObject();
        $.post('/customer', info, function (html) {
            console.log(html); 
        });
        return false;
    });

	// upload product to mongodb
	$('#uploadForm').submit(function () {
		var info = $(this).serializeObject();
		var number = $('tr').length;
		info['index'] = number
		$.post('/product', info, function (html) {
			$('#productTable').prepend(html);
			$('input[name="url"]').val('');
		});
		return false;
	});

	$('#skwl').keydown(function (event) {
		if(13 === event.keyCode) {
			$.post('/add_keywords', {'key_words':$(this).val()}, function (data) {
				alert(data.ok);
			});
		}
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

	$('#nkw').keydown(function (event) {
		if (13 === event.keyCode) {
			var pid = $('#nkw').attr('pid');
			var kws = $('#nkw').val();
			data = {'key_words':kws, 'pid':pid};
			$.post('/change_key_words', data, function (data) {
				if (data.success) {
					$('tr[pid="' + pid + '"]').remove();
					$('#ckwModal').modal('toggle');
				}
			});
		}
	})
	
	$(document).on('click', '.changeKW', function () {
		$('#nkw').val(get_kws(this));
		$('#nkw').attr('pid', get_pid(this));
	});

	$(document).on('click', '.showKW', function () {
		var keywords = get_kws(this);
		$.post('/list_key_words', {'key_words':keywords}, function (html) {
			$('#kwt').html(html);
			$('#skwl').val(keywords + ':');
			$('#myTab li:eq(1) a').tab('show');
		});
	});

	$(document).on('click', '#getKWS', function () {
		var keywords = $('#skwl').val();
		$.post('/list_key_words', {'key_words':keywords}, function (html) {
			$('#kwt').html(html);
		});
	});

	$(document).on('click', '.uploadProduct', function () {
		if (!logged) {
			alert('Need to Login');
			return false;
		}
		var keywords = get_kws(this);
		var pid = get_pid(this);
		$.post('/check_keyword', {'keywords':keywords}, function (data) {
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

	$(document).on('click', '.reRichDesc', function () {
		var pid = get_pid(this);
		$.post('/rich', {'pid':pid}, function (data) {
			alert(data.ok);
		});
	});

	$(document).on('click', '.selectCategory', function () {
		var keywords = $(this).text();
		$.post('/list_product_by_kw', {'keywords':keywords}, function (html) {
			$('input[name="key_words"]').val(keywords);
			$('#productTable').html(html);
		});
	});
	// alter product name 
	$(document).on('click', '.changeProductName', function () {
		var pid = get_pid(this);
		var product_name = $(this).parent().siblings('input').val();

		$.post('/change_product_name', {'product_name':product_name,'pid':pid}, function (data) {
			alert(data.ok);
		});
	});
	// collect product variant names
	$(document).on('click', '.collectProductName', function () {
		var product_name = $(this).parent().siblings('input').val();
		$.post('/collect_variant_names', {'product_name':product_name}, function (data) {
			alert(data.ok);
		});
	});

	$(document).on('click', '.kwRemove', function () {
		var span = $(this).parent();
		var keywords = span.text();

		$.post('/remove_keywords', {'keywords':keywords}, function (data) {
			if (data.ok) {
				span.remove();
			}
		});
		return false;
	});

	$(document).on('click', '.logBtn', function () {
		var email = $(this).attr('email');
		var password = $(this).attr('password');
		var cmd = ['login', email, password].join('<>');
		if (ws.readyState === 1) {
			ws.send(cmd);
		} else{
			console.log('WebSocket error')
		}
	});
});
