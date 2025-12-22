import random
from typing import Optional


class MockVMManager:
    def __init__(self):
        self.vms = [
            {"name": "ubuntu-test", "state": "Running"},
            {"name": "debian-dev", "state": "Stopped"},
            {"name": "centos-lab", "state": "Paused"},
        ]

    def list_vms(self):
        for vm in self.vms:
            vm["state"] = random.choice(["Running", "Stopped", "Paused"])
        return self.vms

    def get_info(self, name: str):
        return (
            f"Name: {name}\n"
            f"State: Running\n"
            f"IP: 10.0.0.{random.randint(10, 200)}\n"
            f"Memory: 2G\nCPUs: 2"
        )

    def create_vm(self, name: str, ip: Optional[str] = None, network_mode: str = "bridge", **kwargs):
        if not ip:
            ip = f"10.0.0.{random.randint(50, 200)}"
        self.vms.append({
            "name": name, 
            "state": "Stopped",
            "ip": ip,
            "network_mode": network_mode
        })
        return {"name": name, "ip": ip, "network_mode": network_mode}
    
    def stop_vm(self, name: str):
        for vm in self.vms:
            if vm["name"] == name:
                vm["state"] = "Stopped"
                return
    
    def destroy_vm(self, name: str):
        self.vms = [vm for vm in self.vms if vm["name"] != name]
    
    def connect_ssh(self, name: str, user: str = "bhyve", port: int = 22):
        for vm in self.vms:
            if vm["name"] == name:
                ip = vm.get("ip", "10.0.0.1")
                return f"SSH connection initiated to {user}@{ip}"
        raise RuntimeError(f"VM {name} not found")
