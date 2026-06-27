import json
import logging
import os
import time
import re
from urllib.parse import urlparse, urljoin
from datetime import datetime

from . import models
from .browser_pool import browser_pool

logger = logging.getLogger(__name__)

HIGH_PRIORITY_URLS = [
    "contact", "contact-us", "reach-us", "enquiry", "inquiry", 
    "book", "book-now", "book-table", "reservation", "reserve", 
    "appointment", "schedule", "demo", "consultation", "quote", 
    "request-quote", "pricing", "services"
]
MEDIUM_PRIORITY_URLS = ["about", "team", "locations", "branches"]
LOW_PRIORITY_URLS = ["gallery", "blog", "press", "career", "privacy", "terms"]

def score_url(url: str) -> int:
    url_lower = url.lower()
    for kw in HIGH_PRIORITY_URLS:
        if kw in url_lower: return 100
    for kw in MEDIUM_PRIORITY_URLS:
        if kw in url_lower: return 50
    for kw in LOW_PRIORITY_URLS:
        if kw in url_lower: return 10
    return 30

async def extract_links(page, base_url):
    try:
        links = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => a.href);
        }''')
        return list(set(links))
    except Exception:
        return []

async def detect_tech_stack(html, page):
    tech = set()
    lower_html = html.lower()
    
    # CMS
    if "wp-content" in lower_html: tech.add("WordPress")
    if "shopify.theme" in lower_html or "cdn.shopify.com" in lower_html: tech.add("Shopify")
    if "wix.com" in lower_html or "x-wix" in lower_html: tech.add("Wix")
    if "squarespace" in lower_html: tech.add("Squarespace")
    if "webflow" in lower_html: tech.add("Webflow")
    if "drupal" in lower_html: tech.add("Drupal")
    if "magento" in lower_html: tech.add("Magento")
    
    # Frameworks
    if 'id="__next"' in lower_html or 'next/router' in lower_html: tech.add("Next.js")
    elif "react" in lower_html or 'data-reactroot' in lower_html: tech.add("React")
    if "ng-version" in lower_html: tech.add("Angular")
    if "data-v-" in lower_html or "__vue_hot_map__" in lower_html: tech.add("Vue")
    if "_nuxt" in lower_html: tech.add("Nuxt")
    
    # Marketing
    has_ga = await page.evaluate('() => !!window.ga || !!window.google_tag_manager || !!window.dataLayer || !!window.gtag || !!window.GoogleAnalyticsObject')
    if has_ga: tech.add("Google Analytics")
    has_fb = await page.evaluate('() => !!window.fbq || !!window._fbq')
    if has_fb: tech.add("Meta Pixel")
    
    # Infrastructure (Simple regex/checks)
    if "cloudflare" in lower_html: tech.add("Cloudflare")
    if "vercel" in lower_html: tech.add("Vercel")
    if "netlify" in lower_html: tech.add("Netlify")
    
    return list(tech)

async def check_conversion_mechanisms(page, html):
    lower_html = html.lower()
    found = []
    
    # Forms
    has_form = await page.evaluate('''() => {
        const forms = document.querySelectorAll('form');
        for (let f of forms) {
            if (f.querySelector('input') || f.querySelector('textarea')) return true;
        }
        return false;
    }''')
    if has_form: found.append("form")
        
    # Reservations & Appointments
    res_systems = ["opentable", "resdiary", "sevenrooms", "tablecheck", "tock", "calendly", "cal.com", "acuity", "booksy"]
    for sys in res_systems:
        if sys in lower_html: found.append(sys)
            
    # Messaging
    msg_systems = ["wa.me", "api.whatsapp.com", "m.me", "t.me", "intercom", "tawk.to", "crisp", "zendesk"]
    for sys in msg_systems:
        if sys in lower_html: found.append("messaging")
            
    # Direct
    if "mailto:" in lower_html: found.append("email_link")
    if "tel:" in lower_html: found.append("phone_link")
        
    return bool(found), found

async def run_audit(lead: models.Lead, db, settings: dict) -> models.WebsiteAudit:
    business = lead.business
    url = business.website
    if not url:
        raise ValueError("Lead business does not have a website.")
        
    if not url.startswith("http"):
        url = "http://" + url
        
    base_domain = urlparse(url).netloc.replace("www.", "")
        
    audit = models.WebsiteAudit(
        lead_id=lead.id,
        url=url,
        is_live=False,
        tech_stack="[]",
        issues_found="[]",
        revenue_leaks="[]",
        nexora_services="[]",
        conversion_score=0,
        lead_capture_present=False,
        sales_readiness_score=0
    )
    
    screenshots_dir = os.path.join(os.path.dirname(__file__), "..", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    ts = int(time.time())
    home_screenshot = os.path.join(screenshots_dir, f"audit_{lead.id}_home_{ts}.png")
    conv_screenshot = os.path.join(screenshots_dir, f"audit_{lead.id}_conv_{ts}.png")
    
    context, page = None, None
    tech_stack_set = set()
    conversion_found = False
    
    try:
        context, page = await browser_pool.get_context(settings)
        
        # QUEUE: (url, depth, priority)
        queue = [(url, 0, 100)]
        visited = set()
        pages_visited = 0
        best_conversion_page = None
        best_conversion_score = -1
        
        while queue and pages_visited < 10 and not conversion_found:
            queue.sort(key=lambda x: x[2], reverse=True) # Sort by priority
            current_url, depth, priority = queue.pop(0)
            
            if current_url in visited: continue
            visited.add(current_url)
            
            try:
                start_time = time.time()
                response = await page.goto(current_url, wait_until="load", timeout=20000)
                pages_visited += 1
                
                if not response or not response.ok:
                    continue
                    
                html = await page.content()
                
                # Metrics only for homepage
                if current_url == url:
                    audit.is_live = True
                    audit.has_ssl = current_url.startswith("https://")
                    
                    # Performance Timing
                    timing = await page.evaluate("JSON.stringify(window.performance.timing)")
                    t = json.loads(timing)
                    if t['loadEventEnd'] > 0 and t['navigationStart'] > 0:
                        audit.page_load_ms = t['loadEventEnd'] - t['navigationStart']
                    else:
                        audit.page_load_ms = int((time.time() - start_time) * 1000)
                        
                    audit.seo_title = await page.title()
                    audit.has_meta_title = bool(audit.seo_title and audit.seo_title.strip())
                    
                    meta_desc = await page.evaluate('''() => {
                        const meta = document.querySelector('meta[name="description"]') || document.querySelector('meta[property="og:description"]');
                        return meta ? meta.content : null;
                    }''')
                    audit.seo_description = meta_desc
                    audit.has_meta_description = bool(meta_desc and meta_desc.strip())
                    
                    audit.mobile_friendly = await page.evaluate('''() => {
                        return !!document.querySelector('meta[name="viewport"]');
                    }''')
                    
                    await page.screenshot(path=home_screenshot, full_page=False)
                    audit.screenshot_path = f"/screenshots/audit_{lead.id}_home_{ts}.png"
                
                # Check for tech stack
                tech = await detect_tech_stack(html, page)
                tech_stack_set.update(tech)
                
                # Check for conversion mechanisms
                has_conv, mechanisms = await check_conversion_mechanisms(page, html)
                if has_conv:
                    audit.lead_capture_present = True
                    conversion_found = True
                    best_conversion_page = current_url
                    await page.screenshot(path=conv_screenshot, full_page=False)
                    audit.conversion_screenshot_path = f"/screenshots/audit_{lead.id}_conv_{ts}.png"
                    # We can stop deep crawling!
                    break
                    
                # Extract links if we want to go deeper
                if depth < 3:
                    links = await extract_links(page, current_url)
                    for link in links:
                        try:
                            parsed = urlparse(link)
                            if parsed.netloc.replace("www.", "") == base_domain:
                                clean_link = urljoin(current_url, parsed.path)
                                if clean_link not in visited:
                                    queue.append((clean_link, depth + 1, score_url(clean_link)))
                        except:
                            pass
                            
            except Exception as e:
                logger.warning(f"Failed to crawl {current_url}: {e}")
                
        audit.tech_stack = json.dumps(list(tech_stack_set))
        
    finally:
        if context and page:
            await browser_pool.release_context(context, page)
            
    # STAGE 9 & 10: Opportunity Engine V2 & AI Sales Intelligence
    issues = []
    revenue_leaks = []
    nexora_services = []
    
    audit_score = 100
    conversion_score = 100
    
    has_ga = "Google Analytics" in tech_stack_set
    has_pixel = "Meta Pixel" in tech_stack_set
    
    if not audit.is_live:
        audit_score = 0
        conversion_score = 0
        issues.append("Website is offline or unreachable")
        revenue_leaks.append("Zero digital footprint. Losing 100% of online customers.")
        nexora_services.append("Website Modernization")
    else:
        if not audit.has_ssl:
            audit_score -= 20
            issues.append("No SSL certificate (Not Secure)")
            revenue_leaks.append("Customers see 'Not Secure' warning, destroying trust.")
            nexora_services.append("Security & Maintenance")
            
        if not audit.mobile_friendly:
            audit_score -= 15
            conversion_score -= 30
            issues.append("Not mobile friendly")
            revenue_leaks.append("High bounce rate on mobile devices (typically 60%+ of traffic).")
            nexora_services.append("Website Modernization")
            
        if audit.page_load_ms and audit.page_load_ms > 4000:
            audit_score -= 10
            conversion_score -= 10
            issues.append(f"Slow page load ({audit.page_load_ms}ms)")
            revenue_leaks.append("Visitors abandon site before it loads, wasting ad spend.")
            nexora_services.append("Performance Optimization")
            
        if not audit.lead_capture_present:
            conversion_score -= 50
            issues.append("No contact forms, booking systems, or direct messaging found.")
            revenue_leaks.append("Website receives traffic but cannot capture leads or bookings.")
            nexora_services.append("Conversion Optimization")
            nexora_services.append("Lead Capture Automation")
            
        if not has_ga and not has_pixel:
            audit_score -= 15
            issues.append("No Analytics or Meta Pixel tracking detected.")
            revenue_leaks.append("Blind to customer behavior. Unable to run retargeting ads.")
            nexora_services.append("Data & Tracking Setup")
            
        if not audit.has_meta_title or not audit.has_meta_description:
            audit_score -= 10
            issues.append("Missing or incomplete SEO meta tags.")
            revenue_leaks.append("Invisible on Google Search for local keywords.")
            nexora_services.append("Local SEO Package")
            
    audit.audit_score = max(0, audit_score)
    audit.conversion_score = max(0, conversion_score)
    audit.opportunity_score = 100 - audit.audit_score
    
    rating = business.rating or 0.0
    rating_boost = 0
    if rating >= 4.5: rating_boost = 40
    elif rating >= 4.0: rating_boost = 25
    elif rating > 0: rating_boost = 10
    
    # Revenue Potential: High if bad website + good rating
    raw_rev = audit.opportunity_score + rating_boost
    audit.revenue_potential_score = min(100, max(0, raw_rev))
    
    # Sales Readiness Score
    # Example logic: Excellent business (rating >= 4.0), terrible website -> Ready to buy.
    readiness = 0
    if not audit.is_live:
        readiness = 100 if rating >= 4.0 else 50
    elif audit.audit_score < 50 and rating >= 4.0:
        readiness = 95
    elif audit.conversion_score < 50 and rating >= 4.0:
        readiness = 90
    elif rating >= 4.0:
        readiness = 45 # They have a good site, might not need us
    else:
        readiness = 10 # Poor rating, poor business, less likely to have budget
        
    audit.sales_readiness_score = readiness
    
    # Deduplicate services
    nexora_services = list(set(nexora_services))
    
    if not audit.is_live:
        audit.opportunity_type = "Full Build Opportunity"
        audit.estimated_deal_size = "$2,500 - $5,000+"
    elif not audit.lead_capture_present:
        audit.opportunity_type = "Conversion & Automation"
        audit.estimated_deal_size = "$1,500 - $3,000"
    elif not has_ga and not has_pixel:
        audit.opportunity_type = "Tracking & Analytics"
        audit.estimated_deal_size = "$500 - $1,500"
    elif audit.audit_score < 70:
        audit.opportunity_type = "SEO & Modernization"
        audit.estimated_deal_size = "$1,000 - $2,500"
    else:
        audit.opportunity_type = "Growth Retainer"
        audit.estimated_deal_size = "$500/mo"
        
    audit.issues_found = json.dumps(issues)
    audit.revenue_leaks = json.dumps(revenue_leaks)
    audit.nexora_services = json.dumps(nexora_services)
    
    # AI Pitch Generation
    pitch = f"This {business.category or 'business'} has a strong market reputation with a {rating} Google rating, indicating proven product-market fit. " if rating >= 4.0 else f"This {business.category or 'business'} has a {rating} Google rating. "
    
    if not audit.is_live:
        pitch += "However, they currently have ZERO digital presence (website offline or non-existent), losing 100% of digital prospects to competitors. "
    elif audit.conversion_score < 50:
        pitch += "Despite this demand, their website is functionally dead-weight. It acts as an expensive brochure but fails to capture leads or bookings. "
    else:
        pitch += "Their website is functional, but lacks advanced growth infrastructure. "
        
    if nexora_services:
        pitch += f"Pitch them on: {', '.join(nexora_services)}."
        
    audit.sales_pitch_angle = pitch
    audit.business_impact = f"Losing high-intent customers due to: {revenue_leaks[0] if revenue_leaks else 'sub-optimal digital infrastructure'}."
    audit.why_contact_summary = pitch
    
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
