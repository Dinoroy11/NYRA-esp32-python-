# decision_engine_v2.py
# NYRA Obstacle Avoidance - Direction Permission Engine V2
#
# IMPORTANT:
# This module calculates direction permissions only.
# It does NOT send commands to the ESP32 or motor drivers.
# Do not use these permissions as the only safety system for physical movement.

SENSORS = ("FRONT", "BACK", "LEFT", "RIGHT")
VALID_STATUSES = {"OBSTACLE", "CAUTION", "CLEAR", "SENSOR ERROR", "UNKNOWN"}
DIRECTIONS = ("FORWARD", "REVERSE", "LEFT", "RIGHT")


def normalize_status(status):
    return " ".join(str(status).strip().upper().replace("_", " ").split())


def evaluate_decision(sensor_data):
    """
    Return primary decision and independent direction permissions.

    A direction is permitted only when its matching sensor reports CLEAR.
    Any missing, invalid, UNKNOWN, or SENSOR ERROR reading blocks all
    directions. This is a preliminary sensor-clearance check, not a complete
    collision-free path planner.
    """
    statuses = {}

    for sensor in SENSORS:
        raw_status = sensor_data.get(sensor)
        if raw_status is None:
            statuses[sensor] = "SENSOR ERROR"
            continue

        status = normalize_status(raw_status)
        statuses[sensor] = status if status in VALID_STATUSES else "SENSOR ERROR"

    faulty_sensors = [
        sensor for sensor, status in statuses.items()
        if status in ("SENSOR ERROR", "UNKNOWN")
    ]

    if faulty_sensors:
        permissions = {direction: False for direction in DIRECTIONS}
        return {
            "decision": "STOP",
            "reason": "SENSOR FAULT - INCOMPLETE OR INVALID SENSOR DATA",
            "suggested_action": "NO MOVEMENT - CHECK SENSOR SYSTEM",
            "faulty_sensors": faulty_sensors,
            "warnings": [],
            "motor_command": "NO COMMAND - PERMISSION CHECK ONLY",
            "direction_permissions": permissions,
            "allowed_directions": [],
            "blocked_directions": list(DIRECTIONS),
            "sensor_status": statuses,
        }

    # Only a CLEAR reading permits movement in that sensor's direction.
    permissions = {
        "FORWARD": statuses["FRONT"] == "CLEAR",
        "REVERSE": statuses["BACK"] == "CLEAR",
        "LEFT": statuses["LEFT"] == "CLEAR",
        "RIGHT": statuses["RIGHT"] == "CLEAR",
    }

    allowed = [d for d, ok in permissions.items() if ok]
    blocked = [d for d, ok in permissions.items() if not ok]

    warnings = []
    for sensor in SENSORS:
        status = statuses[sensor]
        if status == "OBSTACLE":
            warnings.append(f"{sensor} OBSTACLE")
        elif status == "CAUTION":
            warnings.append(f"{sensor} CAUTION")

    if statuses["FRONT"] == "OBSTACLE":
        decision = "STOP"
        reason = "FRONT OBSTACLE DETECTED"

        if permissions["LEFT"] and permissions["RIGHT"]:
            suggestion = (
                "FRONT BLOCKED - LEFT OR RIGHT MAY BE CONSIDERED "
                "AFTER TURNING-AREA SAFETY CHECK"
            )
        elif permissions["LEFT"]:
            suggestion = (
                "FRONT BLOCKED - LEFT MAY BE CONSIDERED "
                "AFTER TURNING-AREA SAFETY CHECK"
            )
        elif permissions["RIGHT"]:
            suggestion = (
                "FRONT BLOCKED - RIGHT MAY BE CONSIDERED "
                "AFTER TURNING-AREA SAFETY CHECK"
            )
        else:
            suggestion = "STOP - NO CLEAR SIDE SENSOR"

    elif statuses["FRONT"] == "CAUTION":
        decision = "CAUTION"
        reason = "FRONT PATH CAUTION"
        suggestion = "STOP FOR V1 - FRONT IS NOT CLEAR"

    else:
        decision = "FORWARD PATH CLEAR"
        reason = "FRONT SENSOR REPORTS CLEAR"
        suggestion = "FORWARD MAY BE CONSIDERED"

    return {
        "decision": decision,
        "reason": reason,
        "suggested_action": suggestion,
        "faulty_sensors": [],
        "warnings": warnings,
        "motor_command": "NO COMMAND - PERMISSION CHECK ONLY",
        "direction_permissions": permissions,
        "allowed_directions": allowed,
        "blocked_directions": blocked,
        "sensor_status": statuses,
    }


