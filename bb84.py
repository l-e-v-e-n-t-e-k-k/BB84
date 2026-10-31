"""Az ideális BB84-modell elemi műveletei."""

import math
import random

def meres(allapot: tuple[str, int], meresi_bazis: str) -> int:
    """Visszaadja a mért bitet, az eredeti állapot módosítása nélkül.

    Az állapot (bázis, bit) alakú. A bázisok "Z" vagy "X",
    a bit 0 vagy 1 lehet. A hívó érvényes bemeneteket ad át
    """
    if allapot[0] == meresi_bazis:
        return allapot[1]
    else:
        return random.choice((0, 1))


def elokeszites(alice_bitek: list[int], alice_bazisok: list[str], bob_bazisok: list[str], eve_bazisok: list[str] | None = None,) -> list[dict]:
    """Létrehozza a futás mérés előtti pozícióit.

    Üres, eltérő hosszúságú vagy érvénytelen értékeket tartalmazó
    bemeneti listáknál ValueError hibát jelez. A bemeneteket megőrzi.
    Eve bázislistája elhagyható: ekkor nincs támadó. Megadott listánál
    Eve minden pozíciót támad, a mért bitje kezdetben None.
    """
    if not alice_bitek:
        raise ValueError("Legalabb egy bitet meg kell adni")
    
    if not (len(alice_bitek) == len(alice_bazisok) == len(bob_bazisok)):
        raise ValueError("A bitek és a bazisok listái legyenek azonos hosszusaguak")
    if eve_bazisok is not None and len(eve_bazisok) != len(alice_bitek):
        raise ValueError("Eve bazislistaja is legyen ugyanolyan hosszusagu")
    
    if any(bit not in (0, 1) for bit in alice_bitek):
        raise ValueError("Alice bitjei csak 0 vagy 1 ertekuek lehetnek")
    
    bazis_listak = [("Alice", alice_bazisok), ("Bob", bob_bazisok)]
    if eve_bazisok is not None:
        bazis_listak.append(("Eve", eve_bazisok))

    for nev, bazisok in bazis_listak:
        if any(bazis not in ("Z", "X") for bazis in bazisok):
            raise ValueError(f"{nev} bazisai csak Z vagy X ertekuek lehetnek")

    #Itt minden kvantumbithez 1 szótárat hozunk létre, a poziciok a szótárak listája.
    poziciok = []
    # A zip a bemeneti listák elemeit párosítja. Bemeneti lista pl.: ([0, 1], ["Z", "X"], ["X", "X"])
    for bit, alice_bazis, bob_bazis in zip(
        alice_bitek, alice_bazisok, bob_bazisok
    ):
        pozicio = {
            "alice": (alice_bazis, bit),
            "eve": None,
            "bob": (bob_bazis, None),
            "megtartva": None,
            "ellenorzo_minta": False,
        }
        poziciok.append(pozicio)

    if eve_bazisok is not None:
        for pozicio, eve_bazis in zip(poziciok, eve_bazisok):
            # A tuple létezik, de Eve mérése még külön lépésben következik.
            pozicio["eve"] = (eve_bazis, None)

    return poziciok


def eve_merese(poziciok: list[dict]) -> None:
    """Megméri Alice állapotait, és eltárolja Eve újraküldött állapotait.

    Helyben módosítja a kapott szótárakat. A None Eve-mező támadó nélküli
    pozíciót jelöl, a (bázis, None) pedig még el nem végzett támadást.
    A már mért biteket megőrzi, ismételt híváskor sem sorsolja újra.
    """
    # Előbb a teljes listát ellenőrizzük, hogy hibánál ne legyen félkész lépés.
    for pozicio in poziciok:
        if (
            pozicio["eve"] is not None
            and pozicio["eve"][1] is None
            and pozicio["bob"][1] is not None
        ):
            raise ValueError("Eve tamadasat Bob merese elott kell vegrehajtani")

    for pozicio in poziciok:
        if pozicio["eve"] is None:
            continue
        eve_bazis, korabbi_bit = pozicio["eve"]
        if korabbi_bit is not None:
            continue

        eve_bitje = meres(pozicio["alice"], eve_bazis)
        # A bit önmagában kevés: Bob az Eve-bázisban előkészített új állapotot méri.
        pozicio["eve"] = (eve_bazis, eve_bitje)


def bob_merese(poziciok: list[dict]) -> None:
    """Eltárolja Bob méréseit, az eredeti Alice-adatok megőrzésével.

    Támadó nélkül Alice, támadással Eve újraküldött állapotát méri.
    Aktív Eve esetén előbb az eve_merese() lépést kell végrehajtani.
    A szótárakat helyben módosítja, a már mért pozíciókat kihagyja.
    """
    for pozicio in poziciok:
        if pozicio["eve"] is not None and pozicio["eve"][1] is None:
            raise ValueError("Bob merese elott Eve mereset is vegre kell hajtani")

    for pozicio in poziciok:
        bob_bazis, korabbi_bit = pozicio["bob"]
        if korabbi_bit is not None:
            continue

        if pozicio["eve"] is None:
            bemeneti_allapot = pozicio["alice"]
        else:
            bemeneti_allapot = pozicio["eve"]

        mert_bit = meres(bemeneti_allapot, bob_bazis)
        pozicio["bob"] = (bob_bazis, mert_bit)


