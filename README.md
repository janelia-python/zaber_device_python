zaber_device_python
===================

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
dev.get\_actuator\_count()
2
dev.get\_position()
[130000, 160000]
dev.home()
dev.moving()
[True, True]
dev.moving()
[False, False]
dev.get\_position()
[0, 0]
dev.move\_relative(10000)
dev.get\_position()
[10000, 10000]
dev.move\_relative(10000,0)
dev.moving()
[True, False]
dev.get\_position()
[20000, 10000]
dev.store\_position(0)
dev.get\_stored\_position(0)
[20000, 10000]
dev.move\_at\_speed(1000)
dev.stop()
dev.get\_position()
[61679, 51679]
dev.move\_to\_stored\_position(0)
dev.get\_position()
[20000, 10000]
```

```python
devs = ZaberDevices()  # Automatically finds all available devices
devs.keys()
dev = devs[serial\_number]
```

```python
stage = ZaberStage() # Automatically finds devices if available
stage.get\_aliases()
{123: [10, 11]}
serial\_number = 123
alias = 10
stage.set\_x\_axis(serial\_number,alias)
alias = 11
stage.set\_y\_axis(serial\number,alias)
stage.home()
stage.moving()
(True,True,True)
stage.moving()
(False,False,False)
stage.get\_positions()
(0,0,0)
stage.move\_x\_at\_speed(1000)
stage.moving()
(True,False,False)
stage.get\_positions()
(14285, 0, 0)
stage.stop\_x()
stage.moving()
(False,False,False)
stage.get\_positions()
(35898, 0, 0)
stage.move\_y\_relative(1234)
stage.moving()
(False,True,False)
stage.moving()
(False,False,False)
stage.get\_positions()
(35898, 1234, 0)
```
