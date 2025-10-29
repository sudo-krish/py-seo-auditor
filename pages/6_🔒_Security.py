"""
Security page for SEO Auditor
Displays HTTPS implementation, security headers, and website security analysis
"""

import streamlit as st
from datetime import datetime
from pathlib import Path
import sys
import pandas as pd

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from reporting.visualizations import ChartGenerator

# Page configuration
st.set_page_config(
    page_title="SEO Auditor - Security",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)


def display_header():
    """Display page header"""
    st.title("🔒 Security & HTTPS Analysis")
    st.markdown("""
    Website security is crucial for SEO, user trust, and data protection. HTTPS is now a standard requirement, 
    and proper security headers protect against common vulnerabilities while improving search rankings.
    """)
    st.markdown("---")


def display_overview_metrics():
    """Display security overview metrics"""
    if not st.session_state.get('audit_results'):
        st.info("⚠️ No audit data available. Please run an audit first.")
        return

    results = st.session_state.audit_results
    security_data = results.get('security', {})

    if not security_data:
        st.warning("Security data not available in audit results.")
        return

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    score = security_data.get('score', 0)

    with col1:
        st.metric(
            label="Security Score",
            value=f"{score}/100",
            delta=_get_score_status(score),
            help="Overall website security score"
        )

    with col2:
        https_pages = security_data.get('https_pages', 0)
        total_pages = results.get('pages_analyzed', 0)
        https_rate = (https_pages / total_pages * 100) if total_pages > 0 else 0
        st.metric(
            label="HTTPS Coverage",
            value=f"{https_rate:.0f}%",
            help="Percentage of pages served over HTTPS"
        )

    with col3:
        security_headers = security_data.get('security_headers_present', 0)
        total_headers = security_data.get('total_security_headers', 8)
        st.metric(
            label="Security Headers",
            value=f"{security_headers}/{total_headers}",
            help="Number of security headers implemented"
        )

    with col4:
        critical_issues = security_data.get('critical_security_issues', 0)
        st.metric(
            label="Critical Issues",
            value=critical_issues,
            delta=f"-{critical_issues}" if critical_issues > 0 else "None",
            delta_color="inverse",
            help="Critical security vulnerabilities"
        )