def szures(poziciok: list[dict]) -> None:
    """Megjelöli az azonos Alice–Bob bázisú pozíciókat megtartottként.

    Bobnak előbb minden pozíciót meg kell mérnie. A függvény helyben
    módosítja a megtartva mezőket.
    """
    for pozicio in poziciok:
        if pozicio["bob"][1] is None:
            raise ValueError("A szures elott Bob minden mereset vegre kell hajtani")

    for pozicio in poziciok:
        # A biteltérés megmarad: Eve hatását majd az ellenőrző minta vizsgálja
        if pozicio["alice"][0] == pozicio["bob"][0]:
            pozicio["megtartva"] = True
        else:
            pozicio["megtartva"] = False


def mintavetel(poziciok: list[dict], szazalek: float) -> None:
    """Százalék alapján megjelöli a nyilvánosan ellenőrzendő pozíciókat.

    A mintaméretet felfelé kerekítjük,
    ezért pozitív százalék és nem üres szűrt sorozat mellett legalább
    egy pozíciót választunk. A 0% és az üres szűrt sorozat üres mintát ad.
    Előbb minden pozíció szűrését el kell végezni.

    Másik minta kipróbálásához új futás kell.
    """
    if (
        isinstance(szazalek, bool)
        or not isinstance(szazalek, (int, float))
        or not 0 <= szazalek <= 100
    ):
        raise ValueError("A mintavetel szazaleka 0 es 100 kozotti szam legyen")

    megtartott_poziciok = []
    for pozicio in poziciok:
        if pozicio["megtartva"] is None:
            raise ValueError("A mintavetel elott a szurest vegre kell hajtani")
        if pozicio["megtartva"] is True:
            megtartott_poziciok.append(pozicio)

    # Egy újabb lekérés nem sorsolhatja újra a már nyilvánosságra hozott mintát.
    if any(pozicio["ellenorzo_minta"] for pozicio in poziciok):
        return

    mintameret = math.ceil(len(megtartott_poziciok) * szazalek / 100)
    # A sample ismétlés nélkül választ. A kiválasztott elemek ugyanazok a
    # szótárak, ezért a jelölés az eredeti pozíciólistában is megjelenik.
    minta = random.sample(megtartott_poziciok, mintameret)
    for pozicio in minta:
        pozicio["ellenorzo_minta"] = True


def qber(poziciok: list[dict]) -> float | None:
    """Visszaadja az ellenőrző mintában eltérő bitek arányát, 0 és 1 között.

    Pl egy eltérés három ellenőrzött bitből 1/3 eredményt ad.
    Százalékos megjelenítéshez ezt 100-zal kell szorozni.
    Üres mintánál None az eredmény: ez nem azonos a hibamentes, 0 QBER-rel.
    """
    ellenorzott_db = 0
    elteresek = 0
    for pozicio in poziciok:
        if not pozicio["ellenorzo_minta"]:
            continue
        if pozicio["megtartva"] is not True:
            raise ValueError("Ellenorzo mintaba csak megtartott pozicio kerulhet")

        alice_bit = pozicio["alice"][1]
        bob_bit = pozicio["bob"][1]
        if alice_bit is None or bob_bit is None:
            raise ValueError("Az ellenorzo mintaban minden bitnek ismertnek kell lennie")
        ellenorzott_db += 1
        if alice_bit != bob_bit:
            elteresek += 1

    if ellenorzott_db == 0:
        return None
    return elteresek / ellenorzott_db


def kulcsjeloltek(poziciok: list[dict]) -> tuple[list[int], list[int]]:
    """Visszaadja Alice és Bob megmaradó bitjeit két külön listában.

    A mintavétel után hívandó. Csak a megtartott, ellenőrzésre fel nem
    fedett pozíciókat gyűjti, az eredeti sorrendben. Az esetleges hibákat
    nem javítja: a két kulcsjelölt eltérhet. Üres eredménynél ([], []) jár
    vissza
    """
    alice_kulcsjelolt = []
    bob_kulcsjelolt = []
    for pozicio in poziciok:
        if pozicio["megtartva"] is None:
            raise ValueError("A kulcsjeloltek elott a szurest vegre kell hajtani")
        if pozicio["bob"][1] is None:
            raise ValueError("A kulcsjeloltekhez Bob mereseinek ismertnek kell lenniuk")

        # A felfedett mintabitek már nem titkosak, ezért kihagyjuk őket
        if pozicio["megtartva"] is True and pozicio["ellenorzo_minta"] is False:
            alice_kulcsjelolt.append(pozicio["alice"][1])
            bob_kulcsjelolt.append(pozicio["bob"][1])

    return alice_kulcsjelolt, bob_kulcsjelolt
