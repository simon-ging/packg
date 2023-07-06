import time


def connect_to_debug_server(host=None, port=None):
    if host is None:
        return
    import pydevd_pycharm  # noqa  # pylint: disable=import-error
    if port is None:
        port = 12345
    while True:
        try:
            pydevd_pycharm.settrace(
                host, port=port, stdoutToServer=True, stderrToServer=True, suspend=False)
            break
        except ConnectionRefusedError:
            print(f"Debug server connection refused: {host}:{port}. Retrying...")
            time.sleep(2)
