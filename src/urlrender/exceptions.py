
class URLRenderError(Exception):
    """Base exception for urlrender."""


class NavigationError(URLRenderError):
    """Raised when navigation to a URL fails."""


class RenderTimeoutError(NavigationError):
    """Raised when rendering exceeds the configured timeout."""


