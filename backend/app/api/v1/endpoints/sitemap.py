"""Sitemap generation endpoint for SEO."""
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.institution import Institution

router = APIRouter()

BASE_URL = "https://shikkhahub.com"


@router.get("/sitemap.xml")
def generate_sitemap(db: Session = Depends(get_db)):
    """Generate XML sitemap for search engines."""
    
    # Static pages
    static_urls = [
        {
            "loc": f"{BASE_URL}/",
            "changefreq": "daily",
            "priority": "1.0",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "loc": f"{BASE_URL}/institutions",
            "changefreq": "daily",
            "priority": "0.9",
            "lastmod": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "loc": f"{BASE_URL}/search",
            "changefreq": "weekly",
            "priority": "0.8",
        },
        {
            "loc": f"{BASE_URL}/compare",
            "changefreq": "weekly",
            "priority": "0.7",
        },
    ]
    
    # Get all verified institutions
    institutions = db.query(Institution).filter(
        Institution.is_active == True,
        Institution.verification_status == "verified"
    ).all()
    
    # Institution pages
    institution_urls = [
        {
            "loc": f"{BASE_URL}/institutions/{inst.slug}",
            "changefreq": "weekly",
            "priority": "0.8",
            "lastmod": inst.updated_at.strftime("%Y-%m-%d") if inst.updated_at else datetime.now().strftime("%Y-%m-%d"),
        }
        for inst in institutions
    ]
    
    # Combine all URLs
    all_urls = static_urls + institution_urls
    
    # Generate XML
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for url in all_urls:
        xml += "  <url>\n"
        xml += f"    <loc>{url['loc']}</loc>\n"
        if "lastmod" in url:
            xml += f"    <lastmod>{url['lastmod']}</lastmod>\n"
        if "changefreq" in url:
            xml += f"    <changefreq>{url['changefreq']}</changefreq>\n"
        if "priority" in url:
            xml += f"    <priority>{url['priority']}</priority>\n"
        xml += "  </url>\n"
    
    xml += "</urlset>"
    
    return Response(
        content=xml,
        media_type="application/xml",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
        }
    )


@router.get("/robots.txt")
def generate_robots_txt(request: Request):
    """Generate robots.txt for search engines."""
    
    content = f"""User-agent: *
Allow: /

# Disallow admin and private areas
Disallow: /admin/
Disallow: /api/
Disallow: /private/

# Sitemap
Sitemap: {BASE_URL}/sitemap.xml

# Crawl rate
Crawl-delay: 1

# Specific bot rules
User-agent: GPTBot
Allow: /institutions/
Allow: /

User-agent: ChatGPT-User
Allow: /institutions/
Allow: /

User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /
"""
    
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
        }
    )
