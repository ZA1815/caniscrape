import click
from rich import print
from rich.prompt import Confirm

from ..config import Config, find_config_in_parents
from ..api_client import ApiClient, ApiError

def telemetry_push_command():
    """
    Contribute your scan data to public telemetry (opt-in).
    """
    print('[bold cyan]📊 Contribute to Public Telemetry[/bold cyan]\n')

    config = find_config_in_parents()

    if not config or not config.is_linked():
        print('[red]❌ Not linked to a cloud project.[/red]')
        print('[yellow]Run [cyan]caniscrape init[/cyan] first to set up your account.[/yellow]')
        return
    
    telemetry_enabled = config.get('telemetry_enabled', False)

    if not telemetry_enabled:
        print('[bold]What is public telemetry?[/bold]')
        print('Public telemetry aggregates scan data from all users to create a')
        print('searchable database of website protections (like Shodan for anti-bot defenses).\n')
        
        print('[bold green]Benefits:[/bold green]')
        print('  • See how site protections change over time')
        print('  • Search for any URL to see its defense history')
        print('  • Compare different sites\' protection strategies')
        print('  • Free access while we build the database\n')
        
        print('[bold yellow]What we collect:[/bold yellow]')
        print('  • URLs you scan')
        print('  • Scan results (WAF, CAPTCHA, rate limits, etc.)')
        print('  • Timestamps of scans\n')
        
        print('[bold red]What we DON\'T collect:[/bold red]')
        print('  • Your IP address or personal info')
        print('  • Any authentication tokens or credentials\n')
        
        print('[dim]You can disable this anytime with: caniscrape telemetry disable[/dim]\n')

        if not Confirm.ask('Enable public telemetry contributions?'):
            print('[blue]Telemetry contributions disabled.[/blue]')
            return
        
        config.set('telemetry_enabled', True)
        config.save()
        print('[green]✅ Telemetry contributions enabled![/green]\n')
    
    project_id = config.get_project_id()
    api_token = config.get_api_token()
    api_endpoint = config.get_api_endpoint()

    print('[dim]Checking for scans to contribute...[/dim]')

    try:
        client = ApiClient(api_endpoint=api_endpoint, api_token=api_token)
        
        scans = client.list_scans(project_id=project_id, per_page=100)
        scans_list = scans.get('scans', [])

        if not scans_list:
            print('[yellow]⚠️  No scans found in your project.[/yellow]')
            print('[dim]Run some scans first, then contribute them to telemetry.[/dim]')
            return
        
        contributed = 0
        for scan in scans_list:
            scan_id = scan.get('id')
            url = scan.get('url', 'unknown')

            already_contributed = scan.get('telemetry_contributed', False)

            if already_contributed:
                continue

            try:
                client._request('POST', f'/api/telemetry/contribute/{scan_id}')
                print(f'[green]✅ Contributed: {url}[/green]')
                contributed += 1
            except ApiError as e:
                print(f'[yellow]⚠️  Failed to contribute {url}: {str(e)}[/yellow]')
        
        if contributed > 0:
            print(f'\n[green]✨ Successfully contributed {contributed} scan(s) to public telemetry![/green]')
            print('[dim]Thank you for helping build the database![/dim]')
        else:
            print('\n[dim]All scans have already been contributed to telemetry.[/dim]')
    except ApiError as e:
        print(f'[red]❌ Failed to contribute to telemetry: {str(e)}[/red]')
    except Exception as e:
        print(f'[red]❌ Unexpected error: {str(e)}[/red]')