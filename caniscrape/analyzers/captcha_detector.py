from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

CAPTCHA_FINGERPRINTS = {
    "reCAPTCHA": [
        "google.com/recaptcha", "recaptcha/api.js", "g-recaptcha"
    ],
    "hCaptcha": [
        "hcaptcha.com", "hcaptcha-box", "h-captcha"
    ],
    "Cloudflare Turnstile": [
        "challenges.cloudflare.com/turnstile", "cf-turnstile"
    ]
}

def _scan_for_captcha_fingerprints(page: Page, network_requests: list[str]) -> str | None:
    """
    Scan the page's HTML and network requests for known CAPTCHA signatures.
    Returns the name of the detected CAPTCHA provider or None.
    """
    html_content = page.content().lower()
    all_evidence = network_requests + [html_content]

    for provider, patterns in CAPTCHA_FINGERPRINTS.items():
        for pattern in patterns:
            for evidence in all_evidence:
                if pattern in evidence:
                    return provider
    return None

def detect_captcha(url: str) -> dict[str, any]:
    """
    Analyzes a URL to detect the presence and type of CAPTCHA.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            captured_requests = []
            def capture_request(request):
                captured_requests.append(request.url.lower())
            page.on('request', capture_request)

            try:
                page.goto(url, wait_until='load', timeout=30000)
                page.wait_for_load_state('networkidle', timeout=5000)
            except:
                pass

            page.wait_for_timeout(2000)

            captcha_on_load = _scan_for_captcha_fingerprints(page, captured_requests)

            if captcha_on_load:
                browser.close()
                return {'status': 'success', 'captcha_detected': True, 'captcha_type': captcha_on_load, 'trigger_condition': 'on page load'}
            
            captured_requests.clear()

            for _ in range(10):
                page.reload(wait_until='domcontentloaded')
            
            captcha_after_burst = _scan_for_captcha_fingerprints(page, captured_requests)
            browser.close()

            if captcha_after_burst:
                return {'status': 'success', 'captcha_detected': True, 'captcha_type': captcha_after_burst, 'trigger_condition': 'after burst of requests'}
            
            return {'status': 'success', 'captcha_detected': False}
    except PlaywrightTimeoutError:
        return {'status': 'error', 'message': 'Page load timed out.'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}