# urlrender

A lightweight Python library for rendering JavaScript-enabled web pages using Playwright and Chromium.

## Features

- Render JavaScript-enabled web pages.
- Extract rendered HTML and visible text.
- Retrieve page title, final URL, HTTP status code, and rendering time.
- Optionally wait for a CSS selector before extracting content.
- Reuse a browser instance across multiple URLs.
- Simple synchronous API with automatic resource cleanup.

## Installation

Install the package:

```bash
pip install urlrender
```

Install Chromium:

```bash
python -m playwright install chromium
```

Requires **Python 3.10+**.

## Quick Start

```python
from urlrender import Renderer

with Renderer() as renderer:
    result = renderer.render("https://example.com")

    print("Title:", result.title)
    print("Status:", result.status_code)
    print("URL:", result.url)
    print("HTML:", result.html)
    print("Text:", result.text)
    print("Elapsed:", result.elapsed_ms, "ms")
```

The context manager automatically closes the browser when finished.

## Get HTML or Text

If you only need one output, use the convenience methods:

```python
from urlrender import Renderer

with Renderer() as renderer:
    html = renderer.get_html("https://example.com")
    text = renderer.get_text("https://example.com")
```

Each method performs a rendering operation. Use `render()` when you need multiple fields from the same page.

## Wait for an Element

Some websites load content dynamically. Use `wait_for_selector` to wait for a CSS selector before extracting the page.

```python
from urlrender import Renderer

url = "https://www.imdb.com/title/tt43595281/"

with Renderer(timeout=20000) as renderer:
    result = renderer.render(
        url,
        wait_for_selector='script[type="application/ld+json"]',
    )

    print(result.html)
```

The selector wait checks that the element is attached to the DOM; it does not need to be visible.

## Configuration

```python
from urlrender import Renderer

with Renderer(
    timeout=15000,                  # Milliseconds
    wait_until="domcontentloaded",  # Navigation event
    headless=True,                  # Run without a visible window
) as renderer:
    result = renderer.render("https://example.com")
```

Supported `wait_until` values:

- `"commit"`
- `"domcontentloaded"` (default)
- `"load"`
- `"networkidle"`

Use `headless=False` to open a visible Chromium window for debugging.

## RenderResult

`renderer.render()` returns a `RenderResult` object:

| Attribute | Description |
|---|---|
| `url` | Final page URL |
| `html` | Rendered HTML |
| `text` | Visible text from the page body |
| `status_code` | Main navigation HTTP status code, or `None` |
| `title` | Page title |
| `elapsed_ms` | Rendering time in milliseconds |

## Error Handling

```python
from urlrender import Renderer, NavigationError, RenderTimeoutError

try:
    with Renderer(timeout=10000) as renderer:
        result = renderer.render(
            "https://example.com",
            wait_for_selector="main",
        )

except RenderTimeoutError as exc:
    print("Rendering timed out:", exc)

except NavigationError as exc:
    print("Navigation failed:", exc)
```

Invalid URLs and invalid configuration values can raise `ValueError`.

## Requirements and Limitations

- Chromium must be installed separately using Playwright.
- Some websites may return CAPTCHA, bot-protection, or access-denied pages.
- Dynamically loaded content may require an appropriate selector wait.
- The library does not automatically click elements, scroll pages, or paginate results.
- Browser rendering consumes more resources than ordinary HTTP requests.

Use the library responsibly and follow the target website's terms and access restrictions.

## License

MIT License. See [LICENSE](LICENSE).

## Author

**Hemant Malik**

- GitHub: [@itsmehemant7](https://github.com/itsmehemant7)
