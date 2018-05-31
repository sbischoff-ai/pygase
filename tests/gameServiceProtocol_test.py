# -*- coding: utf-8 -*-

import pytest
import pygase.shared

class TestUDPPackage:

    package = pygase.shared.UDPPackage(pygase.shared.PackageType.GetGameStateRequest)

    def test_package_instantiation(self):
        assert self.package.body is None
        other_package = pygase.shared.UDPPackage(pygase.shared.PackageType.PostClientActivityRequest)
        assert self.package != other_package
        other_package.header.package_type = pygase.shared.PackageType.GetGameStateRequest
        assert self.package == other_package
        other_package.body = pygase.shared.GameState()
        assert self.package != other_package
        assert other_package.body.game_status == pygase.shared.GameStatus.Paused

    def test_package_header_bytepacking(self):
        bytepack = self.package.header.to_bytes()
        unpacked_header = pygase.shared.UDPPackageHeader.from_bytes(bytepack)
        assert self.package.header == unpacked_header
        with pytest.raises(TypeError) as exception:
            pygase.shared.UDPPackageHeader.from_bytes('This is not a header'.encode('utf-8'))
            assert str(exception.value) == \
                'Bytes could no be parsed into pygase.shared.UDPPackageHeader.'

    def test_package_datagrams(self):
        datagram = self.package.to_datagram()
        received_package = pygase.shared.UDPPackage.from_datagram(datagram)
        assert received_package == self.package
        other_package = pygase.shared.UDPPackage(
            pygase.shared.PackageType().GetGameStateUpdateRequest,
            body=pygase.shared.GameState()
        )
        datagram = other_package.to_datagram()
        received_package = pygase.shared.UDPPackage.from_datagram(datagram)
        assert received_package.body.game_status == pygase.shared.GameStatus.Paused
