from textual.widgets import DataTable
from textual.message import Message
import re

class VMSelected(Message):
    def __init__(self, name: str):
        super().__init__()
        self.name = name


class VMListView(DataTable):
    def __init__(self, manager, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.selected_name = None

    def on_mount(self):
        self.add_columns("Name", "State")
        self.refresh_list()

    def refresh_list(self):
        self.clear()
        vms = self.manager.list_vms()
        for vm in vms:
            state = vm["state"]
            color = "green" if state.lower() == "running" else "red"
            self.add_row(
                f"[b]{vm['name']}[/b]",
                f"[{color}]{state}[/{color}]"
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        row = self.get_row_at(event.cursor_row)
        name = re.sub(r"\[\/?b\]", "", row[0])
        self.selected_name = name 
        self.post_message(VMSelected(name))
