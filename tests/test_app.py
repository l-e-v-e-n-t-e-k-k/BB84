import unittest
from unittest.mock import patch

from app import create_app


class WebTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()

    def inditas(self, **valtozasok):
        adatok = {
            "darab": 2, "alice_bitek": "01", "alice_bazisok": "ZZ",
            "bob_bazisok": "ZZ", "eve_aktiv": True, "eve_bazisok": "XX",
            "mintaszazalek": 50,
        }
        adatok.update(valtozasok)
        return self.client.post("/api/inditas", json=adatok)

    def test_felulet_es_minden_helyi_asset_elerheto(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn('lang="hu"', response.text)
        for path in ("style.css", "app.js", "fonts/Anybody.ttf", "fonts/Commissioner.ttf",
                     "fonts/anybody-OFL.txt", "fonts/commissioner-OFL.txt"):
            with self.subTest(path=path):
                asset = self.client.get("/static/" + path)
                self.assertEqual(asset.status_code, 200)
                self.assertGreater(len(asset.data), 100)
                asset.close()

    def test_elso_lekeres_nem_indit_futast(self):
        response = self.client.get("/api/allapot")
        self.assertEqual(response.json, {"allapot": None, "elozmenyek": []})
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_futas_nelkul_nem_lehet_merni(self):
        for endpoint in ("kovetkezo", "osszes"):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.client.post("/api/" + endpoint).status_code, 409)

    def test_egy_meres_osszes_meres_es_frissites(self):
        initial = self.inditas().json
        with patch("bb84.random.choice", side_effect=[1, 0]):
            first = self.client.post("/api/kovetkezo").json
            self.assertEqual(first["allapot"]["poziciok"][0]["eve"], ["X", 1])
            self.assertEqual(first["allapot"]["poziciok"][1]["eve"], ["X", None])
            complete = self.client.post("/api/osszes").json
        self.assertEqual(complete["allapot"]["fazis"], "eve_merese")
        self.assertTrue(all(p["bob"][1] is None for p in complete["allapot"]["poziciok"]))
        self.assertEqual(self.client.get("/api/allapot").json, complete)
        # A korábbi fázisban továbbra is a mérés előtti állapot látható.
        self.assertEqual(complete["elozmenyek"][0], initial["allapot"])

    def test_teljes_futas_es_mintaveteli_elozmenyek(self):
        self.inditas()
        with patch("bb84.random.choice", side_effect=[1, 0, 1, 1]):
            self.client.post("/api/osszes")
            self.client.post("/api/kovetkezo")
            self.client.post("/api/osszes")
        filtered = self.client.post("/api/kovetkezo").json
        self.assertEqual(filtered["allapot"]["fazis"], "szures")
        self.client.post("/api/kovetkezo")
        final = self.client.post("/api/kovetkezo").json
        self.assertEqual(final["allapot"]["fazis"], "eredmenyek")
        self.assertEqual(len(final["allapot"]["alice_kulcs"]), 1)
        self.assertEqual([s["fazis"] for s in final["elozmenyek"]], [
            "elokeszites", "eve_merese", "bob_merese", "szures", "mintavetel", "eredmenyek",
        ])
        self.assertEqual(final["elozmenyek"][3], filtered["allapot"])
        self.assertEqual(self.client.post("/api/kovetkezo").json, final)
        self.assertEqual(self.client.post("/api/osszes").status_code, 400)
        self.assertEqual(self.client.get("/api/allapot").json, final)

    def test_kulon_bongeszomunkamenetek_nem_keverednek(self):
        first = self.inditas().json
        other = self.app.test_client()
        self.assertIsNone(other.get("/api/allapot").json["allapot"])
        self.assertEqual(self.client.get("/api/allapot").json, first)

    def test_hibas_uj_beallitas_megorzi_a_regi_futast(self):
        initial = self.inditas().json
        for valtozas in (
            {"darab": 0}, {"darab": 257}, {"darab": True},
            {"alice_bitek": "0"}, {"alice_bitek": "02"}, {"alice_bazisok": "ZY"},
            {"bob_bazisok": ["Z", "Z"]}, {"eve_bazisok": "Z"},
            {"mintaszazalek": 101}, {"mintaszazalek": True}, {"eve_aktiv": "true"},
        ):
            with self.subTest(valtozas=valtozas):
                response = self.inditas(**valtozas)
                self.assertEqual(response.status_code, 400)
                self.assertIn("hiba", response.json)
                self.assertEqual(self.client.get("/api/allapot").json, initial)

    def test_szokoz_es_kisbetus_bazis_elfogadhato(self):
        response = self.inditas(alice_bitek="0 1", alice_bazisok="z z", eve_bazisok="x x")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["allapot"]["poziciok"][0]["alice"], ["Z", 0])

    def test_eve_nelkul_nullas_mintaval_is_befejezheto(self):
        self.inditas(eve_aktiv=False, eve_bazisok="", mintaszazalek=0)
        self.client.post("/api/osszes")
        for _ in range(3):
            final = self.client.post("/api/kovetkezo").json
        self.assertIsNone(final["allapot"]["hibaarany"])
        self.assertEqual(final["allapot"]["alice_kulcs"], [0, 1])
        self.assertEqual(final["allapot"]["bob_kulcs"], [0, 1])
        self.assertNotIn("eve_merese", [s["fazis"] for s in final["elozmenyek"]])

    def test_uj_futas_torli_az_elozmenyeket(self):
        self.inditas()
        self.client.post("/api/kovetkezo")
        response = self.inditas(eve_aktiv=False)
        self.assertEqual(len(response.json["elozmenyek"]), 1)
        self.assertTrue(all(p["bob"][1] is None for p in response.json["allapot"]["poziciok"]))
        self.assertIsNone(self.client.post("/api/uj").json["allapot"])
        self.assertIsNone(self.client.get("/api/allapot").json["allapot"])

    def test_hibas_json_ertheto_valaszt_ad(self):
        response = self.client.post("/api/inditas", data="{", content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("hiba", response.json)
        self.assertEqual(self.client.post("/api/inditas", json=[]).status_code, 400)


if __name__ == "__main__":
    unittest.main()
