
# ============================================
# NYRA INTEGRATED MONITOR V2
# TCP + Decision Engine V2 + Data Logger V2
# ============================================

import socket
import csv
import re
import time
from pathlib import Path
from datetime import datetime

from decision_engine_v2 import evaluate_decision, print_decision
from motor_interface_safety import prepare_motor_request


# ============================================
# CONFIGURATION
# ============================================

ESP32_IP = "192.168.8.114"
ESP32_PORT = 3333

BUFFER_SIZE = 1024
CONNECTION_TIMEOUT = 5
DATA_TIMEOUT = 3
RECONNECT_DELAY = 3

SENSORS = ["FRONT", "BACK", "LEFT", "RIGHT"]


# ============================================
# CSV CONFIGURATION
# ============================================

LOG_FOLDER = Path(__file__).resolve().parent / "nyra_logs"
LOG_FOLDER.mkdir(exist_ok=True)

CSV_FILE = LOG_FOLDER / (
    "NYRA_integrated_log_v2_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + ".csv"
)

CSV_COLUMNS = [
    "timestamp",

    "front_distance_cm", "front_status",
    "back_distance_cm", "back_status",
    "left_distance_cm", "left_status",
    "right_distance_cm", "right_status",

    "decision",
    "reason",
    "suggested_action",

    "motor_request_direction",
    "motor_request_authorized",
    "motor_request_reason",

    "forward_allowed",
    "reverse_allowed",
    "left_allowed",
    "right_allowed",

    "allowed_directions",
    "blocked_directions",

    "warnings",
    "faulty_sensors"
]


# ============================================
# SENSOR DATA REGEX
# ============================================

SENSOR_PATTERN = re.compile(
    r"^\s*(FRONT|BACK|LEFT|RIGHT)\s*:\s*"
    r"(NO ECHO|[0-9]+(?:\.[0-9]+)?)"
    r"\s*(?:cm)?\s*\|\s*"
    r"(OBSTACLE|CAUTION|CLEAR|SENSOR ERROR|UNKNOWN)\s*$",
    re.IGNORECASE
)


# ============================================
# CREATE CSV
# ============================================

def create_csv_file():

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CSV_COLUMNS
        )

        writer.writeheader()

    print("\n[LOG CREATED]")
    print(CSV_FILE)


# ============================================
# PARSE SENSOR DATA
# ============================================

def parse_sensor_line(line):

    match = SENSOR_PATTERN.match(line)

    if not match:
        return None

    sensor, raw_distance, status = match.groups()

    if raw_distance.upper() == "NO ECHO":
        distance = ""
    else:
        distance = float(raw_distance)

    return {
        "sensor": sensor.upper(),
        "distance": distance,
        "status": status.upper()
    }


# ============================================
# SAVE COMPLETE SENSOR CYCLE
# ============================================

def save_cycle(cycle, result, motor_request):

    row = {
        "timestamp": datetime.now().isoformat(
            timespec="milliseconds"
        )
    }

    for sensor in SENSORS:

        item = cycle[sensor]
        prefix = sensor.lower()

        row[f"{prefix}_distance_cm"] = item["distance"]
        row[f"{prefix}_status"] = item["status"]

    permissions = result["direction_permissions"]

    row.update({

        "decision": result["decision"],
        "reason": result["reason"],
        "suggested_action": result["suggested_action"],

        "motor_request_direction":
            motor_request["requested_direction"],

        "motor_request_authorized":
            motor_request["authorized"],

        "motor_request_reason":
            motor_request["reason"],

        "forward_allowed": permissions["FORWARD"],
        "reverse_allowed": permissions["REVERSE"],
        "left_allowed": permissions["LEFT"],
        "right_allowed": permissions["RIGHT"],

        "allowed_directions":
            "; ".join(result["allowed_directions"]),

        "blocked_directions":
            "; ".join(result["blocked_directions"]),

        "warnings":
            "; ".join(result["warnings"]),

        "faulty_sensors":
            "; ".join(result["faulty_sensors"])
    })

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
        f"| DECISION={row['decision']} "
        f"| ALLOWED={row['allowed_directions'] or 'NONE'} "
        f"| MOTOR_AUTHORIZED={row['motor_request_authorized']}"
    )


