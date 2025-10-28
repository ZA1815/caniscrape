"""
Telemetry Manager - Privacy-first usage analytics

Two types of telemetry:
1. Usage Telemetry: Anonymous CLI usage stats (errors, commands used)
2. Scan Telemetry: Public scan database (like Shodan) - opt-in separately
"""

import os
import json
import platform
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import requests
from rich import print
from rich.prompt import Confirm

class TelemetryManager:
    """
    Manages both usage telemetry and public scan contributions.
    """
    def __init__(self):
        self.config_dir = Path.home() / '.caniscrape'
        self.config_file = self.config_dir / 'telemetry.json'
        self.api_base = 'https://caniscrape-web-production.up.railway.app'

    def _load_config(self) -> dict[str, Any]:
        """
        Load telemetry configuration.
        """
        if not self.config_file.exists():
            return {}
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_config(self, config: dict[str, Any]) -> None:
        """
        Save telemetry configuration.
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def is_usage_telemetry_enabled(self) -> bool:
        """
        Check if user has opted into usage telemetry.
        """
        config = self._load_config()
        return config.get('usage_telemetry_enabled', False)
    
    def is_scan_telemetry_enabled(self) -> bool:
        """
        Check if user has opted into public scan contributions.
        """
        config = self._load_config()
        return config.get('scan_telemetry_enabled', False)
    
    def get_or_create_device_id(self) -> str:
        """
        Get or create anonymous device ID.
        """
        config = self._load_config()

        if 'device_id' not in config:
            config['device_id'] = str(uuid.uuid4())
            self._save_config(config)
        
        return config['device_id']
    
    def prompt_usage_telemetry(self) -> bool:
        """
        Prompt for usage telemetry opt-in.
        """
        config = self._load_config()

        if 'usage_telemetry_enabled' in config:
            return config['usage_telemetry_enabled']
        
        print("\n[bold cyan]📊 Help us improve caniscrape![/bold cyan]\n")
        print("We'd like to collect [bold]anonymous usage data[/bold] to improve the tool.")
        print("\n[dim]What we collect:[/dim]")
        print("  • CLI version and Python version")
        print("  • Operating system type")
        print("  • Commands used (scan/init)")
        print("  • Success/failure rates")
        print("  • Error types (no URLs or personal data)")
        
        print("\n[dim]What we DON'T collect:[/dim]")
        print("  • Your name, email, or IP address")
        print("  • URLs you scan")
        print("  • Any personally identifiable information")
        
        print("\n[dim]You can opt-out anytime with:[/dim] [bold]caniscrape telemetry usage off[/bold]\n")
        
        response = Confirm.ask("Share anonymous usage data?", default=False)
        
        config['usage_telemetry_enabled'] = response
        config['usage_telemetry_decided_at'] = datetime.now(timezone.utc).isoformat()
        self._save_config(config)
        
        if response:
            print("\n[green]✅ Usage telemetry enabled.[/green]")
        else:
            print("\n[blue]Usage telemetry disabled.[/blue]")
        
        return response
    
    def prompt_scan_telemetry(self) -> bool:
        """Prompt for public scan telemetry opt-in."""
        config = self._load_config()

        if 'scan_telemetry_enabled' in config:
            return config['scan_telemetry_enabled']
        
        print("\n[bold cyan]🌍 Contribute to Public Scan Database[/bold cyan]\n")
        print("Help build a [bold]searchable database of website protections[/bold].")
        
        print("\n[dim]What we collect:[/dim]")
        print("  • URLs you scan")
        print("  • Scan results (WAF, CAPTCHA, difficulty scores)")
        print("  • Protection details")
        
        print("\n[dim]What we DON'T collect:[/dim]")
        print("  • Your name, email, or IP address")
        print("  • Any authentication tokens")
        
        print("\n[bold green]Benefits:[/bold green]")
        print("  • Search any URL to see its protection history")
        print("  • Compare sites' defense strategies")
        print("  • Track changes over time")
        print("  • The more everyone contributes the better it is!")
        
        print("\n[dim]You can opt-out anytime with:[/dim] [bold]caniscrape telemetry scans off[/bold]")
        print("[dim]This is separate from usage telemetry.[/dim]\n")
        
        response = Confirm.ask("Contribute your scans to the public database?", default=False)
        
        config['scan_telemetry_enabled'] = response
        config['scan_telemetry_decided_at'] = datetime.now(timezone.utc).isoformat()
        self._save_config(config)
        
        if response:
            print("\n[green]✅ Scan contributions enabled. Thank you![/green]")
        else:
            print("\n[blue]Scan contributions disabled.[/blue]")
        
        return response
    
    def get_system_info(self, cli_version: str) -> dict[str, str]:
        """
        Get anonymous system information.
        """
        return {
            'cli_version': cli_version,
            'python_version': f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}',
            'os': platform.system(),
            'os_version': platform.release(),
            'architecture': platform.machine()
        }
    
    def track_usage_event(self, event_type: str, cli_version: str, metadata: dict[str, Any] | None = None, silent: bool = False) -> None:
        """
        Track a usage telemetry event (if user opted in).
        """
        if not self.is_usage_telemetry_enabled():
            return
        
        try:
            device_id = self.get_or_create_device_id()
            system_info = self.get_system_info(cli_version)

            payload = {
                'device_id': device_id,
                'event_type': event_type,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_info': system_info,
                'metadata': metadata or {}
            }

            response = requests.post(
                f'{self.api_base}/telemetry/receive',
                json=payload,
                timeout=2
            )

            if not silent and response.status_code != 200:
                pass
        
        except Exception:
            pass
    
    def contribute_scan(self, url: str, scan_data: dict, cli_version: str, silent: bool = False) -> bool:
        """
        Contribute a scan to the public database (if user opted in).
        """
        if not self.is_scan_telemetry_enabled():
            return False
        
        try:
            score_card = scan_data.get('score_card', {})
            
            payload = {
                'url': url,
                'difficulty_score': score_card.get('score', 0),
                'difficulty_label': score_card.get('label', 'Unknown'),
                'scan_data': scan_data,
                'cli_version': cli_version
            }

            response = requests.post(
                f'{self.api_base}/telemetry/contribute-scan',
                json=payload,
                timeout=5
            )

            if response.status_code == 201:
                if not silent:
                    data = response.json()
                    if data.get('is_new'):
                        print('[dim]🌍 Scan contributed to public database (new entry)[/dim]')
                    else:
                        print('[dim]🌍 Scan contributed to public database (updated)[/dim]')
                return True
            else:
                return False
        
        except Exception:
            return False
    
    def enable_usage_telemetry(self):
        """
        Enable usage telemetry.
        """
        config = self._load_config()
        config['usage_telemetry_enabled'] = True
        config['usage_telemetry_decided_at'] = datetime.now(timezone.utc).isoformat()
        self._save_config(config)
        print("[green]✅ Usage telemetry enabled.[/green]")
    
    def disable_usage_telemetry(self):
        """
        Disable usage telemetry.
        """
        config = self._load_config()
        config['usage_telemetry_enabled'] = False
        config['usage_telemetry_decided_at'] = datetime.now(timezone.utc).isoformat()
        self._save_config(config)
        print("[blue]Usage telemetry disabled.[/blue]")
    
    def enable_scan_telemetry(self):
        """
        Enable public scan contributions.
        """
        config = self._load_config()
        config['scan_telemetry_enabled'] = True
        config['scan_telemetry_decided_at'] = datetime.now(timezone.utc).isoformat()
        self._save_config(config)
        print("[green]✅ Scan contributions enabled.[/green]")
    
    def disable_scan_telemetry(self):
        """
        Disable public scan contributions.
        """
        config = self._load_config()
        config['scan_telemetry_enabled'] = False
        config['scan_telemetry_decided_at'] = datetime.now(timezone.utc).isoformat()
        self._save_config(config)
        print("[blue]Scan contributions disabled.[/blue]")
    
    def request_data_deletion(self) -> bool:
        """
        Request deletion of all usage telemetry data.
        """
        if not self.config_file.exists():
            print("[yellow]No telemetry data found locally.[/yellow]")
            return False
        
        config = self._load_config()
        device_id = config.get('device_id')

        if not device_id:
            print("[yellow]No device ID found. No data to delete.[/yellow]")
            return False
        
        print(f"\n[bold yellow]⚠️  Delete all usage telemetry data?[/bold yellow]")
        print(f"[dim]Device ID: {device_id}[/dim]")
        print(f"[dim]Note: This only deletes usage stats, not public scan contributions.[/dim]\n")

        confirm = Confirm.ask('Are you sure? This cannot be undone.')

        if not confirm:
            print("[blue]Deletion cancelled.[/blue]")
            return False
        
        try:
            response = requests.delete(
                f'{self.api_base}/telemetry/{device_id}',
                timeout=10
            )

            if response.status_code == 200:
                self.config_file.unlink()
                print("\n[green]✅ All usage telemetry data deleted.[/green]")
                return True
            else:
                error = response.json().get('detail', 'Unknown error')
                print(f"\n[red]❌ Failed to delete data: {error}[/red]")
                return False
            
        except requests.exceptions.RequestException as e:
            print(f"\n[red]❌ Network error: {str(e)}[/red]")
            return False
    
    def show_status(self) -> None:
        """
        Show current telemetry status.
        """
        config = self._load_config()

        print("\n[bold cyan]📊 Telemetry Status[/bold cyan]\n")
        
        usage_enabled = config.get('usage_telemetry_enabled', False)
        print(f"[bold]Usage Telemetry:[/bold] {'[green]✅ Enabled[/green]' if usage_enabled else '[red]❌ Disabled[/red]'}")
        if 'usage_telemetry_decided_at' in config:
            print(f"  [dim]Decided: {config['usage_telemetry_decided_at'][:10]}[/dim]")
        
        scan_enabled = config.get('scan_telemetry_enabled', False)
        print(f"\n[bold]Public Scan Contributions:[/bold] {'[green]✅ Enabled[/green]' if scan_enabled else '[red]❌ Disabled[/red]'}")
        if 'scan_telemetry_decided_at' in config:
            print(f"  [dim]Decided: {config['scan_telemetry_decided_at'][:10]}[/dim]")
        
        if config.get('device_id'):
            print(f"\n[dim]Device ID: {config['device_id']}[/dim]")
        
        print("\n[bold]Commands:[/bold]")
        print("  • [cyan]caniscrape telemetry usage on/off[/cyan]  - Toggle usage telemetry")
        print("  • [cyan]caniscrape telemetry scans on/off[/cyan]  - Toggle scan contributions")
        print("  • [cyan]caniscrape telemetry delete[/cyan]       - Delete usage data (GDPR)")
        print("  • [cyan]caniscrape telemetry status[/cyan]       - Show this status")
        print()


_telemetry_manager = None

def get_telemetry_manager() -> TelemetryManager:
    """
    Get or create the global telemetry manager.
    """
    global _telemetry_manager
    if _telemetry_manager is None:
        _telemetry_manager = TelemetryManager()
    return _telemetry_manager