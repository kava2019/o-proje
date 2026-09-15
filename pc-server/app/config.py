import os

HOST = os.environ.get("PC_SERVER_HOST", "0.0.0.0")
PORT = int(os.environ.get("PC_SERVER_PORT", "8000"))
DEVICES_FILE = os.environ.get("PC_SERVER_DEVICES_FILE", "devices.json")
