import platform
import logging
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import Horizontal

from ui.vm_list_view import VMListView, VMSelected
from ui.vm_info_view import VMInfoPanel
from ui.create_vm_modal import CreateVMModal, CreateVMSubmit

if platform.system() == "FreeBSD":
    from core.vm_manager import VMManager
else:
    from core.mock_vm_manager import MockVMManager as VMManager

logging.basicConfig(filename="debug.log", level=logging.DEBUG)


class BhyveApp(App):
    CSS_PATH = "ui/style.css"

    BINDINGS = [
        ("r", "refresh", "Refresh list"),
        ("c", "create", "Create VM"),
        ("s", "stop_vm", "Stop VM"),
        ("d", "delete_vm", "Delete VM"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.manager = VMManager()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            self.vm_list = VMListView(self.manager, id="vm_list")
            self.vm_info = VMInfoPanel("Select a VM to view info", id="vm_info")
            yield self.vm_list
            yield self.vm_info
        yield Footer()

    async def on_vm_selected(self, event: VMSelected):
        info = self.manager.get_info(event.name)
        logging.debug(f"Info content: {info}")
        self.vm_info.update_info(info)

    async def action_refresh(self):
        self.vm_list.refresh_list()
        self.notify("VM list refreshed")

    async def action_create(self):
        await self.push_screen(CreateVMModal())

    async def on_create_vm_submit(self, event: CreateVMSubmit):
        self.manager.create_vm(event.name, ip=event.ip)
        self.vm_list.refresh_list()
        self.notify(f"Created VM {event.name} with IP {event.ip}")

    async def action_stop_vm(self):
        if not self.vm_list.selected_name:
            self.notify("Select a VM first", severity="warning")
            return

        name = self.vm_list.selected_name
        try:
            self.manager.stop_vm(name)
            self.notify(f"VM {name} stopped")
            self.vm_list.refresh_list()
        except Exception as exc:
            self.notify(str(exc), severity="error")

    async def action_delete_vm(self):
        if not self.vm_list.selected_name:
            self.notify("Select a VM to delete", severity="warning")
            return

        name = self.vm_list.selected_name
        try:
            self.manager.destroy_vm(name)
            self.notify(f"VM {name} deleted")
            self.vm_list.refresh_list()
        except Exception as exc:
            self.notify(str(exc), severity="error")

if __name__ == "__main__":
    BhyveApp().run()
