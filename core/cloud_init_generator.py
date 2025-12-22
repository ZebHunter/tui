from string import Template
from pathlib import Path
import logging
from typing import Optional

LOG = logging.getLogger(__name__)

TEMPLATE_PATH = Path(__file__).parent / "templates" / "cloud-init-template.yaml"


def find_user_ssh_key() -> Optional[str]:
    ssh_dir = Path.home() / ".ssh"
    key_files = [
        "id_ed25519.pub",
        "id_rsa.pub",
        "id_ecdsa.pub",
        "id_dsa.pub"
    ]
    
    for key_file in key_files:
        key_path = ssh_dir / key_file
        if key_path.exists() and key_path.is_file():
            try:
                key_content = key_path.read_text().strip()
                if key_content and not key_content.startswith("#"):
                    LOG.info("Found SSH key at %s", key_path)
                    return key_content
            except Exception as exc:
                LOG.warning("Failed to read SSH key from %s: %s", key_path, exc)
                continue
    
    LOG.warning("No SSH public key found in ~/.ssh/. User 'bhyve' will be created without SSH access.")
    return None


def generate_cloud_init(
    name: str,
    ip: str,
    gateway: str = "10.0.0.1",
    network_mode: str = "bridge",
    ssh_key: Optional[str] = None
) -> str:
    if ssh_key is None:
        ssh_key = find_user_ssh_key()
    
    template_content = TEMPLATE_PATH.read_text()
    
    if ssh_key:
        template = Template(template_content)
        return template.substitute(
            VM_NAME=name,
            IP=ip,
            GATEWAY=gateway,
            SSH_KEY=ssh_key
        )
    else:
        LOG.warning("No SSH key provided for VM %s. User 'bhyve' will be created without SSH access.", name)
        
        yaml_lines = [
            "#cloud-config",
            f"hostname: {name}",
            "",
            "users:",
            "  - name: bhyve",
            "    sudo: ALL=(ALL) NOPASSWD:ALL",
            "",
            "network:",
            "  version: 2",
            "  ethernets:",
            "    eth0:",
            "      dhcp4: false",
            f"      addresses: [{ip}/24]",
            f"      gateway4: {gateway}",
            "      nameservers: [8.8.8.8]"
        ]
        return "\n".join(yaml_lines)