def print_decision(result):
    print("\n========== NYRA DECISION ENGINE V2 ==========")
    print(f"DECISION         : {result['decision']}")
    print(f"REASON           : {result['reason']}")
    print(f"SUGGESTED ACTION : {result['suggested_action']}")
    print(f"MOTOR COMMAND    : {result['motor_command']}")
    print("\nDIRECTION PERMISSIONS:")

    for direction, allowed in result["direction_permissions"].items():
        state = "ALLOWED (SENSOR CLEAR)" if allowed else "BLOCKED"
        print(f"  {direction:<8}: {state}")

    print("ALLOWED DIRECTIONS : " + (", ".join(result["allowed_directions"]) or "NONE"))
    print("BLOCKED DIRECTIONS : " + (", ".join(result["blocked_directions"]) or "NONE"))

    if result["faulty_sensors"]:
        print("FAULTY SENSORS     : " + ", ".join(result["faulty_sensors"]))
    if result["warnings"]:
        print("WARNINGS           : " + ", ".join(result["warnings"]))

    print("=============================================\n")


def run_tests():
    test_cases = [
        ("All four directions clear",
         {"FRONT": "CLEAR", "BACK": "CLEAR", "LEFT": "CLEAR", "RIGHT": "CLEAR"},
         {"FORWARD": True, "REVERSE": True, "LEFT": True, "RIGHT": True},
         "FORWARD PATH CLEAR"),

        ("Front obstacle - left clear only",
         {"FRONT": "OBSTACLE", "BACK": "CLEAR", "LEFT": "CLEAR", "RIGHT": "OBSTACLE"},
         {"FORWARD": False, "REVERSE": True, "LEFT": True, "RIGHT": False},
         "STOP"),

        ("Back obstacle - reverse blocked",
         {"FRONT": "CLEAR", "BACK": "OBSTACLE", "LEFT": "CLEAR", "RIGHT": "CLEAR"},
         {"FORWARD": True, "REVERSE": False, "LEFT": True, "RIGHT": True},
         "FORWARD PATH CLEAR"),

        ("Left obstacle - left blocked",
         {"FRONT": "CLEAR", "BACK": "CLEAR", "LEFT": "OBSTACLE", "RIGHT": "CLEAR"},
         {"FORWARD": True, "REVERSE": True, "LEFT": False, "RIGHT": True},
         "FORWARD PATH CLEAR"),

        ("Right obstacle - right blocked",
         {"FRONT": "CLEAR", "BACK": "CLEAR", "LEFT": "CLEAR", "RIGHT": "OBSTACLE"},
         {"FORWARD": True, "REVERSE": True, "LEFT": True, "RIGHT": False},
         "FORWARD PATH CLEAR"),

        ("Front and left obstacles",
         {"FRONT": "OBSTACLE", "BACK": "CLEAR", "LEFT": "OBSTACLE", "RIGHT": "CLEAR"},
         {"FORWARD": False, "REVERSE": True, "LEFT": False, "RIGHT": True},
         "STOP"),

        ("All four obstacles",
         {"FRONT": "OBSTACLE", "BACK": "OBSTACLE", "LEFT": "OBSTACLE", "RIGHT": "OBSTACLE"},
         {"FORWARD": False, "REVERSE": False, "LEFT": False, "RIGHT": False},
         "STOP"),

        ("One sensor error - all directions blocked",
         {"FRONT": "CLEAR", "BACK": "CLEAR", "LEFT": "SENSOR ERROR", "RIGHT": "CLEAR"},
         {"FORWARD": False, "REVERSE": False, "LEFT": False, "RIGHT": False},
         "STOP"),

        ("Caution is not treated as clear",
         {"FRONT": "CAUTION", "BACK": "CLEAR", "LEFT": "CAUTION", "RIGHT": "CLEAR"},
         {"FORWARD": False, "REVERSE": True, "LEFT": False, "RIGHT": True},
         "CAUTION"),
    ]

    passed = 0
    print("\n========== NYRA DIRECTION TESTS V2 ==========")

    for index, (name, data, expected_permissions, expected_decision) in enumerate(test_cases, 1):
        result = evaluate_decision(data)
        ok = (
            result["direction_permissions"] == expected_permissions
            and result["decision"] == expected_decision
        )
        print(f"[{'PASS' if ok else 'FAIL'}] Test {index}: {name}")

        if not ok:
            print("  Expected permissions:", expected_permissions)
            print("  Actual permissions  :", result["direction_permissions"])
            print("  Expected decision   :", expected_decision)
            print("  Actual decision     :", result["decision"])
        else:
            passed += 1

    print("---------------------------------------------")
    print(f"RESULT: {passed}/{len(test_cases)} TESTS PASSED")
    print("=============================================\n")


if __name__ == "__main__":
    run_tests()
