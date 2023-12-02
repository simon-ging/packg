from __future__ import annotations

import time
import types
from collections import defaultdict
from multiprocessing import Process, Queue
from statistics import mean
from timeit import default_timer
from typing import Optional, Any
from attr import define, field
from loguru import logger

from packg.dtime import format_seconds_adaptive
from packg.stats import AvgMetric
from packg.tqdmext import tqdm_max_ncols


@define
class MultiProcessorProducerConsumer:
    """
    Run P producers on some input, pass their output to N consumers, and aggregate their output.

    Usage:
        1) specify producer and consumer. Either as a simple function

        - define producer function that takes input_args and produces output_args
        - subclass Consumer and define setup, __call__, complete. __call__ takes output_args
        - create instance. (optionally set n_producers = n_consumers = 0 for foreground execution)
        - loop put(input_args) some tasks
        - outputs = run()  # list of length n_consumers with the return from complete()

    todo
        Improve error handling with error queues if needed
        Improve passing dict of flags / config, instead of one bool for each config item
        Create another example in this file
    """

    n_producers: int
    n_consumers: int
    producer_class_or_fn: callable
    consumer_class_or_fn: callable

    producer_args: tuple = field(factory=tuple)
    producer_kwargs: dict = field(factory=dict)
    consumer_args: tuple = field(factory=tuple)
    consumer_kwargs: dict = field(factory=dict)
    ignore_errors: bool = False
    verbose: bool = False
    total: Optional[int] = None
    pbar_desc: str = "Multiprocessing"

    producer_class: Any = field(init=False)
    consumer_class: Any = field(init=False)
    producer_worker_list: list[Process] = field(factory=list, init=False)
    producer_object_list: list[Any] = field(factory=list, init=False)
    consumer_worker_list: list[Process] = field(factory=list, init=False)
    consumer_object_list: list[Any] = field(factory=list, init=False)
    q_in: Optional[Queue] = field(init=False, default=None)
    q_producer_out: Optional[Queue] = field(init=False, default=None)
    q_consumer_out: Optional[Queue] = field(init=False, default=None)
    q_timer: Optional[Queue] = field(init=False, default=None)
    pbar: tqdm_max_ncols = field(init=False)
    start_time: int = field(init=False)
    processed: int = field(init=False)
    input_counter: int = field(init=False)
    is_foreground: bool = field(init=False, default=True)
    wait_times_put: AvgMetric = field(init=False, default=AvgMetric())

    def __attrs_post_init__(self):
        assert self.n_producers >= 0, f"n_producers={self.n_producers} but must be >= 0"
        assert self.n_consumers >= 0, f"n_consumers={self.n_consumers} but must be >= 0"

        self._setup_worker_classes()
        is_foreground_producer = self.n_producers == 0
        is_foreground_consumer = self.n_consumers == 0
        if is_foreground_consumer != is_foreground_producer:
            raise ValueError(
                f"n_consumers={self.n_producers} and n_consumers={self.n_consumers} but must be "
                f"either both 0 (running in foreground) or both > 0 (running in background)."
            )

        if is_foreground_producer and is_foreground_consumer:
            self.producer_object_list = [self.producer_class(0)]
            self.producer_object_list[0].setup(*self.producer_args, **self.producer_kwargs)
            self.consumer_object_list = [self.consumer_class(0)]
            self.consumer_object_list[0].setup(*self.consumer_args, **self.consumer_kwargs)
        else:
            self.q_in = Queue(maxsize=self.n_producers * 2)
            self.q_producer_out = Queue(maxsize=self.n_producers * 2)
            self.q_consumer_out = Queue(maxsize=0)
            self.q_timer = Queue(maxsize=0)
            self.is_foreground = False

        for n in range(self.n_producers):
            producer_object = self.producer_class(n)
            producer_object.setup(*self.producer_args, **self.producer_kwargs)
            self.producer_object_list.append(producer_object)
            w = Process(
                target=producer_object.multi_fn_producer,
                args=(self.q_in, self.q_producer_out, self.q_timer, self.ignore_errors),
            )
            w.start()
            self.producer_worker_list.append(w)

        for n in range(self.n_consumers):
            consumer_object = self.consumer_class(n)
            consumer_object.setup(*self.consumer_args, **self.consumer_kwargs)
            self.consumer_object_list.append(consumer_object)
            w = Process(
                target=consumer_object.multi_fn_consumer,
                args=(self.q_producer_out, self.q_consumer_out, self.q_timer, self.ignore_errors),
            )
            w.start()
            self.consumer_worker_list.append(w)

        self.pbar = tqdm_max_ncols(total=self.total, desc=self.pbar_desc)
        self.start_time = default_timer()
        self.processed = 0
        self.input_counter = 0

    def _setup_worker_classes(self):
        if isinstance(self.consumer_class_or_fn, types.FunctionType):
            # detected consumer function
            assert len(self.consumer_args) == 0, (
                f"{len(self.consumer_args)} consumer_args given but must be empty "
                f"when using a consumer function."
            )
            assert len(self.consumer_kwargs) == 0, (
                f"{len(self.consumer_kwargs)} consumer_kwargs given but must be empty "
                f"when using a consumer function."
            )
            self.consumer_class = SimpleConsumer
            self.consumer_args = (self.consumer_class_or_fn,)
        else:
            # detected consumer class
            self.consumer_class = self.consumer_class_or_fn

        if isinstance(self.producer_class_or_fn, types.FunctionType):
            # detected producer function
            assert len(self.producer_args) == 0, (
                f"{len(self.producer_args)} producer_args given but must be empty "
                f"when using a producer function."
            )
            assert len(self.producer_kwargs) == 0, (
                f"{len(self.producer_kwargs)} producer_kwargs given but must be empty "
                f"when using a producer function."
            )
            self.producer_class = SimpleProducer
            self.producer_args = (self.producer_class_or_fn,)
        else:
            # detected producer class
            self.producer_class = self.producer_class_or_fn

    def _debug_print(self, msg):
        if self.verbose:
            self.pbar.write(msg)

    def put(self, *args):
        if self.is_foreground:
            output = self.producer_object_list[0](*args)
            output = _ensure_fn_output_is_tuple(output)
            self.consumer_object_list[0](*output)
            self.update_pbar(1)
            return

        start_time = default_timer()
        self.q_in.put(args)
        self.wait_times_put.update(default_timer() - start_time)

        self.input_counter += 1
        # with W workers, the first W will be immediately accepted. 2*W will be queued.
        # so only start counting after 3*W for an accurate pbar.
        if self.input_counter > self.n_producers * 3:
            self.update_pbar(1)

    def update_pbar(self, amount=1):
        # if there are more producers than queue items, safeguard pbar against overflow
        if self.total is not None:
            amount = min(amount, self.total - self.processed)
        if amount <= 0:
            return

        self.processed += amount
        sec_per_iter = (default_timer() - self.start_time) / max(self.processed, 1)
        desc_post = f" {sec_per_iter:10.2f} s/it"
        if sec_per_iter < 1:
            iter_per_sec = 1 / sec_per_iter
            desc_post = f" {iter_per_sec:10.2f} it/s"
        if self.total is None:
            rem_time_fmt = f""
        else:
            rem_time = sec_per_iter * (self.total - self.processed)
            rem_time_fmt = format_seconds_adaptive(rem_time, "{:5.2f}{}")
        self.pbar.set_description(f"{self.pbar_desc}{desc_post} {rem_time_fmt} left", refresh=False)
        self.pbar.update(amount)

    def run(self):
        if self.is_foreground:
            # already done
            self.pbar.close()
            return [self.consumer_object_list[0].complete()]

        self._debug_print(f"Add {self.n_producers} term signals for producers to input queue")
        for _ in range(self.n_producers):
            start_time = default_timer()
            self.q_in.put(None)
            self.wait_times_put.update(default_timer() - start_time)

        remaining = self.q_in.qsize()
        self._debug_print(f"Wait for producers to read input queue ({remaining} rem.)")
        wait_counter = 0
        delay = 0.2
        while not self.q_in.empty():
            if wait_counter % 5 == 0:
                now_remaining = self.q_in.qsize()
                if now_remaining < remaining:
                    delta = remaining - now_remaining
                    remaining = now_remaining
                    self.update_pbar(delta)
            wait_counter += 1
            time.sleep(delay)
        self.update_pbar(remaining)

        remaining = self.q_producer_out.qsize()
        self._debug_print(f"Wait for consumers to read producer output queue ({remaining} rem.)")
        while not self.q_producer_out.empty():
            time.sleep(delay)

        self._debug_print(f"Add {self.n_consumers} term signals for consumers to input queue")
        for _ in range(self.n_consumers):
            self.q_producer_out.put(None)

        self._debug_print(f"Collect data from consumer output queue")
        outputs = []
        for _ in range(self.n_consumers):
            out = self.q_consumer_out.get()
            outputs.append(out)

        # note: all queues have to be empty before workers can be joined otherwise this will hang
        self._debug_print(f"Joining workers")
        for w in self.producer_worker_list:
            w.join()
            self.update_pbar(1)
            w.terminate()
        for w in self.consumer_worker_list:
            w.join()
            w.terminate()

        m_wait_put = self.wait_times_put.avg

        times = defaultdict(list)
        for _ in range(self.n_consumers + self.n_producers * 2):
            time_k, _time_i, time_v = self.q_timer.get()
            times[time_k].append(time_v)

        time_str = ", ".join([f"{k}: {mean(vs):.1f}s" for k, vs in times.items()])

        self.pbar.close()
        self.q_in.close()
        self.q_producer_out.close()
        self.q_consumer_out.close()
        self.q_timer.close()
        total_speed = (default_timer() - self.start_time) / max(self.processed, 1)
        self.pbar.write(
            f"Average wait: main put: {m_wait_put:.2f}s, {time_str}. "
            f"Final speed: {total_speed:.3f}s/it"
        )

        return outputs


