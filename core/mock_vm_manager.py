import random


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

    def create_vm(self, name: str, ip: str):
        self.vms.append({"name": name, "state": "Stopped"})
