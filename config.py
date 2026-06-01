# config.py
from urllib.parse import urlparse, urlunparse

def is_safe_url(url) -> bool:
    """Returns True if the URL contains our target domain block."""
    try:
        # If url is a Request object, extract the URL string
        url_str = url.url if hasattr(url, "url") else str(url)
        parsed_url = urlparse(url_str)
        # Pull the hostname (e.g., 'www.novoxcore.com' or 'novoxcore.com')
        hostname = parsed_url.hostname
        
        if hostname:
            # Check if novoxcore is anywhere inside the domain structure
            return "novoxcore.com" in hostname
        return False
    except Exception:
        return False

def canonicalize_url(url) -> str:
    """Normalizes and canonicalizes a URL to a standard HTTPS format without query params or trailing extensions."""
    try:
        url_str = url.url if hasattr(url, "url") else str(url)
        parsed = urlparse(url_str)
        
        # Force HTTPS
        scheme = "https"
        
        # Normalize hostname (lowercase, strip www.)
        hostname = parsed.hostname.lower() if parsed.hostname else ""
        if hostname.startswith("www."):
            hostname = hostname[4:]
            
        # Normalize path
        path = parsed.path
        if not path or path == "/":
            path = "/"
        else:
            path = path.lower()
            if path.endswith("/"):
                path = path[:-1]
            if path.endswith(".html"):
                path = path[:-5]
            elif path.endswith(".htm"):
                path = path[:-4]
                
            if path.endswith("/index"):
                path = path[:-6]
            elif path == "index":
                path = ""
                
            if not path:
                path = "/"
                
        return urlunparse((scheme, hostname, path, "", "", ""))
    except Exception:
        return str(url)

def is_allowed_url(url) -> bool:
    """Returns True if the URL is within the target domain and represents an allowed business-relevant page."""
    try:
        url_str = url.url if hasattr(url, "url") else str(url)
        if not is_safe_url(url_str):
            return False
            
        canon_url = canonicalize_url(url_str)
        parsed = urlparse(canon_url)
        path = parsed.path.lower()
        
        # Explicitly excluded page patterns
        excluded_patterns = ["terms", "privacy", "cookie", "gallery", "blog", "feed", "tag"]
        for pattern in excluded_patterns:
            if pattern in path:
                return False
                
        # Homepage
        if path == "/" or not path:
            return True
            
        # Explicitly allowed business-relevant pages
        allowed_patterns = ["about", "services", "careers", "contact", "team"]
        for pattern in allowed_patterns:
            if pattern in path:
                return True
                
        return False
    except Exception:
        return False