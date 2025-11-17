from textual.widgets import Input, Button
from textual.containers import Vertical, Horizontal
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.message import Message


class CreateVMSubmit(Message):
    def __init__(self, name: str, ip: str):
        super().__init__()
        self.name = name
        self.ip = ip


class CreateVMModal(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Vertical(
            Input(placeholder="VM name", id="vm_name"),
            Input(placeholder="Static IP (e.g. 10.0.0.50)", id="vm_ip"),
            Horizontal(
                Button("Create", id="create"),
                Button("Cancel", id="cancel")
            )
        )

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "create":
            name = self.query_one("#vm_name", Input).value
            ip = self.query_one("#vm_ip", Input).value
            self.dismiss(CreateVMSubmit(name, ip))
        else:
            self.dismiss(None)