def _ensure_fn_output_is_tuple(output):
    if not isinstance(output, tuple):
        output = (output,)
    return output


class Producer:
    def __init__(self, i: int):
        self.i = i
        self.wait_times_get = AvgMetric()
        self.wait_times_put = AvgMetric()

    def setup(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def __call__(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def multi_fn_producer(
        self,
        q_in: Queue,
        q_producer_out: Queue,
        q_timer: Queue,
        ignore_errors: bool,
    ):
        while True:
            start_time = default_timer()
            args = q_in.get()
            self.wait_times_get.update(default_timer() - start_time)
            if args is None:
                break
            try:
                # producer_fn: callable,
                out = self(*args)
            except Exception as e:
                if ignore_errors:
                    logger.error(f"Error in multi_function: {e}")
                    q_producer_out.put(e)
                    continue
                raise e
            out = _ensure_fn_output_is_tuple(out)
            start_time = default_timer()
            q_producer_out.put(out)
            delta = default_timer() - start_time
            self.wait_times_put.update(delta)

        q_timer.put((f"producer-get", self.i, self.wait_times_get.avg))
        q_timer.put((f"producer-put", self.i, self.wait_times_put.avg))


class SimpleProducer(Producer):
    def setup(self, producer_fn: callable):
        self.producer_fn = producer_fn

    def __call__(self, *args, **kwargs) -> None:
        return self.producer_fn(*args, **kwargs)


class Consumer:
    def __init__(self, i: int):
        self.i = i
        self.wait_times_get = AvgMetric()

    def setup(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def __call__(self, *args, **kwargs) -> None:
        raise NotImplementedError

    def complete(self) -> Any:
        raise NotImplementedError

    def multi_fn_consumer(
        self, q_producer_out: Queue, q_consumer_out: Queue, q_timer: Queue, ignore_errors: bool
    ):
        while True:
            start_time = default_timer()
            args = q_producer_out.get()
            self.wait_times_get.update(default_timer() - start_time)
            if args is None:
                break
            try:
                self(*args)
            except Exception as e:
                if ignore_errors:
                    logger.error(f"Error in multi_function: {e}")
                else:
                    raise e
        final_output = self.complete()
        # print(f"Putting output to consumer out q: {type(final_output)=} {len(final_output)=}")
        # q_consumer_out never blocks so no reason to time it.
        q_consumer_out.put(final_output)
        q_timer.put((f"consumer-get", self.i, self.wait_times_get.avg))


class SimpleConsumer(Consumer):
    def setup(self, consumer_fn: callable):
        self.collected_outputs = []
        self.consumer_fn = consumer_fn

    def __call__(self, *args, **kwargs):
        self.collected_outputs.append(self.consumer_fn(*args, **kwargs))

    def complete(self):
        return self.collected_outputs


def fn_produce_one_value(t_x: int):
    time.sleep(t_x / 10)
    return t_x * 2


def fn_consume_one_value(t_y: int):
    time.sleep(t_y / 20)
    return t_y


def main():
    ix = list(range(10))
    proc = MultiProcessorProducerConsumer(
        30, 2, fn_produce_one_value, fn_consume_one_value, total=10, pbar_desc="Test", verbose=True
    )
    for in_x in ix:
        proc.put(in_x)
    outputs = proc.run()
    print(outputs)
    print("Done")


if __name__ == "__main__":
    main()
