from lightning_app import LightningWork
from lightning_app.components import serve
from lightning_app.utilities.state import AppState
import time

class StudioUI(LightningWork):
    def __init__(self):
        super().__init__()
        self.ready = False

    def run(self):
        @serve
        def studio_ui(state: AppState):
            return {
                "status": "running",
                "comfy_port": state.comfy_ui.comfy_port,
                "web_port": state.comfy_ui.web_port,
                "lightning_port": state.comfy_ui.lightning_port,
                "ready": state.comfy_ui.ready
            }
        
        self.ready = True
        while True:
            time.sleep(1) 