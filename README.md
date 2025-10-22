# caniscrape 🔍

**Know before you scrape.** Analyze any website's anti-bot protections in seconds.

Stop wasting hours building scrapers only to discover the site has Cloudflare + JavaScript rendering + CAPTCHA + rate limiting. `caniscrape` does reconnaissance upfront so you know exactly what you're dealing with before writing a single line of code.

## 🎯 What It Does

`caniscrape` analyzes a URL and tells you:

- **What protections are active** (WAF, CAPTCHA, rate limits, TLS fingerprinting, honeypots)
- **Difficulty score** (0-10 scale: Easy → Very Hard)
- **Specific recommendations** on what tools/proxies you'll need
- **Estimated complexity** so you can decide: build it yourself or use a service
- **CAPTCHA solving capability** (NEW in v0.2.0)
- **Proxy rotation support** (NEW in v0.2.0)

## 🚀 Quick Start

### Installation
```bash
pip install caniscrape
```

**Required dependency:**
```bash
# Install wafw00f (WAF detection)
pipx install wafw00f

# Install Playwright browsers (for JS detection)
playwright install chromium
```

### Basic Usage
```bash
caniscrape https://example.com
```

### Example Output
![caniscrape output](https://github.com/user-attachments/assets/59ad9092-9d24-4ec0-8ea1-da4051c3e05e)

## 🔬 What It Analyzes

### 1. **WAF Detection**
Identifies Web Application Firewalls (Cloudflare, Akamai, Imperva, DataDome, PerimeterX, etc.)

### 2. **Rate Limiting**
- Tests with burst and sustained traffic patterns
- Detects HTTP 429s, timeouts, throttling, soft bans
- Determines blocking threshold (requests/min)

### 3. **JavaScript Rendering**
- Compares content with/without JS execution
- Detects SPAs (React, Vue, Angular)
- Calculates percentage of content missing without JS

### 4. **CAPTCHA Detection & Solving**
- Scans for reCAPTCHA, hCaptcha, Cloudflare Turnstile
- Tests if CAPTCHA appears on load or after rate limiting
- Monitors network traffic for challenge endpoints
- **NEW**: Attempt to solve detected CAPTCHAs using Capsolver or 2Captcha

### 5. **TLS Fingerprinting**
- Compares standard Python clients vs browser-like clients
- Detects if site blocks based on TLS handshake signatures

### 6. **Behavioral Analysis**
- Scans for invisible "honeypot" links (bot traps)
- Detects if site is monitoring mouse/scroll behavior

### 7. **robots.txt**
- Checks scraping permissions
- Extracts recommended crawl-delay

## 🛠️ Advanced Usage

### Aggressive WAF Detection
```bash
# Find ALL WAFs (slower, may trigger rate limits)
caniscrape https://example.com --find-all
```

### Browser Impersonation
```bash
# Use curl_cffi for better stealth (slower but more likely to succeed)
caniscrape https://example.com --impersonate
```

### Deep Honeypot Scanning
```bash
# Check 2/3 of links (more accurate, slower)
caniscrape https://example.com --thorough

# Check ALL links (most accurate, very slow on large sites)
caniscrape https://example.com --deep
```

### Proxy Rotation (NEW in v0.2.0)
```bash
# Use a single proxy
caniscrape https://example.com --proxy "http://user:pass@host:port"

# Use multiple proxies (random rotation)
caniscrape https://example.com \
  --proxy "http://user:pass@host1:port" \
  --proxy "socks5://user:pass@host2:port" \
  --proxy "http://host3:port"
```

**Proxy rotation features:**
- Supports `http` and `socks5` protocols
- Randomly rotates through proxy pool for each request
- Works with all analyzers including WAF detection and headless browser sessions
- Helps bypass basic IP-based blocks and rate limits

### CAPTCHA Solving (NEW in v0.2.0)
```bash
# Detect and attempt to solve CAPTCHAs
caniscrape https://example.com \
  --captcha-service capsolver \
  --captcha-api-key "YOUR_API_KEY"

# Supported services: capsolver, 2captcha
caniscrape https://example.com \
  --captcha-service 2captcha \
  --captcha-api-key "YOUR_API_KEY"
```

**CAPTCHA solving notes:**
- By default, `caniscrape` only detects CAPTCHAs
- To attempt solving, you must provide `--captcha-service` and `--captcha-api-key`
- Only attempts solving if a CAPTCHA is detected
- Provides deeper analysis of site defenses when solving is enabled

### Combine Options
```bash
caniscrape https://example.com \
  --impersonate \
  --find-all \
  --thorough \
  --proxy "http://proxy1:port" \
  --proxy "http://proxy2:port" \
  --captcha-service capsolver \
  --captcha-api-key "YOUR_KEY"
```

## 📊 Difficulty Scoring

The tool calculates a 0-10 difficulty score based on:

| Factor | Impact |
|--------|--------|
| **CAPTCHA on page load** | +5 points |
| **CAPTCHA after rate limit** | +4 points |
| **DataDome/PerimeterX WAF** | +4 points |
| **Akamai/Imperva WAF** | +3 points |
| **Aggressive rate limiting** | +3 points |
| **Cloudflare WAF** | +2 points |
| **Honeypot traps detected** | +2 points |
| **TLS fingerprinting active** | +1 point |

**Score interpretation:**
- **0-2**: Easy (basic scraping will work)
- **3-4**: Medium (need some precautions)
- **5-7**: Hard (requires advanced techniques)
- **8-10**: Very Hard (consider using a service)

## 🔧 Installation Details

### System Requirements
- Python 3.9+
- pip or pipx

### Full Installation
```bash
# 1. Install caniscrape
pip install caniscrape

# 2. Install wafw00f (WAF detection)
# Option A: Using pipx (recommended)
python -m pip install --user pipx
pipx install wafw00f

# Option B: Using pip
pip install wafw00f

# 3. Install Playwright browsers (for JS/CAPTCHA/behavioral detection)
playwright install chromium
```

### Dependencies

Core dependencies (installed automatically):
- `click` - CLI framework
- `rich` - Terminal formatting
- `aiohttp` - Async HTTP requests
- `beautifulsoup4` - HTML parsing
- `playwright` - Headless browser automation
- `curl_cffi` - Browser impersonation

External tools (install separately):
- `wafw00f` - WAF detection

## 🎓 Use Cases

### For Developers
- **Before building a scraper**: Check if it's even feasible
- **Debugging scraper issues**: Identify what protection broke your scraper
- **Client estimates**: Give accurate time/cost estimates for scraping projects
- **Proxy testing**: Verify your proxy pool works against target sites
- **CAPTCHA assessment**: Determine if CAPTCHA solving is required

### For Data Engineers
- **Pipeline planning**: Know what infrastructure you'll need (proxies, CAPTCHA solvers)
- **Cost estimation**: Calculate proxy/CAPTCHA costs before committing to a data source
- **Vendor selection**: Test different proxy and CAPTCHA solving services

### For Researchers
- **Site selection**: Find the easiest data sources for your research
- **Compliance**: Check robots.txt before scraping
- **Anonymity**: Test data collection through proxy infrastructure

## 🆕 What's New in v0.2.0 (Beta)

This is a **beta release** introducing two major features:

### 1. Integrated CAPTCHA Solving
- Attempt to solve detected CAPTCHAs using third-party services
- Supported services: Capsolver, 2Captcha
- Provides deeper analysis when solving is enabled
- Only attempts solving if CAPTCHA is detected

### 2. Full Proxy Support & Rotation
- Route all requests through proxies
- Create proxy rotation pools for better anonymity
- Supports HTTP and SOCKS5 protocols
- Works across all analyzers including WAF detection and browser sessions

### 3. Additional Improvements
- **Smarter URL handling**: Automatically adds `http://` to URLs missing a scheme
- **Bug fixes**: Numerous stability and error-handling improvements
- **Better error messages**: More informative output when things go wrong

### 🧪 Beta Testing
We need your help to stabilize these features! Please:
- Test proxy rotation with different proxy providers
- Test CAPTCHA solving with Capsolver and 2Captcha
- Report any bugs, crashes, or unexpected behavior
- Provide feedback on the new features

The next update (v0.3.0) will focus on improving detection for tough sites like Amazon and YouTube.

## ⚠️ Limitations & Disclaimers

### What It Can't Detect
- **Dynamic protections**: Some sites only trigger defenses under specific conditions
- **Behavioral AI**: Advanced ML-based bot detection that adapts in real-time
- **Account-based restrictions**: Protections that only activate for logged-in users

### Legal & Ethical Notes
- This tool is for **reconnaissance only** - it does not bypass protections
- Always respect `robots.txt` and terms of service
- Some sites may consider aggressive scanning hostile - use `--find-all` and `--deep` sparingly
- CAPTCHA solving should only be used for legitimate testing purposes
- You are responsible for how you use this tool and any scrapers you build
- Ensure your use of proxies and CAPTCHA solving complies with applicable laws and terms of service

### Technical Notes
- Analysis takes 30-60 seconds per URL (longer with CAPTCHA solving)
- Some checks require making multiple requests (may trigger rate limits)
- Results are a snapshot - protections can change over time
- Proxy rotation adds latency but improves anonymity
- CAPTCHA solving success depends on service quality and site complexity

## 🤝 Contributing

Found a bug? Have a feature request? Contributions are welcome!

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

Built on top of:
- [wafw00f](https://github.com/EnableSecurity/wafw00f) - WAF detection
- [Playwright](https://playwright.dev/) - Browser automation
- [curl_cffi](https://github.com/yifeikong/curl_cffi) - Browser impersonation

## 📬 Contact

Questions? Feedback? Open an issue on GitHub.

---

**Remember**: This tool tells you HOW HARD it will be to scrape. It doesn't do the scraping for you. Use it to make informed decisions before you start building.
