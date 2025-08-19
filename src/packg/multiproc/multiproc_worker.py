"""
utility to run a simple worker in multiple processes with a progress bar and error handling
"""

# pylint: disable=duplicate-code
# TODO either fix duplicate-code or remove this TODO comment
# TODO move the main() example outside of this file
from __future__ import annotations

import random
import time
from multiprocessing import Process, Queue
from timeit import default_timer
from traceback import format_exception
from typing import Optional

from attr import define, field
from loguru import logger

from packg.dtime import format_seconds_adaptive
from packg.log import configure_logger
from packg.tqdmext import tqdm_max_ncols
from packg.typext import NoneType


@define
class WorkerMultiProcessor:
    """
    Simple multiprocessor with N workers and
        - either no output at all
        - or all output is append to an infinitely large queue and read after everything is done

    The worker should implement setup() which is called at the beginning of the spawned process,
    and run() which is called for each task.

    Usage:
        1. create instance
        2. loop put(arg1, arg2, ...) some tasks
        3. run()
        4. only if with_output is True: loop get() until output queue is empty
        5. close()

    Args:
        workers: number of workers (0 = foreground)
        target_class: function to call in the worker
        target_class_args: arguments for the target class
        ignore_errors: do not raise errors in the worker
        verbose: show progress bar
        with_output: return output from worker
        total: total number of tasks for progress bar or None if unknown
        desc: description for progress bar
        smoothing: smoothing factor for progress bar (0 = average speed, 1 = instantaneous speed)

    """

    workers: int
    target_class: type
    target_class_args: tuple | None = None
    ignore_errors: bool = False
    verbose: bool = True
    with_output: bool = True
    total: Optional[int] = None
    desc: str = "Multiprocessing"
    smoothing: float = 0.0

    worker_list: list[Worker] = field(factory=list, init=False)
    process_list: list[Process] = field(factory=list, init=False)
    q_in: Queue = field(init=False)
    q_out: Optional[Queue] = field(init=False)
    pbar: tqdm_max_ncols = field(init=False)
    start_time: float = field(init=False)
    processed: int = field(init=False)
    input_counter: int = field(init=False)

    def __attrs_post_init__(self):
        assert self.workers >= 0, f"workers must be >= 0 but is {self.workers}"
        if self.target_class_args is None:
            self.target_class_args = ()
        maxsize = self.workers * 2
        self.q_in = Queue(maxsize=maxsize)
        self.q_out = Queue(maxsize=0) if self.with_output else None
        for i in range(self.workers):
            wi = self.target_class(i, self.target_class_args)
            target_fn = wi.multi_fn_with_output if self.with_output else wi.multi_fn_no_output
            w = Process(target=target_fn, args=(self.q_in, self.q_out, self.ignore_errors))
            w.start()
            self.worker_list.append(wi)
            self.process_list.append(w)
        self.pbar = tqdm_max_ncols(
            total=self.total,
            desc=self.desc,
            disable=not self.verbose or self.workers == 0,
            smoothing=self.smoothing,
        )
        self.start_time = default_timer()
        self.processed = 0
        self.input_counter = 0

    def put(self, *args):
        self.q_in.put(args)
        self.input_counter += 1
        # with W workers, the first W will be immediately accepted. 2*W will be queued.
        # so only start counting after 3*W for an accurate pbar.
        if self.input_counter > self.workers * 3:
            self.update_pbar(1)

    def update_pbar(self, amount=1):
        self.processed += amount
        sec_per_iter = (default_timer() - self.start_time) / max(self.processed, 1)
        desc_post = f" {sec_per_iter:10.2f} s/it"
        if sec_per_iter < 1:
            iter_per_sec = 1 / sec_per_iter
            desc_post = f" {iter_per_sec:10.2f} it/s"
        rem_time_fmt = ""
        if self.total is not None:
            rem_time = sec_per_iter * (self.total - self.processed)
            rem_time_fmt = format_seconds_adaptive(rem_time, "{:5.2f}{}")
        self.pbar.set_description(f"{self.desc}{desc_post} {rem_time_fmt}", refresh=False)
        self.pbar.update(amount)

    def run(self):
        # add poison pills for workers
        for _ in range(self.workers):
            self.q_in.put(None)

        if self.workers == 0:
            # no multiprocessing, queue is full, run one worker in foreground
            self.q_in.put(None)
            wi = self.target_class(0, self.target_class_args)
            target_fn = wi.multi_fn_with_output if self.with_output else wi.multi_fn_no_output
            target_fn(self.q_in, self.q_out, self.ignore_errors, foreground=True, desc=self.desc)
        else:
            # wait for input queue to be empty
            wait_counter = 0
            delay = 0.2
            remaining = self.q_in.qsize()
            while not self.q_in.empty():
                if wait_counter % 5 == 0:
                    now_remaining = self.q_in.qsize()
                    if now_remaining < remaining:
                        delta = remaining - now_remaining
                        remaining = now_remaining
                        self.update_pbar(delta)

                wait_counter += 1
                time.sleep(delay)
            self.pbar.update(remaining)

    def get(self):
        return self.q_out.get()

    def close(self):
        # note: output queue has to be empty before workers can be joined otherwise this will hang
        logger.debug(f"Joining workers")
        for w in self.worker_list:
            w.close()
        for p in self.process_list:
            p.join()
            self.update_pbar(1)
            p.terminate()
        self.pbar.close()

        self.q_in.close()
        if self.q_out is not None:
            self.q_out.close()


