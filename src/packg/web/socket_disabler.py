import socket
import sys

_module = sys.modules[__name__]


def disable_socket(verbose: bool = True):
    """disable socket.socket to disable the Internet. useful in testing.
    from https://gist.github.com/hangtwenty/9200597e3be274c79896
    """
    setattr(_module, "_socket_disabled", True)
    original_socket = socket.socket

    def guarded(*args, **kwargs):
        do_raise = True
        if getattr(_module, "_socket_disabled", False) and do_raise:
            raise RuntimeError(
                "A test tried to use socket.socket without explicitly un-blocking it."
            )
        socket.socket = original_socket
        return socket.socket(*args, **kwargs)

    socket.socket = guarded
    if verbose:
        print("[!] socket.socket is now blocked. The network should be inaccessible.")


def enable_socket(verbose: bool = True):
    """re-enable socket.socket to enable the Internet."""
    setattr(_module, "_socket_disabled", False)
    if verbose:
        print("[!] socket.socket is UN-blocked, and the network can be accessed.")
