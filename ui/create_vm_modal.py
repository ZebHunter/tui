from textual.widgets import Input, Button, Select
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.message import Message


class CreateVMSubmit(Message):
    def __init__(self, name: str, ip: str, network_mode: str = "bridge"):
        super().__init__()
        self.name = name
        self.ip = ip
        self.network_mode = network_mode


class CreateVMModal(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Input(placeholder="VM name", id="vm_name"),
            Input(placeholder="Static IP (empty = auto)", id="vm_ip"),
            Select(
                options=[("Bridge", "bridge"), ("NAT", "nat")],
                value="bridge",
                prompt="Network mode",
                id="network_mode"
            ),
            Horizontal(
                Button("Create", id="create"),
                Button("Cancel", id="cancel")
            )
        )

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "create":
            name = self.query_one("#vm_name", Input).value.strip()
            ip = self.query_one("#vm_ip", Input).value.strip()
            network_mode_select = self.query_one("#network_mode", Select)
            network_mode = network_mode_select.value
            if isinstance(network_mode, tuple):
                network_mode = network_mode[1]

            if not name:
                return

            import logging
            logging.debug(f"Creating VM: name={name}, ip={ip}, network_mode={network_mode}")
            if hasattr(self.app, '_handle_vm_creation'):
                submit_data = CreateVMSubmit(name, ip, network_mode)
                logging.debug(f"Calling _handle_vm_creation directly")
                self.app._handle_vm_creation(submit_data)
            self.dismiss()
        else:
            self.dismiss()
