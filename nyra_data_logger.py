
import socket
import csv
import re
import time
from pathlib import Path
from datetime import datetime

# ========================================
# NYRA DATA LOGGER V1
# ESP32-S3 + FOUR HC-SR04 SENSORS
# ========================================

ESP32_IP = "192.168.8.114"
ESP32_PORT = 3333

BUFFER_SIZE = 1024
CONNECTION_TIMEOUT = 5
RECONNECT_DELAY = 3

SENSORS = ["FRONT", "BACK", "LEFT", "RIGHT"]

# CSV file created beside this Python script
LOG_FOLDER = Path(__file__).resolve().parent / "nyra_logs"
LOG_FOLDER.mkdir(exist_ok=True)

LOG_FILENAME = (
    "NYRA_sensor_log_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + ".csv"
)

CSV_FILE = LOG_FOLDER / LOG_FILENAME

CSV_COLUMNS = [
    "timestamp",
    "front_distance_cm", "front_status",
    "back_distance_cm", "back_status",
    "left_distance_cm", "left_status",
    "right_distance_cm", "right_status"
]

# Example:
# FRONT: 49.92 cm | OBSTACLE
# RIGHT: NO ECHO | SENSOR ERROR

SENSOR_PATTERN = re.compile(
    r"^\s*(FRONT|BACK|LEFT|RIGHT)\s*:\s*"
    r"(NO ECHO|[0-9]+(?:\.[0-9]+)?)"
    r"\s*(?:cm)?\s*\|\s*"
    r"(OBSTACLE|CAUTION|CLEAR|SENSOR ERROR|UNKNOWN)\s*$",
    re.IGNORECASE
)


def create_csv_file():

    with open(CSV_FILE, "w", newline="", encoding="utf-8") as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CSV_COLUMNS
        )

        writer.writeheader()

    print("\n[LOG] CSV file created:")
    print(CSV_FILE)


def parse_sensor_line(line):

    match = SENSOR_PATTERN.match(line)

    if not match:
        return None

    sensor = match.group(1).upper()
    raw_distance = match.group(2).upper()
    status = match.group(3).upper()

    if raw_distance == "NO ECHO":
        distance = ""
    else:
        distance = float(raw_distance)

    return {
        "sensor": sensor,
        "distance": distance,
        "status": status
    }


def save_completed_cycle(cycle):

    row = {
        "timestamp": datetime.now().isoformat(
            timespec="milliseconds"
        )
    }

    for sensor in SENSORS:

        data = cycle[sensor]

        prefix = sensor.lower()

        row[f"{prefix}_distance_cm"] = data["distance"]
        row[f"{prefix}_status"] = data["status"]

    with open(
        CSV_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CSV_COLUMNS
        )

        writer.writerow(row)
        file.flush()

    print(
        f"\n[LOG SAVED] {row['timestamp']} "
        f"| FRONT={row['front_status']} "
        f"| BACK={row['back_status']} "
        f"| LEFT={row['left_status']} "
        f"| RIGHT={row['right_status']}"
    )


def process_line(line, cycle):

    result = parse_sensor_line(line)

    if result is None:
        return

    sensor = result["sensor"]

    # A repeated sensor before a full cycle means
    # the previous cycle was incomplete.
    if sensor in cycle:
        cycle.clear()

    cycle[sensor] = {
        "distance": result["distance"],
        "status": result["status"]
    }

    # Save only when all four sensors are received.
    if all(name in cycle for name in SENSORS):

        save_completed_cycle(cycle)
        cycle.clear()


def start_data_logger():

    print("\n======================================")
    print("       NYRA DATA LOGGER V1")
    print("======================================")

    print(f"[INFO] ESP32 IP   : {ESP32_IP}")
    print(f"[INFO] TCP PORT   : {ESP32_PORT}")
    print(f"[INFO] CSV FILE   : {CSV_FILE}")

    create_csv_file()

    while True:

        try:

            print("\n[INFO] Connecting to ESP32-S3...")

            with socket.create_connection(
                (ESP32_IP, ESP32_PORT),
                timeout=CONNECTION_TIMEOUT
            ) as client:

                client.settimeout(None)

                print("[CONNECTED] ESP32-S3")
                print("[INFO] Data logging started")

                cycle = {}
                buffer = ""

                while True:

                    data = client.recv(BUFFER_SIZE)

                    if not data:
                        print("\n[DISCONNECTED] ESP32 connection closed")
                        break

                    buffer += data.decode(
                        "utf-8",
                        errors="replace"
                    )

                    while "\n" in buffer:

                        line, buffer = buffer.split("\n", 1)
                        line = line.strip("\r")

                        if line.strip():
                            print(line)

                        process_line(line, cycle)

        except socket.timeout:

            print("\n[ERROR] Connection timeout")

        except ConnectionRefusedError:

            print("\n[ERROR] TCP connection refused")

        except OSError as error:

            print(f"\n[NETWORK ERROR] {error}")

        except KeyboardInterrupt:

            print("\n\n[STOPPED] NYRA Data Logger stopped")
            break

        print(
            f"\n[INFO] Reconnecting in "
            f"{RECONNECT_DELAY} seconds..."
        )

        try:
            time.sleep(RECONNECT_DELAY)

        except KeyboardInterrupt:
            print("\n\n[STOPPED] NYRA Data Logger stopped")
            break


if __name__ == "__main__":

    start_data_logger()
