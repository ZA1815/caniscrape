from __future__ import annotations

def get_impersonate_target(user_agent: str) -> str:
    ua_lower = user_agent.lower()
    
    if "edg/" in ua_lower:
        return "edge101"
    elif "chrome/" in ua_lower and "edg/" not in ua_lower:
        if "android" in ua_lower:
            return "chrome131"
        else:
            return "chrome131"
    elif "firefox/" in ua_lower:
        return "firefox133"
    elif "safari/" in ua_lower and "chrome" not in ua_lower:
        if "iphone" in ua_lower or "ipad" in ua_lower:
            return "safari172_ios"
        else:
            return "safari155"
    
    return "chrome131"