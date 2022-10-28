# This file is part of CoVeriTeam, a tool for on-demand composition of cooperative verification systems:
# https://gitlab.com/sosy-lab/software/coveriteam
#
# SPDX-FileCopyrightText: 2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import os
import shutil
import sys
from pathlib import Path
import yaml

SCRIPT_PATH = Path(os.path.dirname(__file__))

DEFAULT_VALUES = {
    "path_hostfile": "./hostfile.txt",
    "path_tunefile": "./tunefile.conf",
    "path_mpiexec": "mpiexec",
    "python_executable": str(sys.executable),
    "custom_command": "%exec -n 1 --mca mca_param_files %path_tunefile --machinefile %path_hostfile %python_exec %script_path",
}


def load_config() -> dict:
    with open(str(SCRIPT_PATH / "command_config.yml"), "r") as config_file:
        d = yaml.safe_load(config_file)
        return d


def sanitize_dict(config_dict: dict) -> dict:
    temp_work_dir = os.getcwd()
    os.chdir(SCRIPT_PATH)
    config_dict = {k: (v if v else DEFAULT_VALUES[k]) for (k, v) in config_dict.items()}

    config_dict["path_hostfile"] = str(Path(config_dict["path_hostfile"]).resolve())
    config_dict["path_tunefile"] = str(Path(config_dict["path_tunefile"]).resolve())

    os.chdir(temp_work_dir)
    return config_dict


def validate_dict(config_dict: dict):
    if not os.path.exists(config_dict["path_hostfile"]):
        raise Exception

    if not os.path.exists(config_dict["path_tunefile"]):
        raise Exception

    if not shutil.which(config_dict["path_mpiexec"]):
        raise Exception

    if not shutil.which(config_dict["python_executable"]):
        raise Exception


def parse_command(config_dict: dict) -> list:
    command: str = config_dict["custom_command"]
    command = command.replace("%exec", config_dict["path_mpiexec"])
    command = command.replace("%path_tunefile", config_dict["path_tunefile"])
    command = command.replace("%path_hostfile", config_dict["path_hostfile"])
    command = command.replace("%python_exec", config_dict["python_executable"])
    command = command.replace("%script_path", str(SCRIPT_PATH / "mpi_scheduler.py"))

    return command.split(" ")


def get_command() -> list:
    d = load_config()
    d = sanitize_dict(d)
    validate_dict(d)
    return parse_command(d)


if __name__ == "__main__":
    print(get_command())
