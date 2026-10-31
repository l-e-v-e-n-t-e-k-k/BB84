"""Az ideális BB84-modell elemi műveletei."""

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


def elokeszites(alice_bitek: list[int],alice_bazisok: list[str],bob_bazisok: list[str],) -> list[dict]:
    """Létrehozza egy Eve nélküli futás mérés előtti pozícióit.

    Üres, eltérő hosszúságú vagy érvénytelen értékeket tartalmazó
    bemeneti listáknál ValueError hibát jelez. A bemeneteket megőrzi.
    """
    if not alice_bitek:
        raise ValueError("Legalább egy bitet meg kell adni")
    if not (len(alice_bitek) == len(alice_bazisok) == len(bob_bazisok)):
        raise ValueError("A bitek és a bázisok listái legyenek azonos hosszúságúak")
    if any(bit not in (0, 1) for bit in alice_bitek):
        raise ValueError("Alice bitjei csak 0 vagy 1 ertekuek lehetnek")
    for nev, bazisok in (("Alice", alice_bazisok), ("Bob", bob_bazisok)):
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

    return poziciok


def bob_merese(poziciok: list[dict]) -> None:
    """Eltárolja Bob méréseit az előkészített, Eve nélküli futásban.
    """
    for pozicio in poziciok:
        bob_bazis, korabbi_bit = pozicio["bob"]
        if korabbi_bit is not None:
            continue

        mert_bit = meres(pozicio["alice"], bob_bazis)
        pozicio["bob"] = (bob_bazis, mert_bit)