def display_https_implementation():
    """Display HTTPS implementation analysis"""
    st.markdown("### 🔐 HTTPS Implementation")

    if not st.session_state.get('audit_results'):
        return

    security_data = st.session_state.audit_results.get('security', {})
    https_data = security_data.get('https', {})

    st.info("""
    **HTTPS is mandatory for SEO in 2025.** Google uses HTTPS as a ranking signal, and browsers 
    display warnings for non-HTTPS sites, especially those with forms.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### HTTPS Status")

        # Check if site is fully HTTPS
        fully_https = https_data.get('fully_https', False)
        http_pages = https_data.get('http_pages', 0)
        https_pages = https_data.get('https_pages', 0)

        if fully_https:
            st.success("✅ Site is fully served over HTTPS")
        elif https_pages > 0 and http_pages > 0:
            st.warning(f"⚠️ Mixed HTTP/HTTPS: {http_pages} pages still on HTTP")
        else:
            st.error("❌ Site is not using HTTPS")

        # HTTP to HTTPS redirects
        st.markdown("#### Redirect Configuration")

        redirect_data = https_data.get('redirects', {})

        has_redirect = redirect_data.get('http_to_https', False)
        redirect_type = redirect_data.get('redirect_type', '')

        if has_redirect and redirect_type == '301':
            st.success("✅ HTTP properly redirects to HTTPS (301)")
        elif has_redirect:
            st.warning(f"⚠️ Using {redirect_type} redirect (should be 301)")
        else:
            st.error("❌ No HTTP to HTTPS redirect configured")

        # HSTS status
        st.markdown("#### HTTP Strict Transport Security (HSTS)")

        hsts_enabled = https_data.get('hsts_enabled', False)
        hsts_max_age = https_data.get('hsts_max_age', 0)

        if hsts_enabled:
            if hsts_max_age >= 31536000:  # 1 year
                st.success(f"✅ HSTS enabled with max-age: {hsts_max_age}s")
            else:
                st.warning(f"⚠️ HSTS max-age too short: {hsts_max_age}s (recommend 1 year)")
        else:
            st.error("❌ HSTS not enabled")

    with col2:
        st.markdown("#### HTTPS Best Practices")
        st.markdown("""
        **2025 Requirements:**

        ✓ Use HTTPS for all pages
        ✓ 301 redirect HTTP to HTTPS
        ✓ Enable HSTS header
        ✓ Use TLS 1.2 or higher
        ✓ Strong cipher suites
        ✓ No mixed content warnings
        ✓ Valid SSL certificate
        ✓ Update all internal links

        **Why HTTPS Matters:**
        - Google ranking signal
        - User trust and confidence
        - Data encryption in transit
        - Browser security indicators
        - Required for HTTP/2
        """)


def display_ssl_certificate():
    """Display SSL certificate analysis"""
    st.markdown("### 📜 SSL/TLS Certificate")

    if not st.session_state.get('audit_results'):
        return

    security_data = st.session_state.audit_results.get('security', {})
    cert_data = security_data.get('ssl_certificate', {})

    tab1, tab2 = st.tabs(["Certificate Status", "Certificate Details"])

    with tab1:
        display_certificate_status(cert_data)

    with tab2:
        display_certificate_details(cert_data)


def display_certificate_status(cert_data):
    """Display SSL certificate validation status"""
    st.markdown("#### Certificate Validation")

    col1, col2 = st.columns(2)

    with col1:
        # Certificate validity
        is_valid = cert_data.get('is_valid', False)
        is_expired = cert_data.get('is_expired', False)
        days_until_expiry = cert_data.get('days_until_expiry', 0)

        if is_valid and not is_expired:
            st.success("✅ Certificate is valid")
            st.metric("Days Until Expiry", days_until_expiry)

            if days_until_expiry < 30:
                st.warning("⚠️ Certificate expires soon - renew immediately")
            elif days_until_expiry < 60:
                st.info("ℹ️ Certificate expires in less than 60 days")
        elif is_expired:
            st.error("❌ Certificate has expired!")
        else:
            st.error("❌ Certificate is not valid")

        # Certificate type
        cert_type = cert_data.get('type', 'Unknown')
        st.markdown(f"**Certificate Type:** {cert_type}")

        if cert_type == 'DV':
            st.info("Domain Validated - Suitable for most websites")
        elif cert_type == 'OV':
            st.success("Organization Validated - Enhanced trust")
        elif cert_type == 'EV':
            st.success("Extended Validation - Highest trust level")

    with col2:
        # Certificate issues
        st.markdown("**Certificate Issues:**")

        issues = cert_data.get('issues', [])

        if not issues:
            st.success("✅ No certificate issues detected")
        else:
            for issue in issues:
                if issue.get('severity') == 'critical':
                    st.error(f"❌ {issue.get('message', '')}")
                elif issue.get('severity') == 'warning':
                    st.warning(f"⚠️ {issue.get('message', '')}")
                else:
                    st.info(f"ℹ️ {issue.get('message', '')}")


def display_certificate_details(cert_data):
    """Display SSL certificate technical details"""
    st.markdown("#### Technical Details")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Certificate Information:**")
        st.markdown(f"- Issuer: {cert_data.get('issuer', 'N/A')}")
        st.markdown(f"- Subject: {cert_data.get('subject', 'N/A')}")
        st.markdown(f"- Valid From: {cert_data.get('valid_from', 'N/A')}")
        st.markdown(f"- Valid Until: {cert_data.get('valid_until', 'N/A')}")
        st.markdown(f"- Serial Number: {cert_data.get('serial_number', 'N/A')}")

    with col2:
        st.markdown("**TLS Configuration:**")

        tls_version = cert_data.get('tls_version', 'Unknown')
        cipher_suite = cert_data.get('cipher_suite', 'Unknown')
        key_size = cert_data.get('key_size', 0)

        st.markdown(f"- TLS Version: {tls_version}")

        if tls_version in ['TLS 1.2', 'TLS 1.3']:
            st.success(f"  ✅ Using modern TLS ({tls_version})")
        else:
            st.error(f"  ❌ Outdated TLS version")

        st.markdown(f"- Key Size: {key_size} bits")

        if key_size >= 2048:
            st.success(f"  ✅ Adequate key size")
        else:
            st.warning(f"  ⚠️ Key size too small (recommend 2048+)")

        st.markdown(f"- Cipher Suite: {cipher_suite}")


def display_mixed_content():
    """Display mixed content analysis"""
    st.markdown("### 🔀 Mixed Content Detection")

    if not st.session_state.get('audit_results'):
        return

    security_data = st.session_state.audit_results.get('security', {})
    mixed_content_data = security_data.get('mixed_content', {})

    st.info("""
    **Mixed content** occurs when HTTPS pages load resources (images, scripts, CSS) over HTTP. 
    This creates security warnings and can block content in modern browsers.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        # Mixed content statistics
        total_mixed = mixed_content_data.get('total_issues', 0)

        if total_mixed == 0:
            st.success("✅ No mixed content detected")
        else:
            st.error(f"❌ {total_mixed} mixed content issues found")

        # Breakdown by type
        st.markdown("#### Mixed Content by Type")

        mixed_by_type = mixed_content_data.get('by_type', {})

        col_a, col_b = st.columns(2)

        with col_a:
            images = mixed_by_type.get('images', 0)
            scripts = mixed_by_type.get('scripts', 0)
            stylesheets = mixed_by_type.get('stylesheets', 0)

            st.metric("Mixed Images", images)
            st.metric("Mixed Scripts", scripts)
            st.metric("Mixed Stylesheets", stylesheets)

        with col_b:
            videos = mixed_by_type.get('videos', 0)
            iframes = mixed_by_type.get('iframes', 0)
            other = mixed_by_type.get('other', 0)

            st.metric("Mixed Videos", videos)
            st.metric("Mixed Iframes", iframes)
            st.metric("Other Resources", other)

        # Pages with mixed content
        problem_pages = mixed_content_data.get('problem_pages', [])
        if problem_pages:
            with st.expander(f"View {len(problem_pages)} Pages with Mixed Content"):
                mixed_df = pd.DataFrame([
                    {
                        'Page': page.get('url', '')[:60],
                        'Mixed Resources': page.get('mixed_count', 0),
                        'Types': ', '.join(page.get('resource_types', []))
                    }
                    for page in problem_pages[:20]
                ])
                st.dataframe(mixed_df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### How to Fix Mixed Content")
        st.markdown("""
        **Quick Fixes:**

        1. Update resource URLs to HTTPS
        2. Use protocol-relative URLs (//example.com/image.jpg)
        3. Use Content Security Policy upgrade-insecure-requests
        4. Check third-party resources
        5. Update hardcoded HTTP links

        **Priority:**
        - 🔴 Scripts & Stylesheets (blocked by browsers)
        - 🟡 Images & Media (warnings)
        - 🟢 Other resources
        """)


def display_security_headers():
    """Display security headers analysis"""
    st.markdown("### 🛡️ Security Headers")

    if not st.session_state.get('audit_results'):
        return

    security_data = st.session_state.audit_results.get('security', {})
    headers_data = security_data.get('security_headers', {})

    st.info("""
    **Security headers** are HTTP response headers that protect against common web vulnerabilities 
    like XSS, clickjacking, and data injection attacks. They're essential for 2025 security standards.
    """)

    # Display each security header
    headers = [
        {
            'name': 'Content-Security-Policy',
            'key': 'csp',
            'description': 'Prevents XSS and code injection attacks',
            'critical': True
        },
        {
            'name': 'Strict-Transport-Security',
            'key': 'hsts',
            'description': 'Forces HTTPS connections',
            'critical': True
        },
        {
            'name': 'X-Frame-Options',
            'key': 'x_frame_options',
            'description': 'Prevents clickjacking attacks',
            'critical': True
        },
        {
            'name': 'X-Content-Type-Options',
            'key': 'x_content_type_options',
            'description': 'Prevents MIME-type sniffing',
            'critical': False
        },
        {
            'name': 'Referrer-Policy',
            'key': 'referrer_policy',
            'description': 'Controls referrer information',
            'critical': False
        },
        {
            'name': 'Permissions-Policy',
            'key': 'permissions_policy',
            'description': 'Controls browser features access',
            'critical': False
        },
        {
            'name': 'X-XSS-Protection',
            'key': 'x_xss_protection',
            'description': 'Legacy XSS protection (deprecated but useful)',
            'critical': False
        },
        {
            'name': 'Cross-Origin-Resource-Policy',
            'key': 'corp',
            'description': 'Controls resource sharing',
            'critical': False
        }
    ]

    for header in headers:
        header_info = headers_data.get(header['key'], {})
        present = header_info.get('present', False)
        value = header_info.get('value', '')

        with st.expander(
                f"{'✅' if present else '❌'} {header['name']} {'🔴' if header['critical'] and not present else ''}",
                expanded=not present and header['critical']):
            st.markdown(f"**Description:** {header['description']}")

            if present:
                st.success(f"✅ Header is present")
                st.code(f"{header['name']}: {value}", language="text")

                # Check for misconfigurations
                issues = header_info.get('issues', [])
                if issues:
                    st.warning("**Configuration Issues:**")
                    for issue in issues:
                        st.markdown(f"- {issue}")
            else:
                st.error(f"❌ Header is not present")

                # Provide recommended configuration
                recommended = header_info.get('recommended', '')
                if recommended:
                    st.markdown("**Recommended Configuration:**")
                    st.code(f"{header['name']}: {recommended}", language="text")


def display_secure_cookies():
    """Display secure cookies analysis"""
    st.markdown("### 🍪 Cookie Security")

    if not st.session_state.get('audit_results'):
        return

    security_data = st.session_state.audit_results.get('security', {})
    cookie_data = security_data.get('cookies', {})

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### Cookie Security Assessment")

        total_cookies = cookie_data.get('total', 0)
        secure_cookies = cookie_data.get('secure', 0)
        httponly_cookies = cookie_data.get('httponly', 0)
        samesite_cookies = cookie_data.get('samesite', 0)

        st.metric("Total Cookies", total_cookies)

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            secure_rate = (secure_cookies / total_cookies * 100) if total_cookies > 0 else 0
            st.metric("Secure Flag", f"{secure_rate:.0f}%")
            if secure_rate < 100:
                st.warning(f"⚠️ {total_cookies - secure_cookies} cookies without Secure flag")

        with col_b:
            httponly_rate = (httponly_cookies / total_cookies * 100) if total_cookies > 0 else 0
            st.metric("HttpOnly Flag", f"{httponly_rate:.0f}%")
            if httponly_rate < 100:
                st.warning(f"⚠️ {total_cookies - httponly_cookies} cookies without HttpOnly")

        with col_c:
            samesite_rate = (samesite_cookies / total_cookies * 100) if total_cookies > 0 else 0
            st.metric("SameSite Attribute", f"{samesite_rate:.0f}%")
            if samesite_rate < 100:
                st.info(f"ℹ️ {total_cookies - samesite_cookies} cookies without SameSite")

        # Insecure cookies list
        insecure_cookies = cookie_data.get('insecure_cookies', [])
        if insecure_cookies:
            with st.expander(f"View {len(insecure_cookies)} Insecure Cookies"):
                for cookie in insecure_cookies[:10]:
                    st.markdown(f"""
                    **{cookie.get('name', 'Unknown')}**  
                    Missing: {', '.join(cookie.get('missing_flags', []))}  
                    Domain: {cookie.get('domain', 'N/A')}
                    """)
                    st.markdown("---")

    with col2:
        st.markdown("#### Cookie Security Best Practices")
        st.markdown("""
        **Essential Attributes (2025):**

        **Secure:** Only transmit over HTTPS
        - Mandatory for production sites
        - Prevents interception over HTTP

        **HttpOnly:** Not accessible via JavaScript
        - Prevents XSS cookie theft
        - Essential for session cookies

        **SameSite:** CSRF protection
        - Strict: Only same-site requests
        - Lax: Some cross-site (default)
        - None: All requests (requires Secure)

        **Example:**
        ```
        Set-Cookie: session=abc123; 
                    Secure; 
                    HttpOnly; 
                    SameSite=Strict
        ```
        """)


def display_vulnerability_scan():
    """Display vulnerability scanning results"""
    st.markdown("### 🔍 Vulnerability Assessment")

    if not st.session_state.get('audit_results'):
        return

    security_data = st.session_state.audit_results.get('security', {})
    vuln_data = security_data.get('vulnerabilities', {})

    st.info("Common web vulnerabilities detected through automated scanning.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Common Vulnerabilities")

        vulnerabilities = {
            "SQL Injection": vuln_data.get('sql_injection', False),
            "Cross-Site Scripting (XSS)": vuln_data.get('xss', False),
            "Cross-Site Request Forgery (CSRF)": vuln_data.get('csrf', False),
            "Insecure Deserialization": vuln_data.get('insecure_deserialization', False),
            "XML External Entities (XXE)": vuln_data.get('xxe', False),
            "Server-Side Request Forgery (SSRF)": vuln_data.get('ssrf', False)
        }

        has_vulnerabilities = any(vulnerabilities.values())

        if not has_vulnerabilities:
            st.success("✅ No common vulnerabilities detected")
        else:
            for vuln, detected in vulnerabilities.items():
                if detected:
                    st.error(f"❌ {vuln} vulnerability detected")
                else:
                    st.success(f"✅ {vuln} - Not detected")

    with col2:
        st.markdown("#### Server Information Disclosure")

        info_disclosure = vuln_data.get('information_disclosure', {})

        server_header = info_disclosure.get('server_header', False)
        x_powered_by = info_disclosure.get('x_powered_by', False)
        directory_listing = info_disclosure.get('directory_listing', False)
        error_messages = info_disclosure.get('verbose_errors', False)

        if server_header:
            st.warning("⚠️ Server header exposes server information")
        if x_powered_by:
            st.warning("⚠️ X-Powered-By header reveals technology stack")
        if directory_listing:
            st.error("❌ Directory listing enabled")
        if error_messages:
            st.warning("⚠️ Verbose error messages detected")

        if not any([server_header, x_powered_by, directory_listing, error_messages]):
            st.success("✅ No information disclosure issues")


def display_recommendations():
    """Display prioritized security recommendations"""
    st.markdown("### 💡 Security Recommendations")

    if not st.session_state.get('audit_results'):
        return

    security_data = st.session_state.audit_results.get('security', {})
    recommendations = security_data.get('recommendations', [])

    if not recommendations:
        st.success("🎉 Your website security is excellent!")
        return

    # Group by priority
    critical = [r for r in recommendations if r.get('priority') == 'critical']
    high_priority = [r for r in recommendations if r.get('priority') == 'high']
    medium_priority = [r for r in recommendations if r.get('priority') == 'medium']

    if critical:
        st.markdown("#### 🔴 Critical (Fix Immediately)")
        for rec in critical:
            with st.expander(f"🚨 {rec.get('title', 'Recommendation')}"):
                st.markdown(rec.get('description', ''))
                st.markdown(f"**Security Risk:** {rec.get('risk', 'High')}")
                st.markdown(f"**Affected:** {rec.get('affected', 'All pages')}")
                if rec.get('solution'):
                    st.markdown(f"**Solution:** {rec.get('solution', '')}")

    if high_priority:
        st.markdown("#### 🟠 High Priority")
        for rec in high_priority[:5]:
            with st.expander(f"✓ {rec.get('title', 'Recommendation')}"):
                st.markdown(rec.get('description', ''))
                st.markdown(f"**Impact:** {rec.get('impact', 'Medium').title()}")

    if medium_priority:
        st.markdown("#### 🟡 Medium Priority")
        for rec in medium_priority[:5]:
            st.markdown(f"- {rec.get('title', 'Recommendation')}")


def _get_score_status(score: float) -> str:
    """Get status text based on score"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Work"


def main():
    """Main function for Security page"""
    display_header()

    # Check if audit data exists
    if not st.session_state.get('audit_results'):
        st.info("👋 No audit data available. Please run an audit from the main page.")
        if st.button("← Go to Main Page", type="primary"):
            st.switch_page("main.py")
        return

    # Display overview metrics
    display_overview_metrics()

    st.markdown("---")

    # Display HTTPS implementation
    display_https_implementation()

    st.markdown("---")

    # Display SSL certificate
    display_ssl_certificate()

    st.markdown("---")

    # Display mixed content
    display_mixed_content()

    st.markdown("---")

    # Display security headers
    display_security_headers()

    st.markdown("---")

    # Display secure cookies
    display_secure_cookies()

    st.markdown("---")

    # Display vulnerability scan
    display_vulnerability_scan()

    st.markdown("---")

    # Display recommendations
    display_recommendations()


if __name__ == "__main__":
    main()
