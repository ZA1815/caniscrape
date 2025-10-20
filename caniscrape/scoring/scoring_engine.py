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
    for waf_name, _ in wafs_found:
        if 'DataDome' in waf_name or 'PerimeterX' in waf_name:
            waf_scores.append(4)
        elif 'Akamai' in waf_name or 'Imperva' in waf_name:
            waf_scores.append(3)
        elif 'Cloudflare' in waf_name or 'Cloudfront' in waf_name:
            waf_scores.append(2)
    if waf_scores:
        score += max(waf_scores)

    rate_limit_results = results.get('rate_limit', {}).get('results', {})
    if rate_limit_results.get('blocking_code') and (rate_limit_results.get('requests_sent', 0) < 5 and rate_limit_results.get('requests_sent', 0) > 1):
        score += 3
    
    if results.get('behavioral', {}).get('honeypot_detected'):
        score += 2
    
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