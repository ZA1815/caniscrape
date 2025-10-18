import click
from rich import print
from rich.markup import escape

from .analyzers.waf_detector import detect_waf
from .analyzers.robots_checker import check_robots_txt

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

    print('🔍 Running WAF detection...')
    waf_result = detect_waf(url)

    print('🤖 Checking robots.txt...')
    robots_result = check_robots_txt(url)

    print('\n🛡️  PROTECTIONS DETECTED: \n')


    # WAF check
    waf_status = waf_result['status']

    if waf_status == 'error':
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
    elif waf_status == 'success':
        waf_list = waf_result['wafs']

        if not waf_list:
            print('    [green]✅ No WAF detected.[/green]')
        
        elif len(waf_list) == 1 and waf_list[0][0] == 'Generic WAF':
            print(f'    [yellow]⚠️  WAF: A generic WAF or security solution was detected.[/yellow]')
        
        else:
            display_lines = []
            for name, manuf in waf_list:
                line = escape(name)
                if manuf:
                    line += f' by ({escape(manuf)})'
                display_lines.append(line)
            if len(display_lines) == 1:
                print(f'    [red]❌ WAF: {display_lines[0]}[/red]')
            else:
                print(f'    [red]❌ WAFs Detected:[/red]')
                for line in display_lines:
                    print(f'        [red]- {line}[/red]')

    # Robots.txt check
    robots_status = robots_result['status']
    if robots_status == 'success':
        if robots_result['scraping_disallowed']:
            print('    [red]❌ robots.txt: Explicitly disallows scraping for all bots (\'Disallow: /\')[/red]')
        else:
            delay = robots_result.get('crawl_delay')
            message = 'Website allows scraping'
            if delay:
                message += f' (Crawl-delay: {delay}s)'
            print(f'    [green]✅ robots.txt: {message}[/green]')
    elif robots_status == 'not_found':
        print('    [green]✅ robots.txt: Website does not have a robots.txt file (no explicit restrictions).[/green]')
    elif robots_status == 'error':
        print(f'    [yellow]⚠️ robots.txt: Could not be analyzed. Reason: {robots_result['message']}[/yellow]')
    print('\n')

    print(f'Analysis complete.')

if __name__ == '__main__':
    cli()