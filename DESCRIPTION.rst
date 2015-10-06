zaber_device_python
===================

This Python package (zaber_device) creates a class named ZaberDevice,
which contains an instance of serial_device2.SerialDevice and adds
methods to it to interface to Zaber motorized linear slides.

Authors::

    Peter Polidoro <polidorop@janelia.hhmi.org>

License::

    BSD

Example Usage::

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
    from zaber_device import ZaberDevices
    devs = ZaberDevices()  # Might automatically find all available devices
    # if they are not found automatically, specify ports to use
    devs = ZaberDevices(use_ports=['/dev/ttyUSB0','/dev/ttyUSB1']) # Linux
    devs = ZaberDevices(use_ports=['/dev/tty.usbmodem262471','/dev/tty.usbmodem262472']) # Mac OS X
    devs = ZaberDevices(use_ports=['COM3','COM4']) # Windows
    devs.keys()
    dev = devs[serial_number]
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
