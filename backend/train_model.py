import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from scipy.signal import butter, filtfilt
from scipy.fft import fft
import joblib

########################################
# Parameter
########################################
DB_PATH = 'sensor_data.db'  # Pfad zur Datenbank
TABLE_NAME = 'sensor_data'  # Tabellenname

# Angepasste Parameter basierend auf Ihren Daten
WINDOW_SIZE = 30  # Anzahl der Datenpunkte pro Fenster (2 Sekunden bei 15 Hz)
STEP_SIZE = 15  # Schrittgröße für überlappende Fenster (1 Sekunde)
USE_FFT = False  # FFT Features nicht verwenden
FS = 15  # Abtastrate der Daten in Hz
CUTOFF = 2  # Grenzfrequenz des Tiefpassfilters in Hz
ORDER = 2  # Ordnung des Butterworth-Filters


########################################
# Funktionen für die Filterung
########################################

def butter_lowpass(cutoff, fs, order=4):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def apply_lowpass_filter(data, cutoff=5, fs=50, order=4):
    """
    Wendet einen Butterworth-Tiefpassfilter auf die Daten an.

    :param data: pandas DataFrame mit den Sensordaten
    :param cutoff: Grenzfrequenz des Filters (Hz)
    :param fs: Abtastrate der Daten (Hz)
    :param order: Ordnung des Filters
    :return: gefilterte Daten als pandas DataFrame
    """
    b, a = butter_lowpass(cutoff, fs, order=order)
    filtered_data = data.copy()
    for column in ['ax', 'ay', 'az', 'gx', 'gy', 'gz']:
        filtered_data[column] = filtfilt(b, a, data[column])
    return filtered_data


########################################
# Daten laden
########################################
conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
conn.close()

# Label-Filter: nur Zeilen mit 0/1 verwenden
df = df.dropna(subset=['label'])
df = df[df['label'].isin([0, 1])]

########################################
# Preprocessing
########################################

# Pulse-Spalte entfernen, falls vorhanden
if 'pulse' in df.columns:
    df = df.drop(columns=['pulse'])

# Timestamp in datetime konvertieren
if not np.issubdtype(df['timestamp'].dtype, np.datetime64):
    df['timestamp'] = pd.to_datetime(df['timestamp'])

# Nach Timestamp sortieren und fehlende Werte behandeln
df = df.sort_values(by='timestamp').reset_index(drop=True)
df = df.ffill().bfill()

# Signalfiltration mit den angepassten Parametern
filtered_df = apply_lowpass_filter(df, cutoff=CUTOFF, fs=FS, order=ORDER)
for axis in ['ax', 'ay', 'az', 'gx', 'gy', 'gz']:
    df[f'{axis}_filtered'] = filtered_df[axis]


########################################
# Feature-Engineering Funktionen
########################################

def compute_features(window):
    """ Berechnet Features für ein Datenfenster """
    feature_dict = {}
    # Achsenlisten für gefilterte Daten
    accel_axes = ['ax_filtered', 'ay_filtered', 'az_filtered']
    gyro_axes = ['gx_filtered', 'gy_filtered', 'gz_filtered']

    # Statistische Merkmale für Beschleunigung
    for axis in accel_axes:
        feature_dict[f'{axis}_mean'] = window[axis].mean()
        feature_dict[f'{axis}_std'] = window[axis].std()
        feature_dict[f'{axis}_max'] = window[axis].max()
        feature_dict[f'{axis}_min'] = window[axis].min()

    # Statistische Merkmale für Gyro
    for axis in gyro_axes:
        feature_dict[f'{axis}_mean'] = window[axis].mean()
        feature_dict[f'{axis}_std'] = window[axis].std()
        feature_dict[f'{axis}_max'] = window[axis].max()
        feature_dict[f'{axis}_min'] = window[axis].min()

    # Magnituden
    accel_mag = np.sqrt(window['ax_filtered'] ** 2 + window['ay_filtered'] ** 2 + window['az_filtered'] ** 2)
    gyro_mag = np.sqrt(window['gx_filtered'] ** 2 + window['gy_filtered'] ** 2 + window['gz_filtered'] ** 2)
    feature_dict['accel_mag_mean'] = accel_mag.mean()
    feature_dict['accel_mag_std'] = accel_mag.std()
    feature_dict['gyro_mag_mean'] = gyro_mag.mean()
    feature_dict['gyro_mag_std'] = gyro_mag.std()

    # Optional: FFT Features (falls USE_FFT = True)
    if USE_FFT:
        fft_vals = np.abs(fft(window['ax_filtered']))
        half_n = len(fft_vals) // 2
        feature_dict['ax_fft_mean'] = fft_vals[:half_n].mean()
        feature_dict['ax_fft_std'] = fft_vals[:half_n].std()

    return feature_dict


########################################
# Fensterbildung & Feature Extraktion
########################################

def sliding_window_features(df, window_size=20, step_size=10):
    """
    Wandelt rohe Sensordaten in Feature-Vektoren um, indem
    überlappende Fenster gebildet werden.
    """
    features_list = []
    labels = []

    for start in range(0, len(df) - window_size + 1, step_size):
        window = df.iloc[start:start + window_size]
        window_label = window['label'].max()

        f = compute_features(window)
        features_list.append(f)
        labels.append(window_label)

    feature_df = pd.DataFrame(features_list)
    label_series = pd.Series(labels, name='label')
    return feature_df, label_series


# Feature-Extraktion mit angepassten Parametern
X, y = sliding_window_features(df, WINDOW_SIZE, STEP_SIZE)
X = X.fillna(0)

########################################
# Trainings-/Testsplit
########################################

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

########################################
# Modelltraining
########################################

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

########################################
# Evaluation
########################################

y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred))

########################################
# Modell speichern (optional)
########################################

joblib.dump(model, 'drink_detection_model.pkl')
print("Modell gespeichert unter drink_detection_model.pkl")
