import os

def save_file(file_path: str, content: bytes):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(content)

def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
