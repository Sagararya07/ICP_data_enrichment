import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'lumora_icp')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

    # Scraping Configuration
    MAX_CONCURRENT_REQUESTS = 100
    REQUEST_TIMEOUT = 15
    RETRY_ATTEMPTS = 3
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '500'))
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    # Industry Keywords
    INDUSTRY_PATTERNS = {
        'B2B_SaaS': ['saas', 'software as a service', 'subscription', 'cloud', 'platform', 'enterprise', 'api'],
        'Healthcare': ['health', 'medical', 'patient', 'clinic', 'doctor', 'hospital', 'pharma', 'wellness'],
        'Real_Estate': ['property', 'real estate', 'home', 'land', 'apartment', 'builder', 'developer'],
        'Retail': ['shop', 'store', 'retail', 'product', 'e-commerce', 'brand', 'consumer'],
        'Education': ['education', 'learning', 'course', 'student', 'training', 'academy', 'school'],
        'IT_Services': ['it services', 'consulting', 'implementation', 'enterprise it', 'managed services'],
        'Manufacturing': ['manufacturing', 'factory', 'production', 'supply', 'industrial', 'plant'],
        'Fintech': ['finance', 'banking', 'payment', 'investment', 'wealth', 'insurance', 'fintech']
    }

    # Business Model Keywords
    BUSINESS_MODEL_PATTERNS = {
        'B2B': ['b2b', 'business', 'enterprise', 'corporate', 'for companies', 'wholesale'],
        'B2C': ['b2c', 'consumer', 'individual', 'personal', 'for customers', 'retail'],
        'SaaS': ['saas', 'subscription', 'cloud', 'platform', 'software as a service'],
        'Services': ['services', 'consulting', 'solutions', 'advisory', 'professional services'],
        'Product': ['product', 'goods', 'merchandise', 'manufacturing', 'hardware']
    }

    # Customer Value Benchmarks by Industry (fallback when no pricing is found)
    CUSTOMER_VALUE_BENCHMARKS = {
        'B2B_SaaS': 25000,
        'Healthcare': 15000,
        'Real_Estate': 50000,
        'Retail': 5000,
        'Education': 10000,
        'IT_Services': 35000,
        'Manufacturing': 45000,
        'Fintech': 30000
    }

    # Growth Signal Keywords
    GROWTH_SIGNALS = {
        'hiring': ['hiring', "we're hiring", 'careers', 'join our team', 'open positions', 'job opening'],
        'funding': ['raised', 'funding', 'series', 'investment', 'seed', 'venture', 'backed'],
        'expansion': ['expand', 'expansion', 'new market', 'global', 'international', 'new location'],
        'new_product': ['launching', 'launched', 'new product', 'introducing', 'announcing', 'coming soon']
    }

    # Marketing Activity Keywords
    MARKETING_KEYWORDS = {
        'blog': ['blog', 'news', 'insights', 'articles', 'resources'],
        'ads': ['google ads', 'adwords', 'facebook ads', 'fb ads', 'display ads'],
        'social': ['linkedin', 'facebook', 'instagram', 'twitter', 'youtube']
    }


config = Config()
