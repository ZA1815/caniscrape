import click
from rich import print
from rich.markup import escape

from .analyzers.waf_detector import detect_waf

@click.group()
def cli():
    """
    A cli tool for analyzing how hard a website is to scrape.
    """
    pass

@cli.command()
@click.argument('url')
def analyze(url: str):
    """
    Analyzes a single URL for scraping difficulty.
    """
    print(f'Analyzing: [bold blue]{url}[/bold blue]...')

    waf_result = detect_waf(url)

    print('\n🛡️  PROTECTIONS DETECTED: \n')

    status = waf_result['status']

    if status == 'error':
        message = waf_result.get('message', '')
        
        if message == 'wafw00f missing':
            print('[bold red]Error: "wafw00f" command not found.[/bold red]')
            print('[yellow]To fix this, please follow these steps in your terminal:')
            print('[yellow]1. Install pipx: [bold]python -m pip install --user pipx[/bold][/yellow]')
            print('[yellow]2. Install wafw00f: [bold]pipx install wafw00f[/bold][/yellow]')
            print('[yellow](You may need to restart your terminal or restart your IDE after step 1 if step 2 doesn\'t work.)')
        elif message == 'timeout':
            print('[yellow]WAF detection timed out.[/yellow]')
        else:
            print(f'[yellow]WAF detection failed. Wafw00f stderr: {message}[/yellow]')
    elif status == 'success':
        waf_list = waf_result['wafs']

        if not waf_list:
            print('[green]✅ No WAF detected.[/green]')
            return
        
        elif len(waf_list) == 1 and waf_list[0][0] == 'Generic WAF':
            print(f"[yellow]⚠️ WAF: A generic WAF or security solution was detected.[/yellow]")
            return
        
        else:
            display_lines = []
            for name, manuf in waf_list:
                line = escape(name)
                if manuf:
                    line += f' by ({escape(manuf)})'
                display_lines.append(line)
            if len(display_lines) == 1:
                print(f"    [red]❌ WAF: {display_lines[0]}[/red]\n")
            else:
                print(f"    [red]❌ WAFs Detected:[/red]")
                for line in display_lines:
                    print(f"    [red]- {line}[/red]")
                print('\n')

    print(f'Analysis complete.')

if __name__ == '__main__':
    cli()