from string import Template
from pathlib import Path


TEMPLATE_PATH = Path(__file__).parent / "templates" / "cloud-init-template.yaml"


def generate_cloud_init(name: str, ip: str, gateway: str = "10.0.0.1", network_mode: str = "bridge") -> str:
    template = Template(TEMPLATE_PATH.read_text())
    
    return template.substitute(
        VM_NAME=name,
        IP=ip,
        GATEWAY=gateway,
        SSH_KEY="ssh-rsa AAAA....yourkey..."
    )
