
import socket
import re
import time

# ==========================================
# NYRA AUTONOMOUS NAVIGATION - SIMULATION
# ==========================================

ESP32_IP = "192.168.8.114"
SENSOR_PORT = 3333

SENSORS = ["FRONT", "BACK", "LEFT", "RIGHT"]

cycle = {}

# ==========================================
# SENSOR DATA PARSER
# ==========================================

def parse_sensor_line(line):

    pattern = (
        r"(FRONT|BACK|LEFT|RIGHT):\s*"
        r"(?:(\d+(?:\.\d+)?)\s*cm|NO ECHO)"
        r"\s*\|\s*"
        r"(OBSTACLE|CAUTION|CLEAR|SENSOR ERROR|UNKNOWN)"
    )

    match = re.search(pattern, line.strip(), re.IGNORECASE)

    if not match:
        return None

    name = match.group(1).upper()

    distance = (
        float(match.group(2))
        if match.group(2) is not None
        else None
    )

    status = match.group(3).upper()

    return name, distance, status


# ==========================================
# NAVIGATION DECISION ENGINE
# ==========================================

def evaluate_navigation(data):

    # Check all sensor errors first
    for name in SENSORS:

        if data[name]["status"] in (
            "SENSOR ERROR",
            "UNKNOWN"
        ):
            return "STOP", "Sensor fault: " + name

    front = data["FRONT"]
    left = data["LEFT"]
    right = data["RIGHT"]

    # Front path is clear
    if front["status"] == "CLEAR":

        return "FORWARD", "Front path is CLEAR"

    # Front is blocked or caution
    left_clear = left["status"] == "CLEAR"
    right_clear = right["status"] == "CLEAR"

    # Both sides are clear
    if left_clear and right_clear:

        if left["distance"] > right["distance"]:

            return "LEFT", "Left has more available distance"

        else:

            return "RIGHT", "Right has more available distance"

    # Only left is clear
    if left_clear:

        return "LEFT", "Left path is CLEAR"

    # Only right is clear
    if right_clear:

        return "RIGHT", "Right path is CLEAR"

    return "STOP", "No clear forward or side path"


# ==========================================
# DISPLAY NAVIGATION RESULT
# ==========================================

def print_navigation_result(data):

    action, reason = evaluate_navigation(data)

    print("\n========== NYRA NAVIGATION ==========")

    for name in SENSORS:

        item = data[name]
        distance = item["distance"]

        distance_text = (
            f"{distance:.2f} cm"
            if distance is not None
            else "NO ECHO"
        )

        print(
            f"{name:6} : "
            f"{distance_text:12} | {item['status']}"
        )

    print("-------------------------------------")

    print("SIMULATED ACTION :", action)
    print("REASON           :", reason)
    print("MOTOR COMMAND    : NOT SENT")

    print("=====================================")


# ==========================================
# MAIN TCP CLIENT
# ==========================================

def main():

    global cycle

    print("NYRA AUTONOMOUS NAVIGATION SIMULATION")

    print("ESP32 IP   :", ESP32_IP)
    print("SENSOR PORT:", SENSOR_PORT)

    print("Connecting to ESP32 sensor TCP...")

    while True:

        try:

            with socket.create_connection(
                (ESP32_IP, SENSOR_PORT),
                timeout=5
            ) as sock:

                print("[TCP] SENSOR CONNECTED")

                sock.settimeout(None)

                buffer = ""

                cycle = {}

                while True:

                    chunk = sock.recv(1024)

                    if not chunk:

                        raise ConnectionError(
                            "ESP32 sensor connection closed"
                        )

                    buffer += chunk.decode(
                        "utf-8",
                        errors="replace"
                    )

                    while "\n" in buffer:

                        line, buffer = buffer.split("\n", 1)

                        parsed = parse_sensor_line(line)

                        if parsed is None:
                            continue

                        name, distance, status = parsed

                        cycle[name] = {
                            "distance": distance,
                            "status": status
                        }

                        # Complete four-sensor cycle
                        if all(sensor in cycle for sensor in SENSORS):

                            snapshot = {
                                sensor: cycle[sensor].copy()
                                for sensor in SENSORS
                            }

                            print_navigation_result(snapshot)

                            cycle = {}

        except KeyboardInterrupt:

            print("\n[STOP] Simulation closed")
            break

        except (OSError, ConnectionError) as error:

            print("[TCP] CONNECTION ERROR:", error)

            print("[TCP] Retrying in 3 seconds...")

            cycle = {}

            time.sleep(3)


# ==========================================
# PROGRAM START
# ==========================================

if __name__ == "__main__":

    main()
