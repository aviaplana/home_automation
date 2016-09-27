$(document).foundation();

var socket = io.connect();

socket.on('message', function(data) {
    console.log(data.message);
});

socket.on('initial', function(data) {
  var values = data.values;
  console.log(data);

  var rslider = new Foundation.Slider($("#rSlider"));
  rslider._setHandlePos($("#rHandle"), values.r);

  var gslider = new Foundation.Slider($("#gSlider"));
  gslider._setHandlePos($("#gHandle"), values.g);

  var bslider = new Foundation.Slider($("#bSlider"));
  bslider._setHandlePos($("#bHandle"), values.b);

  $("#fade").val(values.t_dim);
  $("#flick").val(values.ms_flick);
});



$('#toggle').click(function() {
  socket.emit('message', {'message': 'rgbToggle'});
});

$('#on').click(function() {
  socket.emit('message', {'message': 'rgbOn'});
});

$('#off').click(function() {
  socket.emit('message', {'message': 'rgbOff'});
});

$("#flick").change(function(e) {
  socket.emit('message', {'message': 'rgbFlick',
                          'values': {'ms_flick': e.target.value}
                        });
});

var red = $("#red");
var green = $("#green");
var blue = $("#blue");
var fade = $("#fade");

function sendValues() {
  var vals = {'r': red.value,
              'g': green.value,
              'b': blue.value,
              't_dim': fade.val(),
              //'ms_flick': $('#flick').val(),
              };
  socket.emit('message', {'message': 'rgbChange', 'values': vals});
}

fade.change(function() {
  sendValues();
})

$('.slider').on('moved.zf.slider', function() {
  sendValues();
});
