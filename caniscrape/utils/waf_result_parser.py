import re

ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

GENERIC_PHRASES = {
    'generic waf',
    'generic detection',
    'a waf or some sort of security solution',
    'a waf',
    'waf',
    'some sort of security solution',
    'security solution',
    'used'
}

def clean_text(text: str | None) -> str:
    """Removes ANSI color codes and normalizes line endings."""
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
        r'(?:is|behind|protected by)\s+'
        r'([A-Z][\w\s-]*)(?:\s+\(in\s+)?(?:\s*WAF)?'
        r'(?:\s*\(([^\)]+)\))?',
        re.IGNORECASE
    )

    for m in narrative_re.finditer(text):
        name = m.group(1).strip() if m.group(1) else None
        manuf = m.group(2).strip() if m.group(2) else None
        if name:
            results.append((name, manuf))

    filtered_results = [
        (name, manuf) for name, manuf in results
        if name.lower().strip() not in GENERIC_PHRASES
    ]

    if not filtered_results:
        generic_re = re.compile(
            r'generic detection|behind a waf|security solution|protected by',
            re.IGNORECASE
        )
        if generic_re.search(text):
            return [('Generic WAF', None)]

    seen = set()
    out = []
    for name, manuf in filtered_results:
        key = (name.lower(), (manuf or '').lower())
        if key not in seen:
            seen.add(key)
            out.append((name, manuf))

    return out