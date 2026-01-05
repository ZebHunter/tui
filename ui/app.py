import platform
import logging
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import Horizontal

from ui.vm_list_view import VMListView, VMSelected
from ui.vm_info_view import VMInfoPanel
from ui.create_vm_modal import CreateVMModal, CreateVMSubmit
from ui.vm_console_screen import VMConsoleScreen

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
        ("space", "start_vm", "Start VM"),
        ("s", "stop_vm", "Stop VM"),
        ("d", "delete_vm", "Delete VM"),
        ("x", "ssh_connect", "SSH Connect"),
        ("t", "console", "VM Console"),
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

    def on_vm_selected(self, event: VMSelected):
        logging.debug(f"on_vm_selected called: event={event}, event.name={event.name}, type={type(event)}")
        try:
            info = self.manager.get_info(event.name)
            logging.debug(f"Info content: {info}")
            self.vm_info.update_info(info)
        except Exception as exc:
            logging.exception(f"Failed to get VM info for {event.name}")
            self.vm_info.update_info(f"Error loading info for {event.name}: {exc}")

    async def action_refresh(self):
        self.vm_list.refresh_list()
        self.notify("VM list refreshed")

    async def action_create(self):
        await self.push_screen(CreateVMModal())
    
    def on_screen_result(self, screen, result):
        logging.debug(f"on_screen_result called: screen={type(screen).__name__}, result={result}, type={type(result)}")
        if isinstance(result, CreateVMSubmit):
            self._handle_vm_creation(result)
    
    def on_create_vm_submit(self, event: CreateVMSubmit):
        logging.debug(f"on_create_vm_submit called: name={event.name}, ip={event.ip}, network_mode={event.network_mode}")
        self._handle_vm_creation(event)
    
    def _handle_vm_creation(self, submit_data: CreateVMSubmit):
        logging.debug(f"Handling VM creation: name={submit_data.name}, ip={submit_data.ip}, network_mode={submit_data.network_mode}")
        try:
            create_result = self.manager.create_vm(
                submit_data.name,
                ip=submit_data.ip if submit_data.ip else None,
                network_mode=submit_data.network_mode,
            )
            logging.debug(f"VM created, result: {create_result}")
            self.vm_list.refresh_list()
            ip = submit_data.ip or None
            if isinstance(create_result, dict):
                ip = create_result.get("ip", ip or "N/A")
            if not ip:
                ip = "N/A"
            self.notify(f"Created VM {submit_data.name} with IP {ip} ({submit_data.network_mode})")
        except Exception as exc:
            self.notify(f"Failed to create VM: {exc}", severity="error")
            logging.exception("Failed to create VM")

    async def action_start_vm(self):
        if not self.vm_list.selected_name:
            self.notify("Select a VM first", severity="warning")
            return

        name = self.vm_list.selected_name
        try:
            self.manager.start_vm(name)
            self.notify(f"VM {name} started")
            self.vm_list.refresh_list()
        except Exception as exc:
            self.notify(str(exc), severity="error")

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
    
    async def action_ssh_connect(self):
        if not self.vm_list.selected_name:
            self.notify("Select a VM first", severity="warning")
            return
        
        name = self.vm_list.selected_name
        try:
            result = self.manager.connect_ssh(name)
            self.notify(f"SSH connection initiated to {name}")
        except Exception as exc:
            self.notify(str(exc), severity="error")
    
    async def action_console(self):
        if not self.vm_list.selected_name:
            self.notify("Select a VM first", severity="warning")
            return
        
        name = self.vm_list.selected_name
        try:
            await self.push_screen(VMConsoleScreen(name, self.manager))
        except Exception as exc:
            self.notify(f"Failed to open console: {exc}", severity="error")
            logging.exception("Failed to open console")

if __name__ == "__main__":
    BhyveApp().run()
