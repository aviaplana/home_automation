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

  switch (parsedURL.pathname) {
    case '/':
      fs.readFile('public/html/index.html', function (err, content) {
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
});



server.listen(SERVER_PORT);
var listener = io.listen(server);

listener.on('connection', function(connection) {
  console.log('[WS] New connection');

  arduino.rgbRequestCurrent(0);
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
    console.log('[WS] Received message from client');
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
    //console.log(data.message);
  });
});





console.log('Up, running and ready for action!!!');

      /*
        case '/api/strip/change':
            if (req.method === 'POST') {
                // Extract the data sorted in the POST body
                var body = '';
                req.on('data', function (dataChunk) {
                    body += dataChunk;
                });

                req.on ('end', function () {
                    // Done pulling data from the Post body.
                    // Turn it into JSON and proceed to store it in the database.
                    if (body != '') {

                        var postJSON = JSON.parse(body); //prevent parse error

                        var rgbpacket = new packets.RGBPacket(postJSON.id);
                        rgbpacket.processPacket(postJSON);

                        if (Object.keys(rgbpacket).length) {
                            sp.sendStripPacket(rgbpacket, req, res);
                        } else {
                            res.writeHead(400, {});
                            res.end('All mandatory fields must be provided');
                        }
                    } else {
                        res.writeHead(400, {});
                        res.end('All mandatory fields must be provided');
                    }
                });
            } else {
                res.writeHead(405, {});
                res.end();
            }
        break;

        case '/api/strip/on':
            if (req.method === 'POST') {
                var body = '';
                req.on('data', function (dataChunk) {
                    body += dataChunk;
                });

                req.on ('end', function () {
                    if (body != '') {
                        var postJSON = JSON.parse(body); //prevent parse error
                        console.log(postJSON);
                        var rgbpacket = new packets.RGBPacket(postJSON.id);

                        rgbpacket.turnOn();
                        sp.sendStripPacket(rgbpacket, req, res);
                    } else {
                        res.writeHead(400, {});
                        res.end('All mandatory fields must be provided');
                    }
                });

            } else {
                res.writeHead(405, {});
                res.end();
            }
        break;

        case '/api/strip/off':
            if (req.method === 'POST') {
                var body = '';
                req.on('data', function (dataChunk) {
                    body += dataChunk;
                });

                req.on ('end', function () {
                    if (body != '') {
                        var postJSON = JSON.parse(body); //prevent parse error
                        var rgbpacket = new packets.RGBPacket(postJSON.id);

                        rgbpacket.turnOff();
                        sp.sendStripPacket(rgbpacket, req, res);
                    } else {
                        res.writeHead(400, {});
                        res.end('All mandatory fields must be provided');
                    }
                 });
            } else {
                res.writeHead(405, {});
                res.end();
            }

        break;

        case '/api/strip/toggle':
            if (req.method === 'POST') {
                var body = '';
                req.on('data', function (dataChunk) {
                    body += dataChunk;
                });

                req.on ('end', function () {
                    if (body != '') {
                        var postJSON = JSON.parse(body); //prevent parse error
                        var rgbpacket = new packets.RGBPacket(postJSON.id);

                        rgbpacket.toggle();
                        sp.sendStripPacket(rgbpacket, req, res);
                    } else {
                        res.writeHead(400, {});
                        res.end('All mandatory fields must be provided');
                    }
                 });
            } else {
                res.writeHead(405, {});
                res.end();
            }
        break;

        case '/api/strip/getCurrent':
            if (req.method === 'POST') {
                var body = '';
                req.on('data', function (dataChunk) {
                    body += dataChunk;
                });

                req.on ('end', function () {
                    if (body != '') {
                        var postJSON = JSON.parse(body); //prevent parse error
                        var rgbpacket = new packets.RGBPacket(postJSON.id);

                        rgbpacket.getCurrent();
                        sp.sendStripPacket(rgbpacket, req, res);
                    } else {
                        res.writeHead(400, {});
                        res.end('All mandatory fields must be provided');
                    }
                 });
            } else {
                res.writeHead(405, {});
                res.end();
            }
        break;

        case '/api/strip/getStored':
            if (req.method === 'POST') {
                var body = '';
                req.on('data', function (dataChunk) {
                    body += dataChunk;
                });

                req.on ('end', function () {
                    if (body != '') {
                        var postJSON = JSON.parse(body); //prevent parse error
                        var rgbpacket = new packets.RGBPacket(postJSON.id);

                        rgbpacket.getStored();
                        sp.sendStripPacket(rgbpacket, req, res);
                    } else {
                        res.writeHead(400, {});
                        res.end('All mandatory fields must be provided');
                    }
                 });
            } else {
                res.writeHead(405, {});
                res.end();
            }
        break;

        default:
            res.writeHead(404, {});
            res.end('You shall not pass!!!!');
        break;

    }

});
*/
