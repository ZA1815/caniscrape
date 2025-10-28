from rich import print
from pathlib import Path
import json
import hashlib
from datetime import datetime, timezone

from .config import Config, find_config_in_parents
from .api_client import ApiClient, ApiError

def save_to_cache(url: str, scan_results: dict, cli_version: str) -> None:
    """
    Save scan results to local cache for later push.
    """
    cache_dir = Path('.caniscrape/cache')
    cache_dir.mkdir(parents=True, exist_ok=True)

    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    filename = f'{timestamp}_{url_hash}.json'

    cache_file = cache_dir / filename

    cache_data = {
        'url': url,
        'scan_data': scan_results,
        'cli_version': cli_version,
        'cached_at': datetime.now(timezone.utc).isoformat()
    }

    with open(cache_file, 'w') as f:
        json.dump(cache_data, f, indent=2)

def try_upload_scan(url: str, scan_results: dict, cli_version: str = '1.0.0') -> bool:
    """
    Try to upload scan to cloud project.
    Returns True if successful, False otherwise.
    """
    config = find_config_in_parents()

    if not config or not config.is_linked():
        return False
    
    project_id = config.get_project_id()
    api_token = config.get_api_token()
    api_endpoint = config.get_api_endpoint()
    project_name = config.get('project_name', 'your project')

    try:
        client = ApiClient(api_endpoint=api_endpoint, api_token=api_token)

        scan = client.upload_scan(
            project_id=project_id,
            url=url,
            scan_data=scan_results,
            cli_version=cli_version
        )

        print(f'\n[green]✨ Results synced to \'{project_name}\'[/green]')
        print(f'[dim]   View: https://caniscrape.org/projects/{project_id}[/dim]')
        return True
    except ApiError as e:
        error_msg = str(e)
        
        if 'Authentication failed' in error_msg or 'expired' in error_msg.lower():
            print(f'\n[yellow]⚠️  Upload failed: API token expired[/yellow]')
            print(f'[dim]   Run [cyan]caniscrape init[/cyan] to re-authenticate[/dim]')
        elif 'Rate limit' in error_msg:
            print(f'\n[yellow]⚠️  Upload failed: Rate limit exceeded[/yellow]')
            print(f'[dim]   Results cached. Try again later.[/dim]')
        else:
            print(f'\n[yellow]⚠️  Upload failed: {error_msg}[/yellow]')
        
        return False
    except Exception:
        return False

def check_for_diff(url: str) -> dict | None:
    """
    Check if there's a previous scan to compare against.
    """
    config = find_config_in_parents()

    if not config or not config.is_linked():
        return None
    
    try:
        project_id = config.get_project_id()
        api_token = config.get_api_token()
        api_endpoint = config.get_api_endpoint()
        
        client = ApiClient(api_endpoint=api_endpoint, api_token=api_token)

        previous_scan = client.get_latest_scan(project_id=project_id, url=url)
        return previous_scan
    except:
        return None