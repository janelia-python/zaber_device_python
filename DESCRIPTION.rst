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
    devs = ZaberDevices()  # Automatically finds all available devices
    devs.keys()
    dev = devs[serial_number]
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
