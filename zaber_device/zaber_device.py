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
    dev.get_serial_number()
    1126493049
    dev.get_balance_data()
    ['XS204', 'Excellence', '220.0090', 'g']
    dev.get_weight_stable()
    [-0.0082, 'g'] #if weight is stable
    None  #if weight is dynamic
    dev.get_weight()
    [-0.6800, 'g', 'S'] #if weight is stable
    [-0.6800, 'g', 'D'] #if weight is dynamic
    dev.zero_stable()
    True  #zeros if weight is stable
    False  #does not zero if weight is not stable
    dev.zero()
    'S'   #zeros if weight is stable
    'D'   #zeros if weight is dynamic
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
        request = request + '\r\n';
        return request

    def _send_request(self,*args):

        '''Sends request to device over serial port and
        returns number of bytes written'''

        request = self._args_to_request(*args)
        self._debug_print('request', request)
        bytes_written = self._serial_device.write_check_freq(request,delay_write=True)
        return bytes_written

    def _send_request_get_response(self,*args):

        '''Sends request to device over serial port and
        returns response'''

        request = self._args_to_request(*args)
        self._debug_print('request', request)
        response = self._serial_device.write_read(request,use_readline=True,check_write_freq=True)
        response = response.replace('"','')
        response_list = response.split()
        if 'ES' in response_list[0]:
            raise ZaberError('Syntax Error!')
        elif 'ET' in response_list[0]:
            raise ZaberError('Transmission Error!')
        elif 'EL' in response_list[0]:
            raise ZaberError('Logical Error!')
        return response_list

    def close(self):
        '''
        Close the device serial port.
        '''
        self._serial_device.close()

    def get_port(self):
        return self._serial_device.port

    def get_commands(self):
        '''
        Inquiry of all implemented MT-SICS commands.
        '''
        response = self._send_request_get_response('I0')
        if 'I' in response[1]:
            raise ZaberError('The list cannot be sent at present as another operation is taking place.')
        return response[2:]

    def get_mtsics_level(self):
        '''
        Inquiry of MT-SICS level and MT-SICS versions.
        '''
        response = self._send_request_get_response('I1')
        if 'I' in response[1]:
            raise ZaberError('Command understood, not executable at present.')
        return response[2:]

    def get_balance_data(self):
        '''
        Inquiry of balance data.
        '''
        response = self._send_request_get_response('I2')
        if 'I' in response[1]:
            raise ZaberError('Command understood, not executable at present.')
        return response[2:]

    def get_software_version(self):
        '''
        Inquiry of balance SW version and type definition number.
        '''
        response = self._send_request_get_response('I3')
        if 'I' in response[1]:
            raise ZaberError('Command understood, not executable at present.')
        return response[2:]

    def get_serial_number(self):
        '''
        Inquiry of serial number.
        '''
        response = self._send_request_get_response('I4')
        if 'I' in response[1]:
            raise ZaberError('Command understood, not executable at present.')
        return int(response[2])

    def get_software_id(self):
        '''
        Inquiry of SW-Identification number.
        '''
        response = self._send_request_get_response('I5')
        if 'I' in response[1]:
            raise ZaberError('Command understood, not executable at present.')
        return response[2]

    def get_weight_stable(self):
        '''
        Send the current stable net weight value.
        '''
        try:
            response = self._send_request_get_response('S')
            if 'I' in response[1]:
                raise ZaberError('Command understood, not executable at present.')
            elif '+' in response[1]:
                raise ZaberError('Balance in overload range.')
            elif '-' in response[1]:
                raise ZaberError('Balance in underload range.')
            response[2] = float(response[2])
            return response[2:]
        except:
            pass

    def get_weight(self):
        '''
        Send the current net weight value, irrespective of balance stability.
        '''
        response = self._send_request_get_response('SI')
        if 'I' in response[1]:
            raise ZaberError('Command understood, not executable at present.')
        elif '+' in response[1]:
            raise ZaberError('Balance in overload range.')
        elif '-' in response[1]:
            raise ZaberError('Balance in underload range.')
        response.append(response[1])
        response[2] = float(response[2])
        return response[2:]

    def zero_stable(self):
        '''
        Zero the balance.
        '''
        try:
            response = self._send_request_get_response('Z')
            if 'I' in response[1]:
                raise ZaberError('Zero setting not performed (balance is currently executing another command, e.g. taring, or timeout as stability was not reached).')
            elif '+' in response[1]:
                raise ZaberError('Upper limit of zero setting range exceeded.')
            elif '-' in response[1]:
                raise ZaberError('Lower limit of zero setting range exceeded.')
            return True
        except:
            return False

    def zero(self):
        '''
        Zero the balance immediately regardless the stability of the balance.
        '''
        response = self._send_request_get_response('ZI')
        if 'I' in response[1]:
            raise ZaberError('Zero setting not performed (balance is currently executing another command, e.g. taring, or timeout as stability was not reached).')
        elif '+' in response[1]:
            raise ZaberError('Upper limit of zero setting range exceeded.')
        elif '-' in response[1]:
            raise ZaberError('Lower limit of zero setting range exceeded.')
        return response[1]

    def reset(self):
        '''
        Resets the balance to the condition found after switching on, but without a zero setting being performed.
        '''
        self._send_request('@')


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
                serial_number = dev.get_serial_number()
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
