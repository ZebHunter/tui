import os
from .vm_bhyve_cli import VmBhyveCLI
from .cloud_init_generator import generate_cloud_init
from .cloud_iso_builder import build_cloud_init_iso


class VMManager:
    def __init__(self):
        self.cli = VmBhyveCLI()

    def list_vms(self):
        out = self.cli.list()
        lines = out.splitlines()[1:]
        result = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                result.append(
                    {"name": parts[0], "state": parts[1]}
                )
        return result

    def get_info(self, name: str):
        return self.cli.info(name)

    def create_vm(self, name: str, ip: str):
        self.cli.create(name, template="linux_temp")

        yaml_data = generate_cloud_init(name=name, ip=ip)
        iso_path = f"/vm/iso/{name}-cloud-init.iso"
        build_cloud_init_iso(yaml_data, iso_path)

        self.cli.install(name, iso_path)

    def start_vm(self, name):
        self.cli.start(name)

    def stop_vm(self, name):
        self.cli.stop(name)

    def destroy_vm(self, name):
        self.cli.destroy(name)
