import os
from datetime import datetime
from pathlib import Path
from typing import Optional


from modguard.constants import MODULE_FILE_NAME, CONFIG_FILE_NAME
from modguard.errors import ModguardError
from modguard.filesystem import validate_project_config_path


def validate_module_config(root: str = ".") -> Optional[str]:
    file_path = os.path.join(root, f"{MODULE_FILE_NAME}.yml")
    if os.path.exists(file_path):
        return file_path
    file_path = os.path.join(root, f"{MODULE_FILE_NAME}.yaml")
    if os.path.exists(file_path):
        return file_path
    return


def validate_path_for_add(path: str) -> None:
    if not os.path.exists(path):
        raise ModguardError(f"{path} does not exist.")
    if os.path.isdir(path):
        if os.path.exists(
            os.path.join(path, f"{MODULE_FILE_NAME}.yml")
        ) or os.path.exists(os.path.join(path, f"{MODULE_FILE_NAME}.yaml")):
            raise ModguardError(f"{path} already contains a {MODULE_FILE_NAME}.yml")
        if not os.path.exists(os.path.join(path, "__init__.py")):
            raise ModguardError(
                f"{path} is not a valid Python package (no __init__.py found)."
            )
        # check for project config
        try:
            validate_project_config_path(path)
        except SystemError:
            pass
        else:
            return
    # this is a file
    else:
        if not path.endswith(".py"):
            raise ModguardError(f"{path} is not a Python file.")
        if os.path.exists(path.removesuffix(".py")):
            raise ModguardError("{path} already has a directory of the same name.")
    path_obj = Path(path)
    # Iterate upwards, looking for project config
    for parent in path_obj.parents:
        try:
            validate_project_config_path(str(parent))
        except SystemError:
            continue
        else:
            return
    raise ModguardError(f"{CONFIG_FILE_NAME} does not exist in any parent directories")


def build_module(path: str, tags: list[str]) -> None:
    if os.path.isdir(path):
        with open(f"{path}/{MODULE_FILE_NAME}.yml", "w") as f:
            f.write(f"tags: [{','.join(tags)}]\n")
            # TODO should we write this into your modguard.yml as a set of minimum deps?
            # move to parent dir
            # run init check logic
            # only iterate over errors belonging to the new module
            return
    else:
        dirname = path.replace(".py", "")
        os.mkdir(dirname)
        with open(f"{dirname}/__init__.py") as new_init:
            new_init.write(f"""
            # Generated by modguard  on {datetime.now()}
            from .main import *""")

        with open(path, "r") as original_file:
            with open(f"{dirname}/main.py", "w") as new_file:
                new_file.write(original_file.read())
                # TODO write init.py, validate existing folder with same name doesn't already exist, write import, write module.yml

        os.remove(path)
