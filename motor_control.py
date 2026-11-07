
import socket
import time

# ==================================
# ESP32 TCP CONFIGURATION
# ==================================

ESP32_IP = "192.168.8.114"
ESP32_PORT = 5000

client = None


# ==================================
# CONNECT TO ESP32
# ==================================

def connect_esp32():

    global client

    try:
        client = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        client.settimeout(5)

        client.connect((ESP32_IP, ESP32_PORT))

        print("\nNYRA ESP32 Connected Successfully!")

        return True

    except socket.error as error:

        print("Connection Failed:", error)

        client = None

        return False


# ==================================
# SEND COMMAND
# ==================================

def send_command(command):

    global client

    try:

        if client is None:
            print("ESP32 Not Connected!")
            return

        message = command + "\n"

        client.sendall(message.encode())

        response = client.recv(1024).decode().strip()

        print("Command :", command)
        print("Response:", response)

    except socket.error as error:

        print("Communication Error:", error)

        client = None


# ==================================
# MAIN CONTROL MENU
# ==================================

def main():

    if not connect_esp32():
        return

    print("\n========== NYRA MOTOR CONTROL ==========")

    print("1. RUN")
    print("2. SWITCH")
    print("3. STOP")
    print("4. STATUS")
    print("5. EXIT")

    try:

        while True:

            choice = input("\nEnter Command: ").strip().upper()

            if choice == "1" or choice == "RUN":

                send_command("RUN")

            elif choice == "2" or choice == "SWITCH":

                send_command("SWITCH")

            elif choice == "3" or choice == "STOP":

                send_command("STOP")

            elif choice == "4" or choice == "STATUS":

                send_command("STATUS")

            elif choice == "5" or choice == "EXIT":

                send_command("STOP")

                print("NYRA Motor Control Closed")

                break

            else:

                print("Invalid Command!")

    except KeyboardInterrupt:

        print("\nEmergency exit requested!")

        send_command("STOP")

    finally:

        if client is not None:
            client.close()


if __name__ == "__main__":
    main()
