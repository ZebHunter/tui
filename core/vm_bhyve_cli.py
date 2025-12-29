import subprocess
import shutil
from typing import Tuple, Optional


class VmBhyveCLI:
    def __init__(self):
        if not shutil.which("vm"):
            raise RuntimeError(
                "vm-bhyve command not found. Install it on FreeBSD:\n"
                "  pkg install vm-bhyve\n"
                "Then initialize with: vm init"
            )

    def run(self, *args) -> Tuple[str, str]:
        cmd = ["vm"] + list(args)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            error_msg = proc.stderr.strip() or proc.stdout.strip() or f"Command failed: {' '.join(cmd)}"
            raise RuntimeError(f"vm-bhyve error: {error_msg}")
        return proc.stdout, proc.stderr

    def list(self) -> str:
        out, err = self.run("list")
        return out

    def create(self, name: str, template: Optional[str] = None):
        args = ["create"]
        if template:
            args += ["-t", template]
        args.append(name)
        return self.run(*args)[0]

    def install(self, name: str, iso_path: str):
        return self.run("install", name, iso_path)[0]

    def start(self, name: str):
        return self.run("start", name)[0]

    def stop(self, name: str, force=False):
        args = ["stop", name]
        if force:
            args.append("-f")
        return self.run(*args)[0]

    def destroy(self, name: str):
        return self.run("destroy", name)[0]

    def info(self, name: str) -> str:
        out, err = self.run("info", name)
        return out
    
    def switch_list(self) -> str:
        out, err = self.run("switch", "list")
        return out
    
    def switch_create(self, name: str, address: Optional[str] = None):
        args = ["switch", "create"]
        if address:
            args.extend(["-a", address])
        args.append(name)
        return self.run(*args)[0]
    
    def switch_add(self, switch_name: str, interface: str):
        return self.run("switch", "add", switch_name, interface)[0]