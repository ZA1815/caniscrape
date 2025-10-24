from __future__ import annotations
import random
from playwright.sync_api import sync_playwright, Playwright, Page, TimeoutError as PlaywrightTimeoutError

FUNCTIONS_TO_CHECK = [
    "HTMLCanvasElement.prototype.toDataURL",
    "HTMLCanvasElement.prototype.getImageData",
    "HTMLCanvasElement.prototype.getContext",
    "navigator.plugins.length",
    "navigator.mimeTypes.length",
    "navigator.webdriver",
    "window.fetch",
    "XMLHttpRequest.prototype.open",
    "Date.now",
    "performance.now",
    "console.log"
]

FUNCTION_SUSPICION_MAP = {
    "HTMLCanvasElement.prototype.toDataURL": "Strong indicator of Canvas Fingerprinting.",
    "HTMLCanvasElement.prototype.getImageData": "Strong indicator of Canvas Fingerprinting.",
    "HTMLCanvasElement.prototype.getContext": "Strong indicator of Canvas Fingerprinting.",
    "navigator.plugins.length": "Indicator of Headless Browser Evasion (Plugin spoofing).",
    "navigator.mimeTypes.length": "Indicator of Headless Browser Evasion (MimeType spoofing).",
    "navigator.webdriver": "Indicator of Headless Browser Evasion.",
    "window.fetch": "Indicator of Network Traffic Monitoring.",
    "XMLHttpRequest.prototype.open": "Indicator of Network Traffic Monitoring.",
    "Date.now": "Indicator of Timing/Behavioral Analysis.",
    "performance.now": "Indicator of Timing/Behavioral Analysis.",
    "console.log": "Indicator of anti-debugging techniques."
}

def _get_function_signatures(page: Page, functions: list[str]) -> dict[str, str]:
    """
    Excecutes JS in the page to get the string representations of functions.
    """
    js_script = """
    (func_paths) => {
        const signatures = {};
        for (const path of func_paths) {
            try {
                let obj = window;
                const parts = path.split('.')
                for (let i = 0; i < parts.length; i++) {
                    if (obj === undefined || obj === null) {
                        break;
                    }
                    obj = obj[parts[i]]
                }
                signatures[path] = String(obj);
            }
            catch (err) {
                signatures[path] = 'Error: ' + e.message;
            }
        }
        return signatures;
    }
    """
    return page.evaluate(js_script, functions)

def analyze_function_integrity(url: str, proxies: tuple[str, ...] = ()) -> dict[str, any]:
    """
    Compares critical browser functions on a target page to
    functions on a "clean" page.
    """
    results = {
        'status': 'error',
        'message': 'Analysis did not complete.',
        'modified_functions': {}
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            clean_context = browser.new_context()
            clean_page = clean_context.new_page()
            clean_page.goto('about:blank')
            clean_signatures = _get_function_signatures(clean_page, FUNCTIONS_TO_CHECK)
            clean_context.close()

            target_context_options = {}
            if proxies:
                proxy = random.choice(proxies)
                target_context_options['proxy'] = {'server': proxy}
            
            target_context = browser.new_context(**target_context_options)
            target_page = target_context.new_page()
            target_page.goto(url, wait_until='load', timeout=30000)
            
            target_signatures = _get_function_signatures(target_page, FUNCTIONS_TO_CHECK)
            target_context.close()

            browser.close()

            modified = {}
            for func_path, clean_sig in clean_signatures.items():
                target_sig = target_signatures.get(func_path)
                if clean_sig != target_sig:
                    modified[func_path] = FUNCTION_SUSPICION_MAP.get(func_path, 'Unknown modification.')

            results['status'] = 'success'
            results['message'] = 'Analysis complete.'
            results['modified_functions'] = modified
            return results
    
    except PlaywrightTimeoutError:
        results['message'] = 'Page load time out.'
        return results
    except Exception as e:
        results['message'] = str(e)
        return results

