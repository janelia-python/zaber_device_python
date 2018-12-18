from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='zaber_device',
    version_format='{tag}',
    setup_requires=['very-good-setuptools-git-version'],
    description='Interface to Zaber motorized linear slides.',
    long_description=long_description,
    url='https://github.com/janelia-pypi/zaber_device_python',
    author='Peter Polidoro',
    author_email='peterpolidoro@gmail.com',
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
    ],
    keywords='zaber serial device',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=['serial_interface',
    ],
)
