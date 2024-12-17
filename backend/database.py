# database.py

import sqlite3
from datetime import datetime

DB_PATH = 'sensor_data.db'

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def create_tables():
    conn = create_connection()
    cursor = conn.cursor()

    # Tabelle für Rohsensordaten
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            ax REAL,
            ay REAL,
            az REAL,
            gx REAL,
            gy REAL,
            gz REAL,
            pulse REAL,
            label INTEGER
        )
    ''')

    # Indizes hinzufügen für bessere Performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_data(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_label ON sensor_data(label)')

    conn.commit()
    conn.close()

def insert_sensor_data(timestamp, ax, ay, az, gx, gy, gz, pulse):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sensor_data (timestamp, ax, ay, az, gx, gy, gz, pulse, label)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
    ''', (timestamp, ax, ay, az, gx, gy, gz, pulse))
    conn.commit()
    conn.close()

def get_unlabeled_data(limit=100):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM sensor_data
        WHERE label IS NULL
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows[::-1]  # Umkehren der Reihenfolge, sodass die ältesten der letzten 'limit' zuerst sind

def update_label(sensor_id, label):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sensor_data
        SET label = ?
        WHERE id = ?
    ''', (label, sensor_id))
    conn.commit()
    conn.close()

def label_range(start_ts, end_ts, label):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sensor_data
        SET label = ?
        WHERE timestamp >= ? AND timestamp <= ?
    ''', (label, start_ts, end_ts))
    conn.commit()
    conn.close()

def batch_label(ids, label):
    if not ids:
        return
    conn = create_connection()
    cursor = conn.cursor()
    placeholders = ','.join(['?'] * len(ids))
    query = f'''
        UPDATE sensor_data
        SET label = ?
        WHERE id IN ({placeholders})
    '''
    cursor.execute(query, [label] + ids)
    conn.commit()
    conn.close()

def get_all_sensor_data():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sensor_data')
    rows = cursor.fetchall()
    conn.close()
    return rows
