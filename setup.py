# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='PyGaSe',
    version='0.1',
    description='A high-performance game server, client and UDP-based network protocol for real-time online gaming.',
    author='Silas Bischoff',
    author_email='silas.bischoff@stud.uni-due.de',
    url='https://github.com/sbischoff-ai/python-game-service',
    download_url= 'https://github.com/sbischoff-ai/python-game-service/archive/0.1.tar.gz',
    keywords=['server', 'client', 'games', 'gaming', 'real-time', 'network', 'UDP', 'protocol', 'game server', 'game service'],
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
    packages=['PyGaSe'],
    install_requires=['umsgpack']
)