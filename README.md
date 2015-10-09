#zaber_device_python

This Python package (zaber\_device) creates a class named ZaberDevice,
which contains an instance of serial\_device2.SerialDevice and adds
methods to it to interface to Zaber motorized linear slides.

Authors:

    Peter Polidoro <polidorop@janelia.hhmi.org>

License:

    BSD

##Example Usage

```python
from zaber_device import ZaberDevice
dev = ZaberDevice() # Might automatically find device if one available
# if it is not found automatically, specify port directly
dev = ZaberDevice(port='/dev/ttyUSB0') # Linux
dev = ZaberDevice(port='/dev/tty.usbmodem262471') # Mac OS X
dev = ZaberDevice(port='COM3') # Windows
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
```

```python
from zaber_device import ZaberDevices
devs = ZaberDevices()  # Might automatically find all available devices
# if they are not found automatically, specify ports to use
devs = ZaberDevices(use_ports=['/dev/ttyUSB0','/dev/ttyUSB1']) # Linux
devs = ZaberDevices(use_ports=['/dev/tty.usbmodem262471','/dev/tty.usbmodem262472']) # Mac OS X
devs = ZaberDevices(use_ports=['COM3','COM4']) # Windows
devs.keys()
dev = devs[serial_number]
```

```python
from zaber_device import ZaberStage
stage = ZaberStage()  # Might automatically find all available devices
# if they are not found automatically, specify ports to use
stage = ZaberStage(use_ports=['/dev/ttyUSB0','/dev/ttyUSB1']) # Linux
stage = ZaberStage(use_ports=['/dev/tty.usbmodem262471','/dev/tty.usbmodem262472']) # Mac OS X
stage = ZaberStage(use_ports=['COM3','COM4']) # Windows
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
```

##First Time Device Setup

```shell
ipython
```

```python
from zaber_device import ZaberDevice
dev = ZaberDevice()
dev.restore_settings()
dev.renumber()
```

##First Time Stage Setup Example

```shell
ipython
```

```python
from zaber_device import ZaberDevice
dev = ZaberDevice()
dev.restore_settings()
dev.renumber()
dev.set_serial_number(123)
dev.set_alias(0,10)
dev.set_alias(1,10)
dev.set_alias(2,11)
dev.set_alias(3,11)
```

##Setting Zaber Stage Units

###Find Actuator ID

```python
from zaber_device import ZaberStage
stage = ZaberStage() # Automatically finds devices if available
stage.get_aliases()
{123: [10, 11]}
stage.set_x_axis(123,10)
stage.set_y_axis(123,11)
stage.get_actuator_ids()
(4452, 4452, None)
```

###Find Microstep Size

[Lookup Zaber Device Name from Device ID](http://www.zaber.com/support/?tab=ID%20Mapping#tabs)

Example: 4452 = T-LSR450B

[Search for Zaber Device Name to find Detailed Specs](http://zaber.com/products/)

Find 'Microstep Size (Default Resolution)'

Example: T-LSR450B = 0.49609375 µm

###Set Microstep Size

Example: T-LSR450B = 0.49609375 µm

1µm = 1e-3mm

To set units of mm, set microstep_size to 0.49609375e-3

```python
from zaber_device import ZaberStage
stage = ZaberStage() # Automatically finds devices if available
stage.get_aliases()
{123: [10, 11]}
stage.set_x_axis(123,10)
stage.set_y_axis(123,11)
stage.set_x_microstep_size(0.49609375e-3)
stage.get_x_microstep_size()
0.00049609375
stage.set_y_microstep_size(0.49609375e-3)
stage.get_y_microstep_size()
0.00049609375
```

###Find Travel

[Lookup Zaber Device Name from Device ID](http://www.zaber.com/support/?tab=ID%20Mapping#tabs)

Example: 4452 = T-LSR450B

[Search for Zaber Device Name to find Detailed Specs](http://zaber.com/products/)

Find 'Travel Range'

Example: T-LSR450B = 450mm

###Set Travel

Example: T-LSR450B = 450mm

```python
from zaber_device import ZaberStage
stage = ZaberStage() # Automatically finds devices if available
stage.get_aliases()
{123: [10, 11]}
stage.set_x_axis(123,10)
stage.set_y_axis(123,11)
stage.set_x_microstep_size(0.49609375e-3)
stage.set_y_microstep_size(0.49609375e-3)
stage.set_x_travel(450)
stage.get_x_travel()
450.0
stage.set_y_travel(450)
stage.get_y_travel()
450.0
stage.home()
stage.move_x_absolute_percent(50)
stage.get_positions()
(224.99984765625, 0.0, 0)
stage.get_positions_percent()
(49.99996614583334, 0.0, 0)
stage.move_x_relative_percent(-25)
stage.move_y_absolute_percent(25)
stage.move_y_relative_percent(25)
stage.get_positions()
(112.500171875, 224.9993515625, 0)
stage.get_positions_percent()
(25.000038194444446, 49.99985590277778, 0)
```

##Installation

[Setup Python](https://github.com/janelia-pypi/python_setup)

###Linux and Mac OS X

```shell
mkdir -p ~/virtualenvs/zaber_device
virtualenv ~/virtualenvs/zaber_device
source ~/virtualenvs/zaber_device/bin/activate
pip install zaber_device
```

###Windows

```shell
virtualenv C:\virtualenvs\zaber_device
C:\virtualenvs\zaber_device\Scripts\activate
pip install zaber_device
```

