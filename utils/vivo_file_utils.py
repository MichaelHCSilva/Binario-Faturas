# utils/vivo_file_utils.py
import os
import time
import shutil
import zipfile

def wait_for_download_file(download_dir, before_files, extension=".pdf", timeout=20):
    
    end_time = time.time() + timeout
    while time.time() < end_time:
        current_files = set(os.listdir(download_dir))
        new_files = current_files - before_files
        for f in new_files:
            if f.lower().endswith(extension.lower()):
                return f
        time.sleep(0.5)
    return None

def move_file(src_path, target_dir, new_name=None, overwrite=False):

    if not os.path.exists(src_path):
        return None
    os.makedirs(target_dir, exist_ok=True)
    dest_name = new_name or os.path.basename(src_path)
    dest_path = os.path.join(target_dir, dest_name)
    if os.path.exists(dest_path) and not overwrite:
        base, ext = os.path.splitext(dest_name)
        count = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(target_dir, f"{base}_{count}{ext}")
            count += 1
    shutil.move(src_path, dest_path)
    return dest_path

def extract_zip(zip_path, extract_to):

    if not os.path.exists(zip_path):
        return
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
