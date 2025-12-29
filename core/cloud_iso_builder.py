import subprocess
import shutil
from pathlib import Path


def _find_iso_tool():
    for tool in ["mkisofs", "genisoimage"]:
        if shutil.which(tool):
            return tool
    raise RuntimeError(
        "No ISO creation tool found. Install 'cdrtools' package on FreeBSD:\n"
        "  pkg install cdrtools\n"
        "Or install 'genisoimage' on Linux."
    )


def build_cloud_init_iso(user_data: str, iso_path: str):
    iso_path = Path(iso_path)
    iso_path.parent.mkdir(parents=True, exist_ok=True)

    temp_dir = iso_path.parent / f".cloud-init-{iso_path.stem}"
    temp_dir.mkdir(exist_ok=True)
    
    user_file = temp_dir / "user-data"
    meta_file = temp_dir / "meta-data"

    user_file.write_text(user_data)
    meta_file.write_text("instance-id: iid-123456\n")

    iso_tool = _find_iso_tool()
    
    if iso_tool == "mkisofs":
        cmd = [
            "mkisofs",
            "-o", str(iso_path),
            "-volid", "cidata",
            "-joliet",
            "-rock",
            str(temp_dir)
        ]
    else:
        cmd = [
            "genisoimage",
            "-output", str(iso_path),
            "-volid", "cidata",
            "-joliet",
            "-rock",
            str(user_file),
            str(meta_file)
        ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(
            f"Failed to create ISO: {e.stderr}\n"
            f"Command: {' '.join(cmd)}\n"
            f"Return code: {e.returncode}"
        )
    
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