class Worker:
    def __init__(self, i: int, target_class_args: tuple):
        self.i = i
        self.target_class_args = target_class_args

    def setup(self, *args):
        raise NotImplementedError

    def run(self, *args):
        raise NotImplementedError

    def multi_fn_with_output(
        self,
        in_q: Queue,
        out_q: Queue,
        ignore_errors: bool,
        foreground: bool = False,
        desc: str = "Processing",
    ):
        self.setup(*self.target_class_args)
        pbar = tqdm_max_ncols(total=in_q.qsize() - 1, disable=not foreground, desc=desc)
        while True:
            args = in_q.get()
            if args is None:
                break
            try:
                out = self.run(*args)
            except Exception as e:
                if ignore_errors:
                    logger.error(f"Error in multi_function:\n\n{''.join(format_exception(e))}")
                    out_q.put(None)
                    continue
                raise e
            out_q.put(out)
            pbar.update(1)
        pbar.close()

    def multi_fn_no_output(
        self,
        in_q: Queue,
        out_q: NoneType,
        ignore_errors: bool,
        foreground: bool = False,
        desc: str = "Processing",
    ):
        assert out_q is None, "out_q must be None"
        self.setup(*self.target_class_args)
        pbar = tqdm_max_ncols(total=in_q.qsize() - 1, disable=not foreground, desc=desc)
        while True:
            args = in_q.get()
            if args is None:
                break
            try:
                self.run(*args)
            except Exception as e:
                if ignore_errors:
                    logger.error(f"Error in multi_function: {e}")
                else:
                    raise e
            pbar.update(1)
        pbar.close()

    def close(self):
        pass


class ExampleWorkerWithOutput(Worker):
    def setup(self):
        pass

    def run(self, t_x: int):
        time.sleep(random.random() * 0.2 + 0.2)
        return t_x * 2


class ExampleWorkerWithoutOutput(Worker):
    def setup(self):
        pass

    def run(self, t_x: int):
        time.sleep(random.random() * 0.2 + 0.2)
        # print(t_x * 3)


def main():
    configure_logger(level="INFO")
    for workers in [3, 0]:
        print(f"Workers: {workers} ******************")
        ix = list(range(10))
        proc = WorkerMultiProcessor(
            workers,
            ExampleWorkerWithOutput,
            None,
            total=len(ix),
            desc=f"With output queue, {workers} workers",
        )
        for in_x in ix:
            proc.put(in_x)
        proc.run()
        outputs = []
        for _ in range(len(ix)):
            outputs.append(proc.get())
        proc.close()
        print(outputs)

        ix = list(range(10))
        proc = WorkerMultiProcessor(
            workers,
            ExampleWorkerWithoutOutput,
            with_output=False,
            total=len(ix),
            desc=f"No output queue, {workers} workers",
        )
        for in_x in ix:
            proc.put(in_x)
        proc.run()
        proc.close()


if __name__ == "__main__":
    main()
