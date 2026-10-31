import unittest
from unittest.mock import patch

from bb84 import bob_merese, elokeszites, eve_merese, meres, szures


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


class EveTests(unittest.TestCase):
    def test_elokeszites_aktiv_de_meg_nem_mert_tamadoval(self):
        eve_bazisok = ["X", "Z"]
        poziciok = elokeszites([0, 1], ["Z", "X"], ["Z", "X"], eve_bazisok)
        self.assertEqual([p["eve"] for p in poziciok], [("X", None), ("Z", None)])
        self.assertEqual(eve_bazisok, ["X", "Z"])

    def test_eve_bazisainak_ellenorzese(self):
        for bazisok in ([], ["Z", "X"], ["Y"]):
            with self.subTest(bazisok=bazisok):
                with self.assertRaises(ValueError):
                    elokeszites([0], ["Z"], ["Z"], bazisok)

    def test_eve_nelkul_a_lepes_nem_valtoztat_a_futason(self):
        poziciok = elokeszites([0], ["Z"], ["X"])
        with patch("bb84.random.choice") as sorsolas:
            eve_merese(poziciok)
        sorsolas.assert_not_called()
        self.assertIsNone(poziciok[0]["eve"])
        self.assertEqual(poziciok[0]["bob"], ("X", None))

    def test_azonos_bazisnal_eve_az_eredeti_allapotot_kuldi_tovabb(self):
        poziciok = elokeszites(
            [0, 1, 0, 1], ["Z", "Z", "X", "X"],
            ["Z", "Z", "X", "X"], ["Z", "Z", "X", "X"]
        )
        with patch("bb84.random.choice") as sorsolas:
            eve_merese(poziciok)
            bob_merese(poziciok)
        sorsolas.assert_not_called()
        for pozicio in poziciok:
            self.assertEqual(pozicio["eve"], pozicio["alice"])
            self.assertEqual(pozicio["bob"], pozicio["alice"])

    def test_bob_eve_allapotat_meri(self):
        poziciok = elokeszites([0], ["Z"], ["X"], ["X"])
        with patch("bb84.random.choice", return_value=1) as sorsolas:
            eve_merese(poziciok)
            self.assertEqual(poziciok[0]["bob"], ("X", None))
            bob_merese(poziciok)
        self.assertEqual(poziciok[0]["eve"], ("X", 1))
        self.assertEqual(poziciok[0]["bob"], ("X", 1))
        self.assertEqual(poziciok[0]["alice"], ("Z", 0))
        sorsolas.assert_called_once_with((0, 1))

    def test_eve_eltero_bazisa_hibat_is_okozhat_de_nem_kotelezo(self):
        for bob_bit in (0, 1):
            with self.subTest(bob_bit=bob_bit):
                poziciok = elokeszites([0], ["Z"], ["Z"], ["X"])
                with patch("bb84.random.choice", side_effect=[1, bob_bit]):
                    eve_merese(poziciok)
                    bob_merese(poziciok)
                self.assertEqual(poziciok[0]["bob"], ("Z", bob_bit))
                self.assertIsNone(poziciok[0]["megtartva"])
                self.assertFalse(poziciok[0]["ellenorzo_minta"])

    def test_ismetelt_tamadas_es_meres_megorzi_a_nullas_bitet(self):
        poziciok = elokeszites([1], ["Z"], ["X"], ["X"])
        with patch("bb84.random.choice", return_value=0) as sorsolas:
            eve_merese(poziciok)
            eve_merese(poziciok)
            bob_merese(poziciok)
            eve_merese(poziciok)
            bob_merese(poziciok)
        self.assertEqual(poziciok[0]["eve"], ("X", 0))
        self.assertEqual(poziciok[0]["bob"], ("X", 0))
        sorsolas.assert_called_once_with((0, 1))

    def test_bob_nem_elozheti_meg_evet_reszleges_modositas_sincs(self):
        poziciok = elokeszites([0, 1], ["Z", "Z"], ["Z", "Z"], ["Z", "X"])
        poziciok[0]["eve"] = ("Z", 0)
        with self.assertRaises(ValueError):
            bob_merese(poziciok)
        self.assertTrue(all(p["bob"][1] is None for p in poziciok))

    def test_eve_nem_irhatja_at_bob_mar_elvegzett_mereset(self):
        poziciok = elokeszites([0, 1], ["Z", "Z"], ["Z", "Z"], ["X", "X"])
        poziciok[1]["bob"] = ("Z", 1)
        with self.assertRaises(ValueError):
            eve_merese(poziciok)
        self.assertTrue(all(p["eve"][1] is None for p in poziciok))


class SzuresTests(unittest.TestCase):
    def test_a_hatpozicios_pelda_szurt_sorozata_010(self):
        poziciok = elokeszites(
            [0, 1, 1, 0, 1, 0],
            ["Z", "X", "Z", "X", "X", "Z"],
            ["Z", "Z", "Z", "X", "Z", "X"],
        )
        with patch("bb84.random.choice", side_effect=[0, 1, 1]):
            bob_merese(poziciok)
        eredeti_adatok = [p.copy() for p in poziciok]

        szures(poziciok)

        self.assertEqual(
            [p["megtartva"] for p in poziciok],
            [True, False, True, True, False, False],
        )
        for resztvevo in ("alice", "bob"):
            self.assertEqual(
                [p[resztvevo][1] for p in poziciok if p["megtartva"]],
                [0, 1, 0],
            )
        self.assertEqual(len(poziciok), len(eredeti_adatok))
        for pozicio, eredeti in zip(poziciok, eredeti_adatok):
            for kulcs in ("alice", "eve", "bob", "ellenorzo_minta"):
                self.assertEqual(pozicio[kulcs], eredeti[kulcs])

    def test_azonos_bazisu_hibas_bitet_is_megtartja(self):
        poziciok = elokeszites([0], ["Z"], ["Z"], ["X"])
        with patch("bb84.random.choice", side_effect=[1, 1]):
            eve_merese(poziciok)
            bob_merese(poziciok)

        szures(poziciok)

        self.assertTrue(poziciok[0]["megtartva"])
        self.assertEqual(poziciok[0]["alice"], ("Z", 0))
        self.assertEqual(poziciok[0]["bob"], ("Z", 1))

    def test_eltero_bazisu_egyezo_bitet_is_elveti(self):
        poziciok = elokeszites([0], ["Z"], ["X"])
        with patch("bb84.random.choice", return_value=0):
            bob_merese(poziciok)

        szures(poziciok)

        self.assertFalse(poziciok[0]["megtartva"])
        self.assertEqual(len(poziciok), 1)

    def test_hianyzo_bob_meresnel_nincs_reszleges_modositas(self):
        poziciok = elokeszites([0, 1], ["Z", "X"], ["Z", "X"])
        bob_merese(poziciok[:1])

        with self.assertRaises(ValueError):
            szures(poziciok)

        self.assertTrue(all(p["megtartva"] is None for p in poziciok))

    def test_ismetelt_szures_megorzi_az_eredmenyt_es_a_mintajelolest(self):
        poziciok = elokeszites([0], ["Z"], ["Z"])
        bob_merese(poziciok)
        szures(poziciok)
        poziciok[0]["ellenorzo_minta"] = True
        elozo_allapot = [p.copy() for p in poziciok]

        szures(poziciok)

        self.assertEqual(poziciok, elozo_allapot)

    def test_ures_poziciolista_is_kezelheto(self):
        poziciok = []
        szures(poziciok)
        self.assertEqual(poziciok, [])


if __name__ == "__main__":
    unittest.main()
