import re
from config import config
from utils.helpers import safe_float


class AIAnalyzer:
    def __init__(self):
        self.industry_patterns = config.INDUSTRY_PATTERNS
        self.business_model_patterns = config.BUSINESS_MODEL_PATTERNS
        self.customer_benchmarks = config.CUSTOMER_VALUE_BENCHMARKS
        self.growth_keywords = config.GROWTH_SIGNALS
        self.marketing_keywords = config.MARKETING_KEYWORDS

        # FIX: patterns are now grouped by the unit they actually matched
        # (monthly vs yearly vs unspecified), instead of being lumped into one
        # list and having the monthly/yearly decision made once for the whole
        # page. A page that mentions "$99/month" and, elsewhere, "annual
        # report" no longer gets the monthly price annualized incorrectly.
        self._monthly_patterns = [
            r'(?:₹|rs\.?|inr)\s*(\d+[\.,]?\d*)\s*per\s*(?:month|monthly)',
            r'(?:₹|rs\.?|inr)\s*(\d+[\.,]?\d*)\s*\/\s*month',
        ]
        self._yearly_patterns = [
            r'(?:₹|rs\.?|inr)\s*(\d+[\.,]?\d*)\s*per\s*(?:year|annually|yearly)',
            r'(?:₹|rs\.?|inr)\s*(\d+[\.,]?\d*)\s*\/\s*year',
        ]
        self._unspecified_patterns = [
            r'starting\s*at\s*(?:₹|rs\.?|inr)\s*(\d+[\.,]?\d*)',
            r'prices?\s*start\s*at\s*(?:₹|rs\.?|inr)\s*(\d+[\.,]?\d*)',
        ]

    def detect_industry(self, text):
        """Detect industry from text content"""
        if not text:
            return 'Unknown', 0

        text_lower = text.lower()
        scores = {}

        for industry, keywords in self.industry_patterns.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            scores[industry] = score

        if scores:
            best_industry = max(scores, key=scores.get)
            max_score = scores[best_industry]
            if max_score >= 3:
                return best_industry, max_score
            else:
                return 'Other', max_score
        return 'Unknown', 0

    def detect_business_model(self, text):
        """Detect business model from text content"""
        if not text:
            return 'Unknown', 0

        text_lower = text.lower()
        scores = {}

        for model, keywords in self.business_model_patterns.items():
            score = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            scores[model] = score

        if not scores:
            return 'Unknown', 0

        primary = max(scores, key=scores.get)
        max_score = scores[primary]

        if max_score == 0:
            return 'Unknown', 0

        if scores.get('B2B', 0) > 0 and scores.get('B2C', 0) > 0:
            return 'Hybrid', max_score

        return primary, max_score

    def estimate_customer_value(self, text, industry, scraped_data):
        """Estimate customer annual value from pricing mentioned on the page,
        falling back to an industry benchmark when no price is found."""
        if not text:
            return self.customer_benchmarks.get(industry, 15000)

        text_lower = text.lower()
        yearly_values = []

        for pattern in self._monthly_patterns:
            for match in re.findall(pattern, text_lower):
                price = safe_float(match)
                if price is not None:
                    yearly_values.append(price * 12)

        for pattern in self._yearly_patterns:
            for match in re.findall(pattern, text_lower):
                price = safe_float(match)
                if price is not None:
                    yearly_values.append(price)

        for pattern in self._unspecified_patterns:
            for match in re.findall(pattern, text_lower):
                price = safe_float(match)
                if price is not None:
                    yearly_values.append(price)

        if yearly_values:
            return round(sum(yearly_values) / len(yearly_values), 2)

        return self.customer_benchmarks.get(industry, 15000)

    def detect_growth_signals(self, text, scraped_data):
        """Detect growth signals from content"""
        if not text:
            return {'hiring': False, 'funding': False, 'expansion': False,
                     'new_product': False, 'marketing_jobs': False}

        text_lower = text.lower()
        signals = {}

        for signal_name, keywords in self.growth_keywords.items():
            signals[signal_name] = any(keyword in text_lower for keyword in keywords)

        signals['marketing_jobs'] = bool(
            scraped_data.get('has_careers') and
            ('marketing' in text_lower or 'growth' in text_lower)
        )

        return signals

    def detect_marketing_activity(self, text, scraped_data):
        """Detect current marketing activities"""
        if not text:
            return {'seo': False, 'paid_ads': False, 'social': False, 'email': False, 'content': False}

        text_lower = text.lower()

        return {
            'seo': scraped_data.get('has_blog', False),
            'paid_ads': scraped_data.get('has_ads', False),
            'social': len(scraped_data.get('social_links', [])) > 0,
            'email': 'newsletter' in text_lower or 'subscribe' in text_lower,
            'content': scraped_data.get('has_blog', False) or 'whitepaper' in text_lower,
        }

    def assess_marketing_maturity(self, activities):
        """Assess overall marketing maturity level"""
        score = 0
        score += 25 if activities.get('seo') else 0
        score += 30 if activities.get('paid_ads') else 0
        score += 20 if activities.get('social') else 0
        score += 15 if activities.get('email') else 0
        score += 10 if activities.get('content') else 0

        if score >= 70:
            return 'High'
        elif score >= 40:
            return 'Medium'
        return 'Low'

    def calculate_icp_fit(self, business_model, customer_value, growth_signals, marketing_maturity, employees=0, revenue=0):
        """Calculate a 0-100 score indicating if this company is a strong fit for a marketing agency"""
        
        # Override for Eligible Company
        if employees and revenue and employees >= 20 and revenue >= 3500000:
            return 100, 'Eligible Company'
            
        score = 0
        
        # 1. Business Model (No points awarded per user request)
        # We still keep the parameter for backwards compatibility, but it awards 0 points.
            
        # 2. Customer Value (Max 35 points) - Scaled for INR
        if customer_value > 2500000:
            score += 35
        elif customer_value > 1000000:
            score += 20
        elif customer_value > 100000:
            score += 10
            
        # 3. Growth Signals (Max 45 points)
        if growth_signals.get('hiring'): score += 10
        if growth_signals.get('funding'): score += 15
        if growth_signals.get('expansion'): score += 10
        if growth_signals.get('marketing_jobs'): score += 10
            
        # 4. Marketing Maturity (Max 20 points)
        if marketing_maturity == 'Low':
            score += 20
        elif marketing_maturity == 'Medium':
            score += 10
            
        # Cap at 100
        score = min(100, score)
        
        if score >= 70:
            status = 'Strong Fit'
        elif score >= 40:
            status = 'Potential Fit'
        else:
            status = 'Not a Fit'
            
        return score, status

    def analyze_company(self, scraped_data, company_data=None):
        """Complete analysis pipeline for a single company"""
        if not scraped_data or 'error' in scraped_data:
            return {
                'error': scraped_data.get('error', 'No data') if scraped_data else 'No data',
                'industry': 'Unknown',
                'business_model': 'Unknown',
                'customer_value': 0,
                'growth_signals': {},
                'marketing_activity': {},
                'marketing_maturity': 'Unknown',
                'icp_fit_score': 0,
                'icp_status': 'Unknown'
            }

        text = scraped_data.get('text', '')
        title = scraped_data.get('title', '')
        meta_desc = scraped_data.get('meta_description', '')

        full_text = f"{title} {meta_desc} {text}"

        industry, industry_score = self.detect_industry(full_text)
        business_model, model_score = self.detect_business_model(full_text)
        customer_value = self.estimate_customer_value(full_text, industry, scraped_data)
        growth_signals = self.detect_growth_signals(full_text, scraped_data)
        marketing_activity = self.detect_marketing_activity(full_text, scraped_data)
        marketing_maturity = self.assess_marketing_maturity(marketing_activity)
        
        employees = company_data.get('employees', 0) if company_data else 0
        revenue = company_data.get('revenue', 0) if company_data else 0
        
        icp_fit_score, icp_status = self.calculate_icp_fit(
            business_model, customer_value, growth_signals, marketing_maturity, employees, revenue
        )

        return {
            'industry': industry,
            'industry_score': industry_score,
            'business_model': business_model,
            'model_score': model_score,
            'customer_value': customer_value,
            'growth_signals': growth_signals,
            'marketing_activity': marketing_activity,
            'marketing_maturity': marketing_maturity,
            'icp_fit_score': icp_fit_score,
            'icp_status': icp_status,
            'emails': scraped_data.get('emails', []),
            'phones': scraped_data.get('phones', [])
        }
