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
    def solve_recaptcha_v2(self, sitekey: str, page_url: str, proxy: str | None = None) -> str:
        pass

    @abstractmethod
    def solve_hcaptcha(self, sitekey: str, page_url: str, proxy: str | None = None) -> str:
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
    
    def solve_recaptcha_v2(self, sitekey: str, page_url: str, proxy: str | None = None) -> str:
        print('INFO: Solving reCAPTCHA v2 with CapSolver...')
        try:
            if proxy:
                proxy_parts = proxy.replace('http://', '').replace('https://', '')
                
                if '@' in proxy_parts:
                    auth_part, server_part = proxy_parts.split('@')
                    if ':' in auth_part:
                        proxy_user, proxy_pass = auth_part.split(':', 1)
                    else:
                        proxy_user = proxy_pass = None
                    
                    if ':' in server_part:
                        proxy_address, proxy_port = server_part.rsplit(':', 1)
                    else:
                        proxy_address = server_part
                        proxy_port = '80'
                else:
                    proxy_user = proxy_pass = None
                    if ':' in proxy_parts:
                        proxy_address, proxy_port = proxy_parts.rsplit(':', 1)
                    else:
                        proxy_address = proxy_parts
                        proxy_port = '80'
                
                task_data = {
                    'type': 'ReCaptchaV2Task',
                    'websiteURL': page_url,
                    'websiteKey': sitekey,
                    'proxyType': 'http',
                    'proxyAddress': proxy_address,
                    'proxyPort': int(proxy_port)
                }
                
                if proxy_user and proxy_pass:
                    task_data['proxyLogin'] = proxy_user
                    task_data['proxyPassword'] = proxy_pass
                
                print(f'INFO: Using proxy {proxy_address}:{proxy_port} for CAPTCHA solving')
            else:
                task_data = {
                    'type': 'ReCaptchaV2TaskProxyLess',
                    'websiteURL': page_url,
                    'websiteKey': sitekey
                }
            
            solution = self.solver.solve(task_data)
            token = solution.get('gRecaptchaResponse')
            if not token:
                raise CaptchaSolverError(f'CapSolver failed to return a token. Response: {solution}')
            return token
        except Exception as e:
            raise CaptchaSolverError(f'CapSolver API error: {str(e)}')
    
    def solve_hcaptcha(self, sitekey: str, page_url: str, proxy: str | None = None) -> str:
        print('INFO: Solving hCaptcha with CapSolver...')
        try:
            if proxy:
                proxy_parts = proxy.replace('http://', '').replace('https://', '')
                
                if '@' in proxy_parts:
                    auth_part, server_part = proxy_parts.split('@')
                    if ':' in auth_part:
                        proxy_user, proxy_pass = auth_part.split(':', 1)
                    else:
                        proxy_user = proxy_pass = None
                    
                    if ':' in server_part:
                        proxy_address, proxy_port = server_part.rsplit(':', 1)
                    else:
                        proxy_address = server_part
                        proxy_port = '80'
                else:
                    proxy_user = proxy_pass = None
                    if ':' in proxy_parts:
                        proxy_address, proxy_port = proxy_parts.rsplit(':', 1)
                    else:
                        proxy_address = proxy_parts
                        proxy_port = '80'
                
                task_data = {
                    'type': 'HCaptchaTask',
                    'websiteURL': page_url,
                    'websiteKey': sitekey,
                    'proxyType': 'http',
                    'proxyAddress': proxy_address,
                    'proxyPort': int(proxy_port)
                }
                
                if proxy_user and proxy_pass:
                    task_data['proxyLogin'] = proxy_user
                    task_data['proxyPassword'] = proxy_pass
                
                print(f'INFO: Using proxy {proxy_address}:{proxy_port} for CAPTCHA solving')
            else:
                task_data = {
                    'type': 'HCaptchaTaskProxyLess',
                    'websiteURL': page_url,
                    'websiteKey': sitekey
                }
            
            solution = self.solver.solve(task_data)
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
            raise CaptchaSolverError(f"Failed to initialize 2Captcha client: {e}")
    
    def solve_recaptcha_v2(self, sitekey: str, page_url: str, proxy: str | None = None) -> str:
        print('INFO: Solving reCAPTCHA v2 with 2Captcha...')
        try:
            kwargs = {'sitekey': sitekey, 'url': page_url}
            
            if proxy:
                proxy_clean = proxy.replace('http://', '').replace('https://', '')
                kwargs['proxy'] = {
                    'type': 'HTTP',
                    'uri': proxy_clean
                }
                print(f'INFO: Using proxy for CAPTCHA solving')
            
            result = self.solver.recaptcha(**kwargs)
            token = result.get('code')
            if not token:
                raise CaptchaSolverError(f'2Captcha failed to return a token. Response: {result}')
            return token
        except Exception as e:
            raise CaptchaSolverError(f'2Captcha API error: {str(e)}')
    
    def solve_hcaptcha(self, sitekey: str, page_url: str, proxy: str | None = None) -> str:
        print('INFO: Solving hCAPTCHA using 2Captcha...')
        try:
            kwargs = {'sitekey': sitekey, 'url': page_url}
            
            if proxy:
                proxy_clean = proxy.replace('http://', '').replace('https://', '')
                kwargs['proxy'] = {
                    'type': 'HTTP',
                    'uri': proxy_clean
                }
                print(f'INFO: Using proxy for CAPTCHA solving')
            
            result = self.solver.hcaptcha(**kwargs)
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