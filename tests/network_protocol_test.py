import pytest

import curio

from pygase.utils import sqn
from pygase.event import Event
from pygase.network_protocol import Package, Connection, DuplicateSequenceError, ProtocolIDMismatchError

class TestPackage:

    def test_bytepacking(self):
        package = Package(4, 5, '10'*16, [Event(1, ('Foo', 'Bar'))])
        datagram = package.to_datagram()
        unpacked_package = Package.from_datagram(datagram)
        #assert package == unpacked_package

    def test_protocol_ID_check(self):
        package = Package(1, 2, '0'*32)
        datagram = package.to_datagram()
        datagram = datagram[1:]
        with pytest.raises(ProtocolIDMismatchError):
            Package.from_datagram(datagram)

    def test_size_restriction(self):
        with pytest.raises(OverflowError) as error:
            Package(1, 4, '0'*32, [Event(2, (bytes(2048-13),))]).to_datagram()
        assert str(error.value) == 'package exceeds the maximum size of 2048 bytes'

class TestConnection:

    def test_recv_first_package(self):
        connection = Connection(('host', 1234))
        assert connection.local_sequence == 0
        assert connection.remote_sequence == 0
        assert connection.ack_bitfield == '0'*32
        curio.run(connection._recv(Package(sequence=1, ack=0, ack_bitfield='0'*32)))
        assert connection.local_sequence == 0
        assert connection.remote_sequence == 1
        assert connection.ack_bitfield == '0'*32

    def test_recv_second_package(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = sqn(1)
        connection.ack_bitfield = '0'*32
        curio.run(connection._recv(Package(sequence=2, ack=1, ack_bitfield='0'*32)))
        assert connection.remote_sequence == 2
        assert connection.ack_bitfield == '1' + '0'*31

    def test_recv_second_package_comes_first(self):
        connection = Connection(('host', 1234))
        assert connection.remote_sequence == 0
        assert connection.ack_bitfield == '0'*32
        curio.run(connection._recv(Package(sequence=2, ack=0, ack_bitfield='0'*32)))
        assert connection.remote_sequence == 2
        assert connection.ack_bitfield == '0'*32

    def test_recv_first_package_comes_second(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = sqn(2)
        connection.ack_bitfield = '0'*32
        curio.run(connection._recv(Package(sequence=1, ack=1, ack_bitfield='0'*32)))
        assert connection.remote_sequence == 2
        assert connection.ack_bitfield == '1' + '0'*31

    def test_recv_three_packages_arrive_out_of_sequence(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = sqn(100)
        connection.ack_bitfield = '0110' + '1'*28
        curio.run(connection._recv(Package(sequence=101, ack=100, ack_bitfield='1'*32)))
        assert connection.remote_sequence == 101
        assert connection.ack_bitfield == '10110' + '1'*27
        curio.run(connection._recv(Package(sequence=99, ack=100, ack_bitfield='1'*32)))
        assert connection.remote_sequence == 101
        assert connection.ack_bitfield == '11110' + '1'*27
        curio.run(connection._recv(Package(sequence=96, ack=101, ack_bitfield='1'*32)))
        assert connection.remote_sequence == 101
        assert connection.ack_bitfield == '1'*32

    def test_recv_duplicate_package_in_sequence(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = sqn(500)
        connection.ack_bitfield = '1'*32
        curio.run(connection._recv(Package(sequence=501, ack=500, ack_bitfield='1'*32)))
        with pytest.raises(DuplicateSequenceError):
            curio.run(connection._recv(Package(sequence=501, ack=500, ack_bitfield='1'*32)))

    def test_recv_duplicate_package_out_of_sequence(self):
        connection = Connection(('host', 1234))
        connection.remote_sequence = sqn(1000)
        connection.ack_bitfield = '1'*32
        with pytest.raises(DuplicateSequenceError):
            curio.run(connection._recv(Package(sequence=990, ack=500, ack_bitfield='1'*32)))

    def test_congestion_avoidance(self):
        connection = Connection(('', 1234))
        state = {
            'throttle_time': Connection.min_throttle_time,
            'last_quality_change': 0.0,
            'last_good_quality_milestone': 0.0
        }
        assert connection.quality == 'good'
        assert connection.latency == 0.0
        assert connection.package_interval == Connection._package_intervals['good']
        t = Connection.min_throttle_time
        connection._throttling_state_machine(t, state)
        assert connection.quality == 'good'
        assert connection.package_interval == Connection._package_intervals['good']
        connection.latency = Connection._latency_threshold + 0.01
        t +=  Connection.min_throttle_time
        connection._throttling_state_machine(t, state)
        assert connection.quality == 'bad'
        assert connection.package_interval == Connection._package_intervals['bad']
        assert state['throttle_time'] == Connection.min_throttle_time
        connection.latency = Connection._latency_threshold - 0.01
        t += Connection.min_throttle_time/2.0
        connection._throttling_state_machine(t, state)
        assert connection.quality == 'good'
        assert connection.package_interval == Connection._package_intervals['bad']
        assert state['throttle_time'] == Connection.min_throttle_time
        t += 1.1*Connection.min_throttle_time
        connection._throttling_state_machine(t, state)
        assert connection.quality == 'good'
        assert connection.package_interval == Connection._package_intervals['good']
        assert state['throttle_time'] == Connection.min_throttle_time
        connection.latency = Connection._latency_threshold + 0.01
        t += Connection.min_throttle_time/2.0
        connection._throttling_state_machine(t, state)
        connection.latency = Connection._latency_threshold - 0.01
        t += Connection.min_throttle_time/2.0
        connection._throttling_state_machine(t, state)
        connection.latency = Connection._latency_threshold + 0.01
        t += Connection.min_throttle_time/2.0
        connection._throttling_state_machine(t, state)
        assert connection.quality == 'bad'
        assert connection.package_interval == Connection._package_intervals['bad']
        assert state['throttle_time'] == 2.0*Connection.min_throttle_time
        connection.latency = Connection._latency_threshold - 0.01
        t += Connection.min_throttle_time/2.0
        connection._throttling_state_machine(t, state)
        t += 2.1*Connection.min_throttle_time
        connection._throttling_state_machine(t, state)
        assert connection.quality == 'good'
        assert connection.package_interval == Connection._package_intervals['good']
        assert state['throttle_time'] == Connection.min_throttle_time
