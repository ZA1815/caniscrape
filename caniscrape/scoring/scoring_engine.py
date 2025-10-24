from __future__ import annotations

def calculate_difficulty_score(results: dict[str, any]) -> dict[str, any]:
    """
    Calculates a difficulty score from 0-10 based on the collected analysis results.
    """
    score = 0

    if results.get('captcha', {}).get('captcha_detected'):
        score += 5 if results['captcha']['trigger_condition'] == 'on page load' else 4
    
    waf_scores = []
    wafs_found = results.get('waf', {}).get('wafs', [])
    has_cloudflare_waf = False
    
    for waf_name, _ in wafs_found:
        if 'DataDome' in waf_name or 'PerimeterX' in waf_name:
            waf_scores.append(4)
        elif 'Akamai' in waf_name or 'Imperva' in waf_name:
            waf_scores.append(3)
        elif 'Cloudflare' in waf_name or 'Cloudfront' in waf_name:
            waf_scores.append(2)
            has_cloudflare_waf = True
    if waf_scores:
        score += max(waf_scores)

    rate_limit_results = results.get('rate_limit', {}).get('results', {})
    if rate_limit_results.get('blocking_code') and (rate_limit_results.get('requests_sent', 0) < 5 and rate_limit_results.get('requests_sent', 0) > 1):
        score += 3
    
    if results.get('behavioral', {}).get('honeypot_detected'):
        score += 2
    
    fingerprint_results = results.get('fingerprint', {})
    if fingerprint_results.get('status') == 'success':
        detected_services = fingerprint_results.get('detected_services', [])
        
        if detected_services:
            is_only_cloudflare = all('Cloudflare' in service for service in detected_services)
            
            if is_only_cloudflare and has_cloudflare_waf:
                pass
            elif any(service in ['PerimeterX (HUMAN)', 'DataDome', 'Akamai Bot Manager', 'Kasada'] for service in detected_services):
                score += 2
            else:
                score += 1
        
        if fingerprint_results.get('canvas_fingerprinting_signal'):
            score += 1
    
    integrity_results = results.get('integrity', {})
    if integrity_results.get('status') == 'success':
        modified_functions = integrity_results.get('modified_functions', {})
        if modified_functions:
            score += 1
    
    if results.get('tls', {}).get('status') == 'active':
        score += 1
    
    final_score = min(score, 10)

    difficulty_label = 'Easy'
    if final_score >= 8:
        difficulty_label = 'Very Hard'
    elif final_score >= 5:
        difficulty_label = 'Hard'
    elif final_score >= 3:
        difficulty_label = 'Medium'

    return {'score': final_score, 'label': difficulty_label}