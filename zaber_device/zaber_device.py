# -*- coding: utf-8 -*-
from __future__ import print_function, division
import serial
import time
import atexit
import platform
import os
from exceptions import Exception
import threading

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
CURRENT_MIN = 1
CURRENT_MAX = 100
ZABER_CURRENT_MIN = 127
ZABER_CURRENT_MAX = 10
ALIAS_MIN = 0
ALIAS_MAX = 98
POSITION_ADDRESS_MIN = 0
POSITION_ADDRESS_MAX = 15
SERIAL_NUMBER_ADDRESS = 123
RESPONSE_ATTEMPTS_MAX = 2

class ZaberError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ZaberNumberingError(Exception):
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
    dev.get_position()
    [130000, 160000]
    dev.home()
    dev.moving()
    [True, True]
    dev.moving()
    [False, False]
    dev.get_position()
    [0, 0]
    dev.move_relative(10000)
    dev.get_position()
    [10000, 10000]
    dev.move_relative(10000,0)
    dev.moving()
    [True, False]
    dev.get_position()
    [20000, 10000]
    dev.store_position(0)
    dev.get_stored_position(0)
    [20000, 10000]
    dev.move_at_speed(1000)
    dev.stop()
    dev.get_position()
    [61679, 51679]
    dev.move_to_stored_position(0)
    dev.get_position()
    [20000, 10000]
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
        self._lock = threading.Lock()
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
        data = int(data)
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
        self._debug_print('len(response)',len(response))
        actuator_count = len(response) // RESPONSE_LENGTH
        self._debug_print('actuator_count',actuator_count)
        data_list = [None for d in range(actuator_count)]
        for actuator_n in range(actuator_count):
            actuator = ord(response[0+actuator_n*RESPONSE_LENGTH]) - 1
            self._debug_print('response_actuator',actuator)
            if actuator >= actuator_count:
                raise ZaberNumberingError('')
            command = ord(response[1+actuator_n*RESPONSE_LENGTH])
            self._debug_print('response_command',command)
            response_copy = response[(2+actuator_n*RESPONSE_LENGTH):(6+actuator_n*RESPONSE_LENGTH)]
            # Reply_Data = 256^3 * Rpl_Byte 6 + 256^2 * Rpl_Byte_5 + 256 * Rpl_Byte_4 + Rpl_Byte_3
            # If Rpl_Byte_6 > 127 then Reply_Data = Reply_Data - 256^4
            data = pow(256,3)*ord(response_copy[3]) + pow(256,2)*ord(response_copy[2]) + 256*ord(response_copy[1]) + ord(response_copy[0])
            data_list[actuator] = data
        return data_list

    def _send_request(self,command,actuator=None,data=None):

        '''Sends request to device over serial port and
        returns number of bytes written'''

        self._lock.acquire()
        if actuator is None:
            actuator = 0
        elif actuator < 0:
            raise ZaberError('actuator must be >= 0')
        else:
            actuator = int(actuator)
            actuator += 1
        args_list = self._data_to_args_list(data)
        request = self._args_to_request(actuator,command,*args_list)
        self._debug_print('request', [ord(c) for c in request])
        bytes_written = self._serial_device.write_check_freq(request,delay_write=True)
        self._debug_print('bytes_written', bytes_written)
        self._lock.release()
        return bytes_written

    def _send_request_get_response(self,command,actuator=None,data=None):

        '''Sends request to device over serial port and
        returns response'''

        self._lock.acquire()
        if actuator is None:
            actuator = 0
        elif actuator < 0:
            raise ZaberError('actuator must be >= 0')
        else:
            actuator = int(actuator)
            actuator += 1
        args_list = self._data_to_args_list(data)
        request = self._args_to_request(actuator,command,*args_list)
        self._debug_print('request', [ord(c) for c in request])
        tries = 0
        while tries < RESPONSE_ATTEMPTS_MAX:
            tries += 1
            try:
                response = self._serial_device.write_read(request,use_readline=False,check_write_freq=True)
                self._debug_print('response', [ord(c) for c in response])
                data = self._response_to_data(response)
                self._debug_print('data', data)
            except ZaberNumberingError:
                raise ZaberError('Improper actuator number detected in response, may need to rearrange zaber cables or use renumber method to fix.')
        self._lock.release()
        return data

    def close(self):
        '''
        Close the device serial port.
        '''
        self._serial_device.close()

    def get_port(self):
        return self._serial_device.port

    def reset(self,actuator=None):
        '''
        Sets the actuator to its power-up condition.
        '''
        self._send_request(0,actuator)

    def home(self,actuator=None):
        '''
        Moves to the home position and resets the actuator's internal position.
        '''
        self._send_request(1,actuator)

    def renumber(self):
        '''
        Assigns new numbers to all the actuators in the order in which they are connected.
        '''
        self._send_request(2,None)

    def store_position(self,address,actuator=None):
        '''
        Saves the current absolute position of the actuator into the address.
        '''
        address = int(address)
        if (address < POSITION_ADDRESS_MIN) or (address > POSITION_ADDRESS_MAX):
            raise ZaberError('address must be between {0} and {1}'.format(POSITION_ADDRESS_MIN,POSITION_ADDRESS_MAX))
        self._send_request(16,actuator,address)

    def get_stored_position(self,address):
        '''
        Gets the current absolute position of the actuator into the address.
        '''
        address = int(address)
        if (address < POSITION_ADDRESS_MIN) or (address > POSITION_ADDRESS_MAX):
            raise ZaberError('address must be between {0} and {1}'.format(POSITION_ADDRESS_MIN,POSITION_ADDRESS_MAX))
        actuator = None
        response = self._send_request_get_response(17,actuator,address)
        return response

    def move_to_stored_position(self,address,actuator=None):
        '''
        Moves the actuator to the position stored in the specified address.
        '''
        address = int(address)
        if (address < POSITION_ADDRESS_MIN) or (address > POSITION_ADDRESS_MAX):
            raise ZaberError('address must be between {0} and {1}'.format(POSITION_ADDRESS_MIN,POSITION_ADDRESS_MAX))
        self._send_request(18,actuator,address)

    def move_absolute(self,position,actuator=None):
        '''
        Moves the actuator to the position specified in microsteps.
        '''
        self._send_request(20,actuator,position)

    def get_actuator_count(self):
        '''
        Return the number of Zaber actuators connected in a chain.
        '''
        data = 123
        actuator = None
        response = self._send_request_get_response(55,actuator,data)
        try:
            actuator_count = len(response)
        except TypeError:
            actuator_count = 1
        return actuator_count

    def move_relative(self,position,actuator=None):
        '''
        Moves the actuator by the positive or negative number of microsteps specified.
        '''
        self._send_request(21,actuator,position)

    def move_at_speed(self,speed,actuator=None):
        '''
        Moves the actuator at a constant speed until stop is commanded or a limit is reached.
        '''
        self._send_request(22,actuator,speed)

    def stop(self,actuator=None):
        '''
        Stops the device from moving by preempting any move instruction.
        '''
        self._send_request(23,actuator)

    def restore_settings(self):
        '''
        Restores the device settings to the factory defaults.
        '''
        self._send_request(36,None)

    def get_actuator_id(self):
        '''
        Returns the id number for the type of actuator connected.
        '''
        actuator = None
        response = self._send_request_get_response(50,actuator)
        return response

    def _return_setting(self,setting,actuator):
        '''
        Returns the current value of the specified setting.
        '''
        response = self._send_request_get_response(53,actuator,setting)
        return response

    def _get_microstep_resolution(self):
        '''
        Returns the number of microsteps per step.
        '''
        actuator = None
        response = self._return_setting(37,actuator)
        return response

    def set_running_current(self,current,actuator=None):
        '''
        Sets the desired current to be used when the actuator is moving. (1-100)
        '''
        if (current < CURRENT_MIN) or (current > CURRENT_MAX):
            raise ZaberError('current must be between {0} and {1}'.format(CURRENT_MIN,CURRENT_MAX))
        zaber_current = self._map(current,CURRENT_MIN,CURRENT_MAX,ZABER_CURRENT_MIN,ZABER_CURRENT_MAX)
        self._send_request(38,actuator,zaber_current)

    def get_running_current(self):
        '''
        Returns the desired current to be used when the actuator is moving. (1-100)
        '''
        actuator = None
        response = self._return_setting(38,actuator)
        response = self._map_list(response,ZABER_CURRENT_MIN,ZABER_CURRENT_MAX,CURRENT_MIN,CURRENT_MAX)
        return response

    def set_hold_current(self,current,actuator=None):
        '''
        Sets the desired current to be used when the actuator is holding its position. (1-100)
        '''
        if (current < CURRENT_MIN) or (current > CURRENT_MAX):
            raise ZaberError('current must be between {0} and {1}'.format(CURRENT_MIN,CURRENT_MAX))
        zaber_current = self._map(current,CURRENT_MIN,CURRENT_MAX,ZABER_CURRENT_MIN,ZABER_CURRENT_MAX)
        self._send_request(39,actuator,zaber_current)

    def get_hold_current(self):
        '''
        Returns the desired current to be used when the actuator is holding its position. (1-100)
        '''
        actuator = None
        response = self._return_setting(39,actuator)
        response = self._map_list(response,ZABER_CURRENT_MIN,ZABER_CURRENT_MAX,CURRENT_MIN,CURRENT_MAX)
        return response

    def _get_actuator_mode(self):
        '''
        Returns the mode for the given actuator.
        '''
        actuator = None
        response = self._return_setting(40,actuator)
        response = ["{0:b}".format(r) for r in response]
        return response

    def set_home_speed(self,speed,actuator=None):
        '''
        Sets the speed at which the actuator moves when using the "Home" command.
        '''
        self._send_request(41,actuator,speed)

    def get_home_speed(self):
        '''
        Returns the speed at which the actuator moves when using the "Home" command.
        '''
        actuator = None
        response = self._return_setting(41,actuator)
        return response

    def set_target_speed(self,speed,actuator=None):
        '''
        Sets the speed at which the actuator moves when using "move_absolute" or "move_relative" commands.
        '''
        self._send_request(42,actuator,speed)

    def get_target_speed(self):
        '''
        Returns the speed at which the actuator moves when using "move_absolute" or "move_relative" commands.
        '''
        actuator = None
        response = self._return_setting(42,actuator)
        return response

    def set_acceleration(self,acceleration,actuator=None):
        '''
        Sets the acceleration used by the movement commands.
        '''
        self._send_request(43,actuator,acceleration)

    def get_acceleration(self):
        '''
        Returns the acceleration used by the movement commands.
        '''
        actuator = None
        response = self._return_setting(43,actuator)
        return response

    def get_alias(self):
        '''
        Returns the alternate device numbers for the actuators.
        '''
        actuator = None
        response = self._return_setting(48,actuator)
        response_corrected = []
        for r in response:
            if r > 0:
                response_corrected.append(r-1)
            else:
                response_corrected.append(None)
        return response_corrected

    def set_alias(self,actuator,alias):
        '''
        Sets the alternate device numbers for the actuator.
        '''
        actuator_count = self.get_actuator_count()
        if (actuator < 0) or (actuator > actuator_count):
            raise ZaberError('actuator must be between {0} and {1}'.format(0,actuator_count))
        if (alias < ALIAS_MIN) or (alias > ALIAS_MAX):
            raise ZaberError('alias must be between {0} and {1}'.format(ALIAS_MIN,ALIAS_MAX))
        self._send_request(48,actuator,alias+1)

    def remove_alias(self,actuator=None):
        '''
        Removes the alternate device number for the actuator.
        '''
        response = self._send_request_get_response(48,actuator,0)
        return response

    def moving(self):
        '''
        Returns True if actuator is moving, False otherwise
        '''
        actuator = None
        response = self._send_request_get_response(54,actuator)
        response = [bool(r) for r in response]
        return response

    def echo_data(self,data):
        '''
        Echoes back the same Command Data that was sent.
        '''
        actuator = None
        response = self._send_request_get_response(55,actuator,data)
        try:
            response = response[0]
        except TypeError:
            pass
        return response

    def get_position(self):
        '''
        Returns the current absolute position of the actuator in microsteps.
        '''
        actuator = None
        response = self._send_request_get_response(60,actuator)
        return response

    def set_serial_number(self,serial_number):
        '''
        Sets serial number. Useful for talking communicating with ZaberDevices on multiple serial ports.
        '''
        actuator = None
        # write
        data = 1 << 7
        address = SERIAL_NUMBER_ADDRESS
        data += address
        serial_number = int(serial_number)
        serial_number = serial_number << 8
        data += serial_number
        self._send_request(35,actuator,data)

    def get_serial_number(self):
        '''
        Gets serial number. Useful for talking communicating with ZaberDevices on multiple serial ports.
        '''
        actuator = None
        # read
        data = 0 << 7
        address = SERIAL_NUMBER_ADDRESS
        data += address
        response = self._send_request_get_response(35,actuator,data)
        response = response[0]
        response = response >> 8
        return response

    def _map_list(self,x_list,in_min,in_max,out_min,out_max):
        return [int((x-in_min)*(out_max-out_min)/(in_max-in_min)+out_min) for x in x_list]

    def _map(self,x,in_min,in_max,out_min,out_max):
        return int((x-in_min)*(out_max-out_min)/(in_max-in_min)+out_min)


