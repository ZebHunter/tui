from core.vm_manager import VMManager
from core.iso_downloader import download_iso

manager = VMManager()

iso_path = download_iso("ubuntu-22.04")

manager.create_vm(
    name="ubuntu-vm",
    template="linux",
    iso_path=iso_path,
    disk_size="20G",
    memory="4G",
    cpus=2
)

manager.start_vm("ubuntu-vm")

print(manager.get_info("ubuntu-vm"))
