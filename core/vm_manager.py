# core/vm_manager.py
import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Optional

from .vm_bhyve_cli import VmBhyveCLI
from .cloud_init_generator import generate_cloud_init
from .cloud_iso_builder import build_cloud_init_iso

LOG = logging.getLogger(__name__)


class VMManager:
    VM_ROOT = Path("/vm")        
    ISO_DIR = VM_ROOT / "iso"
    TEMPLATES_DIR = VM_ROOT / ".templates"

    def __init__(self):
        self.cli = VmBhyveCLI()
        logging.basicConfig(filename="vm_manager.log", level=logging.DEBUG)

    def list_vms(self):
        return self.cli.list()

    def get_info(self, name: str):
        return self.cli.info(name)

    def ensure_templates(self):
        tpl_dir = self.TEMPLATES_DIR / "linux_temp"
        tpl_dir.mkdir(parents=True, exist_ok=True)

        tpl_conf = tpl_dir / "linux_temp.conf"
        if not tpl_conf.exists():
            LOG.info("Creating linux_temp template at %s", tpl_conf)
            tpl_conf.write_text(
                '\n'.join([
                    '# linux_temp template for vm-bhyve',
                    'loader="uefi"',
                    'cpu=2',
                    'memory="2G"',
                    'graphics="no"',
                    '',
                    'disk0_type="virtio-blk"',
                    'disk0_name="disk0.img"',
                    '',
                    'network0_type="virtio-net"',
                    'network0_switch="public"',
                    '',
                    'cdrom0_type="ahci-cd"',
                ]) + "\n"
            )

    def ensure_vm_root(self):
        self.VM_ROOT.mkdir(parents=True, exist_ok=True)
        self.ISO_DIR.mkdir(parents=True, exist_ok=True)
        self.TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    def create_disk(self, vm_name: str, disk_size: str = "20G") -> Path:
        vm_dir = self.VM_ROOT / vm_name
        vm_dir.mkdir(parents=True, exist_ok=True)
        disk_path = vm_dir / "disk0.img"

        if disk_path.exists():
            LOG.info("Disk already exists: %s", disk_path)
            return disk_path

        LOG.info("Creating disk %s size=%s", disk_path, disk_size)
        try:
            subprocess.run(["truncate", "-s", disk_size, str(disk_path)], check=True)
        except Exception as exc:
            LOG.exception("Failed to create disk via truncate: %s", exc)
            LOG.info("Falling back to manual sparse creation")
            with open(disk_path, "wb") as f:
                f.truncate(0)
        return disk_path

    def add_cloud_iso_to_vmconf(self, vm_name: str, iso_path: Path):
        vm_conf = self.VM_ROOT / vm_name / "vm.conf"
        if not vm_conf.exists():
            LOG.warning("vm.conf not found for %s at %s", vm_name, vm_conf)
            return

        LOG.info("Appending cloud-init ISO to %s", vm_conf)
        with vm_conf.open("a") as f:
            f.write("\n# cloud-init seed added by VMManager\n")
            f.write(f'cdrom1_type="ahci-cd"\n')
            f.write(f'cdrom1_name="{str(iso_path)}"\n')

    def check_installer_iso(self, installer_name: str) -> Optional[Path]:
        iso_path = self.ISO_DIR / installer_name
        if iso_path.exists():
            return iso_path
        for candidate in self.ISO_DIR.glob("*.iso"):
            LOG.info("Found installer ISO candidate: %s", candidate)
            return candidate
        LOG.warning("No installer ISO found in %s", self.ISO_DIR)
        return None

    def stop_vm(self, name: str):
        try:
            return self.cli.stop(name)
        except Exception as exc:
            raise RuntimeError(f"Failed to stop VM {name}: {exc}")

    def destroy_vm(self, name: str):
        try:
            return self.cli.destroy(name)
        except Exception as exc:
            raise RuntimeError(f"Failed to destroy VM {name}: {exc}")
        

    def create_vm(self,
                  name: str,
                  ip: str,
                  disk_size: str = "20G",
                  memory: str = "2G",
                  cpus: int = 2,
                  installer_iso_name: str = "ubuntu.iso",
                  switch: str = "public"):
       
        LOG.info("Creating VM %s ip=%s disk=%s mem=%s cpus=%d", name, ip, disk_size, memory, cpus)

        self.ensure_vm_root()
        self.ensure_templates()

        try:
            self.cli.create(name, template="linux_temp")
        except Exception as exc:
            LOG.exception("vm create failed: %s", exc)
            raise

        disk_path = self.create_disk(name, disk_size=disk_size)

        vm_conf = self.VM_ROOT / name / "vm.conf"
        if vm_conf.exists():
            LOG.info("Updating vm.conf %s (cpu/memory settings)", vm_conf)
            with vm_conf.open("a") as f:
                f.write(f'\n# Settings injected by VMManager\n')
                f.write(f'cpu={cpus}\n')
                f.write(f'memory="{memory}"\n')
                f.write(f'disk0_name="{disk_path.name}"\n')
                f.write(f'disk0_type="virtio-blk"\n')
                f.write(f'network0_switch="{switch}"\n')
        else:
            LOG.warning("vm.conf does not exist after vm create: %s", vm_conf)

        yaml_data = generate_cloud_init(name=name, ip=ip)
        iso_path = self.ISO_DIR / f"{name}-cloud-init.iso"
        try:
            build_cloud_init_iso(yaml_data, str(iso_path))
        except Exception:
            LOG.exception("Failed to build cloud-init ISO")
            raise

        self.add_cloud_iso_to_vmconf(name, iso_path)

        installer_iso = self.check_installer_iso(installer_iso_name)
        if not installer_iso:
            msg = f"No installer ISO found in {self.ISO_DIR}; place installer (e.g. ubuntu.iso) there and run 'vm install {name} <installer.iso>' manually."
            LOG.error(msg)
            raise FileNotFoundError(msg)

        try:
            LOG.info("Installing OS %s into VM %s", installer_iso, name)
            self.cli.install(name, str(installer_iso))
        except Exception:
            LOG.exception("vm install failed")
            raise

        LOG.info("VM %s created and installer attached. Cloud-init seed: %s", name, iso_path)

        try:
            LOG.info("Starting VM %s", name)
            self.cli.start(name)
        except Exception:
            LOG.exception("Failed to start VM %s", name)

        return {"name": name, "disk": str(disk_path), "cloud_iso": str(iso_path)}
