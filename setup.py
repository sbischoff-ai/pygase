# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='pygase',
    version='0.1.1',
    description='A high-performance game server, client and UDP-based network protocol for real-time online gaming.',
    author='Silas Bischoff',
    author_email='silas.bischoff@stud.uni-due.de',
    license='MIT',
    url='https://github.com/sbischoff-ai/python-game-service',
    keywords=['server', 'client', 'games', 'gaming', 'real-time', 'network', 'UDP', 'protocol', 'game server', 'game service', 'gameservice'],
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
    install_requires=['u-msgpack-python']
)