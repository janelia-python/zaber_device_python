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
```

```python
devs = ZaberDevices()  # Automatically finds all available devices
devs.keys()
dev = devs[serial_number]
```

```python
stage = ZaberStage() # Automatically finds devices if available
stage.get_aliases()
{123: [10, 11]}
serial_number = 123
alias = 10
stage.set_x_axis(serial_number,alias)
alias = 11
stage.set_y_axis(serial\number,alias)
stage.home()
stage.moving()
(True, True, False)
stage.moving()
(False, False, False)
stage.get_positions()
(0, 0, 0)
stage.move_x_at_speed(1000)
stage.moving()
(True, False, False)
stage.get_positions()
(148140, 0, 0)
stage.stop_x()
stage.moving()
(False, False, False)
stage.get_positions()
(245984, 0, 0)
stage.move_y_relative(123456)
stage.moving()
(False, True, False)
stage.moving()
(False, False, False)
stage.get_positions()
(245984, 123456, False)
stage.move_x_absolute(200000)
stage.move_y_absolute(100000)
stage.moving()
(False, False, False)
stage.store_x_position(0)
stage.get_stored_x_position(0)
200000
stage.move_x_relative(10000)
stage.get_positions()
(210000, 100000, 0)
stage.move_to_stored_x_position(0)
stage.get_positions()
(200000, 100000, 0)
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
stage = ZaberStage() # Automatically finds devices if available
stage.get_aliases()
{123: [10, 11]}
serial_number = 123
alias = 10
stage.set_x_axis(serial_number,alias)
alias = 11
stage.set_y_axis(serial\number,alias)
stage.get_actuator_ids()
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
dev = ZaberDevice() # Automatically finds devices if available
dev.set_microstep_size(0.49609375e-3)
dev.get_microstep_size()
0.00049609375
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

