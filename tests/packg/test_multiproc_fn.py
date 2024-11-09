from packg.multiproc.multiproc_fn import FnMultiProcessor


def dummy_function(x):
    return x * 2


def test_fn_multiprocessor():
    proc = FnMultiProcessor(workers=2, target_fn=dummy_function, total=5)
    for i in range(5):
        proc.put(i)
    proc.run()
    results = [proc.get() for _ in range(5)]
    proc.close()
    assert set(results) == set([0, 2, 4, 6, 8]), results  # use set since order is not guaranteed
