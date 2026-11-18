
import time
import tcp_client


# =====================================================
# NYRA MOTOR CONTROL MENU
# =====================================================

def show_menu():
    print("\n========== NYRA MOTOR CONTROL ==========")

    print("1. FORWARD")
    print("2. BACKWARD")
    print("3. LEFT")
    print("4. RIGHT")
    print("5. STOP")
    print("6. EXIT")

    print("========================================")


# =====================================================
# MAIN MOTOR CONTROL
# =====================================================

def main():
    print("\nNYRA TIME-BASED MOTOR CONTROL")

    if not tcp_client.connect_to_esp32():
        print("ESP32 CONNECTION FAILED!")
        return

    print("\nNYRA MOTOR CONTROL READY!")

    print("LEFT / RIGHT timing:")
    print("Pause before turn : 2 seconds")
    print("Turn duration     : 3 seconds")
    print("Pause after turn  : 0.3 seconds")

    command_map = {
        "1": "FORWARD",
        "FORWARD": "FORWARD",

        "2": "BACKWARD",
        "BACKWARD": "BACKWARD",

        "3": "LEFT",
        "LEFT": "LEFT",

        "4": "RIGHT",
        "RIGHT": "RIGHT",

        "5": "STOP",
        "STOP": "STOP",

        "6": "EXIT",
        "EXIT": "EXIT"
    }

    try:
        while tcp_client.is_connected():
            show_menu()

            choice = input(
                "Enter your choice: "
            ).strip().upper()

            if not tcp_client.is_connected():
                print("TCP CONNECTION LOST!")
                break

            command = command_map.get(choice)

            if command is None:
                print("INVALID COMMAND!")
                continue

            if not tcp_client.send_command(command):
                print("COMMAND FAILED")
                break

            if command == "EXIT":
                time.sleep(0.2)
                break

    except KeyboardInterrupt:
        print("\nMOTOR CONTROL INTERRUPTED")

    finally:
        if tcp_client.is_connected():
            tcp_client.send_command("STOP")
            time.sleep(0.1)

        tcp_client.disconnect()

        print("NYRA MOTOR CONTROL CLOSED")


# =====================================================
# PROGRAM START
# =====================================================

if __name__ == "__main__":
    main()
