def parse_proxy_for_playwright(proxy_url: str) -> dict | None:
    """
    Parse proxy URL into Playwright-compatible format.
    
    Supports formats:
    - http://user:pass@host:port
    - http://customer-user-sessid-123:pass@host:port
    - host:port (no auth)
    
    Returns:
        dict with 'server', 'username', 'password' keys
        or None if parsing fails
    """
    import re
    
    if not proxy_url:
        return None
    
    # Pattern: [scheme://][username:password@]host:port
    pattern = r'^(?:(\w+)://)?(?:([^:@]+):([^@]+)@)?([^:]+):(\d+)$'
    match = re.match(pattern, proxy_url)
    
    if not match:
        print(f"⚠️  Failed to parse proxy: {proxy_url[:50]}...")
        return None
    
    scheme, username, password, host, port = match.groups()
    
    # Default to http if no scheme
    scheme = scheme or 'http'
    
    result = {
        'server': f'{scheme}://{host}:{port}'
    }
    
    if username and password:
        result['username'] = username
        result['password'] = password
    
    return result