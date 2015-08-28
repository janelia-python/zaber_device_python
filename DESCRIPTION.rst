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

