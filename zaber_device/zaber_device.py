# -*- coding: utf-8 -*-
from __future__ import print_function, division
import serial
import time
import atexit
import platform
import os
from exceptions import Exception

from serial_device2 import SerialDevice, SerialDevices, find_serial_device_ports, WriteFrequencyError

try:
    from pkg_resources import get_distribution, DistributionNotFound
    _dist = get_distribution('zaber_device')
    # Normalize case for Windows systems
    dist_loc = os.path.normcase(_dist.location)
    here = os.path.normcase(__file__)
    if not here.startswith(os.path.join(dist_loc, 'zaber_device')):
        # not installed, but there is another version that *is*
        raise DistributionNotFound
except (ImportError,DistributionNotFound):
    __version__ = None
else:
    __version__ = _dist.version


DEBUG = False
BAUDRATE = 9600
RESPONSE_LENGTH = 6

class ZaberError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ZaberDevice(object):
    '''
    This Python package (zaber_device) creates a class named ZaberDevice,
    which contains an instance of serial_device2.SerialDevice and adds
    methods to it to interface to Zaber motorized linear slides.

    Example Usage:

    dev = ZaberDevice() # Automatically finds device if one available
    dev = ZaberDevice('/dev/ttyUSB0') # Linux
    dev = ZaberDevice('/dev/tty.usbmodem262471') # Mac OS X
    dev = ZaberDevice('COM3') # Windows
    dev.get_actuator_count()
    2
    dev.get_current_position()
    [130000, 160000]
    dev.home()
    dev.get_current_position()
    [0, 0]
    dev.move_relative(10000)
    dev.get_current_position()
    [10000, 10000]
    dev.move_relative(10000,0)
    dev.get_current_position()
    '''
    _TIMEOUT = 0.05
    _WRITE_WRITE_DELAY = 0.05
    _RESET_DELAY = 2.0

    def __init__(self,*args,**kwargs):
        if 'debug' in kwargs:
            self.debug = kwargs['debug']
        else:
            kwargs.update({'debug': DEBUG})
            self.debug = DEBUG
        kwargs['debug'] = False
        if 'try_ports' in kwargs:
            try_ports = kwargs.pop('try_ports')
        else:
            try_ports = None
        if 'baudrate' not in kwargs:
            kwargs.update({'baudrate': BAUDRATE})
        elif (kwargs['baudrate'] is None) or (str(kwargs['baudrate']).lower() == 'default'):
            kwargs.update({'baudrate': BAUDRATE})
        if 'timeout' not in kwargs:
            kwargs.update({'timeout': self._TIMEOUT})
        if 'write_write_delay' not in kwargs:
            kwargs.update({'write_write_delay': self._WRITE_WRITE_DELAY})
        if ('port' not in kwargs) or (kwargs['port'] is None):
            port =  find_zaber_device_port(baudrate=kwargs['baudrate'],
                                                    try_ports=try_ports,
                                                    debug=kwargs['debug'])
            kwargs.update({'port': port})

        t_start = time.time()
        self._serial_device = SerialDevice(*args,**kwargs)
        atexit.register(self._exit_zaber_device)
        time.sleep(self._RESET_DELAY)
        t_end = time.time()
        self._debug_print('Initialization time =', (t_end - t_start))

    def _debug_print(self, *args):
        if self.debug:
            print(*args)

    def _exit_zaber_device(self):
        pass

    def _args_to_request(self,*args):
        request = ''.join(map(chr,args))
        return request

    def _data_to_args_list(self,data):
        if data is None:
            return [0,0,0,0]
        # Handle negative data
        # If Cmd_Data < 0 then Cmd_Data = 256^4 + Cmd_Data
        # Cmd_Byte_6 = Cmd_Data / 256^3
        # Cmd_Data   = Cmd_Data - 256^3 * Cmd_Byte_6
        # Cmd_Byte_5 = Cmd_Data / 256^2
        # Cmd_Data   = Cmd_Data - 256^2 * Cmd_Byte_5
        # Cmd_Byte_4 = Cmd_Data / 256
        # Cmd_Data   = Cmd_Data - 256   * Cmd_Byte_4
        # Cmd_Byte 3 = Cmd_Data
        if data < 0:
            data += pow(256,4)
        arg3 = data // pow(256,3)
        data -= pow(256,3)*arg3
        arg2 = data // pow(256,2)
        data -= pow(256,2)*arg2
        arg1 = data // 256
        data -= 256*arg1
        arg0 = data
        return [arg0,arg1,arg2,arg3]

    def _response_to_data(self,response):
        data_list = []
        self._debug_print('len(response)',len(response))
        actuator_count = len(response) // RESPONSE_LENGTH
        self._debug_print('actuator_count',actuator_count)
        for actuator_n in range(actuator_count):
            actuator = ord(response[0+actuator_n*RESPONSE_LENGTH])
            self._debug_print('response_actuator',actuator)
            command = ord(response[1+actuator_n*RESPONSE_LENGTH])
            self._debug_print('response_command',command)
            response_copy = response[(2+actuator_n*RESPONSE_LENGTH):(6+actuator_n*RESPONSE_LENGTH)]
            # Reply_Data = 256^3 * Rpl_Byte 6 + 256^2 * Rpl_Byte_5 + 256 * Rpl_Byte_4 + Rpl_Byte_3
            # If Rpl_Byte_6 > 127 then Reply_Data = Reply_Data - 256^4
            data = pow(256,3)*ord(response_copy[3]) + pow(256,2)*ord(response_copy[2]) + 256*ord(response_copy[1]) + ord(response_copy[0])
            data_list.append(data)
        if len(data_list) == 1:
            return data_list[0]
        else:
            return data_list

    def _send_request(self,command,actuator=-1,data=None):

        '''Sends request to device over serial port and
        returns number of bytes written'''

        actuator += 1
        args_list = self._data_to_args_list(data)
        request = self._args_to_request(actuator,command,*args_list)
        self._debug_print('request', [ord(c) for c in request])
        bytes_written = self._serial_device.write_check_freq(request,delay_write=True)
        self._debug_print('bytes_written', bytes_written)
        return bytes_written

    def _send_request_get_response(self,command,actuator=-1,data=None):

        '''Sends request to device over serial port and
        returns response'''

        actuator += 1
        args_list = self._data_to_args_list(data)
        request = self._args_to_request(actuator,command,*args_list)
        self._debug_print('request', [ord(c) for c in request])
        response = self._serial_device.write_read(request,use_readline=False,check_write_freq=True)
        self._debug_print('response', [ord(c) for c in response])
        data = self._response_to_data(response)
        self._debug_print('data', data)
        return data

    def close(self):
        '''
        Close the device serial port.
        '''
        self._serial_device.close()

    def get_port(self):
        return self._serial_device.port

    def reset(self,actuator=-1):
        '''
        Sets the actuator to its power-up condition.
        '''
        self._send_request(0,actuator)

    def home(self,actuator=-1):
        '''
        Moves to the home position and resets the actuator's internal position.
        '''
        self._send_request(1,actuator)

    def renumber(self):
        '''
        Assigns new numbers to all the actuators in the order in which they are connected.
        '''
        self._send_request(2,0)

    def move_absolute(self,position,actuator=-1):
        '''
        Moves the actuator to the position specified in the Command Data in microsteps.
        '''
        self._send_request(20,actuator,position)

    def get_actuator_count(self):
        '''
        Return the number of Zaber actuators connected in a chain.
        '''
        data = 123
        response = self._send_request_get_response(55,-1,data)
        try:
            actuator_count = len(response)
        except TypeError:
            actuator_count = 1
        return actuator_count

    def move_relative(self,position,actuator=-1):
        '''
        Moves the actuator by the positive or negative number of microsteps specified in the Command Data.
        '''
        self._send_request(21,actuator,position)

    def get_actuator_id(self,actuator=-1):
        '''
        Returns the id number for the type of actuator connected.
        '''
        response = self._send_request_get_response(50,actuator)
        return response

    def get_status(self,actuator=-1):
        '''
        Returns the current status of the actuator.
        '''
        response = self._send_request_get_response(54,actuator)
        return response

    def echo_data(self,data,actuator=-1):
        '''
        Echoes back the same Command Data that was sent.
        '''
        response = self._send_request_get_response(55,actuator,data)
        try:
            response = response[0]
        except TypeError:
            pass
        return response

    def get_current_position(self,actuator=-1):
        '''
        Returns the current absolute position of the actuator in microsteps.
        '''
        response = self._send_request_get_response(60,actuator)
        return response


