"""Small, dependency-free utility functions shared across the pipeline."""

import re


def normalize_url(url):
    """Ensure a URL has a scheme; return None for empty/placeholder values."""
    if not url or str(url).strip().lower() in ('na', 'unknown', ''):
        return None
    url = str(url).strip()
    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'
    return url


def clean_text(text, max_len=None):
    """Collapse whitespace in scraped text; optionally truncate."""
    if not text:
        return ''
    cleaned = re.sub(r'\s+', ' ', text).strip()
    if max_len:
        cleaned = cleaned[:max_len]
    return cleaned


def chunked(iterable, size):
    """Yield successive chunks of `size` from a list-like iterable."""
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def safe_float(value, default=None):
    """Parse a string like '1,234.50' into a float, or return `default`."""
    try:
        return float(str(value).replace(',', '').strip())
    except (TypeError, ValueError):
        return default
