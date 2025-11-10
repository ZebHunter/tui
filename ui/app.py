from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import Horizontal
from core.vm_manager import VMManager
from ui.vm_list_view import VMListView, VMSelected
from ui.vm_info_view import VMInfoPanel

class BhyveApp(App):
    CSS_PATH = "ui/style.css"

    BINDINGS = [
        ("r", "refresh", "Refresh list"),
        ("c", "create", "Create VM"),
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
        self.vm_info.update_info(info)

    async def action_refresh(self):
        self.vm_list.refresh_list()
        self.notify("VM list refreshed")

    async def action_create(self):
        pass

if __name__ == "__main__":
    BhyveApp().run()