# BLE.py

import asyncio
import json
import logging
from datetime import datetime

import aiohttp
from bleak import BleakClient

# Konfiguriere das Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# UUIDs for Service and Characteristic, as defined on the ESP32
SERVICE_UUID = "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
CHARACTERISTIC_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# MAC-Adresse deiner Smartwatch (Beispiel: "54:32:04:22:52:1A")
WATCH_MAC_ADDRESS = "54:32:04:22:52:1A"  # Ersetze dies durch die MAC-Adresse deiner Smartwatch

# Backend-URL
INGEST_ENDPOINT = "http://localhost:5000/ingest"  # Ersetze dies, falls dein Backend anders läuft

async def send_data(session, payload):
    """
    Sendet die Sensordaten an das Backend.
    """
    try:
        async with session.post(INGEST_ENDPOINT, json=payload) as response:
            if response.status == 200:
                logging.info("Daten erfolgreich an das Backend gesendet.")
            else:
                text = await response.text()
                logging.error(f"Fehler beim Senden der Daten: {response.status} - {text}")
    except Exception as e:
        logging.error(f"Exception beim Senden der Daten: {e}")

async def data_sender(queue):
    """
    Konsumiert Daten aus der Queue und sendet sie asynchron an das Backend.
    """
    async with aiohttp.ClientSession() as session:
        while True:
            payload = await queue.get()
            await send_data(session, payload)
            queue.task_done()

async def handle_sensor_data(sender, data, queue):
    """
    Callback-Funktion, die aufgerufen wird, wenn neue Daten von der Charakteristik empfangen werden.
    """
    try:
        raw_data = data.decode('utf-8').strip()
        logging.info(f"Received data: {raw_data}")
        parts = raw_data.split(';')  # Passe den Trenner an, z.B. ',' oder ';'

        if len(parts) != 8:
            logging.error("Unerwartetes Datenformat. Erwartet 8 Werte.")
            return

        timestamp_str, ax, ay, az, gx, gy, gz, pulse = parts
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Aktueller Timestamp

        sensor_data = {
            "timestamp": timestamp,
            "ax": float(ax),
            "ay": float(ay),
            "az": float(az),
            "gx": float(gx),
            "gy": float(gy),
            "gz": float(gz),
            "pulse": float(pulse)
        }

        logging.info(f"Parsed Sensor Data: {sensor_data}")

        await queue.put(sensor_data)

    except Exception as e:
        logging.error(f"Fehler beim Verarbeiten der Sensordaten: {e}")

async def run():
    """
    Hauptfunktion zum Herstellen der Verbindung und Empfangen von Daten.
    """
    queue = asyncio.Queue()
    asyncio.create_task(data_sender(queue))  # Starte den Daten-Sender Task

    client = BleakClient(WATCH_MAC_ADDRESS)
    try:
        logging.info(f"Verbinde mit der Smartwatch: {WATCH_MAC_ADDRESS}")
        await client.connect()
        logging.info("Verbindung hergestellt.")

        # Überprüfe, ob der Service und die Charakteristik vorhanden sind
        services = await client.get_services()
        if SERVICE_UUID not in [service.uuid for service in services]:
            logging.error(f"Service UUID {SERVICE_UUID} nicht gefunden.")
            return

        if CHARACTERISTIC_UUID not in [char.uuid for char in services.get_service(SERVICE_UUID).characteristics]:
            logging.error(f"Charakteristik UUID {CHARACTERISTIC_UUID} nicht gefunden.")
            return

        # Starte das Benachrichtigen
        def notification_handler(sender, data):
            asyncio.create_task(handle_sensor_data(sender, data, queue))

        await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
        logging.info("Benachrichtigungen gestartet. Warte auf Daten...")

        # Halte das Skript am Laufen
        while True:
            await asyncio.sleep(1)

    except Exception as e:
        logging.error(f"Fehler: {e}")
    finally:
        if client.is_connected:
            await client.stop_notify(CHARACTERISTIC_UUID)
            await client.disconnect()
            logging.info("Verbindung getrennt.")

if __name__ == "__main__":
    asyncio.run(run())
