import unittest
from unittest.mock import patch

from bb84 import bob_merese, elokeszites, meres


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


class ElokeszitesTests(unittest.TestCase):
    def test_letrehozza_a_meres_elotti_poziciokat(self):
        bitek = [0, 1]
        alice_bazisok = ["Z", "X"]
        bob_bazisok = ["X", "X"]

        poziciok = elokeszites(bitek, alice_bazisok, bob_bazisok)

        self.assertEqual(poziciok, [
            {
                "alice": ("Z", 0),
                "eve": None,
                "bob": ("X", None),
                "megtartva": None,
                "ellenorzo_minta": False,
            },
            {
                "alice": ("X", 1),
                "eve": None,
                "bob": ("X", None),
                "megtartva": None,
                "ellenorzo_minta": False,
            },
        ])
        self.assertEqual(bitek, [0, 1])
        self.assertEqual(alice_bazisok, ["Z", "X"])
        self.assertEqual(bob_bazisok, ["X", "X"])

    def test_eltero_hossznal_nem_vagja_le_a_listakat(self):
        for bitek, alice_bazisok, bob_bazisok in (
            ([0, 1], ["Z"], ["X", "Z"]),
            ([0, 1], ["Z", "Z"], ["X"]),
            ([0], ["Z", "Z"], ["X", "X"]),
        ):
            with self.subTest(bitek=bitek, alice=alice_bazisok, bob=bob_bazisok):
                with self.assertRaises(ValueError):
                    elokeszites(bitek, alice_bazisok, bob_bazisok)

    def test_ures_bemenetet_visszautasit(self):
        with self.assertRaises(ValueError):
            elokeszites([], [], [])

    def test_ervenytelen_bitet_visszautasit(self):
        for bit in (2, -1, "0", None):
            with self.subTest(bit=bit):
                with self.assertRaises(ValueError):
                    elokeszites([bit], ["Z"], ["Z"])

    def test_ervenytelen_bazist_mindket_felnel_visszautasit(self):
        for alice_bazis, bob_bazis in (("Y", "Z"), ("Z", "Y")):
            with self.subTest(alice=alice_bazis, bob=bob_bazis):
                with self.assertRaises(ValueError):
                    elokeszites([0], [alice_bazis], [bob_bazis])


class BobMereseTests(unittest.TestCase):
    def test_minden_poziciot_megmer_es_megorzi_alice_adatait(self):
        poziciok = elokeszites(
            [0, 1, 0, 1], ["Z", "X", "Z", "X"], ["Z", "X", "X", "Z"]
        )
        alice_eredeti = [pozicio["alice"] for pozicio in poziciok]

        with patch("bb84.random.choice", side_effect=[1, 0]):
            bob_merese(poziciok)

        self.assertEqual(
            [pozicio["bob"] for pozicio in poziciok],
            [("Z", 0), ("X", 1), ("X", 1), ("Z", 0)],
        )
        self.assertEqual([pozicio["alice"] for pozicio in poziciok], alice_eredeti)
        for pozicio in poziciok:
            self.assertIsNone(pozicio["eve"])
            self.assertIsNone(pozicio["megtartva"])
            self.assertFalse(pozicio["ellenorzo_minta"])

    def test_ismetelt_hivas_megorzi_a_nullas_eredmenyt_is(self):
        poziciok = elokeszites([1], ["Z"], ["X"])
        with patch("bb84.random.choice", return_value=0) as sorsolas:
            bob_merese(poziciok)
            bob_merese(poziciok)

        self.assertEqual(poziciok[0]["bob"], ("X", 0))
        sorsolas.assert_called_once_with((0, 1))

    def test_ures_poziciolistaval_is_hivhato(self):
        bob_merese([])


if __name__ == "__main__":
    unittest.main()
