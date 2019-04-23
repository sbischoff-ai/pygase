# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='pygase',
    version='0.2.0',
    description='A lightweight client-server technology and UDP-based network protocol for real-time online gaming.',
    long_description_content_type='text/markdown',
    long_description = open('README.md').read(),
    author='Silas Bischoff',
    author_email='silas.bischoff@googlemail.com',
    license='MIT',
    url='https://github.com/sbischoff-ai/python-game-service',
    keywords=[
        'server',
        'client',
        'games',
        'gaming',
        'real-time',
        'network',
        'networking',
        'UDP',
        'protocol',
        'game server',
        'game service',
        'gameservice',
        'backend',
        'performance',
        'library',
        'connection',
        'online',
        'multiplayer',
        'event-driven',
        'state synchronization',
        'throttling'
    ],
    classifiers=[
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Topic :: Games/Entertainment',
        'Topic :: Internet',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
        'Intended Audience :: Developers',
        'Development Status :: 3 - Alpha'
    ],
    packages=['pygase'],
    install_requires=['u-msgpack-python', 'ifaddr', 'curio']
)