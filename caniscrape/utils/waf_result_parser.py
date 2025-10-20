from __future__ import annotations

import re

ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def clean_text(text: str | None) -> str:
    if not text:
        return ''
    txt = ANSI_RE.sub('', text)
    txt = txt.replace('\r\n', '\n').replace('\r', '\n')
    return txt

def parse_wafw00f_output(stdout: str, stderr: str = '') -> list[tuple[str, str | None]]:
    """
    Parse wafw00f output and return a list of detected WAFs.
    Each item is a tuple: (waf_name, manufacturer_or_None)
    """
    text = clean_text((stdout or '') + '\n' + (stderr or ''))
    results = []

    narrative_re = re.compile(
        r'(?:The site\s+\S+|\[?\+?\]?)\s*'
        r'(?:is|appears to be|seems to be|might be|probably is|is probably)\s+'
        r'(?:protected\s+by\s+|behind\s+)?'
        r'([A-Za-z0-9](?:[A-Za-z0-9\s\-_]*[A-Za-z0-9])?)'
        r'\s*(?:\(([^\)]+)\))?'
        r'(?:\s*WAF\.?)?',
        re.IGNORECASE
    )

    for m in narrative_re.finditer(text):
        name = m.group(1).strip() if m.group(1) else None
        manuf = m.group(2).strip() if m.group(2) else None
        if name:
            results.append((name, manuf))

    if not results:
        generic_re = re.compile(
            r'generic detection|behind a waf|security solution|protected by',
            re.IGNORECASE
        )
        if generic_re.search(text):
            results.append(('Generic WAF', None))

    seen = set()
    out = []
    for name, manuf in results:
        key = (name.lower(), (manuf or '').lower())
        if key not in seen:
            seen.add(key)
            out.append((name, manuf))

    return out