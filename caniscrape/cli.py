from __future__ import annotations

import click
from rich import print
from rich.markup import escape
from rich.panel import Panel
from rich.rule import Rule
from time import sleep
import asyncio

import warnings
import logging

warnings.filterwarnings("ignore", message="Event loop is closed", category=RuntimeWarning)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

from .analyzers.waf_detector import detect_waf
from .analyzers.robots_checker import check_robots_txt
from .analyzers.rate_limit_profiler import profile_rate_limits
from .analyzers.tls_analyzer import analyze_tls_fingerprint
from .analyzers.js_detector import analyze_js_rendering
from .analyzers.behavioral_detector import detect_honeypots
from .analyzers.captcha_detector import detect_captcha
from .analyzers.fingerprint_analyzer import analyze_fingerprinting
from .analyzers.integrity_analyzer import analyze_function_integrity
from .scoring.scoring_engine import calculate_difficulty_score
from .recommendations.recommender import generate_recommendations

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
@click.option(
    '--proxy',
    'proxies',
    multiple=True,
    type=str,
    help='Proxy to use for requests. Can be used multiple times to create a rotation pool.'
)
@click.option(
    '--captcha-service',
    type=click.Choice(['capsolver', '2captcha'], case_sensitive=False),
    default=None,
    help='The CAPTCHA solving service to use (optional).'
)
@click.option(
    '--captcha-api-key',
    type=str,
    default=None,
    help='API key for the selected CAPTCHA solving service.'
)
def cli(url: str, find_all: bool, impersonate: bool, scan_depth: str | None, proxies: tuple[str, ...], captcha_service: str | None, captcha_api_key: str | None, ):
    """
    Analyzes a single URL for scraping difficulty.
    """
    if not url.startswith(('http://', 'https://')):
        url = f'http://{url}'
        print(f"[yellow]⚠️  URL scheme missing. Assuming 'http://'. Analyzing: [bold blue]{url}[/bold blue]...[/yellow]")

    print(f'🔍 Analyzing: [bold blue]{url}[/bold blue]...')

    if find_all:
        print(f'    [yellow]⚠️  Running with --find-all is aggressive and may trigger rate limits or temporary IP bans.[/yellow]\n')
    if scan_depth == 'thorough':
        print(f'    [yellow]⚠️  --thorough scan selected. Behavioral analysis may take several minutes on large sites.[/yellow]')
    if scan_depth == 'deep':
        print(f'    [yellow]⚠️  --deep scan selected. Behavioral analysis may take 10+ minutes on large sites.[/yellow]')
    if find_all or scan_depth:
        print('    [yellow]You have 5 seconds after the above message(s) to cancel. (Ctrl + C to cancel)[/yellow]')
        sleep(5)

    print('Checking robots.txt...')
    robots_result = check_robots_txt(url, proxies=proxies)
    crawl_delay = robots_result.get('crawl_delay')

    print('Analyzing TLS fingerprint...')
    tls_result = asyncio.run(analyze_tls_fingerprint(url, proxies=proxies))

    print('Analyzing for advanced fingerprinting...')
    fingerprint_result = analyze_fingerprinting(url, proxies=proxies)

    print('Performing function integrity analysis...')
    integrity_result = analyze_function_integrity(url, proxies=proxies)

    print('Analyzing JavaScript rendering...')
    js_result = analyze_js_rendering(url, proxies=proxies)

    if scan_depth is None:
        print('Analyzing for behavioral traps (default scan)...')
    else:
        print(f'Analyzing for behavioral traps ({scan_depth} scan)...')
    behavioral_result = detect_honeypots(url, scan_depth=scan_depth, proxies=proxies)

    print('Detecting CAPTCHA...')
    captcha_result = detect_captcha(url, service_name=captcha_service, api_key=captcha_api_key, proxies=proxies)

    if impersonate:
        print('Profiling rate limits with browser-like client...')
    else:
        print('Profiling rate limits with Python client...')
    rate_limit_result = asyncio.run(profile_rate_limits(url, crawl_delay, impersonate, proxies=proxies))

    print('Running WAF detection...')
    waf_result = detect_waf(url, find_all, proxies=proxies)

    all_results = {
        'robots': robots_result,
        'tls': tls_result,
        'js': js_result,
        'behavioral': behavioral_result,
        'captcha': captcha_result,
        'rate_limit': rate_limit_result,
        'waf': waf_result,
        'fingerprint': fingerprint_result,
        'integrity': integrity_result
    }

    score_card = calculate_difficulty_score(all_results)
    recommendations = generate_recommendations(all_results)

    print('\n')
    print(Rule(f"[bold white on blue] DIFFICULTY SCORE: {score_card['score']}/10 ({score_card['label']}) [/]", style="blue"))
    print()

    print()
    print("[bold yellow]🛡️  ACTIVE PROTECTIONS[/bold yellow]")
    print()

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
        print(f'    [yellow]⚠️  robots.txt: Could not be analyzed. Reason: {robots_result["message"]}[/yellow]')

    # TLS check
    tls_status = tls_result['status']
    if tls_status == 'active':
        print(f'    [red]❌ TLS Fingerprinting: {tls_result["details"]}[/red]')
    elif tls_status == 'inactive':
        print(f'    [green]✅ TLS Fingerprinting: {tls_result["details"]}[/green]')
    elif tls_status == 'inconclusive':
        print(f'    [yellow]⚠️  TLS Fingerprinting: {tls_result["details"]}[/yellow]')

    # Advanced fingerprinting check
    fingerprint_status = fingerprint_result['status']
    if fingerprint_status == 'success':
        red_flags = []
        yellow_flags = []

        if fingerprint_result['detected_services']:
            services = ', '.join(fingerprint_result['detected_services'])
            red_flags.append(f'Known Services Found: {services}')

        if fingerprint_result['canvas_fingerprinting_signal']:
            yellow_flags.append('Canvas Fingerprinting Suspected (canvas function is not native)')

        if fingerprint_result['behavioral_listeners_detected']:
            listeners = ', '.join(fingerprint_result['behavioral_listeners_detected'])
            yellow_flags.append(f'Behavioral Tracking Suspected (listeners found for: {listeners})')

        if red_flags:
            print('    [red]❌ Advanced Bot Detection:[/red]')
            for flag in red_flags:
                print(f'    [red]- {flag}[/red]')
        
        elif yellow_flags:
            print('    [yellow]⚠️  Suspicious Signals:[/yellow]')
            for flag in yellow_flags:
                print(f'    [yellow]- {flag}[/yellow]')
        
        else:
            print('    [green]✅ Advanced Bot Detection: No obvious fingerprinting services or signals detected.[/green]')
    else:
        print(f'    [yellow]⚠️  Fingerprinting: Analysis failed. Reason: {fingerprint_result["message"]}[/yellow]')

    # Integrity check
    integrity_status = integrity_result['status']
    if integrity_status == 'success':
        modified_funcs = integrity_result.get('modified_functions', {})
        if modified_funcs:
            print('    [red]❌ Browser Integrity Compromised:[/red]')
            for func, reason in modified_funcs.items():
                print(f'    [red]- Function "{func}" was modified.[/red]')
                print(f'      [red]Reason: {reason}[/red]')
        else:
            print('    [green]✅ Browser Integrity: No modifications detected.[/green]')
    else:
        print(f'    [yellow]⚠️  Integrity Analysis: Test failed. Reason: {integrity_result["message"]}[/yellow]')

    # JS rendering check
    js_status = js_result['status']
    if js_status == 'success':
        if js_result.get('is_spa'):
            print(f'    [red]❌ JavaScript: Required (React/Vue/Angular SPA). {js_result["content_difference_%"]}% of content is missing without JS.[/red]')
        elif js_result.get('js_required'):
            print(f'    [yellow]⚠️  JavaScript: Required for some content. {js_result["content_difference_%"]}% of content is missing without JS.[/yellow]')
        else:
            print(f'    [green]✅ JavaScript: Not required for main content.[/green]')
    else:
        print(f'    [yellow]⚠️  JavaScript: Analysis failed. Reason: {js_result["message"]}[/yellow]')

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
        print(f'    [yellow]⚠️  Behavioral Analysis: Test failed. Reason: {behavioral_result["message"]}[/yellow]')

    # CAPTCHA check
    captcha_status = captcha_result['status']
    if captcha_status == 'success':
        if captcha_result.get('captcha_detected'):
            type = captcha_result['captcha_type']
            trigger = captcha_result['trigger_condition']
            print(f'    [red]❌ CAPTCHA: {type} detected ({trigger}).[/red]')
            if captcha_result.get('solve_status') == 'solved':
                print(f'        [green]✅ {captcha_result["details"]}[/green]')
            elif captcha_result.get('solve_status') == 'failed':
                print(f'        [red]❌ {captcha_result["details"]}[/red]')
            else:
                print(f'        [blue]ℹ️  {captcha_result["details"]}[/blue]')
        else:
            print(f'    [green]✅ CAPTCHA: No CAPTCHA detected during initial analysis.[/green]')
    else:
        print(f'    [yellow]⚠️  CAPTCHA: Analysis failed. Reason: {captcha_result["message"]}[/yellow]')

    # Rate limit check
    rate_limit_status = rate_limit_result['status']
    if rate_limit_status == 'success':
        results = rate_limit_result['results']
        if results.get('blocking_code') and results.get('requests_sent') == 1:
            print(f'    [red]❌ Rate Limiting: Blocked Immediately ({results["details"]})[/red]')
            print(f'    [yellow]💡 [bold]Advice:[/bold] This is likely due to client fingerprinting (TLS fingerprinting, User-Agent, etc.), not a classic rate limit.[/yellow]')
            print(f'       [yellow]Run the analysis again. A different browser identity will be used, which may not be blocked.[/yellow]')
            print(f'    [yellow]   Otherwise, try the --impersonate flag, it will take longer but is likely to succeed.[/yellow]')
        else:
            print(f'    [green]✅ Rate Limiting: {results["details"]}[/green]')
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

    print()
    print(Rule("[bold]💡 RECOMMENDATIONS[/bold]", style="cyan"))

    print("\n[bold]Required Tools:[/bold]")
    if recommendations['tools']:
        for tool in recommendations['tools']:
            print(f"  • {tool}")
    else:
        print("  • No special tools required.")

    print("\n[bold]Scraping Strategy:[/bold]")
    for tip in recommendations['strategy']:
        print(f"  • {tip}")

    print()
    print(Rule("[bold]Analysis Complete[/bold]", style="green"))
    print()

if __name__ == '__main__':
    cli()