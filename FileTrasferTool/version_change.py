import sys

new_version = sys.argv[1]
path_to_work_dir = sys.argv[2]

with open(f"{path_to_work_dir}\scripts\Autotester_FileTransfer.py", "r") as file:
    lines = file.readlines()

with open(f"{path_to_work_dir}\scripts\Autotester_FileTransfer.py", "w") as file:
    for line in lines:
        if line.startswith("version = "):
            file.write(f'version = "{new_version}"\n')
        else:
            file.write(line)
