import click
from rich import print
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from pathlib import Path

from ..config import Config
from ..api_client import ApiClient, ApiError

def init_command():
    print('[bold blue]🚀 caniscrape Cloud Setup[/bold blue]\n')

    config = Config()
    if config.is_linked():
        project_name = config.get('project_name', 'Unknown')
        print(f'[yellow]⚠️  This directory is already linked to project: [bold]{project_name}[/bold][/yellow]')

        if not Confirm.ask('Do you want to unlink and create a new project?'):
            print('[dim]Cancelled.[/dim]')
            return
        
        config.clear()
        print('[green]✅ Unlinked from previous project.[/green]\n')
    
    print('[bold]Step 1: Authentication[/bold]')
    print('You need to authenticate with caniscrape Cloud.')
    print('Visit [link]https://caniscrape.org/dashboard/settings [/link]to get your API token.\n')

    api_token = Prompt.ask('Enter your API token', password=True)

    if not api_token or not api_token.strip():
        print('[red]❌ Token cannot be empty.[/red]')
        return
    
    api_endpoint = config.get_api_endpoint()

    print('[dim]Authenticating...[/dim]')
    client = ApiClient(api_endpoint=api_endpoint, api_token=api_token.strip())

    try:
        projects = client.list_projects()
        print(f'[green]✅ Authenticated successfully![/green]')

        if len(projects) > 1:
            print(f'\n[dim]You have {len(projects)} existing project(s):[/dim]')
            for p in projects[:3]:
                print(f'  - {p["name"]}')
            if len(projects) > 3:
                print(f'  ... and {len(projects) - 3} more')
        else:
            print(f'\n[dim]You don\'t have any existing projects. Create one now![/dim]')
    except ApiError as e:
        print(f'[red]❌ Authentication failed: {str(e)}[/red]')
        return
    
    print('\n[bold]Step 2: Create Project[/bold]')
    print('Give this project a name (e.g., "E-commerce Scraper", "News Aggregator")\n')

    project_name = Prompt.ask('Project name?')

    if not project_name or not project_name.strip():
        print('[red]❌ Project name cannot be empty.[/red]')
        return
    
    project_description = Prompt.ask('Project description (optional, press Enter to skip)?', default='')

    print('\n[dim]Creating project...[/dim]')
    try:
        project = client.create_project(name=project_name.strip(), description=project_description.strip() if project else None)
        print(f'[green]✅ Project created: {project["name"]}[/green]')
    except ApiError as e:
        print(f'[red]❌ Failed to create project: {str(e)}[/red]')
        return
    
    print('\n[bold]Step 3: Auto-Upload Settings[/bold]')
    print('Automatically push scan results to your cloud project?\n')
    print('[dim]  • Yes: Every scan uploads instantly (recommended)[/dim]')
    print('[dim]  • No: Results stay local until you run "caniscrape push"[/dim]\n')

    auto_upload = Confirm.ask('Enable auto-upload?', default=True)

    config.set('auto_upload', auto_upload)
    config.save()

    if auto_upload:
        print('[green]✅ Auto-upload enabled[/green]')
    else:
        print('[blue]ℹ️  Auto-upload disabled. Use [cyan]caniscrape push[/cyan] to upload manually.[/blue]')
    
    config.set('project_id', project['id'])
    config.set('project_name', project['name'])
    config.set('api_token', api_token.strip())
    config.set('api_endpoint', api_endpoint)
    config.set('auto_upload', auto_upload)

    try:
        config.save()
        print(f'[green]✅ Configuration saved to .caniscrape/config[/green]')
    except Exception as e:
        print(f'[red]❌ Failed to save config: {str(e)}[/red]')
        return
    
    print('\n' + '='*60)
    print(Panel.fit(
        f'[bold green]✨ Success! Your project is ready.[/bold green]\n\n'
        f'[bold]Project:[/bold] {project["name"]}\n'
        f'[bold]Project ID:[/bold] {project["id"]}\n\n'
        f'[bold]Next steps:[/bold]\n'
        f'1. Run [cyan]caniscrape <url>[/cyan] to analyze a website\n'
        f'2. Your scan results will automatically upload to the cloud\n'
        f'3. View your scan history at [link]https://caniscrape.org/projects[/link]\n\n'
        f'[dim]💡 Tip: Create projects on the web dashboard and use[/dim]\n'
        f'[dim]   [cyan]caniscrape link[/cyan] to connect them to different directories[/dim]',
        title='🎉 Setup Complete',
        border_style='green'
    ))