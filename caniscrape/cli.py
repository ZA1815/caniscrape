import click
from rich import print
from rich.markup import escape
from time import sleep

from .analyzers.waf_detector import detect_waf
from .analyzers.robots_checker import check_robots_txt
from .analyzers.rate_limit_profiler import profile_rate_limits
from .analyzers.tls_analyzer import analyze_tls_fingerprint
from .analyzers.js_detector import analyze_js_rendering
from .analyzers.behavioral_detector import detect_honeypots

@click.command()
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
@click.option(
    '--thorough',
    'scan_depth',
    flag_value='thorough',
    help='Makes the behavioral detector scan through about 2/3 of the total links. Will give great accuracy in detecting honeypots but is slower on large sites.'
)
@click.option(
    '--deep',
    'scan_depth',
    flag_value='deep',
    help='Makes the behavioral detector scan through all the links. Will give excellent accuracy in detecing honeypots but is very slow on large sites.'
)
def cli(url: str, find_all: bool, impersonate: bool, scan_depth: str | None):
    """
    Analyzes a single URL for scraping difficulty.
    """
    print(f'Analyzing: [bold blue]{url}[/bold blue]...')

    if find_all:
        print(f'    [yellow]⚠️  Running with --find-all is aggressive and may trigger rate limits or temporary IP bans.[/yellow]\n')
    if scan_depth == 'thorough':
        print(f'    [yellow]⚠️  --thorough scan selected. Behavioral analysis may take several minutes on large sites.[/bold yellow]')
    if scan_depth == 'deep':
        print(f'    [yellow]⚠️  --deep scan selected. Behavioral analysis may take 10+ minutes on large sites.[/bold yellow]')
    if find_all or scan_depth:
        print('    [yellow]You have 5 seconds after the above message(s) to cancel. (Ctrl + C to cancel)[/yellow]')
        sleep(5)

    print('🤖 Checking robots.txt...')
    robots_result = check_robots_txt(url)
    crawl_delay = robots_result.get('crawl_delay')

    print('🔬 Analyzing TLS fingerprint...')
    tls_result = analyze_tls_fingerprint(url)

    print('⚙️  Analyzing JavaScript rendering...')
    js_result = analyze_js_rendering(url)

    if scan_depth is None:
        print('🕵️  Analyzing for behavioral traps (default scan)...')
    else:
        print(f'🕵️  Analyzing for behavioral traps ({scan_depth} scan)...')
    behavioral_result = detect_honeypots(url, scan_depth=scan_depth)

    if impersonate:
        print('⏱️ Profiling rate limits with browser-like client...')
    else:
        print('⏱️  Profiling rate limits with Python client...')
    rate_limit_result = profile_rate_limits(url, crawl_delay, impersonate)

    print('🔍 Running WAF detection...')
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
            message = 'Website allows scraping (for details on specific pages, navigate to <url>/robots.txt in your browser.)'
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

    # JS rendering check
    js_status = js_result['status']
    if js_status == 'success':
        if js_result.get('is_spa'):
            print(f'    [red]❌ JavaScript: Required (React/Vue/Angular SPA). {js_result['content_difference_%']}% of content is missing without JS.[/red]')
        elif js_result.get('js_required'):
            print(f'    [yellow]⚠️  JavaScript: Required for some content. {js_result['content_difference_%']}% of content is missing without JS.[/yellow]')
        else:
            print(f'    [green]✅ JavaScript: Not required for main content.[/green]')
    else:
        print(f'    [yellow]⚠️  JavaScript: Analysis failed. Reason: {js_result['message']}[/yellow]')

    # Behavioral check
    behavioral_status = behavioral_result['status']
    if behavioral_status == 'success':
        if behavioral_result.get('honeypot_detected'):
            count = behavioral_result['invisible_links']
            checked = behavioral_result['links_checked']
            print(f'    [red]❌ Behavioral Analysis: Found {count} invisible "honeypot" links (out of {checked} checked). There are many bot traps.[/red]')
        else:
            print(f'    [green]✅ Behavioral Analysis: No obvious honeypot traps detected.[/green]')
    else:
        print(f'    [yellow]⚠️  Behavioral Analysis: Test failed. Reason: {behavioral_result['message']}[/yellow]')

    # Rate limit check
    rate_limit_status = rate_limit_result['status']
    if rate_limit_status == 'success':
        results = rate_limit_result['results']
        if results.get('blocking_code') and results.get('requests_sent') == 1:
            print(f'    [red]❌ Rate Limiting: Blocked Immediately ({results['details']})[/red]')
            print(f'    [yellow]💡 [bold]Advice:[/bold] This is likely due to client fingerprinting (TLS fingerprinting, User-Agent, etc.), not a classic rate limit.[/yellow]')
            print(f'       [yellow]Run the analysis again. A different browser identity will be used, which may not be blocked.[/yellow]')
            print (f'    [yellow]   Otherwise, try the --impersonate flag, it will take longer but is likely to succeed.')
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