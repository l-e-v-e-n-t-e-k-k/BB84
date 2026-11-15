"""Elindítja a BB84 helyi szerverét, majd megnyitja a böngészőt."""

import errno
from http.client import HTTPConnection, HTTPException
import socket
import sys
from threading import Event, Thread
from time import monotonic, sleep
import webbrowser


HELYI_CIM = "127.0.0.1"
ALAPERTELMEZETT_PORT = 8765
INDITASI_HATARIDO = 5


def _port_foglalasa(figyelo: socket.socket) -> int:
    # Windowson a kizárólagos foglalás megakadályozza, hogy más is ráálljon a portra.
    opcio = getattr(socket, "SO_EXCLUSIVEADDRUSE", socket.SO_REUSEADDR)
    figyelo.setsockopt(socket.SOL_SOCKET, opcio, 1)
    try:
        figyelo.bind((HELYI_CIM, ALAPERTELMEZETT_PORT))
    except OSError as hiba:
        # A Windows egy kizárólagosan foglalt portnál WSAEACCES-t is adhat.
        if hiba.errno not in (errno.EADDRINUSE, getattr(errno, "WSAEACCES", -1)):
            raise
        figyelo.bind((HELYI_CIM, 0))
    return figyelo.getsockname()[1]


def _var_a_feluletre(port: int, kiszolgalo: Thread) -> None:
    hatarido = monotonic() + INDITASI_HATARIDO
    while monotonic() < hatarido and kiszolgalo.is_alive():
        kapcsolat = HTTPConnection(HELYI_CIM, port, timeout=0.5)
        try:
            kapcsolat.request("GET", "/")
            with kapcsolat.getresponse() as valasz:
                if valasz.status != 200:
                    raise RuntimeError(f"A felület nem töltődött be (HTTP {valasz.status}).")
                valasz.read()
                return
        except (OSError, HTTPException):
            sleep(0.05)
        finally:
            kapcsolat.close()
    if not kiszolgalo.is_alive():
        raise RuntimeError("A helyi szerver indítás közben leállt.")
    raise TimeoutError("A helyi szerver nem válaszolt időben.")


def _szerver_leallitasa(szerver, kiszolgalo: Thread) -> None:
    szerver.accepting = False
    szerver.task_dispatcher.shutdown()

    def socketek_bezarasa():
        for csatorna in szerver.active_channels.copy().values():
            csatorna.handle_close()
        szerver.close()

    if not kiszolgalo.is_alive():
        socketek_bezarasa()
        return

    # A WSGI válasz lezárásakor a Waitressnek még lehet kiküldendő adata.
    hatarido = monotonic() + 1
    while monotonic() < hatarido and any(
        csatorna.total_outbufs_len for csatorna in szerver.active_channels.copy().values()
    ):
        sleep(0.02)

    # A socketeket ugyanaz a szál zárja be, amelyik figyeli őket.
    szerver.trigger.pull_trigger(socketek_bezarasa)
    kiszolgalo.join(timeout=1)
    if kiszolgalo.is_alive():
        raise RuntimeError("A helyi szerver nem állt le időben.")


def main() -> int:
    try:
        from waitress import create_server

        from app import create_app

        leallitasi_keres = Event()
        alkalmazas = create_app(leallitasi_jelzes=leallitasi_keres.set)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as figyelo:
            port = _port_foglalasa(figyelo)
            szerver = create_server(alkalmazas, sockets=[figyelo], asyncore_loop_timeout=0.2)
            kiszolgalo = Thread(target=szerver.run, name="BB84-Waitress", daemon=True)
            try:
                kiszolgalo.start()
                _var_a_feluletre(port, kiszolgalo)

                cim = f"http://{HELYI_CIM}:{port}"
                if port != ALAPERTELMEZETT_PORT:
                    print(f"Az alapértelmezett port ({ALAPERTELMEZETT_PORT}) nem érhető el. A BB84 szabad porton fut.", flush=True)
                print(f"BB84 labor: {cim} — leállítás a böngészőből vagy Ctrl+C-vel", flush=True)
                try:
                    megnyilt = webbrowser.open(cim)
                except (OSError, webbrowser.Error):
                    megnyilt = False
                if not megnyilt:
                    print(f"A böngésző nem nyílt meg automatikusan. Nyisd meg ezt a címet: {cim}", flush=True)

                while kiszolgalo.is_alive():
                    if leallitasi_keres.wait(0.2):
                        break
                else:
                    raise RuntimeError("A helyi szerver váratlanul leállt.")
            finally:
                _szerver_leallitasa(szerver, kiszolgalo)
    except KeyboardInterrupt:
        print(flush=True)
    except Exception as hiba:
        print(f"Hiba történt a BB84 futtatásakor. {hiba}", file=sys.stderr, flush=True)
        return 1
    print("A BB84 leállt.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
