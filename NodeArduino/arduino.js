var serialport = require("serialport");
var packets = require("./packets");

var stripStatus;
var packetSent;
var toConfirm;
var lastSend;

function Arduino() {
  var portName;
  toConfirm = false;
  lastSend = 0;

  serialport.list(function(err, ports) {
    /*ports.forEach(function(port) {
      if (port.comName.indexOf('cu.wchusbserial') !== -1) {
        portName = port.comName;
      }
    });*/
    portName = '/dev/cu.wchusbserial1420';//'/dev/cu.usbserial-A7027D4F';
    //portName = '/dev/cu.usbserial-A7027D4F';

    this.myPort = new serialport(portName, {
        baudRate: 9600
    });

    this.myPort.on('open', function () {
        console.log('[SP] Open Connection with ' + portName);
    });

    this.myPort.on('close', function () {
        console.log('[SP] Connection with ' + portName + ' closed');
    });
        this.myPort.on('error', function () {
            console.log('[SP] ERROR ' + portName);
        });


    this.myPort.on('data', function(data) {
      var initSeq = data.toString().substring(0, 2);
/*      if (initSeq === '\\C') {
        if (data[2] === 1) {
          console.log('[SP] Confirmation received');
          toConfirm = false;
          packetSent.packetConfirmed();
        } else{
          console.log('[SP] Failed to send packet');
        }
      } else
*/

/*
 *  Packet structure:
 *  | \B | Type | ID | Payload | \E |
 *     2    1     1      ?        2    Bytes
 */
      if (initSeq === '\\B') {
        process.stdout.write("[SP] Got response packet from " + data[3] + ": ");
        console.log(data);

        // Type of packet
        switch (data[2]) {
          // Confirmation
          case 1:
            // Payload : 0 if not sent, 1 if sent
            if (data[4] === 1) {
              console.log('[SP] Confirmation received');
              toConfirm = false;
              packetSent.packetConfirmed();
            } else{
              console.log('[SP] Failed to send packet');
            }
            break;
          // RGBStrip
          case 10:
            var rgbpacket = new packets.RGBPacket();
            rgbpacket.interpreteSerialBuffer(data);
            break;

          default:
            break;
        }
      }
    })

  });
}

Arduino.prototype.getCurrentStatus = function (id) {
  if (typeof id === "undefined") {
    return;
  }

  switch (id) {
    case 1:
      var temp = new packets.RGBPacket();
      return temp.getCurrentValues();
      break;

    default:
      break;
  }
}

Arduino.prototype.sendStripPacket = function (strip_packet, req, res) {
  var date = new Date();
  var millis = date.getTime();

  if ((millis - lastSend) < 45) {
    return;
  } else if (toConfirm) {
    console.log('[SP] Confirmation timed out');
    toConfirm = false;
  }

  if (myPort.isOpen()) {
    this.gotData = false;
    myPort.write(strip_packet.getBuffer());

    packetSent = strip_packet;

    process.stdout.write('[SP] Sent ');
    console.log(strip_packet.getBuffer());
    lastSend = date.getTime();
    toConfirm = true;
  } else {
    console.log('[SP] ERROR: Not connected to Arduino.')
  }
}

Arduino.prototype.rgbRequestCurrent = function(id) {
  if (typeof id === "undefined") {
    return;
  }

  var pack = new packets.RGBPacket(id);
  pack.getCurrent();
  this.sendStripPacket(pack);
}

Arduino.prototype.rgbToggle = function(id) {
  if (typeof id === "undefined") {
    return;
  }

  var pack = new packets.RGBPacket(id);
  pack.toggle();
  this.sendStripPacket(pack);
}

Arduino.prototype.rgbOn = function(id) {
  if (typeof id === "undefined") {
    return;
  }

  var pack = new packets.RGBPacket(id);
  pack.turnOn();
  this.sendStripPacket(pack);
}

Arduino.prototype.rgbOff = function(id) {
  if (typeof id === "undefined") {
    return;
  }

  var pack = new packets.RGBPacket(id);
  pack.turnOff();
  this.sendStripPacket(pack);
}

Arduino.prototype.rgbChange = function(id, values) {
  if (typeof id === "undefined" ||
      typeof values.r === "undefined" ||
      typeof values.g === "undefined" ||
      typeof values.b === "undefined" ) {
    return;
  }

  var pack = new packets.RGBPacket(id);
  pack.processPacket(values);
  this.sendStripPacket(pack);
}

Arduino.prototype.rgbFlick = function(id, values) {
  console.log(values);
  if (typeof id === "undefined" ||
      typeof values.ms_flick === "undefined") {
    return;
  }

  var pack = new packets.RGBPacket(id);
  pack.processPacket(values);
  this.sendStripPacket(pack);
}

Arduino.prototype.createRGBPacket = function(id) {
  return new packets.RGBPacket(id);
}

Arduino.prototype.write = function(data) {
  myPort.write(data);
}

module.exports = Arduino;
