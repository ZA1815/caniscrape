from abc import ABC, abstractmethod

class CaptchaSolverError(Exception):
    """
    Custom exception for CAPTCHA solving errors.
    """
    pass

class CaptchaSolver(ABC):
    """
    Abstract base class that defines the interface for a CAPTCHA solver.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError('API Key cannot be empty.')
        self.api_key = api_key
    
    @abstractmethod
    def solve_recaptcha_v2(self, sitekey: str, page_url: str) -> str:
        pass

    @abstractmethod
    def solve_hcaptcha(self, sitekey: str, page_url: str) -> str:
        pass

class CapSolverService(CaptchaSolver):
    """
    CaptchaSolver implementation for CapSolver.com
    Requires the capsolver-python package.
    """
    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            import capsolver
            capsolver.api_key = api_key
            self.solver = capsolver
        except ImportError:
            raise ImportError('CapSolver requires the "capsolver" package. Please install it using "pip install capsolver"')
        except Exception as e:
            raise CaptchaSolverError(f"Failed to initialize CapSolver client: {e}")
    
    def solve_recaptcha_v2(self, sitekey: str, page_url: str) -> str:
        print('INFO: Solving reCAPTCHA v2 with CapSolver...')
        try:
            solution = self.solver.solve({
                'type': 'ReCaptchaV2TaskProxyLess',
                'websiteURL': page_url,
                'websiteKey': sitekey
            })
            token = solution.get('gRecaptchaResponse')
            if not token:
                raise CaptchaSolverError(f'CapSolver failed to return a token. Response: {solution}')
            return token
        except Exception as e:
            raise CaptchaSolverError(f'CapSolver API error: {str(e)}')
    
    def solve_hcaptcha(self, sitekey: str, page_url: str) -> str:
        print('INFO: Solving hCaptcha with CapSolver...')
        try:
            solution = self.solver.solve({
                'type': 'HCaptchaTaskProxyLess',
                'websiteURL': page_url,
                'websiteKey': sitekey
            })
            token = solution.get('gRecaptchaResponse')
            if not token:
                raise CaptchaSolverError(f'CapSolver failed to return a token. Response: {solution}')
            return token
        except Exception as e:
            raise CaptchaSolverError(f'CapSolver API error: {str(e)}')

class TwoCaptchaService(CaptchaSolver):
    """
    CaptchaSolver implementation for 2Captcha.com
    Requires the 'twocaptcha-python' package.
    """
    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from twocaptcha import TwoCaptcha
            self.solver = TwoCaptcha(api_key)
        except ImportError:
            raise ImportError('2Captcha requires the "2captcha-python" package. Please install it using "pip install 2captcha-python"')
        except Exception as e:
            raise CaptchaSolverError(f"Failed to initialize CapSolver client: {e}")
    
    def solve_recaptcha_v2(self, sitekey: str, page_url: str) -> str:
        print('INFO: Solving reCAPTCHA v2 with 2Captcha...')
        try:
            result = self.solver.recaptcha(sitekey=sitekey, url=page_url)
            token = result.get('code')
            if not token:
                raise CaptchaSolverError(f'2Captcha failed to return a token. Response: {result}')
            return token
        except Exception as e:
            raise CaptchaSolverError(f'2Captcha API error: {str(e)}')
    
    def solve_hcaptcha(self, sitekey: str, page_url: str) -> str:
        print('INFO: Solving hCAPTCHA using 2Captcha...')
        try:
            result = self.solver.hcaptcha(sitekey=sitekey, url=page_url)
            token = result.get('code')
            if not token:
                raise CaptchaSolverError(f'2Captcha failed to return a token. Response: {result}')
            return token
        except Exception as e:
            raise CaptchaSolverError(f'2Captcha API error: {str(e)}')

def get_solver(service_name: str, api_key: str) -> CaptchaSolver:
    """
    Factory function to get an instance of the specified CAPTCHA solver.
    """
    solvers = {
        'capsolver': CapSolverService,
        '2captcha': TwoCaptchaService
    }

    solver_class = solvers.get(service_name.lower())

    if not solver_class:
        raise ValueError(f'Unknown CAPTCHA service "{service_name}". Supported services are: {list(solvers.keys())}')
    
    return solver_class(api_key)