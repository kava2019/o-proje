from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import DEVICES_FILE
from .routers import devices, ws_gateway, ws_ui
from .state import DeviceRegistry

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="Akıllı Ev - PC Server")
    app.state.registry = DeviceRegistry(devices_file=DEVICES_FILE)

    app.include_router(devices.router)
    app.include_router(ws_gateway.router)
    app.include_router(ws_ui.router)

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()
