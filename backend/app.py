# app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from database import (
    create_tables,
    insert_sensor_data,
    get_unlabeled_data,
    update_label,
    get_all_sensor_data,
    label_range,
    batch_label
)
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Erstelle Tabellen beim Starten
create_tables()

@app.route('/ingest', methods=['POST'])
def ingest_data():
    """
    Empfängt Sensordaten im JSON-Format:
    {
       "timestamp": "2024-12-07 12:55:09",
       "ax": -14112,
       "ay": 5804,
       "az": 12704,
       "gx": 10283,
       "gy": 11596,
       "gz": 13391,
       "pulse": 6.1
    }
    """
    data = request.get_json()
    if data is None:
        return jsonify({"error": "No JSON data provided"}), 400

    required_fields = ["timestamp", "ax", "ay", "az", "gx", "gy", "gz", "pulse"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Werte auslesen und validieren
        timestamp = data["timestamp"]
        ax = float(data["ax"])
        ay = float(data["ay"])
        az = float(data["az"])
        gx = float(data["gx"])
        gy = float(data["gy"])
        gz = float(data["gz"])
        pulse = float(data["pulse"])

        if not is_valid_sensor_data(ax, ay, az, gx, gy, gz, pulse):
            return jsonify({"error": "Invalid sensor data"}), 400

        insert_sensor_data(timestamp, ax, ay, az, gx, gy, gz, pulse)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        # Logge den Fehler für Debugging-Zwecke
        print(f"Fehler beim Einfügen der Daten: {e}")
        return jsonify({"error": "Invalid data format"}), 400

@app.route('/get_unlabeled', methods=['GET'])
def get_unlabeled():
    # Lese das 'limit' aus den Query-Parametern, standardmäßig 200
    limit = request.args.get('limit', default=200, type=int)
    if limit <= 0:
        return jsonify({"error": "Limit must be a positive integer"}), 400

    data = get_unlabeled_data(limit=limit)
    result = []
    for row in data:
        result.append({
            'id': row[0],
            'timestamp': row[1],
            'ax': row[2],
            'ay': row[3],
            'az': row[4],
            'gx': row[5],
            'gy': row[6],
            'gz': row[7],
            'pulse': row[8],
            'label': row[9]
        })
    return jsonify({"sensor_data": result})

@app.route('/label_data', methods=['POST'])
def label_data_endpoint():
    """
    Erwartetes JSON-Format:
    {
       "id": 123,
       "label": 1  // 1 für positives Ereignis, 0 für kein Ereignis
    }
    """
    data = request.get_json()
    if "id" not in data or "label" not in data:
        return jsonify({"error": "Missing id or label"}), 400

    sensor_id = data["id"]
    label = data["label"]
    if label not in [0, 1]:
        return jsonify({"error": "Invalid label"}), 400

    try:
        update_label(sensor_id, label)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Fehler beim Aktualisieren des Labels: {e}")
        return jsonify({"error": "Failed to update label"}), 500

@app.route('/batch_label', methods=['POST'])
def batch_label_endpoint():
    """
    Erwartetes JSON-Format:
    {
        "ids": [123, 124, 125],  // Liste von IDs
        "label": 1  // 1 für Trinkvorgang, 0 für kein Trinkvorgang
    }
    """
    data = request.get_json()
    ids = data.get('ids', [])
    label = data.get('label')

    if not ids or label not in [0, 1]:
        return jsonify({"error": "Missing ids or invalid label"}), 400

    try:
        batch_label(ids, label)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Fehler beim Batch-Labeln: {e}")
        return jsonify({"error": "Failed to batch label"}), 500

@app.route('/export', methods=['GET'])
def export_data():
    """
    Exportiere alle Sensordaten, um sie für das Training einer KI zu verwenden.
    """
    data = get_all_sensor_data()
    result = []
    for row in data:
        result.append({
            'id': row[0],
            'timestamp': row[1],
            'ax': row[2],
            'ay': row[3],
            'az': row[4],
            'gx': row[5],
            'gy': row[6],
            'gz': row[7],
            'pulse': row[8],
            'label': row[9]
        })
    return jsonify({"all_data": result})

def is_valid_sensor_data(ax, ay, az, gx, gy, gz, pulse):
    """
    Überprüft, ob die Sensordaten innerhalb erwarteter Bereiche liegen.
    """
    try:
        if not (-32768 <= ax <= 32767):
            return False
        if not (-32768 <= ay <= 32767):
            return False
        if not (-32768 <= az <= 32767):
            return False
        if not (-32768 <= gx <= 32767):
            return False
        if not (-32768 <= gy <= 32767):
            return False
        if not (-32768 <= gz <= 32767):
            return False
        if not (0.0 <= pulse <= 300.0):  # Beispielbereich für Puls
            return False
    except:
        return False
    return True

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
