# urlrender

**A lightweight Python library for rendering JavaScript-enabled web pages with Playwright and Chromium.**

`urlrender` makes it easy to navigate to a URL, let the page render in a real browser engine, and retrieve its HTML, visible text, page title, HTTP status code, and rendering time.

Unlike a simple HTTP request, `urlrender` uses Chromium through Playwright, allowing websites that rely on JavaScript to populate their content before extraction.

## Features

- **JavaScript-enabled rendering** — execute client-side JavaScript using Chromium.
- **Rendered HTML extraction** — retrieve the HTML after the page has been rendered.
- **Visible text extraction** — extract readable text from the page body.
- **Page metadata** — access the final URL, page title, HTTP status code, and elapsed rendering time.
- **Optional selector waiting** — wait for a CSS selector before extracting page content.
- **Configurable timeouts** — control navigation and element-wait timeouts.
- **Configurable browser mode** — run Chromium in headless or visible mode.
- **Reusable browser instance** — render multiple URLs without launching a new browser for every request.
- **Simple synchronous API** — use familiar Python functions without writing asynchronous code.
- **Context manager support** — automatically close browser resources when finished.
- **Custom exceptions** — distinguish navigation failures from rendering timeouts.
- **Minimal dependencies** — Playwright is the only declared runtime dependency.

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Installation and Browser Setup](#installation-and-browser-setup)
- [Basic Usage](#basic-usage)
- [Waiting for Page Elements](#waiting-for-page-elements)
- [Rendering Configuration](#rendering-configuration)
- [RenderResult](#renderresult)
- [API Reference](#api-reference)
- [Exception Handling](#exception-handling)
- [Rendering Multiple URLs](#rendering-multiple-urls)
- [Extracting Structured Data](#extracting-structured-data)
- [Working with HTML](#working-with-html)
- [Troubleshooting](#troubleshooting)
- [Performance Considerations](#performance-considerations)
- [Limitations](#limitations)
- [Security Considerations](#security-considerations)
- [Contributing](#contributing)
- [License](#license)

## Requirements

- Python 3.10 or newer
- Playwright for Python
- A compatible Chromium browser installed through Playwright

`urlrender` uses Chromium for browser rendering. Installing the Python package and installing the browser binary are separate steps.

## Installation

Install `urlrender` using pip:

```bash
python -m pip install urlrender
```

If you use a virtual environment, activate it before installing the package.

### Install Chromium

After installing `urlrender`, install the Chromium browser binary required by Playwright:

```bash
python -m playwright install chromium
```

On Linux servers, you may also need the operating-system libraries required by Chromium. Playwright can install supported system dependencies on compatible Linux distributions:

```bash
python -m playwright install --with-deps chromium
```

The second command is intended for Linux environments and may require administrator privileges.

### Verify the installation

```python
from urlrender import Renderer

with Renderer() as renderer:
    result = renderer.render("https://example.com")

    print("Title:", result.title)
    print("Status:", result.status_code)
    print("HTML:", result.html[:200])
```

If the installation is successful, the script should print the page title, HTTP status code, and a portion of the rendered HTML.

## Quick Start

The simplest way to use `urlrender` is with a context manager:

```python
from urlrender import Renderer

url = "https://example.com"

with Renderer() as renderer:
    result = renderer.render(url)

    print("URL:", result.url)
    print("Title:", result.title)
    print("Status Code:", result.status_code)
    print("Elapsed Time:", result.elapsed_ms, "ms")

    print("\nRendered HTML:")
    print(result.html)

    print("\nVisible Text:")
    print(result.text)
```

The `render()` method returns a `RenderResult` object containing the rendered page and its metadata.

Using `with Renderer() as renderer` ensures that the browser resources are closed when the block exits, including when an exception occurs.

## Basic Usage

### 1. Render a URL

```python
from urlrender import Renderer

with Renderer() as renderer:
    result = renderer.render("https://example.com")

    print(result.title)
    print(result.html)
```

By default, the renderer navigates using the `domcontentloaded` event. This means the initial HTML document has been parsed, but it does not guarantee that every asynchronous request or dynamically generated element has finished loading.

### 2. Retrieve only the HTML

If you only need the rendered HTML, use `get_html()`:

```python
from urlrender import Renderer

with Renderer() as renderer:
    html = renderer.get_html("https://example.com")

    print(html)
```

### 3. Retrieve only the visible text

If you only need the readable text from the page body, use `get_text()`:

```python
from urlrender import Renderer

with Renderer() as renderer:
    text = renderer.get_text("https://example.com")

    print(text)
```

**Tip:** If you need HTML, text, and metadata from the same navigation, call `render()` once and reuse the result. Calling `get_html()` and `get_text()` separately performs separate rendering operations.

## Waiting for Page Elements

Modern websites frequently load content asynchronously. The initial document may be available before a product listing, review section, movie details, or other important element has appeared.

To wait for a particular CSS selector, pass `wait_for_selector` to `render()`.

### Example: Wait for JSON-LD structured data

```python
from urlrender import Renderer

url = "https://www.imdb.com/title/tt43595281/"

with Renderer(headless=False) as renderer:
    result = renderer.render(
        url,
        wait_for_selector='script[type="application/ld+json"]',
    )

    print("Title:", result.title)
    print("Status:", result.status_code)
    print(result.html)
```

This instructs the renderer to wait until an element matching the selector exists in the DOM before extracting the HTML.

The selector wait uses the `attached` state, meaning the element does not have to be visible. This is particularly useful for script elements such as JSON-LD, which are normally hidden.

### Example: Wait for a product listing

```python
with Renderer() as renderer:
    result = renderer.render(
        "https://example.com/products",
        wait_for_selector=".product-list",
    )

    print(result.html)
```

### Example: Wait for a review section

```python
with Renderer() as renderer:
    result = renderer.render(
        "https://example.com/reviews",
        wait_for_selector="[data-testid='reviews']",
    )

    print(result.text)
```

These selectors are examples. Replace them with selectors that match the actual website.

### What if the selector does not exist?

If the requested element does not appear before the configured timeout, `urlrender` raises `RenderTimeoutError`.

```python
from urlrender import Renderer, RenderTimeoutError

try:
    with Renderer(timeout=10_000) as renderer:
        result = renderer.render(
            "https://example.com",
            wait_for_selector=".element-that-does-not-exist",
        )

except RenderTimeoutError as exc:
    print("The requested element did not appear in time:", exc)
```

The timeout is expressed in milliseconds.

### Optional selector waiting

You do not need to specify a selector for every URL.

```python
with Renderer() as renderer:
    # Render without waiting for a specific selector.
    result = renderer.render("https://example.com")

    # Wait for an element on another page.
    result2 = renderer.render(
        "https://example.com/products",
        wait_for_selector=".product-list",
    )
```

This keeps the library generic and suitable for different kinds of websites.

## Rendering Configuration

Configure the renderer using its constructor:

```python
from urlrender import Renderer

with Renderer(
    timeout=20_000,
    wait_until="domcontentloaded",
    headless=True,
) as renderer:
    result = renderer.render("https://example.com")
```

### Constructor parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `timeout` | `int` | `15000` | Timeout in milliseconds for navigation and default Playwright operations. |
| `wait_until` | `str` | `"domcontentloaded"` | Navigation event to wait for. |
| `headless` | `bool` | `True` | Whether Chromium runs without a visible browser window. |

### `timeout`

The default timeout is 15 seconds.

```python
with Renderer(timeout=30_000) as renderer:
    result = renderer.render("https://example.com")
```

Increase the timeout for slower websites or pages that take longer to render.

A larger timeout does not guarantee that a website will become accessible or that all of its content will load.

### `wait_until`

The following navigation events are supported:

| Value | Description |
|---|---|
| `"commit"` | Wait until the navigation response has started arriving and the document response is committed. |
| `"domcontentloaded"` | Wait until the HTML document has been parsed and the `DOMContentLoaded` event has fired. |
| `"load"` | Wait until the page's load event has fired. |
| `"networkidle"` | Wait until network activity reaches Playwright's network-idle condition. |

Example:

```python
with Renderer(
    wait_until="load",
    timeout=20_000,
) as renderer:
    result = renderer.render("https://example.com")
```

For general-purpose rendering, `domcontentloaded` is a practical default. Some sites continuously make network requests, so `networkidle` may take longer or time out.

If you need a specific dynamically generated element, using `wait_for_selector` is often more targeted than waiting for all network activity to stop.

### `headless`

By default, Chromium runs in headless mode:

```python
with Renderer(headless=True) as renderer:
    result = renderer.render("https://example.com")
```

For debugging, you can run Chromium with a visible window:

```python
with Renderer(headless=False) as renderer:
    result = renderer.render("https://example.com")
```

A visible browser is useful for observing navigation, inspecting page behavior, and diagnosing rendering issues.

Headless and visible modes may behave differently on some websites. Neither mode guarantees successful access to every page.

## RenderResult

The `render()` method returns an instance of `RenderResult`.

```python
result = renderer.render("https://example.com")
```

### Available attributes

| Attribute | Type | Description |
|---|---|---|
| `url` | `str` | The final URL reported by the browser after navigation, including redirects when applicable. |
| `html` | `str` | The rendered HTML document. |
| `text` | `str` | Readable text extracted from the page body. |
| `status_code` | `int \| None` | HTTP status code of the main navigation response, or `None` if no response was available. |
| `title` | `str` | The page title. |
| `elapsed_ms` | `float` | Approximate elapsed time for the rendering operation, in milliseconds. |

### Example

```python
from urlrender import Renderer

with Renderer() as renderer:
    result = renderer.render("https://example.com")

    print(result.url)
    print(result.status_code)
    print(result.title)
    print(result.elapsed_ms)
    print(result.html)
    print(result.text)
```

`elapsed_ms` includes the time spent on navigation and the rendering operations performed before the result is returned, including any selector wait.

The `text` attribute is extracted using the page body's `inner_text()` behavior. It is not a complete representation of all text in the HTML, and hidden text, metadata, and script contents may not appear in it.

The `html` attribute contains the DOM serialization returned by Playwright. It is not necessarily identical to the original HTTP response body because JavaScript may have modified the page.

## API Reference

### `Renderer`

The main class for rendering web pages.

```python
Renderer(
    *,
    timeout=15_000,
    wait_until="domcontentloaded",
    headless=True,
)
```

### `Renderer.start()`

Starts Playwright and launches Chromium.

```python
renderer.start()
```

Returns the renderer instance, allowing method chaining.

The browser is started automatically when `render()` is called, so explicit startup is optional.

### `Renderer.render(url, *, wait_for_selector=None)`

Navigates to a URL and returns a `RenderResult`.

```python
result = renderer.render(
    "https://example.com",
    wait_for_selector="main",
)
```

Parameters:

- `url`: HTTP or HTTPS URL to render. A URL without a scheme is interpreted as HTTPS.
- `wait_for_selector`: Optional CSS selector to wait for before extracting page data.

The selector is optional. If supplied, the renderer waits for a matching element to be attached to the DOM.

### `Renderer.get_html(url)`

Returns the rendered HTML as a string.

```python
html = renderer.get_html("https://example.com")
```

### `Renderer.get_text(url)`

Returns the readable text from the page body as a string.

```python
text = renderer.get_text("https://example.com")
```

### `Renderer.close()`

Closes the browser and stops Playwright.

```python
renderer.close()
```

Calling `close()` more than once is safe. A renderer that has been closed cannot be started again.

### Context manager support

Use the renderer as a context manager for automatic cleanup:

```python
with Renderer() as renderer:
    result = renderer.render("https://example.com")
```

The browser is closed when the block exits.

## Exception Handling

`urlrender` provides a small exception hierarchy:

```text
URLRenderError
├── NavigationError
└── RenderTimeoutError
```

### `URLRenderError`

Base exception for errors exposed by the library.

```python
from urlrender import URLRenderError
```

### `NavigationError`

Raised when navigation or another rendering operation fails.

Potential causes include network errors, browser errors, and failures while accessing the page.

```python
from urlrender import NavigationError, Renderer

try:
    with Renderer() as renderer:
        result = renderer.render("https://example.com")

except NavigationError as exc:
    print("Navigation or rendering failed:", exc)
```

### `RenderTimeoutError`

Raised when a rendering operation exceeds the configured timeout.

It is a subclass of `NavigationError`, so it can be handled separately or caught as a navigation error.

```python
from urlrender import NavigationError, RenderTimeoutError, Renderer

try:
    with Renderer(timeout=5_000) as renderer:
        result = renderer.render(
            "https://example.com",
            wait_for_selector=".important-content",
        )

except RenderTimeoutError as exc:
    print("Rendering timed out:", exc)

except NavigationError as exc:
    print("Other navigation or rendering error:", exc)
```

### `ValueError`

Invalid input, such as an unsupported URL scheme, an empty URL, or an invalid timeout, raises `ValueError`.

```python
from urlrender import Renderer

try:
    with Renderer() as renderer:
        renderer.render("ftp://example.com/file")

except ValueError as exc:
    print("Invalid input:", exc)
```

Note that `Renderer` validates the URL before navigation. A valid HTTP or HTTPS URL can still fail later because of DNS, connectivity, TLS, browser, or website-related problems.

## Rendering Multiple URLs

You can reuse a single renderer to process multiple URLs sequentially.

```python
from urlrender import Renderer

urls = [
    "https://example.com",
    "https://www.python.org",
    "https://www.djangoproject.com",
]

with Renderer(timeout=20_000) as renderer:
    for url in urls:
        try:
            result = renderer.render(url)

            print("-" * 60)
            print("URL:", result.url)
            print("Title:", result.title)
            print("Status:", result.status_code)
            print("Elapsed:", result.elapsed_ms, "ms")

        except Exception as exc:
            print(f"Failed to render {url}: {exc}")
```

A single browser instance can handle multiple sequential rendering operations. Each rendering operation creates a new browser context, which is closed when that operation finishes.

This helps separate page state between rendering operations while avoiding the cost of launching a new Chromium process each time.

If you need cookies or other session state to persist across URLs, the current API does not expose a persistent browser context. You would need an appropriate extension to the library for that use case.

## Extracting Structured Data

Many websites include structured metadata in their HTML, such as JSON-LD.

`urlrender` does not automatically parse JSON-LD or return website-specific fields. Instead, it provides the rendered HTML so you can process the data using your preferred Python libraries.

### Example: Extract JSON-LD

Install Beautiful Soup if you want to use it for HTML parsing:

```bash
python -m pip install beautifulsoup4
```

Then:

```python
import json

from bs4 import BeautifulSoup
from urlrender import Renderer

url = "https://example.com"

with Renderer() as renderer:
    result = renderer.render(
        url,
        wait_for_selector='script[type="application/ld+json"]',
    )

soup = BeautifulSoup(result.html, "html.parser")

json_ld_items = []

for script in soup.select('script[type="application/ld+json"]'):
    raw_json = script.string or script.get_text()

    if not raw_json.strip():
        continue

    try:
        json_ld_items.append(json.loads(raw_json))
    except json.JSONDecodeError:
        continue

print(json_ld_items)
```

This example collects valid JSON-LD blocks from the rendered HTML. It does not assume that every website uses the same schema.

A JSON-LD block might describe a movie, product, article, organization, event, or another entity. The available properties depend on the website.

**Important:** The example selector wait assumes that the page contains at least one JSON-LD script. If the page does not contain that selector, rendering raises `RenderTimeoutError`. Omit `wait_for_selector` when the element is optional, or handle the timeout if you want to continue without it.

## Working with HTML

The `html` attribute contains the serialized page DOM. You can process it with Beautiful Soup, lxml, or another HTML parser.

### Example: Extract all links

```python
from bs4 import BeautifulSoup
from urlrender import Renderer

with Renderer() as renderer:
    result = renderer.render("https://example.com")

soup = BeautifulSoup(result.html, "html.parser")

for link in soup.select("a[href]"):
    print(link.get_text(" ", strip=True), link["href"])
```

### Example: Extract headings

```python
from bs4 import BeautifulSoup
from urlrender import Renderer

with Renderer() as renderer:
    result = renderer.render("https://example.com")

soup = BeautifulSoup(result.html, "html.parser")

for heading in soup.select("h1, h2, h3"):
    print(heading.get_text(" ", strip=True))
```

### Example: Save rendered HTML to a file

```python
from pathlib import Path
from urlrender import Renderer

with Renderer() as renderer:
    result = renderer.render("https://example.com")

Path("rendered.html").write_text(
    result.html,
    encoding="utf-8",
)
```

You can open the saved HTML in an editor for inspection. Keep in mind that external scripts, stylesheets, images, and other resources may not load correctly when the file is opened locally.

## Troubleshooting

### Chromium executable not found

**Symptom:** Playwright reports that the browser executable does not exist.

**Solution:**

```bash
python -m playwright install chromium
```

Run the command in the same Python environment where Playwright is installed.

### `net::ERR_NAME_NOT_RESOLVED`

**Meaning:** Chromium could not resolve the requested hostname through DNS.

**What to check:**

- Confirm the URL is spelled correctly.
- Check your internet connection and DNS configuration.
- Check whether a VPN or proxy affects hostname resolution.
- Try navigating to the URL in another browser or testing it with a command-line HTTP client.

This error does not necessarily indicate a bug in `urlrender`.

### `RenderTimeoutError`

**Meaning:** A navigation or rendering operation exceeded its timeout.

**Possible solutions:**

- Increase `timeout`.
- Check whether the website is responding slowly.
- Use an appropriate `wait_until` value.
- Check whether the requested selector actually exists.
- Ensure you are not waiting for a hidden element to become visible.

For example, a script element should normally be waited for using the attached state rather than the visible state.

Increasing the timeout is not a guaranteed solution when a page never produces the requested element.

### The page opens, but the HTML is incomplete

**Possible reasons:**

- JavaScript is still loading additional content.
- The website loads data after scrolling.
- The content appears only after a user interaction.
- The requested selector is not specific enough.
- The website returned a challenge page or an error page.

Use `wait_for_selector` when a known element indicates that the content you need has appeared.

Some pages require additional interaction, such as clicking a button, scrolling, or selecting a tab. The current API does not automate those interactions automatically.

### The browser displays a CAPTCHA or access-denied page

Some websites use anti-bot systems, rate limiting, or access controls.

`urlrender` does not guarantee that a website will allow automated access. A successful browser navigation does not necessarily mean that the intended content was returned.

Check the page title, status code, final URL, and rendered HTML to determine whether you received the expected content.

Use permitted access methods and respect the website's terms and access restrictions.

### The status code is `None`

The status code is `None` when Playwright does not provide a main navigation response, such as in certain navigation scenarios.

This does not necessarily mean the page contains no HTML. Inspect the returned HTML, title, and final URL to understand the result.

### The page is slow

Try the default `domcontentloaded` event rather than waiting for `load` or `networkidle`, and wait for a specific selector if you need a particular element.

```python
with Renderer(
    wait_until="domcontentloaded",
    timeout=15_000,
) as renderer:
    result = renderer.render(
        "https://example.com",
        wait_for_selector="main",
    )
```

Choose a selector that reflects the content you actually need.

## Performance Considerations

Browser rendering is more resource-intensive than downloading HTML with a basic HTTP client because Chromium executes JavaScript and manages browser contexts.

For better performance:

1. **Reuse the renderer.** Avoid launching a new browser for every URL.
2. **Choose an appropriate navigation event.** Use `domcontentloaded` when you do not need to wait for every resource.
3. **Use targeted selector waits.** Wait for the relevant content instead of adding unnecessary delays.
4. **Set reasonable timeouts.** Avoid allowing one slow page to block your workflow for too long.
5. **Process pages sequentially when resources are limited.** Running many browser instances simultaneously can consume substantial memory and CPU.
6. **Avoid redundant rendering.** Use one `RenderResult` when you need multiple attributes from the same page.

Actual rendering time depends on the website, network conditions, JavaScript execution, and the resources available to the machine.

## Limitations

`urlrender` is a browser-rendering library, not a complete web-scraping framework.

The current implementation has the following limitations:

- It does not automatically bypass CAPTCHAs, bot protection, access restrictions, or rate limits.
- It does not guarantee that every website will render successfully.
- It does not automatically click buttons, scroll pages, or interact with forms.
- It does not automatically paginate through results.
- It does not parse JSON-LD, metadata, or website-specific data into structured objects.
- It does not provide a persistent session or cookie-management API.
- It does not expose a dedicated asynchronous API.
- It does not provide built-in proxy configuration or browser fingerprint customization.
- It does not automatically retry failed navigation.
- It does not guarantee that dynamically loaded content will be complete when the result is returned.
- It does not automatically determine whether a returned page is an error page, a CAPTCHA, or the intended content.

These features can be implemented separately when required by a particular application.

## Security Considerations

`urlrender` navigates to URLs using a real browser. Treat URLs as untrusted input when building applications around it.

If you expose a renderer through a web API or service, take precautions against server-side request forgery (SSRF). An attacker may attempt to make the browser access internal services or restricted network resources.

Consider the following safeguards:

- Restrict permitted URL schemes to HTTP and HTTPS.
- Validate and allowlist hostnames when possible.
- Block access to loopback, private, link-local, and other restricted IP ranges where appropriate.
- Revalidate destinations after redirects.
- Consider DNS rebinding and changes in resolved IP addresses.
- Apply network-level restrictions to prevent access to internal infrastructure.
- Set timeouts and resource limits.
- Avoid rendering untrusted URLs with access to sensitive local files, credentials, or privileged network resources.

URL validation alone is not a complete SSRF defense. Applications exposed to untrusted users should enforce appropriate network-level protections.

## Contributing

Contributions, bug reports, and suggestions are welcome.

When reporting an issue, include:

- Python version
- Operating system
- Installed `urlrender` and Playwright versions
- A minimal reproducible example
- The exception and relevant traceback
- Whether the issue occurs in headless mode, visible mode, or both

Please avoid including passwords, authentication tokens, private cookies, or other sensitive information in issue reports.

### Development setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/YOUR_USERNAME/urlrender.git
cd urlrender
```

Replace the repository URL with the actual public repository.

Create and activate a virtual environment:

```bash
python -m venv venv
```

On macOS and Linux:

```bash
source venv/bin/activate
```

On Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install the package in editable mode:

```bash
python -m pip install -e .
python -m playwright install chromium
```

Run the example test script:

```bash
python test.py
```

If you add automated tests, please include them in your contribution and ensure they do not depend unnecessarily on a single third-party website.

## License

`urlrender` is distributed under the MIT License.

See the [LICENSE](LICENSE) file for the complete license text.

---

**Built with Python and Playwright.**
