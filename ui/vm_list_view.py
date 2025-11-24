import re
from textual.widgets import DataTable
from textual.message import Message


class VMSelected(Message):
    def __init__(self, name: str):
        super().__init__()
        self.name = name


class VMListView(DataTable):
    def __init__(self, manager, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager

    def on_mount(self):
        self.add_columns("Name", "State")
        self.refresh_list()

    def refresh_list(self):
        self.clear()
        for vm in self.manager.list_vms():
            color = "green" if vm["state"].lower() == "running" else "red"
            self.add_row(f"[b]{vm['name']}[/b]", f"[{color}]{vm['state']}[/{color}]")

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        row = self.get_row_at(event.cursor_row)
        vm_name = re.sub(r"\[/?b\]", "", row[0])
        self.post_message(VMSelected(vm_name))
