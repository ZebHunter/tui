import os
import requests
from pathlib import Path

ISO_SOURCES = {
    "ubuntu-22.04": "https://releases.ubuntu.com/22.04/ubuntu-22.04.5-live-server-amd64.iso",
}


def download_iso(name: str, dest_dir: str = "/vm/iso") -> str:
    if name not in ISO_SOURCES:
        raise ValueError(f"Unknown ISO name: {name}")

    url = ISO_SOURCES[name]
    dest_path = Path(dest_dir)
    dest_path.mkdir(parents=True, exist_ok=True)
    file_path = dest_path / os.path.basename(url)

    if file_path.exists():
        print(f"[INFO] ISO already exists: {file_path}")
        return str(file_path)

    print(f"[INFO] Downloading {name} from {url} ...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"[INFO] Download complete: {file_path}")
    return str(file_path)
