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
    
    def start(self, name : str):
        self.run("start", name)
    
    def stop(self, name : str):
        self.run("stop", name)
    
    def destroy(self, name : str):
        self.run("destroy", name)

    def info(self, name : str) -> str:
        out, err = self.run("info", name)
        if err:
            raise RuntimeError(err)
        return out
    def console(self, name : str) -> subprocess.Popen:
        cmd = ["vm", "console", name]
        return subprocess.Popen(cmd)
    def install(self, name: str, iso_path: str):
        self.run("install", name, iso_path)
    
    def create(
            self,
            name : str,
            template : Optional[str] = None,
            disk_size : str = "20G",
            memory : str = "2G",
            cpus : int = 2
    ) -> str :
        args = ["create", name, "-s", disk_size, "-m", memory, str(cpus)]
        if template:
            args += ["-t", template]
        out, err = self.run(*args)
        if err:
            raise RuntimeError(err)
        return out
