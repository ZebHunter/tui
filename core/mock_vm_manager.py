from dataclasses import dataclass
from typing import List
import random

@dataclass
class VM:
    name: str
    state: str
    memory: str = "2G"
    cpus: int = 2

class MockVM:
    def __init__(self, name, state="Stopped", ip="0.0.0.0"):
        self.name = name
        self.state = state
        self.ip = ip

class MockVMManager:
    def __init__(self):
        self.vms = [
            VM(name="ubuntu-test", state="Running"),
            VM(name="debian-dev", state="Stopped"),
            VM(name="centos-lab", state="Paused"),
        ]

    def list_vms(self) -> List[VM]:
        for vm in self.vms:
            vm.state = random.choice(["Running", "Stopped", "Paused"])
        return self.vms

    def get_info(self, name: str) -> str:
        vm = next((v for v in self.vms if v.name == name), None)
        if not vm:
            return "VM not found"
        return (
            f"Name: {vm.name}\n"
            f"State: {vm.state}\n"
            f"Memory: {vm.memory}\n"
            f"CPUs: {vm.cpus}\n"
            f"Network: 192.168.0.{random.randint(10,99)}"
        )

    def create_vm(self, name: str, **kwargs):
        vm = MockVM(name=name, state="Stopped", ip=ip)
        self.vms.append(vm)
