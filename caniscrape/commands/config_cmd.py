from ..config import find_config_in_parents

def set_config_command(key, value):
    """
    Update configuration settings.
    """
    config = find_config_in_parents()

    if not config or not config.is_linked():
        print('[red]❌ Not linked to a project. Run [cyan]caniscrape init[/cyan] first.[/red]')
        return
    
    if key == 'auto-upload':
        config.set('auto_upload', value == 'on')
        config.save()
        
        if value == 'on':
            print('[green]✅ Auto-upload enabled[/green]')
            print('[dim]Scans will now automatically sync to your cloud project.[/dim]')
        else:
            print('[blue]ℹ️  Auto-upload disabled[/blue]')
            print('[dim]Run [cyan]caniscrape push[/cyan] to upload scans manually.[/dim]')

def show_config_command():
    """
    Show current configuration.
    """
    config = find_config_in_parents()
    
    if not config or not config.is_linked():
        print('[red]❌ Not linked to a project[/red]')
        print('[dim]Run [cyan]caniscrape init[/cyan] or [cyan]caniscrape link[/cyan] to get started.[/dim]')
        return
    
    print('\n[bold cyan]📋 Project Configuration[/bold cyan]\n')
    print(f'Project: [bold]{config.get("project_name", "Unknown")}[/bold]')
    print(f'Project ID: [dim]{config.get_project_id()}[/dim]')
    print(f'Auto-upload: {"[green]✅ Enabled[/green]" if config.get("auto_upload") else "[yellow]❌ Disabled[/yellow]"}')
    print()