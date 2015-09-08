'''
This Python package (zaber_device) creates classes named
ZaberDevice, ZaberDevices, and ZaberStage, which contain an instance
of serial_device2.SerialDevice and adds methods to it to interface to
Zaber motorized linear slides.
'''
from zaber_device import ZaberDevice, ZaberDevices, ZaberStage, ZaberError, find_zaber_device_ports, find_zaber_device_port, __version__
