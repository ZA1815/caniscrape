import requests
from typing import Any
from requests.exceptions import RequestException, HTTPError, Timeout

class ApiClient:
    def __init__(self, api_endpoint: str, api_token: str | None = None):
        self.api_endpoint = api_endpoint.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()

        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'caniscrape-cli/1.0.0'
        })

        if api_token:
            self.session.headers.update({
                'Authorization': f'Bearer {api_token}'
            })
        
    def _request(
        self,
        method: str,
        endpoint: str,
        json: dict | None = None,
        params: dict | None = None,
        timeout: int = 30
    ) -> dict[str, Any]:
        url = f'{self.api_endpoint}{endpoint}'

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                timeout=timeout
            )

            response.raise_for_status()

            if response.status_code == 204:
                return {}
            
            return response.json()
        
        except Timeout:
            raise ApiError(f'Request timed out after {timeout} seconds. Check your internet connection.')
        except HTTPError as e:
            try:
                error_detail = e.response.json().get('detail', 'Unknown error')
            except:
                error_detail = e.response.text or 'Unknown error'
            
            if e.response.status_code == 401:
                raise ApiError('Authentication failed. Your token may have expired. Run `caniscrape init` to re-authenticate.')
            elif e.response.status_code == 403:
                raise ApiError(f'Permission denied: {error_detail}')
            elif e.response.status_code == 404:
                raise ApiError(f'Not found: {error_detail}')
            elif e.response.status_code == 429:
                raise ApiError('Rate limit exceeded. Please try again later.')
            elif 500 <= e.response.status_code < 600:
                raise ApiError(f'Server error: {error_detail}. Please try again later.')
            else:
                raise ApiError(f'API error: {error_detail}')
            
        except RequestException as e:
            raise ApiError(f'Network error: {str(e)}. Check your internet connection.')
        
    def create_project(self, name: str, description: str | None = None) -> dict:
        return self._request(
            'POST',
            '/api/projects',
            json={
                'name': name,
                'description': description
            }
        )
    
    def list_projects(self) -> list[dict]:
        return self._request('GET', '/api/projects')
    
    def get_project(self, project_id: str) -> dict:
        return self._request('GET', f'/api/projects/{project_id}')
    
    def upload_scan(self, project_id: str, url: str, scan_data: dict, cli_version: str | None = None) -> dict:
        return self._request('POST', f'/api/projects/{project_id}/scans', json={'url': url, 'scan_data': scan_data, 'cli_version': cli_version})
    
    def list_scans(self, project_id: str, page: int = 1, per_page: int = 50, url_filter: str | None = None) -> dict:
        params = {'page': page, 'per_page': per_page}
        if url_filter:
            params['url'] = url_filter

        return self._request('GET', f'/api/projects/{project_id}/scans', params=params)
    
    def get_latest_scan(self, project_id: str, url: str) -> dict | None:
        try:
            return self._request('GET', f'/api/projects/{project_id}/scans/latest', params={'url': url})
        except ApiError as e:
            if 'not found' in str(e).lower():
                return None
            raise

    def contribute_scan_to_telemetry(self, scan_id: str) -> dict:
        """
        Contribute a scan to public telemetry.
        """
        return self._request('POST', f'/api/telemetry/contribute/{scan_id}')
    
    def get_telemetry_stats(self) -> dict:
        """
        Get public telemetry statistics.
        """
        return self._request('GET', '/api/telemetry/stats')

class ApiError(Exception):
    pass