import click
from rich import print
from rich.markup import escape
from time import sleep

from .analyzers.waf_detector import detect_waf
from .analyzers.robots_checker import check_robots_txt
from .analyzers.rate_limit_profiler import profile_rate_limits
from .analyzers.tls_analyzer import analyze_tls_fingerprint

@click.group()
def cli():
    """
    A cli tool for analyzing how hard a website is to scrape.
    """
    pass

@cli.command()
@click.argument('url')
@click.option(
    '--find-all',
    is_flag=True,
    default=False,
    help='Uses --find-all tag for wafw00f. Default is false. Using the flag is aggressive but is more likely to detect multi-WAF setups.'
)
@click.option(
    '--impersonate',
    is_flag=True,
    default=False,
    help='Switches from using a basic python script to impersonating a real browser (curl_cffi library). Default is False. Impersonating will likely take longer but is more likely to succeed.'
)
def analyze(url: str, find_all: bool, impersonate: bool):
    """
    Analyzes a single URL for scraping difficulty.
    """
    print(f'Analyzing: [bold blue]{url}[/bold blue]...')

    print('🤖 Checking robots.txt...')
    robots_result = check_robots_txt(url)
    crawl_delay = robots_result.get('crawl_delay')

    print('🔬 Analyzing TLS fingerprint...')
    tls_result = analyze_tls_fingerprint(url)

    if impersonate:
        print('⏱️ Profiling rate limits with browser-like client...')
    else:
        print('⏱️ Profiling rate limits with Python client...')
    rate_limit_result = profile_rate_limits(url, crawl_delay, impersonate)

    print('🔍 Running WAF detection...')

    if find_all:
        print(f'  [yellow]⚠️  Heads up: Running with --find-all is aggressive and may trigger rate limits or temporary IP bans.[/yellow]\n')
        print('   [yellow]You have 5 seconds after this message to cancel. (Ctrl + C to cancel)[/yellow]')
        sleep(5)

    waf_result = detect_waf(url, find_all)

    # Start of output
    print('\n🛡️  PROTECTIONS DETECTED: \n')

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

    # TLS check
    tls_status = tls_result['status']
    if tls_status == 'active':
        print(f'    [red]❌ TLS Fingerprinting: {tls_result['details']}[/red]')
    elif tls_status == 'inactive':
        print(f'    [green]✅ TLS Fingerprinting: {tls_result['details']}[/green]')
    elif tls_status == 'inconclusive':
        print(f'    [yellow]⚠️  TLS Fingerprinting: {tls_result['details']}[/yellow]')

    # Rate limit check
    rate_limit_status = rate_limit_result['status']
    if rate_limit_status == 'success':
        results = rate_limit_result['results']
        if results.get('blocking_code') and results.get('requests_sent') == 1:
            print(f'    [red]❌ Rate Limiting: {results['details']}[/red]')
            print(f'    [yellow]💡 [bold]Advice:[/bold] This is likely due to client fingerprinting (TLS fingerprinting, User-Agent, etc.), not a classic rate limit.[/yellow]')
            print(f'       [yellow]Run the analysis again. A different browser identity will be used, which may not be blocked.[/yellow]')
        else:
            print(f'    [green]✅ Rate Limiting: {results['details']}[/green]')
    else:
        error_message = rate_limit_result.get('message', 'Unknown error')
        print(f'    [yellow]⚠️  Rate Limiting: Test failed. Reason: {error_message}[/yellow]')

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
            print(f'    [blue]ℹ️  WAF: A generic firewall or server security rule might be present (low confidence).[/blue]')
        
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
    print('\n')

    print(f'Analysis complete.')

if __name__ == '__main__':
    cli()