from string import Template
from pathlib import Path


TEMPLATE_PATH = Path(__file__).parent / "templates" / "cloud-init-template.yaml"


def generate_cloud_init(name: str, ip: str) -> str:
    template = Template(TEMPLATE_PATH.read_text())
    return template.substitute(
        VM_NAME=name,
        IP=ip,
        SSH_KEY="ssh-rsa AAAA....yourkey..."
    )
