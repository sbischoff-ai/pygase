import threading
import socket
import pytest
from pygase.server import Server
from pygase.network_protocol import Package, Connection, DuplicateSequenceError

class TestConnection:

    def test_update_first_package(self):
        connection = Connection(('host', 1234))
        assert connection.local_sequence == 0
        assert connection.remote_sequence == 0
        assert connection.ack_bitfield == '0'*32
        connection.update(Package(sequence=1, ack=0, ack_bitfield='0'*32))
        assert connection.local_sequence == 0
        assert connection.remote_sequence == 1
        assert connection.ack_bitfield == '0'*32

    def test_update_second_package(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = 1
        connection.ack_bitfield = '0'*32
        connection.update(Package(sequence=2, ack=1, ack_bitfield='0'*32))
        assert connection.remote_sequence == 2
        assert connection.ack_bitfield == '1' + '0'*31

    def test_update_second_package_comes_first(self):
        connection = Connection(('host', 1234))
        assert connection.remote_sequence == 0
        assert connection.ack_bitfield == '0'*32
        connection.update(Package(sequence=2, ack=0, ack_bitfield='0'*32))
        assert connection.remote_sequence == 2
        assert connection.ack_bitfield == '0'*32

    def test_update_first_package_comes_second(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = 2
        connection.ack_bitfield = '0'*32
        connection.update(Package(sequence=1, ack=1, ack_bitfield='0'*32))
        assert connection.remote_sequence == 2
        assert connection.ack_bitfield == '1' + '0'*31

    def test_update_three_packages_arrive_out_of_sequence(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = 100
        connection.ack_bitfield = '0110' + '1'*28
        connection.update(Package(sequence=101, ack=100, ack_bitfield='1'*32))
        assert connection.remote_sequence == 101
        assert connection.ack_bitfield == '10110' + '1'*27
        connection.update(Package(sequence=99, ack=100, ack_bitfield='1'*32))
        assert connection.remote_sequence == 101
        assert connection.ack_bitfield == '11110' + '1'*27
        connection.update(Package(sequence=96, ack=101, ack_bitfield='1'*32))
        assert connection.remote_sequence == 101
        assert connection.ack_bitfield == '1'*32

    def test_update_duplicate_package_in_sequence(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = 500
        connection.ack_bitfield = '1'*32
        connection.update(Package(sequence=501, ack=500, ack_bitfield='1'*32))
        with pytest.raises(DuplicateSequenceError):
            connection.update(Package(sequence=501, ack=500, ack_bitfield='1'*32))

    def test_update_duplicate_package_out_of_sequence(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = 1000
        connection.ack_bitfield = '1'*32
        with pytest.raises(DuplicateSequenceError):
            connection.update(Package(sequence=990, ack=500, ack_bitfield='1'*32))
