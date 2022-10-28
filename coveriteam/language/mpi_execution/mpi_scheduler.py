# This file is part of CoVeriTeam, a tool for on-demand composition of cooperative verification systems:
# https://gitlab.com/sosy-lab/software/coveriteam
#
# SPDX-FileCopyrightText: 2020 Dirk Beyer <https://www.sosy-lab.org>
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import signal
import sys
import traceback

from mpi4py import MPI
from pathlib import Path
from multiprocessing import Queue

from typing import List

import mpi_util

mpi_util.set_sys_path()

from coveriteam.language.parallel_portfolio import (  # noqa E402
    ParallelPortfolio,
    QueueManager,
)
from coveriteam.language.artifact import Verdict  # noqa E402
from coveriteam.language import CoVeriLangException  # noqa E402
import coveriteam.util as util  # noqa E402

comm: MPI.Comm = MPI.COMM_WORLD
my_rank = comm.Get_rank()
mode: str


class Scheduler:
    queue: Queue = None
    portfolio: ParallelPortfolio = None
    kwargs: dict = None
    i_comm: MPI.Intercomm
    possible_res = None
    running_workers: List[int] = []
    receive_buffer: List[MPI.Request] = []
    running: bool = True

    def receive_portfolio(
        self, portfolio: ParallelPortfolio = None, kwargs: dict = None
    ):
        """
        Receives the portfolio to execute.
        When no portfolio and no kwargs are given, try to get the portfolio from the queue process_sync
        """
        if portfolio is None and kwargs is None:
            self.queue = QueueManager.get_server_queue(
                auth_code=mpi_util.get_server_auth_code(),
                port=mpi_util.get_server_port_from_env(),
            )
            self.portfolio, self.kwargs = self.queue.get()
            self.queue.task_done()

        elif portfolio is None or kwargs is None:
            raise CoVeriLangException("Critical error: Portfolio or kwargs are missing")
        else:
            self.portfolio = portfolio
            self.kwargs = kwargs
        util.set_cache_directories(self.portfolio.settings.cache_dir)
        logging.basicConfig(
            level=self.portfolio.settings.log_level,
            format=mpi_util.get_logging_config(),
        )

    def spawn_worker(self):
        """
        Spawning the workers for actor execution.
        """
        global comm
        actor_count: int = len(self.portfolio.actors)
        logging.debug(f"Spawning {actor_count} worker")

        worker_script_path = Path(os.path.dirname(__file__)) / "mpi_worker.py"
        logging.debug(f"Used worker script is {worker_script_path}")

        # Spawning actor_count processes.
        self.i_comm = MPI.COMM_SELF.Spawn(
            sys.executable, args=[str(worker_script_path)], maxprocs=actor_count
        )

    def send_actors_and_kwargs(self):
        """
        Send the actors and kwargs to execute to the workers.
        """
        # Send actors to corresponding spawned workers.
        for i in range(self.i_comm.Get_remote_size()):
            self.i_comm.send(self.portfolio.actors[i], dest=i, tag=1)

        # Broadcast the input artifacts to all the actors in the parallel portfolio.
        self.i_comm.bcast(self.kwargs, root=MPI.ROOT)

        self.i_comm.bcast(self.portfolio.settings, root=MPI.ROOT)

    def receive_actor_result(self):

        # possible_res is a tuple (rank, message),
        # where rank is the rank of the sender and message contains the output artifacts.
        (process_id, produced_result) = MPI.Request.waitany(
            requests=self.receive_buffer
        )

        if isinstance(produced_result, Exception):
            raise produced_result

        logging.debug(f"Received result {produced_result}")

        # count the number of received results
        self.portfolio.counter += 1
        logging.debug(f"Received result {produced_result}")

        # Return the output artifacts produced by the actor.
        return produced_result

    def go_to_listening_mode(self):
        """
        In listening mode, the scheduler is waiting for any results produced by its workers.
        When a result is produced, the scheduler checks if the result satisfies the conditon
        to shutdown all workers or not.
        If assigns the result that satisfies the condition.
        If none of the workers produce the desired result
        then the result of the worker that finishes last is taken.
        """
        for i in range(self.i_comm.Get_remote_size()):
            self.receive_buffer.append(self.i_comm.irecv(source=i, tag=10))
            self.running_workers.append(i)

        self.possible_res = self.receive_actor_result()

        while not self.portfolio.termination_reached(self.possible_res):
            self.possible_res = self.receive_actor_result()

    def shutdown_workers(self):
        """
        Sends a shutdown signal to all still running workers.

        Note: After the shutdown you need to provide a MPI.recv for all stopped workers.
        This is not done in this method to prevent a potential
        deadlock with the waitany statement in self.go_to_listening_mode()
        """

        # Only one shutdown possible, so multiple signals are not sent
        if self.running:
            self.running = False
            # Termination of the running actors
            for i in self.running_workers:
                self.i_comm.isend("stop", dest=i, tag=99)

    def main(self, portfolio: ParallelPortfolio = None, kwargs: dict = None):
        # Using this try catch to always send something in the queue.
        # Otherwise the main CoVeriTeam process is blocking eternally
        try:
            self.receive_portfolio(portfolio, kwargs)
            self.spawn_worker()
            self.send_actors_and_kwargs()
            self.go_to_listening_mode()
        except (SystemExit, Exception) as e:
            traceback.print_exc()
            self.possible_res = e
            logging.fatal(
                f"{my_rank}: Terminating mpi environment without producing a good result"
            )
        finally:
            self.shutdown_workers()

            # Provide a receive for all pending requests
            MPI.Request.waitall(self.receive_buffer)
            logging.debug("Received all results. Finishing MPI execution")

            if self.possible_res is None:
                self.possible_res = Verdict("UNKNOWN")
            if self.queue is not None:
                # In this case, this scheduler is the one directly started by the portfolio
                # The result is put into the queue, which will be read by the portfolio
                self.queue.put(self.possible_res)
        return self.possible_res


if __name__ == "__main__":
    scheduler: Scheduler
    scheduler = Scheduler()

    def on_stop_signal(signum, frame):
        logging.warning("Shutting down MPI forcefully")
        scheduler.shutdown_workers()
        if scheduler.queue:
            scheduler.queue.put(Verdict("UNKNOWN"))

    signal.signal(signal.SIGTERM, on_stop_signal)

    scheduler.main()
