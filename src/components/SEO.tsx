import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

interface SEOProps {
  title?: string;
  description?: string;
  keywords?: string[];
  image?: string;
  type?: 'website' | 'article' | 'organization' | 'educational';
  schema?: Record<string, any>;
  noIndex?: boolean;
  canonicalUrl?: string;
}

const DEFAULT_TITLE = 'ShikkhaHub - Find the Best Schools, Colleges & Universities in Bangladesh';
const DEFAULT_DESCRIPTION = 'Discover and compare educational institutions in Bangladesh. Find top schools, colleges, universities, and madrasas with detailed information, reviews, and admission guidance.';
const DEFAULT_IMAGE = 'https://shikkhahub.com/og-image.jpg';
const SITE_URL = 'https://shikkhahub.com';

export function SEO({
  title,
  description,
  keywords = [],
  image = DEFAULT_IMAGE,
  type = 'website',
  schema,
  noIndex = false,
  canonicalUrl,
}: SEOProps) {
  const location = useLocation();
  const currentUrl = `${SITE_URL}${location.pathname}`;
  const fullTitle = title ? `${title} | ShikkhaHub` : DEFAULT_TITLE;
  const fullDescription = description || DEFAULT_DESCRIPTION;
  const fullKeywords = [
    'education',
    'Bangladesh',
    'schools',
    'colleges',
    'universities',
    ...keywords,
  ].join(', ');

  useEffect(() => {
    // Update document title
    document.title = fullTitle;

    // Meta tags helper
    const setMetaTag = (name: string, content: string, property = false) => {
      const selector = property ? `meta[property="${name}"]` : `meta[name="${name}"]`;
      let meta = document.querySelector(selector) as HTMLMetaElement;
      
      if (!meta) {
        meta = document.createElement('meta');
        if (property) {
          meta.setAttribute('property', name);
        } else {
          meta.setAttribute('name', name);
        }
        document.head.appendChild(meta);
      }
      meta.setAttribute('content', content);
    };

    // Set standard meta tags
    setMetaTag('description', fullDescription);
    setMetaTag('keywords', fullKeywords);
    setMetaTag('robots', noIndex ? 'noindex, nofollow' : 'index, follow');

    // Open Graph meta tags
    setMetaTag('og:title', fullTitle, true);
    setMetaTag('og:description', fullDescription, true);
    setMetaTag('og:type', type, true);
    setMetaTag('og:url', canonicalUrl || currentUrl, true);
    setMetaTag('og:image', image, true);
    setMetaTag('og:site_name', 'ShikkhaHub', true);
    setMetaTag('og:locale', 'en_US', true);

    // Twitter Card meta tags
    setMetaTag('twitter:card', 'summary_large_image');
    setMetaTag('twitter:title', fullTitle);
    setMetaTag('twitter:description', fullDescription);
    setMetaTag('twitter:image', image);
    setMetaTag('twitter:site', '@ShikkhaHub');

    // Canonical URL
    let canonical = document.querySelector('link[rel="canonical"]') as HTMLLinkElement;
    if (!canonical) {
      canonical = document.createElement('link');
      canonical.setAttribute('rel', 'canonical');
      document.head.appendChild(canonical);
    }
    canonical.setAttribute('href', canonicalUrl || currentUrl);

    // Schema.org JSON-LD
    let scriptTag = document.querySelector('#schema-org-data') as HTMLScriptElement;
    if (!scriptTag) {
      scriptTag = document.createElement('script');
      scriptTag.setAttribute('id', 'schema-org-data');
      scriptTag.setAttribute('type', 'application/ld+json');
      document.head.appendChild(scriptTag);
    }
    
    const defaultSchema = {
      '@context': 'https://schema.org',
      '@type': type === 'educational' ? 'Organization' : type,
      name: fullTitle,
      description: fullDescription,
      url: canonicalUrl || currentUrl,
      image: image,
    };

    scriptTag.textContent = JSON.stringify(schema || defaultSchema);

    // Cleanup function
    return () => {
      // Meta tags are updated on next render, no need to remove
    };
  }, [fullTitle, fullDescription, fullKeywords, image, type, schema, noIndex, canonicalUrl, currentUrl]);

  return null;
}

// Predefined SEO configurations for different pages
export const InstitutionSEO = (institution: any) => ({
  title: `${institution.name_en} - ${institution.type_name} in ${institution.division_name}`,
  description: institution.description || `Learn about ${institution.name_en}, admission process, courses, and more. Located in ${institution.division_name}, Bangladesh.`,
  keywords: [
    institution.name_en,
    institution.type_name,
    institution.division_name,
    'admission',
    'education',
    'Bangladesh',
  ],
  type: 'educational' as const,
  schema: {
    '@context': 'https://schema.org',
    '@type': 'EducationalOrganization',
    name: institution.name_en,
    alternateName: institution.name_bn,
    description: institution.description,
    url: `https://shikkhahub.com/institutions/${institution.slug}`,
    address: {
      '@type': 'PostalAddress',
      addressLocality: institution.district_name,
      addressRegion: institution.division_name,
      addressCountry: 'BD',
    },
    telephone: institution.phone,
    email: institution.email,
    sameAs: institution.website,
    foundingDate: institution.established_year?.toString(),
  },
});

export const SearchResultsSEO = (query: string, count: number) => ({
  title: `Search results for "${query}" - ${count} institutions found`,
  description: `Find educational institutions matching "${query}". Compare schools, colleges, and universities in Bangladesh.`,
  keywords: [query, 'search', 'education', 'Bangladesh'],
  type: 'website' as const,
});

export default SEO;
