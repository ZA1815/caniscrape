import click
from ..telemetry import get_telemetry_manager

@click.command(name='telemetry')
@click.argument('action', required=False, type=click.Choice(['on', 'off', 'delete', 'status'], case_sensitive=False))
def telemetry_command(action):
    """
    Manage telemetry and privacy settings.

    Examples:
        caniscrape telemetry           Show current status
        caniscrape telemetry on        Enable telemetry
        caniscrape telemetry off       Disable telemetry
        caniscrape telemetry delete    Delete all collected data
    """
    manager = get_telemetry_manager()

    if action is None or action == 'status':
        manager.show_status()
    elif action == 'on':
        manager.opt_in()
    elif action == 'off':
        manager.opt_out()
    elif action == 'delete':
        manager.request_data_deletion