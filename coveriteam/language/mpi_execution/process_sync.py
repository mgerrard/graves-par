# This file is part of CoVeriTeam, a tool for on-demand composition of cooperative verification systems:
# https://gitlab.com/sosy-lab/software/coveriteam
#
# SPDX-FileCopyrightText: 2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0
import random
import string
from multiprocessing import Queue, Process
from multiprocessing.managers import BaseManager


class QueueManager(BaseManager):
    """
    This is another process, which is only used to send things between the mpi environment
    and the process of CoVeriTeam.
    """

    server_port: int = 50_000
    process: Process
    auth_code: str

    @classmethod
    def create_server(cls, queue: Queue):
        cls.register("get_queue", callable=lambda: queue)
        found = False
        base_manager = None

        cls.auth_code = create_random_auth_code(20)
        # basic search for open ports. Searching ports from 50000 to 50010
        while cls.server_port < 50_010 and not found:
            try:
                manager = cls(
                    address=("", cls.server_port), authkey=bytes(cls.auth_code, "utf-8")
                )
                base_manager = manager.get_server()
                found = True
            except OSError:
                cls.server_port += 1

        if base_manager is None:
            raise Exception(
                "Ports 50000 - 50010 where not available for the creation of the manager for mpi process syncing"
            )

        cls.process = Process(target=base_manager.serve_forever)
        cls.process.start()

    @classmethod
    def stop_server(cls):
        cls.process.terminate()

    @classmethod
    def get_server_queue(
        cls, auth_code: str = None, address: str = "127.0.0.1", port: int = None
    ) -> Queue:
        if auth_code is None:
            auth_code = cls.auth_code

        if auth_code is None:
            raise ValueError("Auth-Code not given in get_server_queue of QueueManager")

        if port is None:
            port = cls.server_port
        cls.register("get_queue")
        manager = cls(address=(address, port), authkey=bytes(auth_code, "utf-8"))
        manager.connect()
        return manager.get_queue()


def create_random_auth_code(length: int) -> str:
    return "".join(
        random.choices(string.ascii_letters + string.digits, k=length)  # noqa S311
    )
