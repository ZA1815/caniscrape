from rich import print
from rich.panel import Panel

def compare_scans(current_scan: dict, previous_scan: dict) -> dict:
    diff ={
        'score_changed': False,
        'score_delta': 0,
        'protections_added': [],
        'protections_removed': [],
        'status_changes': {}
    }

    if 'scan_data' in previous_scan:
        prev_data = previous_scan['scan_data']
    else:
        prev_data = previous_scan

    curr_data = current_scan

    prev_score = prev_data.get('score_card', {}).get('score', 0)
    curr_score = curr_data.get('score_card', {}).get('score', 0)

    if curr_score != prev_score:
        diff['score_changed'] = True
        diff['score_delta'] = curr_score - prev_score

    prev_protections = prev_data.get('protections', {})
    curr_protections = curr_data.get('protections', {})

    prev_wafs = set()
    curr_wafs = set()

    if 'waf' in prev_protections and prev_protections['waf'].get('status') == 'success':
        for waf in prev_protections['waf'].get('wafs', []):
            if isinstance(waf, dict):
                prev_wafs.add(waf.get('name', ''))
            else:
                prev_wafs.add(waf[0] if waf else '')
    
    if 'waf' in curr_protections and curr_protections['waf'].get('status') == 'success':
        for waf in curr_protections['waf'].get('wafs', []):
            if isinstance(waf, dict):
                curr_wafs.add(waf.get('name', ''))
            else:
                curr_wafs.add(waf[0] if waf else '')
    
    prev_wafs = {w for w in prev_wafs if w}
    curr_wafs = {w for w in prev_wafs if w}

    wafs_added = curr_wafs - prev_wafs
    wafs_removed = prev_wafs - curr_wafs

    for waf in wafs_added:
        diff['protections_added'].append(f'WAF: {waf}')
    for waf in wafs_removed:
        diff['protections_removed'].append(f'WAF: {waf}')
    
    prev_captcha = prev_protections.get('captcha', {}).get('captcha_detected', 'Unknown')
    curr_captcha = curr_protections.get('captcha', {}).get('captcha_detected', 'Unknown')

    if curr_captcha and not prev_captcha:
        captcha_type = curr_protections['captcha'].get('captcha_type', 'Unknown')
        diff['protections_added'].append(f'CAPTCHA: {captcha_type}')
    elif not curr_captcha and prev_captcha:
        captcha_type = prev_protections['captcha'].get('captcha_type', 'Unknown')
        diff['protections_removed'].append(f'CAPTCHA: {captcha_type}')
    
    prev_tls = prev_protections.get('tls', {}).get('status', 'inactive')
    curr_tls = curr_protections.get('tls', {}).get('status', 'inactive')

    if curr_tls == 'active' and prev_tls != 'active':
        diff['protections_added'].append('TLS Fingerprinting')
    elif curr_tls != 'active' and prev_tls == 'active':
        diff['protections_removed'].append('TLS Fingerprinting')

    prev_honeypot = prev_protections.get('behavioral', {}).get('honeypot_detected', False)
    curr_honeypot = prev_protections.get('behavioral', {}).get('honeypot_detected', False)

    if curr_honeypot and not prev_honeypot:
        diff['protections_added'].append('Honeypot Traps')
    elif not curr_honeypot and prev_honeypot:
        diff['protections_removed'].append('Honeypot Traps')

    prev_js = prev_protections.get('js', {}).get('js_required', False)
    curr_js = curr_protections.get('js', {}).get('js_required', False)

    if curr_js and not prev_js:
        diff['protections_added'].append('JavaScript rendering required')
    elif not curr_js and prev_js:
        diff['protections_removed'].append('JavaScript rendering required')

    return diff

def display_diff(diff: dict, previous_scan_date: str) -> None:
    has_changes = (
        diff['score_changed'] or
        diff['protections_added'] or
        diff['protections_removed'] or
        diff['status_changes']
    )

    if not has_changes:
        print(f'\n[dim]ℹ️  No changes detected since last scan ({previous_scan_date})[/dim]')
        return
    
    lines = []
    lines.append(f'\n[bold]📊 Changes Since Last Scan ({previous_scan_date})[/bold]')

    if diff['score_changed']:
        delta = diff['score_delta']
        if delta > 0:
            lines.append(f'[red]⚠️  Difficulty Score: +{delta} points (site got harder to scrape)[/red]')
        else:
            lines.append(f'[green]✅ Difficulty Score: {delta} points (site got easier to scrape)[/green]')
        
    if diff['protections_added']:
        lines.append('\n[red][bold]⚠️  New Protections Detected:[/bold][/red]')
        for protection in diff['protections_added']:
            lines.append(f'  [red]+ {protection}[/red]')
    
    if diff['protections_removed']:
        lines.append('\n[green][bold]✅ Protections Removed:[/bold][/green]')
        for protection in diff['protections_removed']:
            lines.append(f'  [green]- {protection}[/green]')
    
    if diff['status_changes']:
        lines.append('\n[yellow][bold]Changed:[/bold][/yellow]')
        for name, change in diff['status_changes']:
            lines.append(f'  [yellow]~ {name}: {change["old"]} → {change["new"]}[/yellow]')

    print()
    print(Panel(
        '\n'.join(lines),
        title='Scan Comparison',
        border_style='cyan',
        expand=False
    ))

def should_show_diff(previous_scan: dict | None) -> bool:
    if not previous_scan:
        return False
    
    scan_data = previous_scan.get('scan_data', previous_scan)

    required_fields = ['score_card', 'protections']
    for field in required_fields:
        if field not in scan_data:
            return False
        
    return True