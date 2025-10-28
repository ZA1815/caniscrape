import click
from rich import print
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel
from datetime import datetime

from ..config import Config
from ..api_client import ApiClient, ApiError

def link_command():
    """
    Link this directory to an existing caniscrape Cloud project.
    """
    print('[bold blue]🔗 Link to Existing Project[/bold blue]\n')
    
    config = Config()
    if config.is_linked():
        project_name = config.get('project_name', 'Unknown')
        print(f'[yellow]⚠️  Already linked to: [bold]{project_name}[/bold][/yellow]')
        
        if not Confirm.ask('Unlink and choose a different project?'):
            print('[dim]Cancelled.[/dim]')
            return
        
        config.clear()
        print('[green]✅ Unlinked.[/green]\n')
    
    print('[bold]Step 1: Authentication[/bold]')
    print('Visit [link]https://caniscrape.org/settings[/link] to get your API token.\n')
    
    api_token = Prompt.ask('Enter your API token', password=True)
    
    if not api_token or not api_token.strip():
        print('[red]❌ Token cannot be empty.[/red]')
        return
    
    api_endpoint = config.get_api_endpoint()
    client = ApiClient(api_endpoint=api_endpoint, api_token=api_token.strip())
    
    print('\n[dim]Fetching your projects...[/dim]')
    try:
        projects = client.list_projects()
    except ApiError as e:
        print(f'[red]❌ Authentication failed: {str(e)}[/red]')
        return
    
    if not projects:
        print('[yellow]⚠️  You have no projects yet.[/yellow]')
        print('[dim]Create one at [link]https://caniscrape.org/projects[/link] or run [cyan]caniscrape init[/cyan][/dim]')
        return
    
    print(f'\n[bold]Step 2: Select Project[/bold]')
    print(f'[dim]Found {len(projects)} project(s)[/dim]\n')
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Project Name", style="bold")
    table.add_column("Scans", justify="right")
    table.add_column("Last Scan", style="dim")
    
    for idx, proj in enumerate(projects, 1):
        last_scan = proj.get('last_scan_at', 'Never')
        if last_scan and last_scan != 'Never':
            try:
                dt = datetime.fromisoformat(last_scan.replace('Z', '+00:00'))
                last_scan = dt.strftime('%Y-%m-%d')
            except:
                pass
        
        table.add_row(
            str(idx),
            proj['name'],
            str(proj.get('scan_count', 0)),
            last_scan
        )
    
    print(table)
    print()
    
    while True:
        choice = Prompt.ask('Select a project', default='1')
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(projects):
                selected_project = projects[idx]
                break
            else:
                print('[red]Invalid choice. Try again.[/red]')
        except ValueError:
            print('[red]Please enter a number.[/red]')
    
    print(f'\n[bold]Step 3: Auto-Upload Settings[/bold]')
    print('Automatically push scan results to this project?\n')
    
    auto_upload = Confirm.ask('Enable auto-upload?', default=True)
    
    config.set('project_id', selected_project['id'])
    config.set('project_name', selected_project['name'])
    config.set('api_token', api_token.strip())
    config.set('api_endpoint', api_endpoint)
    config.set('auto_upload', auto_upload)
    
    try:
        config.save()
    except Exception as e:
        print(f'[red]❌ Failed to save config: {str(e)}[/red]')
        return
    
    print('\n' + '='*60)
    print(Panel.fit(
        f'[bold green]✨ Successfully linked![/bold green]\n\n'
        f'[bold]Project:[/bold] {selected_project["name"]}\n'
        f'[bold]Scans:[/bold] {selected_project.get("scan_count", 0)}\n'
        f'[bold]Auto-upload:[/bold] {"✅ Enabled" if auto_upload else "❌ Disabled"}\n\n'
        f'[bold]Next steps:[/bold]\n'
        f'• Run [cyan]caniscrape <url>[/cyan] to add a scan\n'
        f'• View history at [link]https://caniscrape.org/projects/{selected_project["id"]}[/link]',
        title='🎉 Project Linked',
        border_style='green'
    ))