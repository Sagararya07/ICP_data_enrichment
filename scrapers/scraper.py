import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from utils.logger import logger
from utils.helpers import normalize_url
from config import config


class AsyncScraper:
    def __init__(self):
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=25)  # Increased timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=self.timeout,
            connector=aiohttp.TCPConnector(limit=config.MAX_CONCURRENT_REQUESTS, ssl=False)  # Ignore SSL errors
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    # FIX: retry now wraps the actual network call, and only transient errors
    # (timeouts / connection errors) are retried. Exceptions are allowed to
    # propagate out of this inner method so tenacity can see and retry them -
    # the original code caught everything internally, which meant tenacity
    # never saw a failure to retry on.
    @retry(
        stop=stop_after_attempt(config.RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((asyncio.TimeoutError, aiohttp.ClientError)),
        reraise=True,
    )
    async def _get(self, url):
        async with self.session.get(url, allow_redirects=True) as response:
            if response.status == 200:
                return await response.text()
            logger.warning(f"Failed to fetch {url}: Status {response.status}")
            return None

    async def fetch_page(self, url):
        """Fetch a single webpage, retrying transient failures, returning None otherwise."""
        url = normalize_url(url)
        if not url:
            return None

        # First attempt (usually https://)
        try:
            html = await self._get(url)
            if html: return html
        except (asyncio.TimeoutError, aiohttp.ClientError) as e:
            logger.warning(f"Primary fetch failed for {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {str(e)}")

        # Fallback to http:// if it was https://
        if url.startswith('https://'):
            fallback_url = url.replace('https://', 'http://', 1)
            try:
                html = await self._get(fallback_url)
                if html: return html
            except Exception as e:
                logger.warning(f"Fallback fetch failed for {fallback_url}: {e}")
                
        return None

    def parse_html(self, html, url):
        """Parse HTML content and extract all relevant data"""
        if not html:
            return {}

        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else ''

        # Extract meta description
        meta_desc = ''
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag and meta_tag.get('content'):
            meta_desc = meta_tag['content'].strip()

        # Extract all text
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        full_text = ' '.join(chunk for chunk in chunks if chunk)

        # Extract headings
        headings = [h.get_text().strip() for h in soup.find_all(['h1', 'h2', 'h3'])]

        # Extract links
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') or href.startswith('/'):
                links.append(href)

        # Detect blog presence
        has_blog = any(keyword in full_text.lower() for keyword in ['/blog', '/news', '/insights'])

        # Detect careers page
        has_careers = any(keyword in full_text.lower() for keyword in ['/careers', '/jobs', '/join-us'])

        # Detect pricing page
        has_pricing = any(keyword in full_text.lower() for keyword in ['/pricing', '/plans', '/packages'])

        # Detect social media links
        social_links = []
        for link in links:
            if 'linkedin.com' in link:
                social_links.append('linkedin')
            elif 'facebook.com' in link:
                social_links.append('facebook')
            elif 'instagram.com' in link:
                social_links.append('instagram')
            elif 'twitter.com' in link or 'x.com' in link:
                social_links.append('twitter')
            elif 'youtube.com' in link:
                social_links.append('youtube')

        social_links = list(set(social_links))

        # Detect ad tracking
        html_lower = str(soup).lower()
        has_ads = any(keyword in html_lower for keyword in [
            'googletagmanager', 'googleadservices', 'facebook.com/tr',
            'googleads', 'adwords', 'analytics.js', 'gtag'
        ])
        
        # Extract Emails
        emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        valid_emails = [e for e in set(emails) if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.css', '.js')) and 'example' not in e.lower()]
        
        # Extract Phones (primarily from tel: links for accuracy)
        phones = []
        for a in soup.find_all('a', href=True):
            if a['href'].startswith('tel:'):
                phones.append(a['href'].replace('tel:', '').strip())
        phones = list(set(phones))

        return {
            'url': url,
            'title': title,
            'meta_description': meta_desc,
            'text': full_text[:50000],  # Limit to first 50K chars
            'headings': headings,
            'has_blog': has_blog,
            'has_careers': has_careers,
            'has_pricing': has_pricing,
            'social_links': social_links,
            'has_ads': has_ads,
            'link_count': len(links),
            'emails': valid_emails,
            'phones': phones
        }

    async def scrape_company(self, url):
        """Complete scrape workflow for a single company"""
        html = await self.fetch_page(url)
        if html:
            return self.parse_html(html, url)
        return {}

    async def scrape_batch(self, urls):
        """Scrape multiple websites in parallel"""
        tasks = [self.scrape_company(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        scraped_data = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing {urls[i]}: {str(result)}")
                scraped_data.append({'error': str(result)})
            else:
                scraped_data.append(result)

        return scraped_data
