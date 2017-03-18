import logging
import bluetooth
import binascii
import constants
import datetime

logging.basicConfig(level=logging.DEBUG)

class AuraBulb(object):
    def __init__(self, address, port=4):
        self._address = address
        self._port = port
        self._connect()

    def _connect(self):
        self._sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM )
        self._sock.connect((self._address, self._port))
        self._sock.recv(4096) # swallow hello message

    def _send(self, msg):
        self._sock.send(msg)
        return(self._sock.recv(4096))

    def toggle_light(self):
        """
        Does what it says on the tin.  Will either set level to 0 or what
        it was last time the bulb was on
        """

        msg = AuraBulb.encode(constants.SPP_LIGHT_TURN_ON_OFF)
        r = AuraBulb.decode(self._send(msg))
        logging.debug("Got: %s", r)

    def get_light_level(self):
        """
        Return the light level as a value between 0 and 210
        """
        msg = AuraBulb.encode(constants.SPP_LIGHT_CURRENT_LEVEL)
        r = AuraBulb.decode(self._send(msg))
        
        logging.debug("Got: %s", r)
        if r['type'] != 'lightlevel':
            # XXX error out
            pass
        return int(r['level'].encode('hex'), 16)

    def set_light_level(self, level):
        """Set light level to level.  Valid values are between 0 and 210"""
        msg = AuraBulb.encode(constants.SPP_LIGHT_ADJUST_LEVEL,[level])
        r = self._send(msg)
        k = AuraBulb.decode(r)
        logging.debug("Got: %s", k)

    def get_light_color(self):
        """
        Return the light colour

        Doesn't work for me with an aurabulb
        """
        msg = AuraBulb.encode(constants.SPP_LIGHT_GET_COLOR)
        r = self._send(msg)
        k = AuraBulb.decode(r)
        logging.debug("Got: %s", r.encode('hex'))

    def set_light_color(self, red, green, blue):
        # XXX: typecheck rgb to be single-byte values
        msg = AuraBulb.encode(constants.SPP_COLOR_ADJUST, [red, green, blue])
        r = self._send(msg)
        k = AuraBulb.decode(r)
        logging.debug("Got: %s", r.encode('hex'))

    def set_light_mode(self, mode):
        # XXX: typecheck mode to be 1..5
        msg = AuraBulb.encode(constants.SPP_LIGHT_SET_MODE, [mode])
        r = self._send(msg)
        k = AuraBulb.decode(r)
        logging.debug("Got: %s", r.encode('hex'))

    def get_voltage(self):
        msg = AuraBulb.encode(constants.SPP_GET_VOLTAGE)
        r = self._send(msg)
        k = AuraBulb.decode(r)
        logging.debug("Got: %s", r.encode('hex'))
        return int(k['level'].encode('hex'), 16)

    def set_time(self, dt):
        century = dt.year / 100
        decicentury = dt.year % 100
        msg = AuraBulb.encode(constants.SPP_SET_SYSTEM_TIME,
                              [decicentury & 0xff,
                               century & 0xff,
                               dt.month & 0xff,
                               dt.day & 0xff,
                               dt.hour & 0xff,
                               dt.minute & 0xff,
                               dt.second & 0xff,
                               (dt.isoweekday()-1) & 0xff])
        r = self._send(msg)
        k = AuraBulb.decode(r)
        logging.debug("Got: %s", r.encode('hex'))

    def set_alarm_time(self, t, scene=1, enabled=True):
        en = 0
        if enabled:
            en = 1
        msg = AuraBulb.encode(constants.SPP_SET_ALARM_TIME_SCENE,
                              [t.hour & 0xff, t.minute & 0xff,
                               scene, en])
        r = self._send(msg)
        k = AuraBulb.decode(r)
        logging.debug("Got: %s", r.encode('hex'))
        return k

    
    def get_alarm_time(self):
        msg = AuraBulb.encode(constants.SPP_GET_ALARM_TIME_SCENE)
        r = self._send(msg)
        k = AuraBulb.decode(r)
        logging.debug("Got: %s", r.encode('hex'))
        return k

    @staticmethod
    def encode(command, data=None):
        if data is None:
            cmd = bytearray('\x00' * 7)
        else:
            cmd = bytearray('\x00' * (7 + len(data)))

        cmd[0] = 1;
        cmd[1] = (len(cmd) - 4) & 0xff
        cmd[2] = ((len(cmd) - 4) >> 8) & 0xff
        cmd[3] = int(command) & 0xff
        if data is not None:
            cmd[4:4+len(data)] = data

        checksum = 0
        for i in cmd[1:-2]:
            checksum = (checksum + (i & 0xff)) & 0xffff
        
        cmd[-3] = checksum & 0xff
        cmd[-2] = (checksum >> 8) & 0xff
        cmd[-1] = 2

        logging.debug("cmd is %s", binascii.hexlify(cmd))

        sendcmd = bytearray('\x00' * (len(cmd) * 2))
        count = 1
        sendcmd[0] = 1
        logging.debug("cmd[1:] is %s", binascii.hexlify(cmd[1:]))
        for i in cmd[1:-1]:
            logging.debug("looking at %x", i)
            i2 = count + 1
            if i == 1:
                sendcmd[count] = 3
                count = i2 + 1
                sendcmd[i2] = 4
            elif i == 2:
                sendcmd[count] = 3
                count = i2 + 1
                sendcmd[i2] = 5
            elif i == 3:
                sendcmd[count] = 3
                count = i2 + 1
                sendcmd[i2] = 6
            else:
                logging.debug("count is %d, sendcmd is %s", count,
                              binascii.hexlify(sendcmd))
                sendcmd[count] = i
                count  = i2
        i2 = count + 1
        sendcmd[count] = 2;
        return str(sendcmd[:i2])

    @staticmethod
    def decode(buf):
        cmd = int(buf[4].encode('hex'), 16)
        if not AuraBulb.is_success(buf):
            logging.error("Not a success")
            return None
        if cmd == constants.SPP_GET_VOL:
            pass
        elif cmd == constants.SPP_GET_VOLTAGE:
            voltage = buf[6]
            logging.debug("Voltage: %s", voltage.encode('hex'))
            return {
                "type": "voltage",
                "level": voltage,
            }
        elif cmd == constants.SPP_LIGHT_CURRENT_LEVEL:
            lightlevel = buf[6]
            logging.debug("Light level: %s", lightlevel.encode('hex'))
            return {
                "type": "lightlevel",
                "level": lightlevel,
            }
        elif cmd == constants.SPP_GET_ALARM_TIME_SCENE:
            alarm_data = buf[6:10]
            logging.debug("alarm data: %s", binascii.hexlify(alarm_data))
            return {
                "type": "alarm_data",
                "hour":  h2b(alarm_data[0]),
                "minute": h2b(alarm_data[1]),
                "scene": h2b(alarm_data[2]),
                "enabled": (h2b(alarm_data[3]) != 0)
            }
#        elif cmd == '46': # get light mode
#            logging.debug("light_mode: %s", binascii.hexlify(buf[6:]))
        elif cmd == constants.SPP_LIGHT_GET_COLOR: # get light colour
            logging.debug("light_colour: %s", binascii.hexlify(buf[6:]))
        else:
            logging.debug("unknown command %x: %s", cmd,
                          binascii.hexlify(buf[6:]))
        return buf[6:-1]

    @staticmethod
    def is_success(buf):
        if len(buf) < 6:
            logging.debug("too short")
            return False
        if buf[0].encode('hex') != '01':
            logging.debug("wrong prefix, got '%c'", buf[0])
            return False
        if buf[-1].encode('hex') != '02':
            logging.debug("wrong suffix")
            return False
        if buf[3].encode('hex') != '04':
            logging.debug("wrong spongebob: %s", buf[3].encode('hex'))
            return False
        if buf[5] != '\x55':
            logging.debug("not marked as success")
            return False
        return True

def h2b(c):
    """Decode a char as hex and then int it"""
    return int(c.encode('hex'), 16)
