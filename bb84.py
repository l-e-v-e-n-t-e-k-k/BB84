"""Az ideális, zajmentes BB84-modell elemi műveletei."""

import random


def meres(allapot: tuple[str, int], meresi_bazis: str) -> int:
    """Visszaadja a mért bitet, az eredeti állapot módosítása nélkül.

    Az állapot (bázis, bit) alakú. A bázisok "Z" vagy "X",
    a bit 0 vagy 1 lehet. A hívó érvényes bemeneteket ad át.
    """
    if allapot[0] == meresi_bazis:
        return allapot[1]
    else:
        return random.choice((0, 1))
