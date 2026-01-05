import asyncio
import logging
import os
import selectors
from textual.screen import Screen
from textual.widgets import Static, Footer
from textual.containers import Container
from textual import events
from textual.app import ComposeResult

LOG = logging.getLogger(__name__)


class VMConsoleScreen(Screen):
    
    BINDINGS = [
        ("escape", "exit_console", "Exit Console"),
        ("ctrl+]", "exit_console", "Exit Console"),
    ]
    
    def __init__(self, vm_name: str, manager):
        super().__init__()
        self.vm_name = vm_name
        self.manager = manager
        self.console_process = None
        self.console_master_fd = None
        self.console_widget = None
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"[bold]VM Console: {self.vm_name}[/bold]\n[dim]Press ESC or Ctrl+] to exit[/dim]\n", id="console_header"),
            Static("", id="console_output"),
            id="console_container"
        )
        yield Footer()
    
    async def on_mount(self) -> None:
        self.console_widget = self.query_one("#console_output", Static)
        try:
            result = self.manager.connect_console(self.vm_name)
            if isinstance(result, tuple):
                self.console_process, self.console_master_fd = result
            else:
                self.console_process = result
                self.console_master_fd = None
            
            if self.console_process:
                asyncio.create_task(self._read_console_output())
                self.console_widget.update("Connected to VM console. Type to interact...\n")
            else:
                self.console_widget.update(f"[red]Failed to connect to console of {self.vm_name}[/red]")
        except Exception as e:
            LOG.exception(f"Failed to connect to console: {e}")
            self.console_widget.update(f"[red]Error connecting to console: {e}[/red]")
    
    async def _read_console_output(self):
        if not self.console_process:
            return
        
        try:
            if self.console_master_fd:
                selector = selectors.DefaultSelector()
                selector.register(self.console_master_fd, selectors.EVENT_READ)
                
                while self.console_process and self.console_process.poll() is None:
                    events = selector.select(timeout=0.1)
                    if events:
                        for key, mask in events:
                            if mask & selectors.EVENT_READ:
                                try:
                                    data = os.read(key.fileobj, 1024)
                                    if data:
                                        line = data.decode('utf-8', errors='replace')
                                        current_text = self.console_widget.renderable
                                        if isinstance(current_text, str):
                                            new_text = current_text + line
                                            lines = new_text.split('\n')
                                            if len(lines) > 1000:
                                                new_text = '\n'.join(lines[-1000:])
                                            self.console_widget.update(new_text)
                                except OSError:
                                    break
                    await asyncio.sleep(0.01)
                selector.close()
            else:
                while self.console_process and self.console_process.poll() is None:
                    if self.console_process.stdout:
                        line = self.console_process.stdout.readline()
                        if line:
                            current_text = self.console_widget.renderable
                            if isinstance(current_text, str):
                                new_text = current_text + line
                                lines = new_text.split('\n')
                                if len(lines) > 1000:
                                    new_text = '\n'.join(lines[-1000:])
                                self.console_widget.update(new_text)
                    await asyncio.sleep(0.01)
        except Exception as e:
            LOG.exception(f"Error reading console output: {e}")
            if self.console_widget:
                self.console_widget.update(f"[red]Error reading console: {e}[/red]")
    
    async def on_key(self, event: events.Key) -> None:
        if event.key == "escape" or (event.key == "ctrl+]"):
            await self.action_exit_console()
            return
        
        try:
            if self.console_master_fd:
                if event.key.startswith("ctrl+"):
                    char = event.key.replace("ctrl+", "")
                    if char:
                        os.write(self.console_master_fd, char.encode())
                elif len(event.key) == 1:
                    os.write(self.console_master_fd, event.key.encode())
                elif event.key == "enter":
                    os.write(self.console_master_fd, b"\n")
                elif event.key == "backspace":
                    os.write(self.console_master_fd, b"\b")
            elif self.console_process and self.console_process.stdin:
                if event.key.startswith("ctrl+"):
                    char = event.key.replace("ctrl+", "")
                    if char:
                        self.console_process.stdin.write(char)
                        self.console_process.stdin.flush()
                elif len(event.key) == 1:
                    self.console_process.stdin.write(event.key)
                    self.console_process.stdin.flush()
                elif event.key == "enter":
                    self.console_process.stdin.write("\n")
                    self.console_process.stdin.flush()
                elif event.key == "backspace":
                    self.console_process.stdin.write("\b")
                    self.console_process.stdin.flush()
        except Exception as e:
            LOG.exception(f"Error sending input to console: {e}")
    
    async def action_exit_console(self) -> None:
        if self.console_master_fd:
            try:
                os.close(self.console_master_fd)
            except:
                pass
            self.console_master_fd = None
        
        if self.console_process:
            try:
                self.console_process.terminate()
                await asyncio.sleep(0.5)
                if self.console_process.poll() is None:
                    self.console_process.kill()
            except Exception as e:
                LOG.exception(f"Error closing console: {e}")
            finally:
                self.console_process = None
        
        self.dismiss()
    
    def on_unmount(self) -> None:
        if self.console_master_fd:
            try:
                os.close(self.console_master_fd)
            except:
                pass
        
        if self.console_process:
            try:
                self.console_process.terminate()
            except:
                pass