class ZaberDevices(dict):
    '''
    ZaberDevices inherits from dict and automatically populates it with
    ZaberDevices on all available serial ports. Access each individual
    device with one key, the device serial_number. If you
    want to connect multiple ZaberDevices with the same name at the
    same time, first make sure they have unique serial_numbers by
    connecting each device one by one and using the set_serial_number
    method on each device.
    Example Usage:
    devs = ZaberDevices()  # Automatically finds all available devices
    devs.keys()
    dev = devs[serial_number]
    '''
    def __init__(self,*args,**kwargs):
        if ('use_ports' not in kwargs) or (kwargs['use_ports'] is None):
            zaber_device_ports = find_zaber_device_ports(*args,**kwargs)
        else:
            zaber_device_ports = use_ports

        for port in zaber_device_ports:
            kwargs.update({'port': port})
            self._add_device(*args,**kwargs)

    def _add_device(self,*args,**kwargs):
        dev = ZaberDevice(*args,**kwargs)
        serial_number = dev.get_serial_number()
        self[serial_number] = dev


class ZaberStage(object):
    '''
    ZaberStage contains an instance of ZaberDevices and adds
    methods to it to use it as an xyz stage.
    Example Usage:
    stage = ZaberStage() # Automatically finds devices if available
    stage.get_aliases()
    {123: [10, 11]}
    serial_number = 123
    alias = 10
    stage.set_x_axis(serial_number,alias)
    alias = 11
    stage.set_y_axis(serial_number,alias)
    # Lookup microstep_size on Zaber website
    stage.set_x_microstep_size(0.49609375e-3)
    stage.get_x_microstep_size()
    0.00049609375
    stage.set_y_microstep_size(0.49609375e-3)
    stage.home()
    stage.moving()
    (True, True, False)
    stage.moving()
    (False, False, False)
    stage.get_positions()
    (0.0, 0.0, 0)
    stage.move_x_at_speed(5)
    stage.moving()
    (True, False, False)
    stage.get_positions()
    (76.4619375, 0.0, 0)
    stage.stop_x()
    stage.moving()
    (False, False, False)
    stage.get_positions()
    (94.38133984375, 0.0, 0)
    stage.move_y_relative(125)
    stage.moving()
    (False, True, False)
    stage.moving()
    (False, False, False)
    stage.get_positions()
    (94.38133984375, 124.99975, 0)
    stage.move_x_absolute(50)
    stage.move_y_absolute(75)
    stage.moving()
    (False, False, False)
    stage.store_x_position(0)
    stage.get_stored_x_position(0)
    49.99980078125
    stage.move_x_relative(50)
    stage.get_positions()
    (99.9996015625, 74.99994921875, 0)
    stage.move_to_stored_x_position(0)
    stage.get_positions()
    (49.99980078125, 74.99994921875, 0)
    '''
    def __init__(self,*args,**kwargs):
        self._devs = ZaberDevices(*args,**kwargs)
        if len(self._devs) == 0:
            raise ZaberError('Could not find any Zaber devices. Check connections and permissions.')
        self._x_axis = None
        self._y_axis = None
        self._z_axis = None
        self._x_microstep_size = 1
        self._y_microstep_size = 1
        self._z_microstep_size = 1

    def get_aliases(self):
        '''
        Returns a dictionary with serial numbers as keys and lists of aliases as values.
        '''
        aliases = {}
        for serial_number in self._devs:
            dev = self._devs[serial_number]
            alias = dev.get_alias()
            aliases[serial_number] = alias
        return aliases

    def set_aliases(self,aliases):
        '''
        Aliases is a dictionary with serial numbers as keys and lists of aliases as values.
        '''
        aliases_prev = self.get_aliases()
        if aliases_prev.keys() != aliases.keys():
            error_string = 'aliases.keys() must equal: {0}'.format(aliases_prev.keys())
            raise ZaberError(error_string)
        for serial_number in aliases:
            try:
                if len(aliases_prev[serial_number]) != len(aliases[serial_number]):
                    error_string = 'len(aliases[{0}]) must equal {1}'.format(serial_number,len(aliases_prev[serial_number]))
                    raise ZaberError(error_string)
            except TypeError:
                error_string = 'aliases[{0}] is incorrect type'.format(serial_number)
                raise ZaberError(error_string)
            dev = self._devs[serial_number]
            for actuator in range(len(aliases[serial_number])):
                dev.set_alias(actuator,aliases[serial_number][actuator])

    def _set_axis(self,axis,serial_number,alias):
        ax = {}
        ax['serial_number'] = serial_number
        ax['dev'] = self._devs[serial_number]
        ax['alias'] = alias
        aliases = self.get_aliases()
        ax['actuator'] = aliases[serial_number].index(alias)
        if axis == 'x':
            self._x_axis = ax
        elif axis == 'y':
            self._y_axis = ax
        elif axis == 'z':
            self._z_axis = ax

    def set_x_axis(self,serial_number,alias):
        self._set_axis('x',serial_number,alias)

    def set_y_axis(self,serial_number,alias):
        self._set_axis('y',serial_number,alias)

    def set_z_axis(self,serial_number,alias):
        self._set_axis('z',serial_number,alias)

    def _move_at_speed(self,axis,speed):
        if axis == 'x':
            ax = self._x_axis
            speed /= (9.375*self._x_microstep_size)
        elif axis == 'y':
            ax = self._y_axis
            speed /= (9.375*self._y_microstep_size)
        elif axis == 'z':
            ax = self._z_axis
            speed /= (9.375*self._z_microstep_size)
        if ax is not None:
            dev = ax['dev']
            alias = ax['alias']
            dev.move_at_speed(speed,alias)

    def move_x_at_speed(self,speed):
        self._move_at_speed('x',speed)

    def move_y_at_speed(self,speed):
        self._move_at_speed('y',speed)

    def move_z_at_speed(self,speed):
        self._move_at_speed('z',speed)

    def _stop(self,axis):
        if axis == 'x':
            ax = self._x_axis
        elif axis == 'y':
            ax = self._y_axis
        elif axis == 'z':
            ax = self._z_axis
        if ax is not None:
            dev = ax['dev']
            alias = ax['alias']
            dev.stop(alias)

    def stop_x(self):
        self._stop('x')

    def stop_y(self):
        self._stop('y')

    def stop_z(self):
        self._stop('z')

    def get_positions(self):
        positions = {}
        for serial_number in self._devs:
            dev = self._devs[serial_number]
            position = dev.get_position()
            positions[serial_number] = position
        if self._x_axis is not None:
            x_position = positions[serial_number][self._x_axis['actuator']]
            x_position *= self._x_microstep_size
        else:
            x_position = 0
        if self._y_axis is not None:
            y_position = positions[serial_number][self._y_axis['actuator']]
            y_position *= self._y_microstep_size
        else:
            y_position = 0
        if self._z_axis is not None:
            z_position = positions[serial_number][self._z_axis['actuator']]
            z_position *= self._z_microstep_size
        else:
            z_position = 0
        return x_position,y_position,z_position

    def moving(self):
        movings = {}
        for serial_number in self._devs:
            dev = self._devs[serial_number]
            moving = dev.moving()
            movings[serial_number] = moving
        if self._x_axis is not None:
            x_moving = movings[serial_number][self._x_axis['actuator']]
        else:
            x_moving = False
        if self._y_axis is not None:
            y_moving = movings[serial_number][self._y_axis['actuator']]
        else:
            y_moving = False
        if self._z_axis is not None:
            z_moving = movings[serial_number][self._z_axis['actuator']]
        else:
            z_moving = False
        return x_moving,y_moving,z_moving

    def home(self):
        for serial_number in self._devs:
            dev = self._devs[serial_number]
            dev.home()

    def stop(self):
        for serial_number in self._devs:
            dev = self._devs[serial_number]
            dev.stop()

    def _move_absolute(self,axis,position):
        if axis == 'x':
            ax = self._x_axis
            position /= self._x_microstep_size
        elif axis == 'y':
            ax = self._y_axis
            position /= self._y_microstep_size
        elif axis == 'z':
            ax = self._z_axis
            position /= self._z_microstep_size
        if ax is not None:
            dev = ax['dev']
            alias = ax['alias']
            dev.move_absolute(position,alias)

    def move_x_absolute(self,position):
        self._move_absolute('x',position)

    def move_y_absolute(self,position):
        self._move_absolute('y',position)

    def move_z_absolute(self,position):
        self._move_absolute('z',position)

    def _move_relative(self,axis,position):
        if axis == 'x':
            ax = self._x_axis
            position /= self._x_microstep_size
        elif axis == 'y':
            ax = self._y_axis
            position /= self._y_microstep_size
        elif axis == 'z':
            ax = self._z_axis
            position /= self._z_microstep_size
        if ax is not None:
            dev = ax['dev']
            alias = ax['alias']
            dev.move_relative(position,alias)

    def move_x_relative(self,position):
        self._move_relative('x',position)

    def move_y_relative(self,position):
        self._move_relative('y',position)

    def move_z_relative(self,position):
        self._move_relative('z',position)

    def _store_position(self,axis,address):
        if axis == 'x':
            ax = self._x_axis
        elif axis == 'y':
            ax = self._y_axis
        elif axis == 'z':
            ax = self._z_axis
        if ax is not None:
            dev = ax['dev']
            alias = ax['alias']
            dev.store_position(address,alias)

    def store_x_position(self,address):
        self._store_position('x',address)

    def store_y_position(self,address):
        self._store_position('y',address)

    def store_z_position(self,address):
        self._store_position('z',address)

    def _get_stored_position(self,axis,address):
        if axis == 'x':
            ax = self._x_axis
            microstep_size = self._x_microstep_size
        elif axis == 'y':
            ax = self._y_axis
            microstep_size = self._y_microstep_size
        elif axis == 'z':
            ax = self._z_axis
            microstep_size = self._z_microstep_size
        if ax is not None:
            dev = ax['dev']
            actuator = ax['actuator']
            positions = dev.get_stored_position(address)
            position = positions[actuator]
            position *= microstep_size
            return position

    def get_stored_x_position(self,address):
        return self._get_stored_position('x',address)

    def get_stored_y_position(self,address):
        return self._get_stored_position('y',address)

    def get_stored_z_position(self,address):
        return self._get_stored_position('z',address)

    def _move_to_stored_position(self,axis,address):
        if axis == 'x':
            ax = self._x_axis
        elif axis == 'y':
            ax = self._y_axis
        elif axis == 'z':
            ax = self._z_axis
        if ax is not None:
            dev = ax['dev']
            alias = ax['alias']
            dev.move_to_stored_position(address,alias)

    def move_to_stored_x_position(self,address):
        self._move_to_stored_position('x',address)

    def move_to_stored_y_position(self,address):
        self._move_to_stored_position('y',address)

    def move_to_stored_z_position(self,address):
        self._move_to_stored_position('z',address)

    def get_actuator_ids(self):
        actuator_ids = {}
        for serial_number in self._devs:
            dev = self._devs[serial_number]
            actuator_id = dev.get_actuator_id()
            actuator_ids[serial_number] = actuator_id
        if self._x_axis is not None:
            x_actuator_id = actuator_ids[serial_number][self._x_axis['actuator']]
        else:
            x_actuator_id = None
        if self._y_axis is not None:
            y_actuator_id = actuator_ids[serial_number][self._y_axis['actuator']]
        else:
            y_actuator_id = None
        if self._z_axis is not None:
            z_actuator_id = actuator_ids[serial_number][self._z_axis['actuator']]
        else:
            z_actuator_id = None
        return x_actuator_id,y_actuator_id,z_actuator_id

    def _set_microstep_size(self,axis,microstep_size):
        if axis == 'x':
            self._x_microstep_size = microstep_size
        elif axis == 'y':
            self._y_microstep_size = microstep_size
        elif axis == 'z':
            self._z_microstep_size = microstep_size

    def set_x_microstep_size(self,microstep_size):
        self._set_microstep_size('x',microstep_size)

    def set_y_microstep_size(self,microstep_size):
        self._set_microstep_size('y',microstep_size)

    def set_z_microstep_size(self,microstep_size):
        self._set_microstep_size('z',microstep_size)

    def get_x_microstep_size(self):
        return self._x_microstep_size

    def get_y_microstep_size(self):
        return self._y_microstep_size

    def get_z_microstep_size(self):
        return self._z_microstep_size


