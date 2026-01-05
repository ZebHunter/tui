# core/vm_manager.py
import subprocess
import logging
import json
from pathlib import Path
from typing import Optional, Dict
import ipaddress

from .vm_bhyve_cli import VmBhyveCLI
from .cloud_init_generator import generate_cloud_init
from .cloud_iso_builder import build_cloud_init_iso

LOG = logging.getLogger(__name__)


class VMManager:
    VM_ROOT = Path("/vm")        
    ISO_DIR = VM_ROOT / "iso"
    TEMPLATES_DIR = VM_ROOT / ".templates"
    METADATA_FILE = VM_ROOT / ".vm_metadata.json"
    IP_POOL_START = "10.0.0.50"
    IP_POOL_END = "10.0.0.250"
    DEFAULT_GATEWAY = "10.0.0.1"

    def __init__(self):
        self.cli = VmBhyveCLI()
        logging.basicConfig(filename="vm_manager.log", level=logging.DEBUG)
        self._ensure_metadata_file()

    def list_vms(self):
        output = self.cli.list()
        metadata = self._load_metadata()
        
        vms = []
        lines = output.strip().split('\n')
        for line in lines[1:] if len(lines) > 1 and 'NAME' in lines[0].upper() else lines:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                state = parts[1]
                vm_data = {"name": name, "state": state}
                
    
                if name in metadata:
                    vm_data.update(metadata[name])
                
                vms.append(vm_data)
        
        return vms

    def get_info(self, name: str):
        info = self.cli.info(name)
        metadata = self.get_vm_metadata(name)
        
        if metadata:
            info_lines = [info]
            info_lines.append("\n--- Network Configuration ---")
            if "ip" in metadata:
                info_lines.append(f"IP Address: {metadata['ip']}")
            if "network_mode" in metadata:
                info_lines.append(f"Network Mode: {metadata['network_mode']}")
            if "switch" in metadata:
                info_lines.append(f"Switch: {metadata['switch']}")
            if "gateway" in metadata:
                info_lines.append(f"Gateway: {metadata['gateway']}")
            return "\n".join(info_lines)
        
        return info

    def ensure_network_switch(self, switch_name: str, network_mode: str = "bridge", gateway_ip: Optional[str] = None):
        try:
            out = self.cli.switch_list()
            if switch_name in out:
                LOG.info("Switch %s already exists", switch_name)
                return
        except Exception:
            pass
        
        if network_mode == "nat":
            if gateway_ip is None:
                gateway_ip = f"{self.DEFAULT_GATEWAY}/24"
            elif "/" not in gateway_ip:
                gateway_ip = f"{gateway_ip}/24"
            
            LOG.info("Creating NAT switch %s with gateway %s", switch_name, gateway_ip)
            try:
                self.cli.switch_create(switch_name, address=gateway_ip)
                LOG.info("NAT switch %s created with gateway %s. Ensure pf NAT rules are configured.", 
                        switch_name, gateway_ip)
            except Exception as exc:
                LOG.warning("Failed to create NAT switch %s: %s", switch_name, exc)
                raise
        else: 
            LOG.info("Creating bridge switch %s", switch_name)
            try:
                self.cli.switch_create(switch_name)
                LOG.info("Bridge switch %s created. Add physical interface manually if needed.", switch_name)
            except Exception as exc:
                LOG.warning("Failed to create bridge switch %s: %s", switch_name, exc)
                raise

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

    def _ensure_metadata_file(self):
        if not self.METADATA_FILE.exists():
            self.METADATA_FILE.write_text("{}")
    
    def _load_metadata(self) -> Dict:
        if not self.METADATA_FILE.exists():
            return {}
        try:
            return json.loads(self.METADATA_FILE.read_text())
        except Exception:
            LOG.exception("Failed to load metadata")
            return {}
    
    def _save_metadata(self, metadata: Dict):
        self.METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.METADATA_FILE.write_text(json.dumps(metadata, indent=2))
    
    def get_vm_metadata(self, name: str) -> Optional[Dict]:
        metadata = self._load_metadata()
        return metadata.get(name)
    
    def _update_vm_metadata(self, name: str, **kwargs):
        metadata = self._load_metadata()
        if name not in metadata:
            metadata[name] = {}
        metadata[name].update(kwargs)
        self._save_metadata(metadata)

    def _delete_vm_metadata(self, name: str) -> None:
        metadata = self._load_metadata()
        if name in metadata:
            del metadata[name]
            self._save_metadata(metadata)

    def _allocated_ips(self) -> set[str]:
        metadata = self._load_metadata()
        ips: set[str] = set()
        for vm_data in metadata.values():
            ip = vm_data.get("ip")
            if ip:
                ips.add(ip)
        return ips

    def _generate_ip(self) -> str:
        used = self._allocated_ips()
        start = ipaddress.IPv4Address(self.IP_POOL_START)
        end = ipaddress.IPv4Address(self.IP_POOL_END)

        for ip_int in range(int(start), int(end) + 1):
            ip_str = str(ipaddress.IPv4Address(ip_int))
            if ip_str not in used:
                return ip_str

        raise RuntimeError("No free IP addresses left in pool "
                           f"{self.IP_POOL_START}–{self.IP_POOL_END}")

    def _guess_gateway(self, ip: str) -> str:
        try:
            addr = ipaddress.IPv4Address(ip)
            net = ipaddress.IPv4Network(f"{ip}/24", strict=False)
            gw = net.network_address + 1
            return str(gw)
        except Exception:
            return self.DEFAULT_GATEWAY

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

    def start_vm(self, name: str):
        try:
            return self.cli.start(name)
        except Exception as exc:
            raise RuntimeError(f"Failed to start VM {name}: {exc}")

    def stop_vm(self, name: str):
        try:
            return self.cli.stop(name)
        except Exception as exc:
            raise RuntimeError(f"Failed to stop VM {name}: {exc}")

    def destroy_vm(self, name: str):
        try:
            result = self.cli.destroy(name)
        except Exception as exc:
            raise RuntimeError(f"Failed to destroy VM {name}: {exc}")
        else:
            self._delete_vm_metadata(name)
            return result
        

    def create_vm(self,
                  name: str,
                  ip: Optional[str] = None,
                  disk_size: str = "20G",
                  memory: str = "2G",
                  cpus: int = 2,
                  installer_iso_name: str = "ubuntu.iso",
                  network_mode: str = "bridge",
                  switch: Optional[str] = None):
       
        LOG.info("Creating VM %s ip=%s disk=%s mem=%s cpus=%d network_mode=%s", 
                 name, ip, disk_size, memory, cpus, network_mode)

        if not ip:
            existing = self.get_vm_metadata(name)
            if existing and "ip" in existing:
                ip = existing["ip"]
                LOG.info("Reusing existing IP %s for VM %s", ip, name)
            else:
                ip = self._generate_ip()
                LOG.info("Allocated new IP %s for VM %s", ip, name)

        self.ensure_vm_root()
        self.ensure_templates()

        gateway = self._guess_gateway(ip)
        
        if switch is None:
            if network_mode == "nat":
                switch = "public" 
            else:
                switch = "public" 
        
        gateway_for_switch = gateway if network_mode == "nat" else None
        self.ensure_network_switch(switch, network_mode, gateway_ip=gateway_for_switch)

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

        yaml_data = generate_cloud_init(name=name, ip=ip, gateway=gateway, network_mode=network_mode)
        iso_path = self.ISO_DIR / f"{name}-cloud-init.iso"
        try:
            build_cloud_init_iso(yaml_data, str(iso_path))
        except Exception:
            LOG.exception("Failed to build cloud-init ISO")
            raise

        self.add_cloud_iso_to_vmconf(name, iso_path)

        self._update_vm_metadata(name, 
                                 ip=ip, 
                                 network_mode=network_mode,
                                 switch=switch,
                                 gateway=gateway)

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

        vm_conf = self.VM_ROOT / name / "vm.conf"
        if vm_conf.exists():
            conf_content = vm_conf.read_text()
            if "cdrom0_name" not in conf_content:
                LOG.warning("cdrom0_name not found after vm install, adding manually")
                with vm_conf.open("a") as f:
                    f.write(f'\n# Installer ISO added by VMManager\n')
                    f.write(f'cdrom0_name="{str(installer_iso)}"\n')

        LOG.info("VM %s created and installer attached. Cloud-init seed: %s", name, iso_path)

        try:
            LOG.info("Starting VM %s", name)
            self.cli.start(name)
        except Exception:
            LOG.exception("Failed to start VM %s", name)

        return {"name": name, "disk": str(disk_path), "cloud_iso": str(iso_path), "ip": ip}
    
    def connect_ssh(self, name: str, user: str = "bhyve", port: int = 22):
        metadata = self.get_vm_metadata(name)
        if not metadata or "ip" not in metadata:
            raise RuntimeError(f"No IP address found for VM {name}. Make sure VM was created with an IP address.")
        
        ip = metadata["ip"]
        LOG.info("Connecting to VM %s via SSH at %s@%s", name, user, ip)
        ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", 
                   "-o", "UserKnownHostsFile=/dev/null",
                   f"{user}@{ip}", "-p", str(port)]
        
        try:
            subprocess.Popen(ssh_cmd)
            return f"SSH connection initiated to {user}@{ip}"
        except Exception as exc:
            LOG.exception("Failed to connect via SSH")
            raise RuntimeError(f"Failed to connect via SSH: {exc}")
    
    def connect_console(self, name: str):
        LOG.info("Connecting to console of VM %s", name)
        try:
            return self.cli.console(name)
        except Exception as exc:
            LOG.exception("Failed to connect to console")
            raise RuntimeError(f"Failed to connect to console of VM {name}: {exc}")
