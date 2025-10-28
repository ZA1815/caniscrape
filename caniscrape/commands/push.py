import click
from rich import print
from pathlib import Path
import json

from ..config import Config, find_config_in_parents
from ..api_client import ApiClient, ApiError

def push_command():
    """
    Push local scan results to your cloud project.
    """
    print('[bold blue]📤 Pushing scan results to cloud...[/bold blue]\n')

    config = find_config_in_parents()

    if not config or not config.is_linked():
        print('[red]❌ Not linked to a cloud project.[/red]')
        print('[yellow]Run [cyan]caniscrape init[/cyan] to link this directory to a project.[/yellow]')
        return
    
    project_id = config.get_project_id()
    project_name = config.get('project_name', 'Unknown')
    api_token = config.get_api_token()
    api_endpoint = config.get_api_endpoint()

    cache_dir = Path('.caniscrape/cache')

    if not cache_dir.exists():
        print('[yellow]⚠️  No local scan results found.[/yellow]')
        print('[dim]Run some scans first, then push them to the cloud.[/dim]')
        return
    
    scan_files = list(cache_dir.glob('*.json'))

    if not scan_files:
        print('[yellow]⚠️  No scan results to push.[/yellow]')
        return
    
    print(f'[dim]Found {len(scan_files)} scan result(s) to push...[/dim]\n')

    client = ApiClient(api_endpoint=api_endpoint, api_token=api_token)

    success_count = 0
    failed_count = 0

    for file in scan_files:
        try:
            with open(file, 'r') as f:
                scan_data = json.load(f)
            
            url = scan_data.get('url', 'Unknown')
            cli_version = scan_data.get('cli_version', '1.0.0')

            client.upload_scan(
                project_id=project_id,
                url=url,
                scan_data=scan_data,
                cli_version=cli_version
            )

            print(f'[green]✅ Pushed: {url}[/green]')
            file.unlink()
            success_count += 1
        except ApiError as e:
            print(f'[red]❌ Failed to push {file.name}: {str(e)}[/red]')
            failed_count += 1
        except Exception as e:
            print(f'[yellow]⚠️  Error reading {file.name}: {str(e)}[/yellow]')
            failed_count += 1
    
    print()
    if success_count > 0:
        print(f'[green]🚀 Successfully pushed {success_count} scan(s) to \'{project_name}\'[/green]')
    if failed_count > 0:
        print(f'[yellow]⚠️  Failed to push {failed_count} scan(s)[/yellow]')