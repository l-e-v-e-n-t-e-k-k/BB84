"""A BB84 léptetése a böngészős felülettől függetlenül."""

from bb84 import (
    bob_merese,
    elokeszites,
    eve_merese,
    kulcsjeloltek,
    mintavetel,
    qber,
    szures,
)


class FutasVezerlo:
    """Egy futás adatait és aktuális fázisát kezeli.

    Létrehozáskor Alice előkészítése már megtörténik, de még senki sem
    mért. A kovetkezo() egy qubitet mér, az osszes_merese() az aktuális
    mérési fázis összes hátralévő qubitjét. Az utolsó mérés után a fázis
    még látható marad; a következő kovetkezo() indítja a következő fázist.

    A mérések után a szűrés, mintavétel és eredményszámítás egy-egy lépés.
    Új beállításokkal új példányt kell létrehozni, így az előző futás
    eredményei nem keverednek az újakkal. A felület az adatokat olvassa,
    a műveleteket ezeken a metódusokon keresztül indítja.
    """

    def __init__(
        self,
        alice_bitek: list[int],
        alice_bazisok: list[str],
        bob_bazisok: list[str],
        eve_bazisok: list[str] | None = None,
        mintaszazalek: float = 25,
    ) -> None:
        # Már induláskor jelezzük a hibát, ne csak a mintavételi fázisban
        if (
            isinstance(mintaszazalek, bool)
            or not isinstance(mintaszazalek, (int, float))
            or not 0 <= mintaszazalek <= 100
        ):
            raise ValueError("A mintavetel szazaleka 0 es 100 kozotti szam legyen")

        self.poziciok = elokeszites(
            alice_bitek, alice_bazisok, bob_bazisok, eve_bazisok
        )
        self.mintaszazalek = mintaszazalek
        self.fazis = "elokeszites"
        self.hibaarany: float | None = None
        self.alice_kulcs: list[int] | None = None
        self.bob_kulcs: list[int] | None = None

    @property
    def kovetkezo_merendo(self) -> int | None:
        """A következő mérendő pozíció 0-tól induló indexe, vagy None.

        Az eltárolt bitekből keressük ki, nem külön számlálót növelünk.
        Így az egyenkénti és az összes mérés ugyanazt a haladást mutatja.
        A tulajdonság olvasása nem hajt végre mérést vagy fázisváltást.
        """
        fazis = self.fazis
        if fazis == "elokeszites":
            fazis = self._elso_meresi_fazis()

        if fazis == "eve_merese":
            resztvevo = "eve"
        elif fazis == "bob_merese":
            resztvevo = "bob"
        else:
            return None

        for index, pozicio in enumerate(self.poziciok):
            if pozicio[resztvevo][1] is None:
                return index
        return None

    def _elso_meresi_fazis(self) -> str:
        """Eve nélkül kihagyjuk a támadási fázist."""
        if self.poziciok[0]["eve"] is None:
            return "bob_merese"
        return "eve_merese"

    def kovetkezo(self) -> None:
        """Egy mérés vagy egy közös protokoll-lépés végrehajtása.

        Az első hívás az előkészítés után rögtön az első qubitet méri.
        Befejezett Eve-fázis után Bob első mérésére lépünk. Befejezett
        Bob-fázis után a szűrés jön.
        """
        if self.fazis == "eredmenyek":
            return
        if self.fazis == "elokeszites":
            self.fazis = self._elso_meresi_fazis()

        # Csak a legutolsó mérés UTÁNI kattintás vált fázist.
        if self.fazis == "eve_merese" and self.kovetkezo_merendo is None:
            self.fazis = "bob_merese"
        elif self.fazis == "bob_merese" and self.kovetkezo_merendo is None:
            szures(self.poziciok)
            self.fazis = "szures"
            return

        if self.fazis == "eve_merese":
            index = self.kovetkezo_merendo
            # Egyetlen szótárat adunk át, ugyanazt, amely a teljes listában van.
            eve_merese([self.poziciok[index]])
        elif self.fazis == "bob_merese":
            index = self.kovetkezo_merendo
            bob_merese([self.poziciok[index]])
        elif self.fazis == "szures":
            mintavetel(self.poziciok, self.mintaszazalek)
            self.fazis = "mintavetel"
        elif self.fazis == "mintavetel":
            self.hibaarany = qber(self.poziciok)
            self.alice_kulcs, self.bob_kulcs = kulcsjeloltek(self.poziciok)
            # Az üres minta hibaaránya None, mégis befejezett az eredményfázis.
            self.fazis = "eredmenyek"

    def osszes_merese(self) -> None:
        """Az aktuális fázis hátralévő méréseit végzi el, fázisváltás nélkül.

        Előkészítés után az első mérési fázist kezdi el. A már mért biteket egyik fázisban sem sorsolja újra.
        Szűréskor, mintavételkor és a kész eredményeknél nem használható.
        """
        if self.fazis == "elokeszites":
            self.fazis = self._elso_meresi_fazis()

        if self.fazis == "eve_merese":
            eve_merese(self.poziciok)
        elif self.fazis == "bob_merese":
            bob_merese(self.poziciok)
        else:
            raise ValueError("Az osszes merese csak meresi fazisban hasznalhato")
