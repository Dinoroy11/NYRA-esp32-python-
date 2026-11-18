
import socket
import time

# ========================================
# NYRA FOUR ULTRASONIC TCP CLIENT V2
# ========================================

ESP32_IP = "192.168.8.114"
ESP32_PORT = 3333

BUFFER_SIZE = 1024
CONNECTION_TIMEOUT = 5
RECONNECT_DELAY = 3


def start_wireless_monitor():

    print("\n======================================")
    print("   NYRA FOUR-SIDE ULTRASONIC MONITOR")
    print("======================================")

    print(f"\n[INFO] ESP32 IP   : {ESP32_IP}")
    print(f"[INFO] TCP PORT   : {ESP32_PORT}")
    print("[INFO] CLIENT MODE: TCP")

    while True:

        try:

            print("\n[INFO] Connecting to ESP32-S3...")

            # Create TCP connection
            with socket.create_connection(
                (ESP32_IP, ESP32_PORT),
                timeout=CONNECTION_TIMEOUT
            ) as client:

                print("\n[CONNECTED] ESP32-S3")
                print("--------------------------------------")
                print("[INFO] Receiving four sensor readings...")
                print("--------------------------------------\n")

                # Wait indefinitely for sensor data
                client.settimeout(None)

                while True:

                    data = client.recv(BUFFER_SIZE)

                    # Server disconnected
                    if not data:

                        print("\n[DISCONNECTED] ESP32 connection closed")
                        break

                    message = data.decode(
                        "utf-8",
                        errors="replace"
                    )

                    print(message, end="", flush=True)

        except socket.timeout:

            print("\n[ERROR] Connection timeout")
            print("[INFO] Check ESP32 TCP server and network")

        except ConnectionRefusedError:

            print("\n[ERROR] TCP connection refused")
            print("[INFO] ESP32 server may not be listening")

        except OSError as error:

            print(f"\n[NETWORK ERROR] {error}")

        except KeyboardInterrupt:

            print("\n\n[STOPPED] NYRA wireless monitor stopped")
            break

        print(
            f"\n[INFO] Retrying connection in "
            f"{RECONNECT_DELAY} seconds..."
        )

        try:
            time.sleep(RECONNECT_DELAY)

        except KeyboardInterrupt:
            print("\n\n[STOPPED] NYRA wireless monitor stopped")
            break


# ========================================
# PROGRAM ENTRY POINT
# ========================================

if __name__ == "__main__":

    start_wireless_monitor()
