
# ============================================
# NYRA MOTOR INTERFACE
# SAFETY PREPARATION V1
# ============================================

# Hardware output is deliberately disabled.
# This module does not communicate with motor drivers.

HARDWARE_ENABLE = False

EMERGENCY_STOP_VERIFIED = False


def prepare_motor_request(decision_result):

    """
    Prepare a proposed motor direction.

    IMPORTANT:
    This function does not send commands to hardware.
    """

    permissions = decision_result.get(
        "direction_permissions",
        {}
    )

    # Sensor fault protection
    if decision_result.get("faulty_sensors"):

        return {
            "requested_direction": "STOP",
            "authorized": False,
            "reason": "SENSOR FAULT - HARDWARE OUTPUT DISABLED"
        }

    # Main decision protection
    if decision_result.get("decision") in ("STOP", "CAUTION"):

        return {
            "requested_direction": "STOP",
            "authorized": False,
            "reason": "PRIMARY DECISION DOES NOT PERMIT MOVEMENT"
        }

    # Current interface proposes FORWARD only.
    # Reverse and turning need a separate maneuver planner.

    if permissions.get("FORWARD", False):

        requested = "FORWARD"

    else:

        requested = "STOP"

    # Hardware disabled
    if not HARDWARE_ENABLE:

        return {
            "requested_direction": requested,
            "authorized": False,
            "reason": "HARDWARE DISABLED - EMERGENCY STOP NOT VERIFIED"
        }

    # Emergency Stop verification
    if not EMERGENCY_STOP_VERIFIED:

        return {
            "requested_direction": requested,
            "authorized": False,
            "reason": "EMERGENCY STOP NOT VERIFIED"
        }

    # No physical motor transport implemented
    return {
        "requested_direction": requested,
        "authorized": False,
        "reason": "NO MOTOR DRIVER TRANSPORT IMPLEMENTED"
    }
