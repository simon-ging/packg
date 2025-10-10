from __future__ import annotations

import time
from typing import Optional

import requests


def send_robust_post_request(
    url: str,
    data: Optional[Any] = None,
    json: Optional[Any] = None,
    n_trials: int = 3,
    n_retry_sleep: int = 5,
    print_fn: callable = print,
    **kwargs,
) -> requests.Response:
    """
    Sends a robust POST request with retries and error logging.

    Parameters:
        url: The URL for the POST request.
        data: dict, list of tuples, bytes, or file-like object to send in the body of the Request
        json: A JSON serializable Python object to send in the body of the Request
        n_trials: Number of retry attempts.
        n_retry_sleep: Seconds to wait between retries.
        print_fn: Function to use for logging.
        **kwargs: Optional arguments that the request takes, e.g., the headers dict

    Returns:
        requests.Response: The response object if successful.

    Raises:
        Exception: If all retries fail.
    """
    for attempt in range(1, n_trials + 1):
        try:
            response = requests.post(url, data=data, json=json, **kwargs)
            if response.status_code == 200:
                return response
            else:
                print_fn(
                    f"Attempt {attempt}/{n_trials}: Query failed with status code "
                    f"{response.status_code}. Response: {response.text}"
                )
        except requests.exceptions.RequestException as e:
            print_fn(f"Attempt {attempt}/{n_trials}: Request failed with exception: {e}")

        if attempt < n_trials:
            print_fn(f"Retrying in {n_retry_sleep} seconds...")
            time.sleep(n_retry_sleep)

    raise Exception(f"Failed to send POST request to {url} after {n_trials} attempts.")
