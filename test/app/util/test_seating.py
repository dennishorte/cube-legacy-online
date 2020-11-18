from unittest import TestCase

from app.util.seating import seat_picks_for_pack


class TestSeatPicksForPack(TestCase):
    def test_seat_0(self):
        result = seat_picks_for_pack(4, 3, 0, 1, False)
        expected = [0, 1, 2, 0]
        self.assertEqual(expected, result)

    def test_seat_1(self):
        result = seat_picks_for_pack(4, 3, 1, 1, False)
        expected = [1, 2, 0, 1]
        self.assertEqual(expected, result)

    def test_seat_0_reverse(self):
        result = seat_picks_for_pack(4, 3, 0, 1, True)
        expected = [0, 2, 1, 0]
        self.assertEqual(expected, result)

    def test_seat_1_reverse(self):
        result = seat_picks_for_pack(4, 3, 1, 1, True)
        expected = [1, 0, 2, 1]
        self.assertEqual(expected, result)

    def test_2_picks_per_pack(self):
        result = seat_picks_for_pack(9, 3, 0, 2, False)
        expected = [0, 0, 1, 1, 2, 2, 0, 0, 1]
        self.assertEqual(expected, result)

    def test_2_picks_per_pack_reverse(self):
        result = seat_picks_for_pack(9, 3, 0, 2, True)
        expected = [0, 0, 2, 2, 1, 1, 0, 0, 2]
        self.assertEqual(expected, result)

    def test_2_picks_per_pack_seat_2_reverse(self):
        result = seat_picks_for_pack(9, 3, 2, 2, True)
        expected = [2, 2, 1, 1, 0, 0, 2, 2, 1]
        self.assertEqual(expected, result)
