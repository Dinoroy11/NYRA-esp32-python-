import socket

ESP32_IP = "192.168.8.114"
ESP32_PORT = 5000

print("===== NYRA WIRELESS CHAT =====")
print("Type your message to NYRA")
print("Type 'exit' to close\n")

try:
    client = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    client.settimeout(10)
    client.connect((ESP32_IP, ESP32_PORT))

    print("Connected to NYRA ESP32!\n")

    while True:

        message = input("VS Code: ")

        if message.lower() == "exit":
            break

        client.sendall(
            (message + "\n").encode("utf-8")
        )

        response = b""

        while not response.endswith(b"\n"):
            data = client.recv(1024)

            if not data:
                break

            response += data

        print(
            "ESP32: ",
            response.decode("utf-8").strip()
        )

    client.close()

except Exception as error:
    print("Connection Error:", error)