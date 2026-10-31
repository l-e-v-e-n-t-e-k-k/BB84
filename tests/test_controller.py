import unittest
from unittest.mock import patch

from controller import FutasVezerlo


class FutasVezerloTests(unittest.TestCase):
    def test_elokesziteskor_meg_nincs_meres_es_a_lekerdezes_sem_indit(self):
        futas = FutasVezerlo([0, 1], ["Z", "X"], ["Z", "X"], ["X", "Z"])
        eredeti = [p.copy() for p in futas.poziciok]

        with patch("bb84.random.choice") as sorsolas:
            self.assertEqual(futas.kovetkezo_merendo, 0)
            self.assertEqual(futas.kovetkezo_merendo, 0)

        self.assertEqual(futas.fazis, "elokeszites")
        self.assertEqual(futas.poziciok, eredeti)
        self.assertIsNone(futas.alice_kulcs)
        self.assertIsNone(futas.bob_kulcs)
        sorsolas.assert_not_called()

    def test_kovetkezo_egyetlen_eve_merest_vegez(self):
        futas = FutasVezerlo([0, 0], ["Z", "Z"], ["Z", "Z"], ["X", "X"])

        with patch("bb84.random.choice", return_value=1) as sorsolas:
            futas.kovetkezo()

        self.assertEqual(futas.fazis, "eve_merese")
        self.assertEqual([p["eve"] for p in futas.poziciok], [("X", 1), ("X", None)])
        self.assertTrue(all(p["bob"][1] is None for p in futas.poziciok))
        self.assertEqual(futas.kovetkezo_merendo, 1)
        sorsolas.assert_called_once_with((0, 1))

    def test_osszes_csak_eve_hatralevo_mereseit_vegezi(self):
        futas = FutasVezerlo([0] * 3, ["Z"] * 3, ["Z"] * 3, ["X"] * 3)

        with patch("bb84.random.choice", side_effect=[1, 0, 1]) as sorsolas:
            futas.kovetkezo()
            futas.osszes_merese()
            futas.osszes_merese()

        self.assertEqual([p["eve"][1] for p in futas.poziciok], [1, 0, 1])
        self.assertTrue(all(p["bob"][1] is None for p in futas.poziciok))
        self.assertEqual(futas.fazis, "eve_merese")
        self.assertIsNone(futas.kovetkezo_merendo)
        self.assertEqual(sorsolas.call_count, 3)

    def test_eve_utan_a_kovetkezo_kattintas_bob_elso_qubitjet_meri(self):
        futas = FutasVezerlo([0, 0], ["Z"] * 2, ["Z"] * 2, ["X"] * 2)
        with patch("bb84.random.choice", side_effect=[1, 0, 1]):
            futas.osszes_merese()
            self.assertTrue(all(p["bob"][1] is None for p in futas.poziciok))
            futas.kovetkezo()

        self.assertEqual(futas.fazis, "bob_merese")
        self.assertEqual([p["bob"] for p in futas.poziciok], [("Z", 1), ("Z", None)])
        self.assertEqual(futas.kovetkezo_merendo, 1)

    def test_eve_nelkul_bobbal_kezd_es_egy_qubitet_mer(self):
        futas = FutasVezerlo([0, 1], ["Z", "X"], ["Z", "X"])
        futas.kovetkezo()

        self.assertEqual(futas.fazis, "bob_merese")
        self.assertEqual([p["bob"] for p in futas.poziciok], [("Z", 0), ("X", None)])
        self.assertTrue(all(p["eve"] is None for p in futas.poziciok))

    def test_bob_osszes_merese_nem_szur_es_nem_sorsol_ujra(self):
        futas = FutasVezerlo([1] * 3, ["Z"] * 3, ["X"] * 3)
        with patch("bb84.random.choice", side_effect=[0, 1, 0]) as sorsolas:
            futas.kovetkezo()
            futas.osszes_merese()
            futas.osszes_merese()

        self.assertEqual([p["bob"][1] for p in futas.poziciok], [0, 1, 0])
        self.assertTrue(all(p["megtartva"] is None for p in futas.poziciok))
        self.assertEqual(futas.fazis, "bob_merese")
        self.assertIsNone(futas.kovetkezo_merendo)
        self.assertEqual(sorsolas.call_count, 3)

    def test_teljes_tamadasos_futas_kulon_szures_minta_es_eredmeny_lepesekkel(self):
        futas = FutasVezerlo([0, 1], ["Z"] * 2, ["Z"] * 2, ["X"] * 2, 50)
        with patch("bb84.random.choice", side_effect=[1, 0, 1, 1]):
            futas.osszes_merese()  # Eve két mérése.
            futas.kovetkezo()     # Bob első mérése.
            futas.osszes_merese()  # Bob második mérése.

        futas.kovetkezo()
        self.assertEqual(futas.fazis, "szures")
        self.assertTrue(all(p["megtartva"] for p in futas.poziciok))
        self.assertTrue(all(not p["ellenorzo_minta"] for p in futas.poziciok))

        with patch("bb84.random.sample", return_value=[futas.poziciok[0]]):
            futas.kovetkezo()
        self.assertEqual(futas.fazis, "mintavetel")
        self.assertIsNone(futas.alice_kulcs)
        self.assertTrue(futas.poziciok[0]["ellenorzo_minta"])

        futas.kovetkezo()
        self.assertEqual(futas.fazis, "eredmenyek")
        self.assertEqual(futas.hibaarany, 1.0)
        self.assertEqual(futas.alice_kulcs, [1])
        self.assertEqual(futas.bob_kulcs, [1])
        self.assertIsNone(futas.kovetkezo_merendo)

    def test_teljesen_egyenkenti_futas_sorrendje(self):
        futas = FutasVezerlo([0, 1], ["Z", "X"], ["Z", "X"], ["Z", "X"], 0)
        fazisok = []
        for _ in range(7):
            futas.kovetkezo()
            fazisok.append(futas.fazis)

        self.assertEqual(fazisok, [
            "eve_merese", "eve_merese", "bob_merese", "bob_merese",
            "szures", "mintavetel", "eredmenyek",
        ])
        self.assertIsNone(futas.hibaarany)
        self.assertEqual(futas.alice_kulcs, [0, 1])
        self.assertEqual(futas.bob_kulcs, [0, 1])

    def test_ures_szures_es_teljes_minta_is_befejezheto(self):
        for bob_bazis, szazalek in (("X", 25), ("Z", 100)):
            with self.subTest(bob_bazis=bob_bazis, szazalek=szazalek):
                futas = FutasVezerlo([0], ["Z"], [bob_bazis], mintaszazalek=szazalek)
                futas.osszes_merese()
                for _ in range(3):
                    futas.kovetkezo()
                self.assertEqual(futas.fazis, "eredmenyek")
                self.assertEqual(futas.alice_kulcs, [])
                self.assertEqual(futas.bob_kulcs, [])

    def test_kesz_futason_ujabb_kattintas_nem_valtoztat(self):
        futas = FutasVezerlo([0], ["Z"], ["Z"], mintaszazalek=100)
        futas.osszes_merese()
        for _ in range(3):
            futas.kovetkezo()
        eredeti = [p.copy() for p in futas.poziciok]

        with patch("bb84.random.choice") as meres, patch("bb84.random.sample") as minta:
            futas.kovetkezo()
            futas.kovetkezo()

        meres.assert_not_called()
        minta.assert_not_called()
        self.assertEqual(futas.poziciok, eredeti)
        self.assertEqual(futas.fazis, "eredmenyek")

    def test_osszes_gomb_csak_mereskor_hasznalhato(self):
        futas = FutasVezerlo([0], ["Z"], ["Z"])
        futas.osszes_merese()
        for fazis in ("szures", "mintavetel", "eredmenyek"):
            futas.kovetkezo()
            self.assertEqual(futas.fazis, fazis)
            eredeti = [p.copy() for p in futas.poziciok]
            with self.assertRaises(ValueError):
                futas.osszes_merese()
            self.assertEqual(futas.poziciok, eredeti)
            self.assertEqual(futas.fazis, fazis)

    def test_hibas_szazalekot_mar_indulaskor_elutasit(self):
        for szazalek in (-1, 101, "25", True, float("nan")):
            with self.subTest(szazalek=szazalek):
                with self.assertRaises(ValueError):
                    FutasVezerlo([0], ["Z"], ["Z"], mintaszazalek=szazalek)

    def test_uj_futas_nem_orokli_a_regi_eredmenyeit(self):
        regi = FutasVezerlo([0], ["Z"], ["Z"])
        regi.osszes_merese()
        for _ in range(3):
            regi.kovetkezo()

        uj = FutasVezerlo([0], ["Z"], ["Z"])

        self.assertEqual(uj.fazis, "elokeszites")
        self.assertEqual(uj.poziciok[0]["bob"], ("Z", None))
        self.assertIsNone(uj.poziciok[0]["megtartva"])
        self.assertFalse(uj.poziciok[0]["ellenorzo_minta"])
        self.assertIsNone(uj.alice_kulcs)
        self.assertEqual(regi.fazis, "eredmenyek")


if __name__ == "__main__":
    unittest.main()
