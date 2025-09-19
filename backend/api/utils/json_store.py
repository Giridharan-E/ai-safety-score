import json
from pathlib import Path

# This file is not actively used in the current version but is kept for reference.

def get_json_store(filename):
    """
    Returns a simple dictionary-like object backed by a JSON file.
    """
    data_dir = Path(__file__).resolve().parent.parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    file_path = data_dir / filename

    if not file_path.exists():
        with open(file_path, "w") as f:
            f.write("{}")

    def read():
        with open(file_path, "r") as f:
            return json.load(f)

    def write(data):
        with open(file_path, "w") as f:
            json.dump(data, f)
    
    return {
        "read": read,
        "write": write
    }
