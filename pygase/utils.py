# -*- coding: utf-8 -*-
"""Use helpful classes and functions.

Provides utilities used in PyGaSe code or helpful to users of this library.

### Contents
- #Comparable: mixin that makes objects compare as equal if their type and attributes match
- #Sendable: mixin that allows to serialize objects to small bytestrings
- #Sqn: subclass of `int` for sequence numbers that always fit in 2 bytes
- #LockedResource: class that attaches a `threading.Lock` to a resource
- #get_available_ip_addresses: function that returns a list of local network interfaces

"""

import logging
import socket
import warnings
from collections.abc import Mapping
from threading import Lock
from typing import Generic, TypeVar

try:
    import umsgpack
except ImportError:  # pragma: no cover - fallback for restricted test envs
    import msgpack

    class _UmsgpackFallback:
        InsufficientDataException = ValueError

        @staticmethod
        def packb(data: object, **kwargs: object) -> bytes:
            """Pack message data with msgpack compatibility options."""
            kwargs.pop("force_float_precision", None)
            return msgpack.packb(data, use_bin_type=True)

        @staticmethod
        def unpackb(data: bytes | bytearray | memoryview) -> object:
            """Unpack message data with string decoding enabled."""
            return msgpack.unpackb(data, raw=False)

    umsgpack = _UmsgpackFallback()

try:
    import ifaddr
except ImportError:  # pragma: no cover - fallback for restricted test envs
    ifaddr = None

logger = logging.getLogger("PyGaSe")


class Comparable:
    """Compare objects by equality of attributes."""

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)


class Sendable(Comparable):
    """Send objects via UDP packages.

    This mixin for classes that are supposed to be sendable as part of a PyGaSe package makes
    objects serializable with the msgpack protocol.
    Sendables can only have attributes of type `str`, `bytes`, `Sqn`, `int`, `float`, `bool`
    as well as `dict`s, `list`s or `tuple`s of such.

    """

    def to_dict(self) -> dict:
        """Return a serializable dictionary representation of this object.

        Subclasses with non-trivial internal state should override this method together
        with :meth:`from_dict` to implement a stable, explicit serialization protocol.

        """
        return dict(self.__dict__)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "Sendable":
        """Create an instance from a dictionary representation."""
        if not isinstance(data, Mapping):
            raise TypeError(f"Payload for {cls.__name__} must be a mapping.")
        received_sendable = object.__new__(cls)
        for key, value in data.items():
            if not isinstance(key, str):
                raise TypeError(f"Payload keys for {cls.__name__} must be strings.")
            setattr(received_sendable, key, value)
        return received_sendable

    def to_bytes(self) -> bytes:
        """Serialize the object to a compact bytestring."""
        return umsgpack.packb(self.to_dict(), force_float_precision="single")

    @classmethod
    def from_bytes(cls, bytepack: bytes) -> "Sendable":
        """Deserialize a bytestring into an instance of this class.

        # Arguments
        bytepack (): the bytestring to be parsed to a subclass of `Sendable`

        # Returns
        a copy of an object that was serialized via `Sendable.to_bytes`

        """
        if not isinstance(bytepack, (bytes, bytearray, memoryview)):
            raise TypeError(f"{cls.__name__}.from_bytes expects a bytes-like object.")
        try:
            payload = umsgpack.unpackb(bytepack)
        except (umsgpack.InsufficientDataException, TypeError, ValueError) as exc:
            raise ValueError(f"Bytes could not be parsed into {cls.__name__}.") from exc
        if not isinstance(payload, Mapping):
            raise TypeError(f"Decoded payload for {cls.__name__} must be a mapping.")
        try:
            return cls.from_dict(payload)
        except (TypeError, ValueError, KeyError) as exc:
            raise ValueError(f"Decoded payload for {cls.__name__} is malformed.") from exc


