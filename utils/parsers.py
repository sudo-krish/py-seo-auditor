"""
HTML/XML parsing utilities for SEO Auditor
Extracts SEO-related data from web pages including meta tags, headers, links, and structured data
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
from collections import Counter

from bs4 import BeautifulSoup, Comment
from lxml import html, etree
import extruct

logger = logging.getLogger(__name__)


class HTMLParser:
    """
    Main HTML parser for extracting SEO elements
    """

    def __init__(self, html_content: str, base_url: str):
        """
        Initialize HTML parser

        Args:
            html_content: Raw HTML content
            base_url: Base URL for resolving relative URLs
        """
        self.html_content = html_content
        self.base_url = base_url

        # Initialize parsers
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.tree = html.fromstring(html_content)

        logger.debug(f"Initialized parser for {base_url}")

    def get_title(self) -> Optional[str]:
        """
        Extract page title

        Returns:
            Page title or None
        """
        title_tag = self.soup.find('title')
        return title_tag.get_text().strip() if title_tag else None

    def get_meta_tags(self) -> Dict[str, str]:
        """
        Extract all meta tags

        Returns:
            Dictionary of meta tag names/properties to content
        """
        meta_tags = {}

        for meta in self.soup.find_all('meta'):
            # Standard meta tags (name attribute)
            name = meta.get('name', '').lower()
            if name:
                meta_tags[name] = meta.get('content', '')

            # Open Graph and other property-based meta tags
            prop = meta.get('property', '').lower()
            if prop:
                meta_tags[prop] = meta.get('content', '')

            # HTTP-equiv meta tags
            http_equiv = meta.get('http-equiv', '').lower()
            if http_equiv:
                meta_tags[f"http-equiv:{http_equiv}"] = meta.get('content', '')

        return meta_tags

    def get_meta_description(self) -> Optional[str]:
        """Extract meta description"""
        meta = self.soup.find('meta', attrs={'name': 'description'})
        return meta.get('content', '').strip() if meta else None

    def get_meta_keywords(self) -> Optional[str]:
        """Extract meta keywords"""
        meta = self.soup.find('meta', attrs={'name': 'keywords'})
        return meta.get('content', '').strip() if meta else None

    def get_meta_robots(self) -> Optional[str]:
        """Extract meta robots directives"""
        meta = self.soup.find('meta', attrs={'name': 'robots'})
        return meta.get('content', '').strip() if meta else None

    def get_canonical_url(self) -> Optional[str]:
        """
        Extract canonical URL

        Returns:
            Canonical URL or None
        """
        link = self.soup.find('link', attrs={'rel': 'canonical'})
        if link and link.get('href'):
            return urljoin(self.base_url, link['href'])
        return None

    def get_headers(self) -> Dict[str, List[str]]:
        """
        Extract all heading tags (H1-H6)

        Returns:
            Dictionary mapping header levels to list of text content
        """
        headers = {f'h{i}': [] for i in range(1, 7)}

        for level in range(1, 7):
            for tag in self.soup.find_all(f'h{level}'):
                text = tag.get_text().strip()
                if text:
                    headers[f'h{level}'].append(text)

        return headers

    def get_h1_tags(self) -> List[str]:
        """Extract all H1 tags"""
        return [h1.get_text().strip() for h1 in self.soup.find_all('h1')]

    def get_images(self) -> List[Dict[str, Any]]:
        """
        Extract all images with attributes

        Returns:
            List of dictionaries containing image data
        """
        images = []

        for img in self.soup.find_all('img'):
            image_data = {
                'src': urljoin(self.base_url, img.get('src', '')),
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', ''),
                'loading': img.get('loading', ''),
                'has_alt': bool(img.get('alt'))
            }
            images.append(image_data)

        return images

    def get_links(self, internal_only: bool = False) -> List[Dict[str, Any]]:
        """
        Extract all links

        Args:
            internal_only: Only return internal links

        Returns:
            List of dictionaries containing link data
        """
        links = []
        base_domain = urlparse(self.base_url).netloc

        for link in self.soup.find_all('a', href=True):
            href = link.get('href', '')
            absolute_url = urljoin(self.base_url, href)
            link_domain = urlparse(absolute_url).netloc

            is_internal = link_domain == base_domain or link_domain == ''

            if internal_only and not is_internal:
                continue

            link_data = {
                'href': absolute_url,
                'text': link.get_text().strip(),
                'title': link.get('title', ''),
                'rel': link.get('rel', []),
                'is_internal': is_internal,
                'is_nofollow': 'nofollow' in link.get('rel', []),
                'target': link.get('target', '')
            }
            links.append(link_data)

        return links

    def get_internal_links(self) -> List[Dict[str, Any]]:
        """Get only internal links"""
        return self.get_links(internal_only=True)

    def get_external_links(self) -> List[Dict[str, Any]]:
        """Get only external links"""
        all_links = self.get_links(internal_only=False)
        return [link for link in all_links if not link['is_internal']]

    def get_structured_data(self) -> List[Dict[str, Any]]:
        """
        Extract JSON-LD structured data

        Returns:
            List of structured data objects
        """
        structured_data = []

        # Find all script tags with type application/ld+json
        for script in self.soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                structured_data.append(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON-LD: {e}")

        return structured_data

    def get_open_graph_tags(self) -> Dict[str, str]:
        """
        Extract Open Graph meta tags

        Returns:
            Dictionary of OG properties
        """
        og_tags = {}

        for meta in self.soup.find_all('meta', property=re.compile('^og:')):
            prop = meta.get('property', '').replace('og:', '')
            content = meta.get('content', '')
            og_tags[prop] = content

        return og_tags

    def get_twitter_card_tags(self) -> Dict[str, str]:
        """
        Extract Twitter Card meta tags

        Returns:
            Dictionary of Twitter Card properties
        """
        twitter_tags = {}

        for meta in self.soup.find_all('meta', attrs={'name': re.compile('^twitter:')}):
            name = meta.get('name', '').replace('twitter:', '')
            content = meta.get('content', '')
            twitter_tags[name] = content

        return twitter_tags

    def get_hreflang_tags(self) -> List[Dict[str, str]]:
        """
        Extract hreflang alternate links

        Returns:
            List of hreflang data
        """
        hreflang_links = []

        for link in self.soup.find_all('link', rel='alternate', hreflang=True):
            hreflang_links.append({
                'hreflang': link.get('hreflang', ''),
                'href': urljoin(self.base_url, link.get('href', ''))
            })

        return hreflang_links

    def get_word_count(self) -> int:
        """
        Calculate word count of visible text

        Returns:
            Word count
        """
        # Remove script and style elements
        for script in self.soup(['script', 'style', 'nav', 'header', 'footer']):
            script.decompose()

        text = self.soup.get_text()
        words = text.split()
        return len(words)

    def get_text_content(self) -> str:
        """
        Extract visible text content

        Returns:
            Cleaned text content
        """
        # Remove unwanted elements
        for element in self.soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()

        # Get text and clean up
        text = self.soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text

    def get_lang_attribute(self) -> Optional[str]:
        """Extract HTML lang attribute"""
        html_tag = self.soup.find('html')
        return html_tag.get('lang') if html_tag else None

    def get_viewport_meta(self) -> Optional[str]:
        """Extract viewport meta tag"""
        meta = self.soup.find('meta', attrs={'name': 'viewport'})
        return meta.get('content') if meta else None

    def get_charset(self) -> Optional[str]:
        """Extract character encoding"""
        # HTML5 charset
        meta = self.soup.find('meta', charset=True)
        if meta:
            return meta.get('charset')

        # HTML4 charset
        meta = self.soup.find('meta', attrs={'http-equiv': 'Content-Type'})
        if meta:
            content = meta.get('content', '')
            match = re.search(r'charset=([^;]+)', content)
            if match:
                return match.group(1)

        return None

    def has_amp_version(self) -> bool:
        """Check if page has AMP version"""
        amp_link = self.soup.find('link', rel='amphtml')
        return amp_link is not None

    def get_schema_types(self) -> List[str]:
        """
        Extract schema.org types from structured data

        Returns:
            List of schema types
        """
        types = []
        structured_data = self.get_structured_data()

        for data in structured_data:
            if isinstance(data, dict) and '@type' in data:
                schema_type = data['@type']
                if isinstance(schema_type, list):
                    types.extend(schema_type)
                else:
                    types.append(schema_type)

        return types

    def check_noindex(self) -> bool:
        """
        Check if page has noindex directive

        Returns:
            True if noindex is present
        """
        robots_meta = self.get_meta_robots()
        if robots_meta and 'noindex' in robots_meta.lower():
            return True

        # Check X-Robots-Tag (not in meta but documented)
        return False

    def get_favicon_url(self) -> Optional[str]:
        """Extract favicon URL"""
        # Try standard favicon link
        icon = self.soup.find('link', rel=lambda x: x and 'icon' in x.lower())
        if icon and icon.get('href'):
            return urljoin(self.base_url, icon['href'])

        # Fallback to default
        return urljoin(self.base_url, '/favicon.ico')


class XMLParser:
    """
    XML parser for sitemaps and RSS feeds
    """

    def __init__(self, xml_content: str):
        """
        Initialize XML parser

        Args:
            xml_content: Raw XML content
        """
        self.xml_content = xml_content
        self.tree = etree.fromstring(xml_content.encode('utf-8'))

    def parse_sitemap(self) -> List[Dict[str, Any]]:
        """
        Parse XML sitemap

        Returns:
            List of URLs with metadata
        """
        urls = []

        # Define namespaces
        namespaces = {
            'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9',
            'image': 'http://www.google.com/schemas/sitemap-image/1.1',
            'news': 'http://www.google.com/schemas/sitemap-news/0.9'
        }

        # Extract URLs
        for url_element in self.tree.xpath('//sm:url', namespaces=namespaces):
            url_data = {
                'loc': self._get_text(url_element, 'sm:loc', namespaces),
                'lastmod': self._get_text(url_element, 'sm:lastmod', namespaces),
                'changefreq': self._get_text(url_element, 'sm:changefreq', namespaces),
                'priority': self._get_text(url_element, 'sm:priority', namespaces)
            }
            urls.append(url_data)

        return urls

    def parse_sitemap_index(self) -> List[str]:
        """
        Parse sitemap index file

        Returns:
            List of sitemap URLs
        """
        namespaces = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        sitemaps = []

        for sitemap in self.tree.xpath('//sm:sitemap', namespaces=namespaces):
            loc = self._get_text(sitemap, 'sm:loc', namespaces)
            if loc:
                sitemaps.append(loc)

        return sitemaps

    def _get_text(self, element, xpath: str, namespaces: Dict) -> Optional[str]:
        """Helper to get text from xpath"""
        result = element.xpath(xpath, namespaces=namespaces)
        return result[0].text if result else None


class RobotsParser:
    """
    Parser for robots.txt files
    """

    def __init__(self, robots_content: str):
        """
        Initialize robots.txt parser

        Args:
            robots_content: Raw robots.txt content
        """
        self.content = robots_content
        self.rules = self._parse_rules()

    def _parse_rules(self) -> Dict[str, List[str]]:
        """Parse robots.txt into rules"""
        rules = {
            'user_agents': [],
            'disallow': [],
            'allow': [],
            'sitemaps': [],
            'crawl_delay': None
        }

        current_agent = None

        for line in self.content.splitlines():
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Parse directive
            if ':' in line:
                directive, value = line.split(':', 1)
                directive = directive.strip().lower()
                value = value.strip()

                if directive == 'user-agent':
                    current_agent = value
                    rules['user_agents'].append(value)
                elif directive == 'disallow':
                    rules['disallow'].append(value)
                elif directive == 'allow':
                    rules['allow'].append(value)
                elif directive == 'sitemap':
                    rules['sitemaps'].append(value)
                elif directive == 'crawl-delay':
                    rules['crawl_delay'] = float(value)

        return rules

    def get_sitemaps(self) -> List[str]:
        """Get sitemap URLs from robots.txt"""
        return self.rules['sitemaps']

    def is_allowed(self, user_agent: str, path: str) -> bool:
        """
        Check if path is allowed for user agent

        Args:
            user_agent: User agent string
            path: URL path to check

        Returns:
            True if allowed
        """
        # Simplified check - for production use urllib.robotparser
        disallowed = any(path.startswith(rule) for rule in self.rules['disallow'] if rule)
        return not disallowed


class StructuredDataExtractor:
    """
    Extract and validate structured data using extruct
    """

    def __init__(self, html_content: str, base_url: str):
        """
        Initialize structured data extractor

        Args:
            html_content: Raw HTML content
            base_url: Base URL for context
        """
        self.html_content = html_content
        self.base_url = base_url

    def extract_all(self) -> Dict[str, Any]:
        """
        Extract all structured data formats

        Returns:
            Dictionary containing all structured data
        """
        try:
            data = extruct.extract(
                self.html_content,
                base_url=self.base_url,
                syntaxes=['json-ld', 'microdata', 'opengraph', 'rdfa']
            )
            return data
        except Exception as e:
            logger.error(f"Error extracting structured data: {e}")
            return {}

    def get_json_ld(self) -> List[Dict]:
        """Extract only JSON-LD data"""
        data = self.extract_all()
        return data.get('json-ld', [])

    def get_microdata(self) -> List[Dict]:
        """Extract only microdata"""
        data = self.extract_all()
        return data.get('microdata', [])

    def get_open_graph(self) -> Dict:
        """Extract Open Graph data"""
        data = self.extract_all()
        og_list = data.get('opengraph', [])
        return og_list[0] if og_list else {}


def analyze_keyword_density(text: str, top_n: int = 10) -> Dict[str, float]:
    """
    Analyze keyword density in text

    Args:
        text: Text content to analyze
        top_n: Number of top keywords to return

    Returns:
        Dictionary of keywords to density percentage
    """
    # Clean and tokenize
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())

    # Count words
    total_words = len(words)
    if total_words == 0:
        return {}

    # Get word frequency
    word_counts = Counter(words)

    # Calculate density for top words
    keyword_density = {}
    for word, count in word_counts.most_common(top_n):
        density = (count / total_words) * 100
        keyword_density[word] = round(density, 2)

    return keyword_density