def find_zaber_device_ports(baudrate=None,
                            try_ports=None,
                            serial_number=None,
                            debug=DEBUG,
                            *args,
                            **kwargs):
    serial_device_ports = find_serial_device_ports(try_ports=try_ports, debug=debug)
    os_type = platform.system()
    if os_type == 'Darwin':
        serial_device_ports = [x for x in serial_device_ports if 'tty.usbmodem' in x or 'tty.usbserial' in x]

    zaber_device_ports = {}
    for port in serial_device_ports:
        try:
            dev = ZaberDevice(port=port,baudrate=baudrate,debug=debug)
            try:
                test_data = 123
                echo_data = dev.echo_data(test_data)
                if test_data == echo_data:
                    s_n = dev.get_serial_number()
                    if (serial_number is None) or (s_n == serial_number):
                        zaber_device_ports[port] = {'serial_number':s_n}
            except ZaberError as e:
                zaber_device_ports[port] = {'serial_number':None}
            except:
                continue
            dev.close()
        except (serial.SerialException, IOError):
            pass
    return zaber_device_ports

def find_zaber_device_port(baudrate=None,
                           try_ports=None,
                           serial_number=None,
                           debug=DEBUG):
    zaber_device_ports = find_zaber_device_ports(baudrate=baudrate,
                                                 try_ports=try_ports,
                                                 serial_number=serial_number,
                                                 debug=debug)
    if len(zaber_device_ports) == 1:
        return zaber_device_ports.keys()[0]
    elif len(zaber_device_ports) == 0:
        serial_device_ports = find_serial_device_ports(try_ports)
        err_string = 'Could not find any Zaber devices. Check connections and permissions.\n'
        err_string += 'Tried ports: ' + str(serial_device_ports)
        raise RuntimeError(err_string)
    else:
        err_string = 'Found more than one Zaber device. Specify port or serial_number.\n'
        err_string += 'Matching ports: ' + str(zaber_device_ports)
        raise RuntimeError(err_string)


# -----------------------------------------------------------------------------------------
if __name__ == '__main__':

    debug = False
    dev = ZaberDevice(debug=debug)