class Sqn(int):
    """Use finite periodic integers that fit in 2 bytes.

    Subclass of `int` that provides a residue-class-like behaviour of wrapping back to 1 after a maximum value.
    Use it to represent sequence numbers with a fixed number of bytes when you only need well-defined ordering
    within a specific finite scale. 0 represents the state before the sequence has started.

    For the default bytesize of 2 the maximum sequence number is 65535.

    """

    _bytesize: int = 2
    _max_sequence: int = int("1" * (_bytesize * 8), 2)

    @classmethod
    def set_bytesize(cls, bytesize: int) -> None:
        """Redefine the bytesize and wrap-over behaviour for all `Sqn` instances.

        # Arguments
        bytesize (): new size for the `bytes` representation of `Sqn` instances

        """
        cls._bytesize = bytesize
        cls._max_sequence = int("1" * (bytesize * 8), 2)

    @classmethod
    def get_max_sequence(cls) -> int:
        """Return the maximum sequence number after which `Sqn`s wrap back to 1."""
        return cls(cls._max_sequence)

    def __new__(cls, value: int | None) -> "Sqn":
        """Create a `Sqn` instance."""
        if value is None:
            value = 0
        elif value > cls._max_sequence:
            raise ValueError("value exceeds maximum sequence number")
        elif value < 0:
            raise ValueError("sequence numbers must not be negative")
        return super(Sqn, cls).__new__(cls, value)  # type: ignore

    def __add__(self, other: int) -> "Sqn":
        """Add sequence numbers.

        # Example
        ```python
        assert Sqn(2) + Sqn(3) == 5
        assert Sqn(2) + 3 == 5
        assert Sqn.get_max_sequence() == 65535
        assert Sqn(2) + 65535 == 2
        ```

        """
        result = super().__add__(other)
        if result > self._max_sequence:
            result -= self._max_sequence
            logger.debug(f"Sequence number wrap-over reached at maximum of {self._max_sequence}.")
        return self.__class__(result)

    def __sub__(self, other: int) -> int:
        """Calculate the difference between sequence numbers.

        # Example
        ```python
        assert Sqn(5) - Sqn(3) == 2
        assert Sqn.get_max_sequence() == 65535
        assert Sqn(5) - Sqn(65530) == 10
        ```

        """
        result = super().__sub__(other)
        threshold = (self._max_sequence - 1) / 2
        if result > threshold:
            result -= self._max_sequence
        elif result < -threshold:
            result += self._max_sequence
        return int(result)

    def __lt__(self, other: int) -> bool:
        """Check if sequence number is lower than `other`.

        # Example
        ```python
        assert not Sqn(5) < Sqn(3)
        assert Sqn.get_max_sequence() == 65535
        assert not Sqn(5) < Sqn(65500)
        assert Sqn(5) < Sqn(100)
        ```

        """
        return super().__lt__(super().__add__((other - self)))

    def __gt__(self, other: int) -> bool:
        """Check if sequence number is greater than `other`.

        # Example
        ```python
        assert Sqn(5) > Sqn(3)
        assert Sqn.get_max_sequence() == 65535
        assert Sqn(5) > Sqn(65500)
        assert not Sqn(5) > Sqn(100)
        ```

        """
        return super().__gt__(super().__add__((other - self)))

    def to_sqn_bytes(self) -> bytes:
        """Return representation of the number in exactly the currently set bytesize.

        The default bytesize is 2.

        """
        return super().to_bytes(self._bytesize, "big")

    @classmethod
    def from_sqn_bytes(cls, bytestring: bytes) -> "Sqn":
        """Return `Sqn` object that was encoded in given bytestring."""
        return cls(super().from_bytes(bytestring, "big"))


ResourceT = TypeVar("ResourceT")


class LockedResource(Generic[ResourceT]):
    """Access a resource in a thread-safe way.

    This class makes an object available via a context manager that essentially attaches a
    `threading.Lock` to it that threads writing to this object should respect.

    Usage example:
    ```python
    my_resource = {"foo": "bar"}
    my_locked_resource = LockedResource(my_resource)
    with my_locked_resource as resource:
        # do stuff without any other threads meddling with the resource
    ```

    # Arguments
    resource (): object to be wrapped

    # Attributes
    lock (): `threading.Lock` that threads writing to `resource` should abide.
    resource ()

    """

    def __init__(self, resource: ResourceT) -> None:
        self.lock: Lock = Lock()
        self.resource = resource

    def __enter__(self) -> ResourceT:
        """Lock `resource` and return it."""
        self.lock.acquire()
        logger.debug(f"Acquired lock for {self.resource}.")
        return self.resource

    def __exit__(self, exception_type: object, exception_value: object, traceback: object) -> None:
        """Release the lock."""
        self.lock.release()
        logger.debug(f"Released lock for {self.resource}.")

    @property
    def ressource(self) -> ResourceT:
        """Return deprecated alias for `resource`."""
        warnings.warn(
            "LockedResource.ressource is deprecated, use LockedResource.resource instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.resource

    @ressource.setter
    def ressource(self, value: ResourceT) -> None:
        """Set deprecated alias for `resource`."""
        warnings.warn(
            "LockedResource.ressource is deprecated, use LockedResource.resource instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.resource = value


class LockedRessource(LockedResource[ResourceT]):
    """Deprecated alias for :class:`LockedResource`."""

    def __init__(self, resource: ResourceT) -> None:
        warnings.warn(
            "LockedRessource is deprecated, use LockedResource instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(resource)


def get_available_ip_addresses() -> list[str]:
    """Return a list of all locally available IPv4 addresses."""
    if ifaddr is None:
        addresses: set[str] = {"127.0.0.1"}
        addr_infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        for result in addr_infos:
            ip_addr = result[4][0]
            if isinstance(ip_addr, str) and ip_addr[:3] in {"10.", "172", "192", "127"}:
                addresses.add(ip_addr)
        return list(addresses)

    detected_addresses: list[str] = []
    for adapter in ifaddr.get_adapters():
        for adapter_ip in adapter.ips:
            if (
                isinstance(adapter_ip.ip, str)
                and adapter_ip.is_IPv4
                and adapter_ip.ip[:3] in {"10.", "172", "192", "127"}
            ):
                detected_addresses.append(adapter_ip.ip)
    return detected_addresses
