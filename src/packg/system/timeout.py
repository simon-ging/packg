import multiprocessing
import time
from timeit import default_timer

from packg.misc import format_exception


def worker(result_queue, fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        result_queue.put(result)
    except Exception as e:
        result_queue.put(e)


def run_function_with_timeout(timeout_seconds, function, *args, **kwargs):
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=worker, args=(result_queue, function, *args), kwargs=kwargs
    )
    process.start()
    process.join(timeout_seconds)
    if process.is_alive():
        process.terminate()
        process.join()
        raise TimeoutError("Conversion timed out.")
    else:
        # Get the result from the queue.
        if not result_queue.empty():
            result = result_queue.get()
            if isinstance(result, Exception):
                raise result
            return result


def _hanging_function():
    t1 = default_timer()
    while True:
        time.sleep(1)
        print(f"Hanging forever (a long time). Time elapsed: {default_timer() - t1:.2f}sec")


def _non_hanging_function(*args, **kwargs):
    time.sleep(2)
    print(args, kwargs)
    return 4


def main():
    print(f"Hanger")
    try:
        print(run_function_with_timeout(1, _hanging_function))
    except TimeoutError as e:
        print(format_exception(e))

    print("Non-hanger directly")
    _non_hanging_function(2, 3, a=4, b=5)

    print("Non-hanger with timeout")
    print(run_function_with_timeout(10, _non_hanging_function, 2, 3, a=4, b=5))


if __name__ == "__main__":
    main()
