//var exports = module.exports = {};

var current_vals = {
  r: 0,
  g: 0,
  b: 0,
  ms_flick: 0,
  t_dim: 0,
  on: false
};

function Packet(id, weight) {
    if (typeof id === "undefined") return;
    this.id = id
    this.weight = weight;
    this.startBits = '\\B';
    this.endBits = '\\E';

    return true;
}

function RGBPacket(id) {
    if (!Packet.call(this, id, 8)) return;
}

RGBPacket.prototype = Object.create(Packet.prototype);
RGBPacket.prototype.constructor = RGBPacket;

RGBPacket.prototype.turnOn = function() {
    this.instruction = 2;
}

RGBPacket.prototype.turnOff = function() {
    this.instruction = 3;
}

RGBPacket.prototype.toggle = function() {
    this.instruction = 4;
}

RGBPacket.prototype.getCurrent = function() {
    this.instruction = 20;
}

RGBPacket.prototype.getStored = function() {
    this.instruction = 21;
}

RGBPacket.prototype.packetConfirmed = function() {
  switch (this.instruction === 3) {
    case 0:
      current_vals.r = this.r;
      current_vals.g = this.g;
      current_vals.b = this.b;
      current_vals.t_dim = this.t_dim;
      break;

    case 2:
      current_vals.on = true;
      break;

    case 3:
      current_vals.on = false;
      break;

    case 4:
      current_vals.on != current_vals.on;
      break;

    case 10:
      current_vals.ms_flick = this.ms_flick;
      break;

    default:
      break;
  }
}

RGBPacket.prototype.processDefault = function(values) {
    if (typeof values.r !== "undefined" &&
        typeof values.g !== "undefined" &&
        typeof values.b !== "undefined" &&
        typeof values.t_dim !== "undefined" &&
        typeof values.ms_flick !== "undefined") {

        this.r = values.r;
        this.g = values.g;
        this.b = values.b;
        this.t_dim = values.t_dim;
        this.ms_flick = values.ms_flick;
        this.instruction = 1;
    } else {
        return;
    }
}

RGBPacket.prototype.processPacket = function(values) {
    if (typeof values.r !== "undefined" &&
        typeof values.g !== "undefined" &&
        typeof values.b !== "undefined") {

        this.r = values.r;
        this.g = values.g;
        this.b = values.b;

        if (typeof values.t_dim !== "undefined") {
            this.t_dim = values.t_dim;
        } else {
            this.t_dim = 0;
        }

        if (typeof values.ms_flick !== "undefined") {
            this.ms_flick = values.ms_flick;
            this.instruction = 0;
        } else {
            this.instruction = 10;
        }
    } else if (typeof values.ms_flick !== "undefined") {
        this.ms_flick = values.ms_flick;
        this.instruction = 11;
    } else {
        return;
    }
}

/*
 *  Packet structure:
 *  | \B | Type | Payload | \E |
 *     2    1       ?        2    Bytes
 *
 *  RGBStrip payload structure:
 *  | id | r | g | b | is_on | reserved | instruction | ms_flick | t_dim |
 *  |    |   |   |   |  1 bit|    1 bit |      6 bits |          |       |
 *    1    1   1   1              1                       2         2      Bytes
 */
RGBPacket.prototype.interpreteSerialBuffer = function(buffer) {
  var instruction = buffer.readUInt8(7);
  // First two bits of the byte are used for the on/off state and reserved
  instruction &= 0x3F;
  this.instruction = instruction;
  if (instruction === 20) {
    current_vals.r = buffer.readUInt8(4);
    current_vals.g = buffer.readUInt8(5);
    current_vals.b = buffer.readUInt8(6);

    if ((buffer[7] >> 7) == 1) {
      current_vals.on = true;
    } else {
      current_vals.on = false;
    }

    current_vals.ms_flick = buffer.readUInt16LE(8);
    current_vals.t_dim = buffer.readUInt16LE(10);
  }
}

RGBPacket.prototype.getBuffer = function() {
  buffer = Buffer.alloc(14);
  buffer.writeUInt8(this.id, 2);    // destination id
  buffer.writeUInt8(0, 3);    // sender id
  buffer.writeUInt8(this.r, 4);    //r
  buffer.writeUInt8(this.g, 5);    //g
  buffer.writeUInt8(this.b, 6);  //b
  buffer.writeUInt8(this.instruction, 7);    //instruction
  buffer.writeUInt16LE(this.ms_flick, 8); //ms_flick
  buffer.writeUInt16LE(this.t_dim, 10); //t_dim
  buffer.write(this.endBits, 12);
  buffer.write(this.startBits, 0);

  return buffer;
}

RGBPacket.prototype.getCurrentValues = function() {
  return current_vals;
}

exports.RGBPacket = RGBPacket;
