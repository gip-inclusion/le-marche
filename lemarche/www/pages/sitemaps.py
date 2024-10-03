from django.contrib.sitemaps import Sitemap
from django.urls import get_resolver, reverse, URLPattern, URLResolver

from lemarche.pages.models import Page
from lemarche.www.pages.views import ContactView, PageView, SitemapView

EXCLUDED_STATIC_PAGES = [
    "2021-10-06-le-marche-fait-peau-neuve",
]

class FlatPageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6
    def items(self):
        return Page.objects.all()
    
    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
    

class StaticPageSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.4
    def _is_included_view(self, callback):
        """
        Check if a view has to be included in the sitemap.

        Args:
            callback: The view callable.

        Returns:
            bool: True if the callback is a is a ContactView, 
            HomeView, PageView, or SitemapView, False otherwise.
        """
        return (
            hasattr(callback, 'view_class') and 
            issubclass(callback.view_class, (ContactView, PageView, SitemapView))
        )

    def items(self):
        """
        Return a list of URL names for static pages.
        
        This method iterates over all URL patterns, checking if a view inherits 
        from certain class views. Excluded pages defined in EXCLUDED_STATIC_PAGES
        are not included in the sitemap.
        """
        urlconf = get_resolver().url_patterns
        static_pages = []

        for pattern in urlconf:
            # Handle nested URLResolver patterns (e.g., 'pages' namespace)
            if isinstance(pattern, URLResolver):
                static_pages.extend(
                    f'pages:{sub_pattern.name}' 
                    for sub_pattern in pattern.url_patterns 
                    if isinstance(sub_pattern, URLPattern) 
                    and self._is_included_view(sub_pattern.callback) 
                    and sub_pattern.name not in EXCLUDED_STATIC_PAGES
                )
            # Handle top-level URLPatterns
            elif isinstance(pattern, URLPattern) and pattern.name:
                if self._is_included_view(pattern.callback) and pattern.name not in EXCLUDED_STATIC_PAGES:
                    static_pages.append(pattern.name)
        
        return static_pages

    def location(self, item):
        return reverse(item)
