from __future__ import annotations

import subprocess
from ..utils.waf_result_parser import parse_wafw00f_output
import random

def detect_waf(url: str, find_all: bool = False, proxies: tuple[str, ...] = ()) -> dict[str, any]:
    """
    Runs wafw00f to detect a WAF and parses its output.
    Returns the WAF name if found, otherwise None.
    -find-all tag can be used to ask wafw00f to find all the WAFs the website is using.
    """
    try:
        command = ['wafw00f', url]

        if find_all:
            command.append('-a')

        if proxies:
            proxy = random.choice(proxies)
            command.extend(['-p', proxy])

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            check=False
        )

        wafs_found = parse_wafw00f_output(result.stdout, result.stderr)

        if wafs_found:
            return {'status': 'success', 'wafs': wafs_found}
        
        if (result.returncode != 0):
            error_message = result.stderr.strip()

            if not error_message:
                error_message = f'wafw00f failed with exit code {result.returncode} but no error message.'
            return {'status': 'error', 'message': error_message}
        
        return {'status': 'success', 'wafs': []}
        
    except FileNotFoundError:
        return {'status': 'error', 'message': 'wafw00f missing'}
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'message': 'timeout'}