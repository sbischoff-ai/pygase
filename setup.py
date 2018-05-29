# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='PyGaSe',
    version='0.1',
    description='A high-performance game server, client and UDP-based network protocol for real-time online gaming.',
    author='Silas Bischoff',
    author_email='silas.bischoff@stud.uni-due.de',
    url='https://github.com/sbischoff-ai/python-game-service',
    license='MIT',
    packages=['PyGaSe'],
    install_requires=['umsgpack']
)