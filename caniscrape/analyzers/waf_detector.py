import subprocess
import re
from ..utils.waf_result_parser import parse_wafw00f_output

def detect_waf(url: str) -> dict[str, any]:
    """
    Runs wafw00f to detect a WAF and parses its output.
    Returns the WAF names if found, otherwise None.
    """
    print('Running WAF detection...')
    try:
        command = ['wafw00f', url]

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