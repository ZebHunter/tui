from textual.widgets import Static

class VMInfoPanel(Static):
    def update_info(self, text: str):
        self.update(f"[bold white]Info:[/bold white]\n{text}")
        self.refresh()