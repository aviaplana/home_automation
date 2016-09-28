var http = require('http');
var URL = require('URL');
var io = require('socket.io');
var fs = require('fs');

var Arduino = require("./arduino");

var SERVER_PORT = 8080;
var connections = new Array;
var arduino = new Arduino();

var data;

var server = http.createServer(function (req, res) {
  // Break down the incoming URL into its components
  var parsedURL = URL.parse(req.url, true);
  console.log("[HTTP] New request " + parsedURL.pathname);

  if (req.url.indexOf('.js') != -1) {
    fs.readFile(__dirname + '/public/js' + parsedURL.pathname, function (err, data) {
      if (err) {
        console.log(err);
      }

      res.writeHead(200, {'Content-Type': 'text/javascript'});
      res.write(data);
      res.end();
    });
  } else if(req.url.indexOf('.css') != -1) {
    fs.readFile(__dirname + '/public/css' + parsedURL.pathname, function (err, data) {
      if (err) {
        console.log(err);
      }
      res.writeHead(200, {'Content-Type': 'text/css'});
      res.write(data);
      res.end();
    });
  } else {
    switch (parsedURL.pathname) {
      case '/':
        fs.readFile(__dirname + '/public/html/index.html', function (err, content) {
          if (err) {
            res.writeHead(500);
            res.end();
          } else {
            res.writeHead(200, {'Content-Type': 'text/html'});
            res.end(content, 'utf-8');
          }
        });
        /*var rgbpacket = arduino.createRGBPacket(0);
        rgbpacket.getCurrent();
        arduino.sendStripPacket(rgbpacket, req, res);
        */
        break;
    };
  }
});



server.listen(SERVER_PORT);
var listener = io.listen(server);

listener.on('connection', function(connection) {
  console.log('[WS] New connection');

  arduino.rgbRequestCurrent(1);
  setTimeout(function() {
    connection.emit('initial', {'values': arduino.getCurrentStatus(1)});
  }, 200);

  connection.emit('message', {'message': 'Welcome!'});

  //connection.on('message', sendToSerial);

  connection.on('close', function() {
    console.log('[WS] Connection closed');
    var pos = connections.indexOf(client);
    connections.splice(pos, 1);
  });

  connection.on('message', function(data) {
    console.log('[WS] Received message from client: ' + data.message);
    
    if (data.message === "rgbToggle") {
      arduino.rgbToggle(1);
    } else if (data.message === "rgbChange") {
      arduino.rgbChange(1, data.values);
    } else if (data.message === "rgbFlick") {
      arduino.rgbFlick(1, data.values);
    } else if (data.message === "rgbOn") {
      arduino.rgbOn(1);
    } else if (data.message === "rgbOff") {
      arduino.rgbOff(1);
    }
  });
});

console.log('Up, running and ready for action!!!');
