# 🕵️ py-seo-auditor

> Because your website deserves better than page 2 of Google.

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![Coffee Powered](https://img.shields.io/badge/powered%20by-coffee-brown.svg)](https://www.buymeacoffee.com/yourusername)

**py-seo-auditor** is your website's brutally honest best friend. It'll tell you everything wrong with your SEO — from that missing meta description to the 47 broken links you've been ignoring since 2019.

Think of it as a health checkup for your website, except instead of telling you to eat more vegetables, it tells you to fix your damn robots.txt.

---

## 🎯 What Does It Do?

Imagine if Google Search Console, Lighthouse, and a very opinionated SEO consultant had a baby. That's this tool.

It crawls your website like a caffeinated spider and generates a report so detailed, you'll wonder why you even asked. Features include:

- ✅ **Technical SEO Audit** - Checks robots.txt, sitemaps, canonicals, and all the boring stuff that actually matters
- 🚀 **Core Web Vitals** - Measures LCP, INP, CLS (a.k.a. "why is my site so slow?")
- 📱 **Mobile-Friendliness** - Because 70% of your traffic is from people on the toilet
- 🔒 **Security Checks** - HTTPS validation, because it's 2025 and we're not savages
- 🧠 **AI-Ready Analysis** - Optimizes for AI Overviews (yes, that's a thing now)
- 🎨 **Accessibility** - Makes sure everyone can use your site, not just people with perfect vision
- 📊 **Pretty Reports** - JSON, CSV, PDF — pick your poison
- 🔥 **Issue Prioritization** - Tells you what to fix first (hint: it's probably the broken links)

---

## 🚀 Quick Start

### Installation

```
# Clone this bad boy
git clone https://github.com/yourusername/py-seo-auditor.git
cd py-seo-auditor

# Install dependencies
pip install -r requirements.txt

# Or if you're fancy
poetry install
```

### Basic Usage

```
# Audit a single URL
python -m seo_auditor audit https://example.com

# Full site crawl (grab coffee, this might take a while)
python -m seo_auditor crawl https://example.com --depth 3

# Generate a pretty report
python -m seo_auditor report https://example.com --format pdf
```

### Configuration

Create a `config.yaml` file:

```
user_agent: "py-seo-auditor/1.0 (Because robots need names too)"
max_pages: 1000
timeout: 30
lighthouse_api_key: "your-key-here"  # Optional but recommended
```

---

## 📈 What Gets Checked?

### Technical SEO (The Nerdy Stuff)
- Robots.txt validation
- XML sitemap structure
- Canonical tags
- Meta robots tags
- Redirect chains (301/302)
- Broken links (404s)
- Orphan pages
- URL structure
- Hreflang tags

### On-Page SEO (The Content Stuff)
- Title tags (50-60 chars or bust)
- Meta descriptions (150-160 chars, be concise)
- H1-H6 hierarchy
- Image alt text
- Schema.org markup
- Open Graph tags
- Content length
- Keyword density

### Performance (The Speed Stuff)
- Core Web Vitals
  - Largest Contentful Paint (LCP) < 2.5s
  - Interaction to Next Paint (INP) < 200ms
  - Cumulative Layout Shift (CLS) < 0.1
- Page load time
- Resource optimization
- Image compression
- CDN usage

### Modern SEO (The 2025 Stuff)
- AI Overview optimization
- E-E-A-T signals
- Featured snippet readiness
- Voice search optimization
- Entity recognition

---

## 📊 Sample Report

```
╔══════════════════════════════════════════╗
║     SEO AUDIT REPORT: example.com       ║
╚══════════════════════════════════════════╝

🎯 Overall Score: 73/100 (Not bad, but we can do better)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 CRITICAL ISSUES (Fix these NOW!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ Missing XML sitemap
❌ 23 broken links found
❌ No HTTPS on 12 pages

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🟡 HIGH PRIORITY (Do these next)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  15 pages missing meta descriptions
⚠️  LCP score: 3.2s (target: <2.5s)
⚠️  8 images without alt text

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 PERFORMANCE METRICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Desktop:  72/100 ⭐⭐⭐
Mobile:   58/100 ⭐⭐
```

---

## 🤖 AI Integration

Want to integrate with your existing workflow? We got you.

```
from seo_auditor import SEOAuditor

auditor = SEOAuditor()
results = auditor.audit("https://example.com")

# Get actionable insights
for issue in results.critical_issues:
    print(f"Fix this: {issue.title}")
    print(f"Why: {issue.description}")
    print(f"How: {issue.fix_guide}")
```

---

## 🛠️ Advanced Features

### Lighthouse Integration

```
# Requires Google Lighthouse API key
python -m seo_auditor audit https://example.com \
  --lighthouse \
  --device mobile
```

### Competitive Analysis

```
# Compare against competitors
python -m seo_auditor compare \
  https://yoursite.com \
  https://competitor1.com \
  https://competitor2.com
```

### Historical Tracking

```
# Track improvements over time
python -m seo_auditor track https://example.com --interval weekly
```

---

## 📚 Documentation

Check out the [full documentation](docs/README.md) for:
- Configuration options
- Custom checks
- API reference
- Extending the auditor
- Report customization

---

## 🤝 Contributing

Found a bug? Have a feature idea? PRs are welcome!

1. Fork it
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -am 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 🐛 Known Issues

- Occasionally mistakes "loading" for "thinking deeply about your life choices"
- May judge your CSS choices (working on it)
- Can't fix existential dread (yet)

---

## 📜 License

MIT License - Because sharing is caring.

---

## ☕ Buy Me a Coffee

If this tool saved you from page 2 of Google, consider [buying me a coffee](https://www.buymeacoffee.com/yourusername). ☕

---

## 💬 Testimonials

> "This tool roasted my website harder than my code reviews." - Anonymous Developer

> "Finally, someone who tells me the truth about my SEO." - Frustrated Marketer

> "10/10 would audit again." - Someone's Website

---

Made with 🔍 and excessive amounts of caffeine by [Your Name](https://github.com/yourusername)

**Remember:** Good SEO is like good code — it should be clean, efficient, and not make people want to cry.
```

***

This README combines technical accuracy with personality—perfect for attracting both users and contributors! 🎯✨
