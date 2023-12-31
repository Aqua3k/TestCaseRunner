import glob
import os

log_file = "result.json"

def is_log_dir(path: str)->bool:
    path = os.path.join(path, log_file)
    return os.path.isfile(path)

log_files = []
for dir in glob.glob(os.path.join("log", "*")):
    if is_log_dir(dir):
        log_files.append(os.path.join(dir, log_file))

