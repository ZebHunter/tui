import subprocess
from typing import Tuple, Optional


class VmBhyveCLI:
    def run(self, *args) -> Tuple[str, str]:
        cmd = ["vm"] + list(args)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.stdout, proc.stderr

    def list(self) -> str:
        out, err = self.run("list")
        if err:
            raise RuntimeError(err)
        return out

    def create(self, name: str, template: Optional[str] = None):
        args = ["create", name]
        if template:
            args += ["-t", template]
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
        if err:
            raise RuntimeError(err)
        return out
