from flask import Flask, Response

def init_security_headers(app: Flask) -> None:
    """
    Hooks into the Flask after_request lifecycle to inject secure headers
    that mitigate common web vulnerabilities like XSS, Clickjacking, and MIME-sniffing.
    """
    @app.after_request
    def apply_headers(response: Response) -> Response:
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Clickjacking defense
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        
        # XSS filtering for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Tight Content Security Policy (CSP)
        # Allows self-served assets, Swagger UI assets from unpkg, and Google Fonts
        csp_rules = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )
        response.headers["Content-Security-Policy"] = csp_rules
        
        # Cache control for sensitive APIs: do not store
        # Specifically target the profile, history, layouts directories
        if request_is_sensitive():
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            
        return response

def request_is_sensitive() -> bool:
    from flask import request
    path = request.path
    # Mark user data and conversion paths as sensitive to prevent browser back-button caching leaks
    return any(p in path for p in ["/auth/profile", "/layouts", "/history", "/converter/convert"])
