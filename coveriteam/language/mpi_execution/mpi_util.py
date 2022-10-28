# This file is part of CoVeriTeam, a tool for on-demand composition of cooperative verification systems:
# https://gitlab.com/sosy-lab/software/coveriteam
#
# SPDX-FileCopyrightText: 2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import sys
import glob

try:
    # Case if it is imported by some of the mpi_*.py scripts
    # This module is imported from mpi_scheduler / worker, before the paths
    # to the whole coveriteam project are set. That's why the import in the
    # except clause is not working.
    import constants
except ModuleNotFoundError:
    # Case if it is imported by portfolio.py
    import coveriteam.language.mpi_execution.constants  # noqa F401


def get_logging_config():
    logging_format = (
        "%(asctime)-15s %(levelname)s p%(process)s %(filename)s: %(message)s"
    )
    return logging_format


# Appending the wheels to the path
def set_sys_path():
    sys.dont_write_bytecode = True  # prevents writing .pyc files

    script = pathlib.Path(__file__).resolve()
    project_dir = script.parent.parent.parent.parent
    lib_dir = project_dir / "lib"
    for wheel in glob.glob(os.path.join(lib_dir, "*.whl")):
        sys.path.insert(0, wheel)

    sys.path.insert(0, str(project_dir))
    sys.path.append(str(lib_dir))

    sys.setrecursionlimit(5000)


def get_server_port_from_env() -> int:
    str_port = os.environ.get(constants.PORT)

    return int(str_port)


def get_server_auth_code() -> str:
    return os.environ.get(constants.AUTH_CODE)


class Settings:
    """
    Used to share information needed for every scheduler and worker
    """

    log_level: int
    data_model: str
    trust_tool_info: bool
    cache_dir: pathlib.Path

    def __init__(
        self, log_level: int, data_model: str, trust_tool_info, cache_dir: pathlib.Path
    ):
        self.log_level = log_level
        self.data_model = data_model
        self.trust_tool_info = trust_tool_info
        self.cache_dir = cache_dir
