"""Helyi webes kapcsolat a felület és a BB84-futásvezérlő között."""

from copy import deepcopy
import secrets
from threading import RLock
from uuid import uuid4

from flask import Flask, jsonify, render_template, request, session
from werkzeug.exceptions import HTTPException

from controller import FutasVezerlo


def create_app() -> Flask:
    """Létrehozza a webalkalmazást, elkülönített böngészőmunkamenetekkel.

    A futások csak a helyi szerver memóriájában élnek. A böngésző sütije
    egy azonosítót tartalmaz, nem a kvantumállapotokat vagy kulcsjelölteket.
    A szerver újraindítása új kísérletet jelent.
    """
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=secrets.token_hex(32),
        MAX_CONTENT_LENGTH=65536,
        SESSION_COOKIE_SAMESITE="Strict",
        SESSION_COOKIE_HTTPONLY=True,
    )
    futasok = {}
    zar = RLock()

    def pillanatkep(futas):
        # Másolatot mentünk: a későbbi mérés nem írhatja át egy korábbi fázis nézetét.
        return deepcopy({
            "fazis": futas.fazis,
            "poziciok": futas.poziciok,
            "kovetkezo_merendo": futas.kovetkezo_merendo,
            "eve_aktiv": futas.poziciok[0]["eve"] is not None,
            "mintaszazalek": futas.mintaszazalek,
            "hibaarany": futas.hibaarany,
            "alice_kulcs": futas.alice_kulcs,
            "bob_kulcs": futas.bob_kulcs,
        })

    def aktualis_futas():
        return futasok.get(session.get("futas_id"))

    def valasz(tarolt):
        if tarolt is None:
            return jsonify(allapot=None, elozmenyek=[])
        fazis = tarolt["vezerlo"].fazis
        return jsonify(
            allapot=tarolt["elozmenyek"][fazis],
            elozmenyek=list(tarolt["elozmenyek"].values()),
        )

    def sorozat(adatok, nev, megengedett):
        ertek = adatok.get(nev)
        if not isinstance(ertek, str):
            raise ValueError("A biteket és bázisokat szöveges sorozatként add meg.")
        # A szóközök segíthetik a csoportosítást; az ismeretlen jeleket nem nyeljük el.
        ertek = "".join(ertek.split()).upper()
        if not ertek or any(jel not in megengedett for jel in ertek):
            raise ValueError("A bitekhez 0/1, a bázisokhoz Z/X jeleket használj.")
        return ertek

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/allapot")
    def allapot():
        # Olvasáskor nem hívunk számítási műveletet: a frissítés nem változtat a futáson.
        with zar:
            return valasz(aktualis_futas())

    @app.post("/api/inditas")
    def inditas():
        adatok = request.get_json()
        if not isinstance(adatok, dict):
            raise ValueError("A beállításoknak objektumként kell érkezniük.")
        darab = adatok.get("darab")
        if type(darab) is not int or not 1 <= darab <= 256:
            raise ValueError("A qubitek száma 1 és 256 közötti egész szám legyen.")
        eve_aktiv = adatok.get("eve_aktiv", False)
        if type(eve_aktiv) is not bool:
            raise ValueError("Eve beállítása be- vagy kikapcsolt érték legyen.")

        bitek = sorozat(adatok, "alice_bitek", "01")
        alice_bazisok = sorozat(adatok, "alice_bazisok", "ZX")
        bob_bazisok = sorozat(adatok, "bob_bazisok", "ZX")
        eve_bazisok = sorozat(adatok, "eve_bazisok", "ZX") if eve_aktiv else None
        sorozatok = [bitek, alice_bazisok, bob_bazisok]
        if eve_bazisok is not None:
            sorozatok.append(eve_bazisok)
        if any(len(sor) != darab for sor in sorozatok):
            raise ValueError(f"Minden aktív sorozat pontosan {darab} jelből álljon.")

        futas = FutasVezerlo(
            [int(bit) for bit in bitek], list(alice_bazisok), list(bob_bazisok),
            list(eve_bazisok) if eve_bazisok is not None else None,
            mintaszazalek=adatok.get("mintaszazalek", 25),
        )
        with zar:
            # Hibás új beállításnál a régi futást megőrizzük; csak kész előkészítés után cserélünk.
            futasok.pop(session.get("futas_id"), None)
            azonosito = uuid4().hex
            session["futas_id"] = azonosito
            tarolt = {"vezerlo": futas, "elozmenyek": {futas.fazis: pillanatkep(futas)}}
            futasok[azonosito] = tarolt
            return valasz(tarolt)

    def muvelet(osszes=False):
        # Egy böngésző párhuzamos kérései sem írhatják egyszerre a futást.
        with zar:
            tarolt = aktualis_futas()
            if tarolt is None:
                return jsonify(hiba="Először indíts egy kísérletet."), 409
            futas = tarolt["vezerlo"]
            if osszes:
                futas.osszes_merese()
            else:
                futas.kovetkezo()
            tarolt["elozmenyek"][futas.fazis] = pillanatkep(futas)
            return valasz(tarolt)

    @app.post("/api/kovetkezo")
    def kovetkezo():
        return muvelet()

    @app.post("/api/osszes")
    def osszes():
        return muvelet(osszes=True)

    @app.post("/api/uj")
    def uj():
        with zar:
            futasok.pop(session.pop("futas_id", None), None)
            return valasz(None)

    @app.errorhandler(ValueError)
    def hibas_bemenet(hiba):
        return jsonify(hiba=str(hiba)), 400

    @app.errorhandler(HTTPException)
    def http_hiba(hiba):
        return jsonify(hiba="A kérés nem dolgozható fel. Ellenőrizd a megadott adatokat."), hiba.code

    @app.after_request
    def gyorsitotar_tiltasa(valasz_obj):
        if request.path.startswith("/api/"):
            valasz_obj.headers["Cache-Control"] = "no-store"
        return valasz_obj

    return app


if __name__ == "__main__":
    from waitress import serve

    print("BB84 labor: http://127.0.0.1:8765 — leállítás: Ctrl+C", flush=True)
    serve(create_app(), host="127.0.0.1", port=8765)
