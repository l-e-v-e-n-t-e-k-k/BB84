import unittest
from unittest.mock import patch

from bb84 import meres


class MeresTests(unittest.TestCase):
    def test_azonos_bazisnal_az_eredeti_bit_marad(self):
        for bazis in ("Z", "X"):
            for bit in (0, 1):
                with self.subTest(bazis=bazis, bit=bit):
                    with patch("bb84.random.choice") as sorsolas:
                        self.assertEqual(meres((bazis, bit), bazis), bit)
                        sorsolas.assert_not_called()

    def test_eltero_bazisnal_a_sorsolt_bit_az_eredmeny(self):
        for bazis, meresi_bazis in (("Z", "X"), ("X", "Z")):
            for eredeti_bit in (0, 1):
                for sorsolt_bit in (0, 1):
                    with self.subTest(
                        bazis=bazis,
                        eredeti_bit=eredeti_bit,
                        sorsolt_bit=sorsolt_bit,
                    ):
                        with patch(
                            "bb84.random.choice", return_value=sorsolt_bit
                        ) as sorsolas:
                            self.assertEqual(
                                meres((bazis, eredeti_bit), meresi_bazis),
                                sorsolt_bit,
                            )
                            sorsolas.assert_called_once_with((0, 1))

    def test_a_meres_megorzi_az_eredeti_allapotot(self):
        allapot = ("Z", 0)
        with patch("bb84.random.choice", return_value=1):
            self.assertEqual(meres(allapot, "X"), 1)
        self.assertEqual(allapot, ("Z", 0))


if __name__ == "__main__":
    unittest.main()
