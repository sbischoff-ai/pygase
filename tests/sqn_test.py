import pytest
from pygase.sqn import sqn

class TestSqn:

    def test_initialize_valid_values(self):
        for i in range(sqn._max_sequence + 1):
            s = sqn(i)
            assert s == i

    def test_initialize_negative_values(self):
        for i in range(-1, -(sqn._max_sequence + 2), -1):
            with pytest.raises(ValueError) as error:
                sqn(i)
            assert str(error.value) == 'sequence numbers must not be negative'

    def test_initialize_with_overflowing_value(self):
        for i in range(sqn._max_sequence + 1, 2*sqn._max_sequence):
            with pytest.raises(ValueError) as error:
                sqn(i)
            assert str(error.value) == 'value exceeds maximum sequence number'

    def test_add_within_sequence(self):
        s = sqn(0)
        for i in range(1, sqn._max_sequence + 1):
            s += sqn(1)
            assert s == i
            assert s.__class__ == sqn

    def test_add_within_sequence_with_ints(self):
        s = sqn(0)
        for i in range(1, sqn._max_sequence + 1):
            s += 1
            assert s == i
            assert s.__class__ == sqn

    def test_sequence_wrap_around(self):
        s = sqn(sqn._max_sequence)
        s += sqn(1)
        assert s == 1

    def test_sequence_wrap_around_with_int(self):
        s = sqn(sqn._max_sequence)
        s += 1
        assert s == 1

    def test_add_negative_int(self):
        s = sqn(2)
        s += -1
        assert s == 1 and s.__class__ == sqn

    def test_add_negative_int_with_larger_norm(self):
        s = sqn(2)
        with pytest.raises(ValueError) as error:
            s += -3
        assert str(error.value) == 'sequence numbers must not be negative'

    def test_small_difference_within_sequence(self):
        s1 = sqn(2)
        s2 = sqn(5)
        assert s2 - s1 == 3
        assert s1 - s2 == -3
        assert s2 > s1 and s1 < s2

    def test_small_difference_around_sequence_edge(self):
        s1 = sqn(2)
        s2 = sqn(sqn._max_sequence - 2)
        assert s2 - s1 == -4
        assert s1 - s2 == 4
        assert s1 > s2 and s2 < s1

    def test_symmetry(self):
        s = sqn(1)
        greater = 0
        lower = 0
        for i in range(1, sqn._max_sequence + 1):
            if(sqn(i) > s):
                greater += 1
            elif(sqn(i) < s):
                lower += 1
        assert greater > 0 and greater == lower

    def test_large_distance(self):
        assert sqn(50000) - sqn(20000) == 30000
        assert sqn(sqn._max_sequence-100) - sqn(20000) == -20100

    def test_bytes(self):
        for i in range(2*sqn._bytesize):
            b = sqn(i).to_bytes()
            assert len(b) == sqn._bytesize
            assert b.__class__ == bytes
            assert sqn.from_bytes(b) == sqn(i)

