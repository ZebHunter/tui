from dataclasses import dataclass
from typing import List, Optional
from .vm_bhyve_cli import VmBhyveCLI

@dataclass
class VM:
    name: str
    state: str
    memory: Optional[str] = None
    cpus: Optional[int] = None
    template: Optional[str] = None


class VMManager:
    def __init__(self):
        self.cli = VmBhyveCLI()

    def list_vms(self) -> List[VM]:
        out = self.cli.list()
        lines = out.splitlines()[1:]
        vms = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                vms.append(VM(name=parts[0], state=parts[1]))
        return vms

    def create_vm(
        self,
        name: str,
        template: Optional[str] = None,
        iso_path: Optional[str] = None,
        disk_size: str = "20G",
        memory: str = "2G",
        cpus: int = 2,
    ):
        self.cli.create(name, template, disk_size, memory, cpus)
        if iso_path:
            self.cli.install(name, iso_path)

    def start_vm(self, name: str):
        self.cli.start(name)

    def stop_vm(self, name: str, force: bool = False):
        self.cli.stop(name, force)

    def destroy_vm(self, name: str, force: bool = False):
        self.cli.destroy(name, force)

    def get_info(self, name: str) -> str:
        return self.cli.info(name)

    def open_console(self, name: str):
        return self.cli.console(name)
