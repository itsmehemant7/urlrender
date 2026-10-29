
from urlrender import Renderer


def main():
    url = "https://www.imdb.com/title/tt43595281/"

    with Renderer(headless=True) as renderer:
        result = renderer.render(url, wait_for_selector='script[type="application/ld+json"]',)

        print("URL:", result.url)
        print("Status Code:", result.status_code)
        print("Title:", result.title)
        print("Elapsed Time:", result.elapsed_ms, "ms")

        print("\n--- HTML (first 500 characters) ---")
        print(result.html[:500])

        print("\n--- Visible Text ---")
        print(result.text[:500])

        # Test convenience methods
        # html = renderer.get_html(url)
        # print("\nHTML extraction successful:", bool(html))

        # text = renderer.get_text(url)
        # print("Text extraction successful:", bool(text))


if __name__ == "__main__":
    main()
