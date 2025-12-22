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
        self.add_columns("Name", "State", "IP Address", "Network")
        self.refresh_list()
        self.cursor_type = "row"

    def refresh_list(self):
        self.clear()
        vms = self.manager.list_vms()
        import logging
        logging.debug(f"Refreshing list with {len(vms)} VMs: {[v.get('name') for v in vms]}")
        for vm in vms:
            name = vm.get("name", "Unknown")
            state = vm.get("state", "Unknown")
            color = "green" if state.lower() == "running" else "red"
            ip = vm.get("ip", "N/A")
            network_mode = vm.get("network_mode", "N/A")
            self.add_row(
                f"[b]{name}[/b]",
                f"[{color}]{state}[/{color}]",
                ip,
                network_mode,
                key=name 
            )

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        import logging
        logging.debug(f"Row selected event received: {event}")
        logging.debug(f"Event type: {type(event)}, dir: {[x for x in dir(event) if not x.startswith('_')]}")
        
        name = None
        
        try:
            if hasattr(event, 'cursor_row'):
                cursor_row = event.cursor_row
                logging.debug(f"cursor_row: {cursor_row}")
                row_key = self.get_row_key_at(cursor_row)
                if row_key:
                    name = str(row_key)
                    logging.debug(f"Got name from get_row_key_at({cursor_row}): {name}")
        except Exception as e:
            logging.debug(f"Error getting name from cursor_row: {e}")
        
        if not name:
            try:
                if hasattr(event, 'row_key') and event.row_key:
                    row_key_obj = event.row_key
                    if hasattr(row_key_obj, 'value'):
                        name = str(row_key_obj.value)
                    else:
                        if hasattr(event, 'cursor_row'):
                            name = str(self.get_row_key_at(event.cursor_row))
                    logging.debug(f"Got name from row_key object: {name}")
            except Exception as e:
                logging.debug(f"Error getting row_key: {e}")
        
        if not name:
            try:
                if hasattr(event, 'cursor_row'):
                    cursor_row = event.cursor_row
                    logging.debug(f"cursor_row: {cursor_row}")
                    try:
                        row_key = self.get_row_key_at(cursor_row)
                        if row_key:
                            name = str(row_key)
                            logging.debug(f"Got name from get_row_key_at: {name}")
                    except Exception as e:
                        logging.debug(f"get_row_key_at failed: {e}")
                    
                    if not name:
                        try:
                            row = self.get_row_at(cursor_row)
                            logging.debug(f"Got row: {row}")
                            if row and len(row) > 0:
                                name = re.sub(r"\[/?b\]", "", str(row[0])).strip()
                                logging.debug(f"Got name from row data: {name}")
                        except Exception as e:
                            logging.debug(f"get_row_at failed: {e}")
            except Exception as e:
                logging.debug(f"Error getting cursor_row: {e}")
        
        if not name:
            try:
                if hasattr(event, 'coordinate'):
                    coord = event.coordinate
                    logging.debug(f"coordinate: {coord}")
                    if coord:
                        row_key = self.get_row_key_at(coord.row)
                        if row_key:
                            name = str(row_key)
                            logging.debug(f"Got name from coordinate.row: {name}")
            except Exception as e:
                logging.debug(f"Error getting coordinate: {e}")
        
        if name:
            self.selected_name = name
            logging.debug(f"Selected VM: {name}, posting VMSelected message")
            self.post_message(VMSelected(name))
        else:
            logging.warning(f"Could not determine selected VM name. Event: {event}, cursor_row: {getattr(event, 'cursor_row', 'N/A')}")
