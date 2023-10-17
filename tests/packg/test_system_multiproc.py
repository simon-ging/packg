from __future__ import annotations

import random
import time
from typing import Any

from packg.system.multiproc_producer_consumer import (
    MultiProcessorProducerConsumer,
    Consumer,
    Producer,
)


def _run_test(n_inputs, producer_class_or_fn: callable, consumer_class_or_fn: callable):
    ix = list(range(n_inputs))
    # for n_producers, n_consumers in [(3, 1), (3, 2), (0, 0)]:
    for n_producers, n_consumers in [
        (3, 1),
        (3, 2),
        (30, 20),
        (0, 0),
    ]:
        proc = MultiProcessorProducerConsumer(
            n_producers,
            n_consumers,
            producer_class_or_fn,
            consumer_class_or_fn,
            total=len(ix),
            pbar_desc=f"n_producers={n_producers} n_consumers={n_consumers} n_inputs={n_inputs}",
            verbose=False,
        )
        for in_x in ix:
            proc.put(in_x)
        outputs = proc.run()
        print(f"Got {len(outputs)} outputs: {outputs}")


_N = 5
_T_MULT = 0.002
_T_MIN = 0.002


def fn_produce_two_values(t_x: int):
    time.sleep(random.random() * _T_MULT + _T_MIN)
    return t_x * 2, True


class TwoValuesProducer(Producer):
    def setup(self) -> None:
        pass

    def __call__(self, *args, **kwargs):
        return fn_produce_two_values(*args, **kwargs)


def fn_consume_two_values(t_y: int, some_bool: bool):
    time.sleep(random.random() * _T_MULT + _T_MIN)
    return t_y, some_bool


class ConsumeTwoValues(Consumer):
    def setup(self) -> None:
        self.collected_outputs = []

    def __call__(self, t_y: int, some_bool: bool):
        self.collected_outputs.append(fn_consume_two_values(t_y, some_bool))

    def complete(self) -> Any:
        return self.collected_outputs


def test_multiproc_producer_consumer_two_values():
    for producer_class_or_fn in [TwoValuesProducer, fn_produce_two_values]:
        for consumer_class_or_fn in [ConsumeTwoValues, fn_consume_two_values]:
            _run_test(_N, producer_class_or_fn, consumer_class_or_fn)


def fn_produce_one_value(t_x: int):
    time.sleep(random.random() * _T_MULT + _T_MIN)
    return t_x * 2


class OneValueProducer(Producer):
    def setup(self) -> None:
        pass

    def __call__(self, t_x: int):
        return fn_produce_one_value(t_x)


def fn_consume_one_value(t_y: int):
    time.sleep(random.random() * _T_MULT + _T_MIN)
    return t_y


class ConsumeOneValue(Consumer):
    def setup(self) -> None:
        self.collected_outputs = []

    def __call__(self, t_y: int):
        self.collected_outputs.append(fn_consume_one_value(t_y))

    def complete(self) -> Any:
        return self.collected_outputs


def test_multiproc_producer_consumer_one_value():
    for producer_class_or_fn in [OneValueProducer, fn_produce_one_value]:
        for consumer_class_or_fn in [ConsumeOneValue, fn_consume_one_value]:
            _run_test(_N, producer_class_or_fn, consumer_class_or_fn)


def main():
    test_multiproc_producer_consumer_two_values()
    test_multiproc_producer_consumer_one_value()


if __name__ == "__main__":
    main()
