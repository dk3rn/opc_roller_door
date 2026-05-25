import asyncio
from roller_door import RolltorApp  # Importiert deine UI-Klasse


async def vollzugriff_steuerung(tor: RolltorApp):
    """
    Diese asynchrone Task demonstriert den Lese- und Schreibzugriff auf alle
    wichtigen Variablen und Funktionen der RolltorApp.
    """
    print("--- SYSTEMSTART ---")
    await asyncio.sleep(1)

    # 1. STATUS AUSLESEN (Sensoren & Position)
    print(f"Startposition: {tor.pos}%")
    print(f"Endschalter Oben erreicht? {tor.var_upper_limit.get()}")
    print(f"Endschalter Unten erreicht? {tor.var_lower_limit.get()}")
    print(f"Ist ein Fehler aktiv? {tor.error}")
    await asyncio.sleep(2)

    # 2. MOTOR STEUERN (AUFWÄRTS)
    print("\n--- MOTOR AUF ---")
    tor.var_up.set(True)  # Schaltet den Motor für Aufwärts ein

    # Warten, bis das Tor exakt 30% erreicht hat
    while tor.pos < 30.0:
        await asyncio.sleep(0.1)

    print(f"Position {tor.pos:.1f}% erreicht - Stoppe Motor.")
    tor.var_up.set(False)
    await asyncio.sleep(1.5)

    # 3. MOTOR STEUERN (ABWÄRTS)
    print("\n--- MOTOR AB ---")
    tor.var_down.set(True)  # Schaltet den Motor für Abwärts ein

    # Warten, bis das Tor wieder bei 15% ist
    while tor.pos > 15.0:
        await asyncio.sleep(0.1)

    print(f"Position {tor.pos:.1f}% erreicht - Stoppe Motor.")
    tor.var_down.set(False)
    await asyncio.sleep(1.5)

    # 4. MANUELLE SENSOREN MANIPULIEREN
    print("\n--- SENSOREN MANIPULIEREN ---")
    print("Täusche per Code vor, dass der obere Sensor blockiert/gedrückt ist...")

    # Du kannst den internen Zustand direkt überschreiben
    tor.manual_upper_pressed = True
    await asyncio.sleep(0.5)
    print(f"Status oberer Sensor (durch Code manipuliert): {tor.var_upper_limit.get()}")

    # Sensor wieder freigeben
    tor.manual_upper_pressed = False
    await asyncio.sleep(1.5)

    # 5. FEHLER PROVOZIEREN & RESET AUSLÖSEN
    print("\n--- FEHLERBEHANDLUNG ---")
    print("Provoziere einen Fehler (Motor gleichzeitig AUF und AB)...")

    tor.var_up.set(True)
    tor.var_down.set(True)
    await asyncio.sleep(0.5)  # Kurz warten, damit das UI den Fehler erkennt

    print(f"Fehlerstatus nach Fehlbedienung: {tor.error}")
    await asyncio.sleep(2)

    print("Führe System-Reset durch...")
    tor.trigger_reset()  # Nutzt die Reset-Funktion der Klasse
    await asyncio.sleep(0.5)
    print(f"Fehlerstatus nach Reset: {tor.error}")

    # 6. KOMPLETT ÖFFNEN BIS ZUR ENDLAGE
    print("\n--- FAHRE IN ENDLAGE OBEN ---")
    tor.var_up.set(True)

    # Schleife läuft, bis der Endschalter oben "True" meldet
    while not tor.var_upper_limit.get():
        await asyncio.sleep(0.1)

    tor.var_up.set(False)
    print(f"Obere Endlage erfolgreich erreicht bei {tor.pos:.1f}%.")
    print("--- DEMO BEENDET ---")


async def main():
    # 1. Tor-Modell instanziieren
    tor = RolltorApp()

    # 2. UI-Loop und unser erweitertes Steuerungs-Skript gleichzeitig starten
    task_ui = asyncio.create_task(tor.async_mainloop())
    task_steuerung = asyncio.create_task(vollzugriff_steuerung(tor))

    # Ausführen, bis das Fenster geschlossen wird
    await task_ui


if __name__ == "__main__":
    asyncio.run(main())