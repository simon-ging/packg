import random
import time
from typing import Any

import pytest

from packg.multiproc.multiproc_producer_consumer import (
    MultiProcessorProducerConsumer,
    Consumer,
    Producer,
)


def _run_test(n_inputs, producer_class_or_fn: callable, consumer_class_or_fn: callable):
    ix = list(range(n_inputs))
    for n_producers, n_consumers in [
        (3, 1),
        (5, 6),
        (0, 0),
    ]:
        proc = MultiProcessorProducerConsumer(
            n_producers,
            n_consumers,
            producer_class_or_fn,
            consumer_class_or_fn,
            total=len(ix),
            pbar_desc=f"{n_producers=} {n_consumers=} {n_inputs=}",
            verbose=False,
        )
        for in_x in ix:
            proc.put(in_x)
        outputs = proc.run()
        print(f"Got {len(outputs)} outputs: {outputs}")


_N = 4
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


_test_names, _test_inputs = [], []
for _p_name, _producer_class_or_fn in [("cls", OneValueProducer), ("fn", fn_produce_one_value)]:
    for _c_name, _consumer_class_or_fn in [("cls", ConsumeOneValue), ("fn", fn_consume_one_value)]:
        _test_names.append(f"onevalue-producer-{_p_name}_consumer-{_c_name}")
        _test_inputs.append((_producer_class_or_fn, _consumer_class_or_fn))

for _p_name, _producer_class_or_fn in [("cls", TwoValuesProducer), ("fn", fn_produce_two_values)]:
    for _c_name, _consumer_class_or_fn in [
        ("cls", ConsumeTwoValues),
        ("fn", fn_consume_two_values),
    ]:
        _test_names.append(f"twovalue-producer-{_p_name}_consumer-{_c_name}")
        _test_inputs.append((_producer_class_or_fn, _consumer_class_or_fn))


@pytest.mark.parametrize("producer_cls_or_fn, consumer_cls_or_fn", _test_inputs, ids=_test_names)
def test_multiproc_producer(producer_cls_or_fn, consumer_cls_or_fn):
    _run_test(_N, producer_cls_or_fn, consumer_cls_or_fn)
