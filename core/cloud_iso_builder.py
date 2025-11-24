import subprocess
from pathlib import Path


def build_cloud_init_iso(user_data: str, iso_path: str):
    iso_path = Path(iso_path)
    iso_path.parent.mkdir(parents=True, exist_ok=True)

    user_file = iso_path.parent / "user-data"
    meta_file = iso_path.parent / "meta-data"

    user_file.write_text(user_data)
    meta_file.write_text("instance-id: iid-123456\n")

    subprocess.run([
        "genisoimage",
        "-output", str(iso_path),
        "-volid", "cidata",
        "-joliet",
        "-rock",
        str(user_file),
        str(meta_file)
    ], check=True)
