# This file is part of CoVeriTeam, a tool for on-demand composition of cooperative verification systems:
# https://gitlab.com/sosy-lab/software/coveriteam
#
# SPDX-FileCopyrightText: 2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import logging
import time
import traceback
from threading import Thread
from mpi4py import MPI
from mpi_scheduler import Scheduler

import mpi_util
import coveriteam.util
from coveriteam.language.actor import Actor

mpi_util.set_sys_path()

from coveriteam.language.parallel_portfolio import ParallelPortfolio  # noqa E402
from coveriteam.language.artifact import Verdict  # noqa E402

comm: MPI.Comm = MPI.COMM_WORLD
my_rank = comm.Get_rank()
mode: str


class MPIWorker:
    parent_comm: MPI.Intercomm
    actor: Actor = None
    kwargs: dict = None
    result: Verdict = None
    log: logging.Logger

    # Only used, if this worker has to execute a portfolio
    scheduler: Scheduler = None

    def __init__(self):
        # Get the parent communicator to communicate with master MPI process
        # There is no need to communicate with other workers
        self.parent_comm = MPI.COMM_SELF.Get_parent()
        self.log = logging.getLogger(self.__class__.__name__)

    def receive_work(self):
        # Actor for execution, each worker receives his own
        self.actor = self.parent_comm.recv(self.actor, source=0, tag=1)

        # Arguments for the actor.act method. Every worker receives the same
        self.kwargs = self.parent_comm.bcast(self.kwargs, root=0)

        settings: mpi_util.Settings = None
        settings = self.parent_comm.bcast(settings, root=0)

        Actor.data_model = settings.data_model
        logging.basicConfig(
            level=settings.log_level, format=mpi_util.get_logging_config()
        )
        coveriteam.util.set_cache_directories(settings.cache_dir)

        Actor.trust_tool_info = settings.trust_tool_info

    def listen_to_stop_signal(self):
        # Tag 99 is always a stop signal
        stop_sig: str = None
        while not self.parent_comm.iprobe(source=0, tag=99):
            time.sleep(0.5)

        self.parent_comm.recv(stop_sig, source=0, tag=99)

        self.log.debug(f"Shutting down MPI worker {my_rank}")

        if self.scheduler is not None:
            self.scheduler.shutdown_workers()
        else:
            self.actor.stop()
        self.log.debug("Shutdown complete")

    def start_working(self):
        thread = Thread(target=self.listen_to_stop_signal)
        thread.start()

        coveriteam.util.CURRENTLY_IN_MPI = True
        try:
            self.result = self.actor.act(**self.kwargs)
        except (SystemExit, Exception) as fatal_error:
            traceback.print_exc()
            self.result = fatal_error
        finally:
            # There must be a send at the end of the execution
            # Otherwise the scheduler may wait for it eternally
            self.parent_comm.send(self.result, dest=0, tag=10)
        self.log.debug(f"{my_rank}: send the results to scheduler")

        thread.join()

    def worker_main(self):
        self.receive_work()
        self.start_working()


if __name__ == "__main__":
    MPIWorker().worker_main()