class ZaberDevices(list):
    '''
    ZaberDevices inherits from list and automatically populates it with
    ZaberDevices on all available serial ports.

    Example Usage:

    devs = ZaberDevices()  # Automatically finds all available devices
    dev = devs[0]
    '''
    def __init__(self,*args,**kwargs):
        if ('use_ports' not in kwargs) or (kwargs['use_ports'] is None):
            zaber_device_ports = find_zaber_device_ports(*args,**kwargs)
        else:
            zaber_device_ports = use_ports

        for port in zaber_device_ports:
            dev = ZaberDevice(*args,**kwargs)
            self.append(dev)


def find_zaber_device_ports(baudrate=None, try_ports=None, debug=DEBUG):
    serial_device_ports = find_serial_device_ports(try_ports=try_ports, debug=debug)
    os_type = platform.system()
    if os_type == 'Darwin':
        serial_device_ports = [x for x in serial_device_ports if 'tty.usbmodem' in x or 'tty.usbserial' in x]

    zaber_device_ports = []
    for port in serial_device_ports:
        try:
            dev = ZaberDevice(port=port,baudrate=baudrate,debug=debug)
            try:
                test_data = 123
                echo_data = dev.echo_data(test_data)
                if test_data == echo_data:
                    zaber_device_ports.append(port)
            except:
                continue
            dev.close()
        except (serial.SerialException, IOError):
            pass
    return zaber_device_ports

def find_zaber_device_port(baudrate=None, model_number=None, serial_number=None, try_ports=None, debug=DEBUG):
    zaber_device_ports = find_zaber_device_ports(baudrate=baudrate,
                                                                   try_ports=try_ports,
                                                                   debug=debug)
    if len(zaber_device_ports) == 1:
        return zaber_device_ports[0]
    elif len(zaber_device_ports) == 0:
        serial_device_ports = find_serial_device_ports(try_ports)
        err_string = 'Could not find any Zaber devices. Check connections and permissions.\n'
        err_string += 'Tried ports: ' + str(serial_device_ports)
        raise RuntimeError(err_string)
    else:
        err_string = 'Found more than one Zaber device. Specify port or model_number and/or serial_number.\n'
        err_string += 'Matching ports: ' + str(zaber_device_ports)
        raise RuntimeError(err_string)


# -----------------------------------------------------------------------------------------
if __name__ == '__main__':

    debug = False
    dev = ZaberDevice(debug=debug)
