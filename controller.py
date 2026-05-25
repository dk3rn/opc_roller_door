import asyncio
from roller_door import RolltorApp


async def automatik_steuerung(tor: RolltorApp):
    """Eine asynchrone Task, die das Tor magisch von außen steuert."""
    print("Warte 2 Sekunden...")
    await asyncio.sleep(2)

    print("Fahre Tor aufwärts...")
    tor.var_up.set(True)

    # Warte, bis das Tor 50% erreicht hat
    while tor.pos < 50:
        await asyncio.sleep(0.1)

    print("Stoppe Tor bei 50%!")
    tor.var_up.set(False)
    await asyncio.sleep(2)

    print("Fahre weiter nach oben...")
    tor.var_up.set(True)


async def main():
    # 1. Tor-Modell instanziieren
    tor = RolltorApp()

    # 2. UI-Loop und unser Steuerungs-Skript gleichzeitig starten
    task_ui = asyncio.create_task(tor.async_mainloop())
    task_steuerung = asyncio.create_task(automatik_steuerung(tor))

    # Ausführen bis das Fenster geschlossen wird
    await task_ui


if __name__ == "__main__":
    asyncio.run(main())