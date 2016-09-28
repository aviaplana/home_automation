$(document).foundation();

var socket = io.connect();

var red = $("#red");
var green = $("#green");
var blue = $("#blue");
var fade = $("#fade");
var canchange = false;

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

  fade.val(values.t_dim);
  $("#flick").val(values.ms_flick);

  setEvents();
});


function sendValues() {
    var vals = {'r': red.val(),
                'g': green.val(),
                'b': blue.val(),
                't_dim': fade.val(),
                //'ms_flick': $('#flick').val(),
                };
console.log(vals);
    socket.emit('message', {'message': 'rgbChange', 'values': vals});
}

function setEvents() {

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


  fade.change(function() {
    sendValues();
  })

  $('.slider').on('moved.zf.slider', function() {
    if (canchange) {
      sendValues();
    }
  });
  //Prevent initial triggers.
  setTimeout(function() { canchange = true; }, 300);

}

fade.change(function() {
  sendValues();
})
