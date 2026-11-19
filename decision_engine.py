
# decision_engine.py
# NYRA Obstacle Avoidance - Decision Engine V1

SENSORS = ("FRONT", "BACK", "LEFT", "RIGHT")

VALID_STATUSES = {
    "OBSTACLE",
    "CAUTION",
    "CLEAR",
    "SENSOR ERROR",
    "UNKNOWN",
}


def normalize_status(status):
    """Normalize status text received from ESP32."""
    return " ".join(str(status).strip().upper().replace("_", " ").split())


def evaluate_decision(sensor_data):
    """
    Input example:
    {
        "FRONT": "CLEAR",
        "BACK": "CLEAR",
        "LEFT": "OBSTACLE",
        "RIGHT": "CLEAR"
    }

    Returns a decision dictionary.
    """

    statuses = {}

    # Check that all four sensor statuses are available.
    for sensor in SENSORS:
        raw_status = sensor_data.get(sensor)

        if raw_status is None:
            statuses[sensor] = "SENSOR ERROR"
        else:
            statuses[sensor] = normalize_status(raw_status)

        if statuses[sensor] not in VALID_STATUSES:
            statuses[sensor] = "SENSOR ERROR"

    # Any sensor error or unknown status means movement is restricted.
    faulty_sensors = [
        sensor for sensor, status in statuses.items()
        if status in ("SENSOR ERROR", "UNKNOWN")
    ]

    if faulty_sensors:
        return {
            "decision": "STOP",
            "reason": "SENSOR FAULT - INCOMPLETE SENSOR DATA",
            "suggested_action": "NO MOVEMENT",
            "faulty_sensors": faulty_sensors,
            "warnings": [],
            "motor_command": "STOP",
        }

    front = statuses["FRONT"]
    back = statuses["BACK"]
    left = statuses["LEFT"]
    right = statuses["RIGHT"]

    warnings = []

    # Directional warnings
    for sensor in ("BACK", "LEFT", "RIGHT"):
        if statuses[sensor] == "OBSTACLE":
            warnings.append(f"{sensor} OBSTACLE")
        elif statuses[sensor] == "CAUTION":
            warnings.append(f"{sensor} CAUTION")

    # Primary forward-path decision
    if front == "OBSTACLE":
        decision = "STOP"
        reason = "FRONT OBSTACLE DETECTED"
        motor_command = "STOP"

        # Recommendation only. This is NOT a motor command.
        if left == "CLEAR" and right != "CLEAR":
            suggested_action = "LEFT TURN MAY BE CONSIDERED"
        elif right == "CLEAR" and left != "CLEAR":
            suggested_action = "RIGHT TURN MAY BE CONSIDERED"
        elif left == "CLEAR" and right == "CLEAR":
            suggested_action = "CHECK BOTH SIDES BEFORE TURNING"
        else:
            suggested_action = "STOP AND REASSESS"

    elif front == "CAUTION":
        decision = "CAUTION"
        reason = "FRONT PATH CAUTION"
        suggested_action = "REDUCED SPEED MAY BE REQUIRED"
        motor_command = "STOP"

    else:  # FRONT == CLEAR
        decision = "FORWARD PATH CLEAR"
        reason = "FRONT SENSOR REPORTS CLEAR"
        suggested_action = "FORWARD MAY BE CONSIDERED"
        motor_command = "FORWARD"

    # Reverse is not allowed when the rear sensor is blocked.
    if back == "OBSTACLE" and motor_command == "REVERSE":
        motor_command = "STOP"

    return {
        "decision": decision,
        "reason": reason,
        "suggested_action": suggested_action,
        "faulty_sensors": [],
        "warnings": warnings,
        "motor_command": motor_command,
        "sensor_status": statuses,
    }


def print_decision(result):
    print("\n========== NYRA DECISION ENGINE V1 ==========")
    print(f"DECISION         : {result['decision']}")
    print(f"REASON           : {result['reason']}")
    print(f"SUGGESTED ACTION : {result['suggested_action']}")
    print(f"MOTOR COMMAND    : {result['motor_command']}")

    if result["faulty_sensors"]:
        print("FAULTY SENSORS   :", ", ".join(result["faulty_sensors"]))

    if result["warnings"]:
        print("WARNINGS         :", ", ".join(result["warnings"]))

    print("=============================================\n")


if __name__ == "__main__":

    test_cases = [
        {
            "name": "All sensors clear",
            "data": {
                "FRONT": "CLEAR",
                "BACK": "CLEAR",
                "LEFT": "CLEAR",
                "RIGHT": "CLEAR",
            },
        },
        {
            "name": "Front obstacle, left clear",
            "data": {
                "FRONT": "OBSTACLE",
                "BACK": "CLEAR",
                "LEFT": "CLEAR",
                "RIGHT": "OBSTACLE",
            },
        },
        {
            "name": "Front caution",
            "data": {
                "FRONT": "CAUTION",
                "BACK": "CLEAR",
                "LEFT": "CLEAR",
                "RIGHT": "CLEAR",
            },
        },
        {
            "name": "Rear obstacle",
            "data": {
                "FRONT": "CLEAR",
                "BACK": "OBSTACLE",
                "LEFT": "CLEAR",
                "RIGHT": "CLEAR",
            },
        },
        {
            "name": "Left and right obstacles",
            "data": {
                "FRONT": "CLEAR",
                "BACK": "CLEAR",
                "LEFT": "OBSTACLE",
                "RIGHT": "OBSTACLE",
            },
        },
        {
            "name": "One sensor error",
            "data": {
                "FRONT": "CLEAR",
                "BACK": "CLEAR",
                "LEFT": "SENSOR ERROR",
                "RIGHT": "CLEAR",
            },
        },
    ]

    for test in test_cases:
        print(f"TEST: {test['name']}")
        result = evaluate_decision(test["data"])
        print_decision(result)