# ============================================
# PROCESS SENSOR LINE
# ============================================

def process_line(line, cycle):

    item = parse_sensor_line(line)

    if item is None:
        return

    sensor = item["sensor"]

    # Discard incomplete cycle if a sensor repeats
    if sensor in cycle:

        print(
            f"[WARNING] Incomplete cycle discarded at {sensor}"
        )

        cycle.clear()

    cycle[sensor] = {
        "distance": item["distance"],
        "status": item["status"]
    }

    # Wait until all four sensor readings arrive
    if all(sensor_name in cycle for sensor_name in SENSORS):

        statuses = {
            sensor_name: cycle[sensor_name]["status"]
            for sensor_name in SENSORS
        }

        print("\n[INFO] Complete four-sensor cycle received")

        # Decision Engine V2
        result = evaluate_decision(statuses)

        print_decision(result)

        # Motor interface - request only, no hardware output
        request = prepare_motor_request(result)

        print(
            f"[MOTOR INTERFACE] "
            f"REQUEST={request['requested_direction']} "
            f"| AUTHORIZED={request['authorized']} "
            f"| REASON={request['reason']}"
        )

        # Save sensor + decision + permissions
        save_cycle(cycle, result, request)

        cycle.clear()


# ============================================
# START INTEGRATED MONITOR
# ============================================

def start():

    print("\n==========================================")
    print("       NYRA INTEGRATED MONITOR V2")
    print("==========================================")

    print(f"[INFO] ESP32 IP : {ESP32_IP}")
    print(f"[INFO] TCP PORT : {ESP32_PORT}")
    print(f"[INFO] CSV FILE : {CSV_FILE}")
    print("[INFO] MOTOR OUTPUT: DISABLED")

    create_csv_file()

    while True:

        try:

            print("\n[INFO] Connecting to ESP32-S3...")

            with socket.create_connection(
                (ESP32_IP, ESP32_PORT),
                timeout=CONNECTION_TIMEOUT
            ) as client:

                print("[CONNECTED] ESP32-S3")

                client.settimeout(DATA_TIMEOUT)

                cycle = {}
                buffer = ""

                while True:

                    data = client.recv(BUFFER_SIZE)

                    if not data:

                        print(
                            "\n[DISCONNECTED] ESP32 closed connection"
                        )

                        break

                    buffer += data.decode(
                        "utf-8",
                        errors="replace"
                    )

                    while "\n" in buffer:

                        line, buffer = buffer.split("\n", 1)

                        line = line.strip("\r").strip()

                        if line:

                            print(f"[SENSOR] {line}")

                            process_line(line, cycle)

        except socket.timeout:

            print("\n[ERROR] No fresh TCP data received")
            print("[SAFE STATE] No motor command is sent.")
            print("[INFO] Incomplete sensor cycle discarded.")

        except ConnectionRefusedError:

            print("\n[ERROR] ESP32 TCP connection refused")

        except OSError as error:

            print(f"\n[NETWORK ERROR] {error}")

        except KeyboardInterrupt:

            print(
                "\n\n[STOPPED] NYRA Integrated Monitor V2 stopped"
            )

            break

        print(
            f"\n[INFO] Reconnecting in {RECONNECT_DELAY} seconds..."
        )

        try:
            time.sleep(RECONNECT_DELAY)

        except KeyboardInterrupt:

            print(
                "\n\n[STOPPED] NYRA Integrated Monitor V2 stopped"
            )

            break


# ============================================
# PROGRAM ENTRY POINT
# ============================================

if __name__ == "__main__":

    start()
