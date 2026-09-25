import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids = set()
        self.links = []
        self.issues = []
        self.headings = []
        self.main_count = 0
        self.title = False
        self.description = False
        self.canonical = ''
        self.lang = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identifier = attrs.get('id')
        if identifier:
            if identifier in self.ids:
                self.issues.append(f'duplicate ID: {identifier}')
            self.ids.add(identifier)
        if tag == 'html':
            self.lang = bool(attrs.get('lang'))
        if tag == 'title':
            self.title = True
        if tag == 'main':
            self.main_count += 1
        if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.headings.append(int(tag[1]))
        if tag == 'meta' and attrs.get('name') == 'description':
            self.description = bool(attrs.get('content'))
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonical = attrs.get('href', '')
        if tag == 'img' and not attrs.get('alt'):
            self.issues.append('image missing descriptive alt text')
        if tag == 'iframe' and not attrs.get('title'):
            self.issues.append('iframe missing a title')
        if tag == 'nav' and not (attrs.get('aria-label') or attrs.get('aria-labelledby')):
            self.issues.append('navigation missing a label')
        for key in ('href', 'src'):
            if attrs.get(key):
                self.links.append(attrs[key])
        if tag == 'meta' and attrs.get('property') == 'og:image':
            self.links.append(attrs.get('content', ''))


def check(root, base_url):
    root = root.resolve()
    base_url = base_url.rstrip('/') + '/'
    base = urlsplit(base_url)
    pages = {}
    problems = []
    checked_links = 0
    for path in sorted(root.rglob('*.html')):
        page = Page(path)
        page.feed(path.read_text(encoding='utf-8'))
        pages[path] = page
    if not pages:
        problems.append('No HTML files found. Run hugo --minify first.')
    for path, page in pages.items():
        relative = path.relative_to(root).as_posix()
        route = relative.removesuffix('index.html')
        page_url = urljoin(base_url, route)
        if not page.lang:
            page.issues.append('missing HTML language')
        if not page.title or not page.description:
            page.issues.append('missing title or description')
        if page.main_count != 1:
            page.issues.append('page must contain exactly one main landmark')
        if page.headings.count(1) != 1:
            page.issues.append('page must contain exactly one h1')
        if any(b > a + 1 for a, b in zip(page.headings, page.headings[1:])):
            page.issues.append('heading levels skip a level')
        if page.canonical != page_url:
            page.issues.append(f'canonical URL is {page.canonical!r}; expected {page_url!r}')
        for raw in page.links:
            target = urlsplit(urljoin(page_url, raw))
            if target.scheme not in ('http', 'https') or target.netloc != base.netloc:
                continue
            checked_links += 1
            target_path = unquote(target.path)
            if not target_path.startswith(base.path):
                page.issues.append(f'link escapes site base path: {raw}')
                continue
            local = (root / target_path[len(base.path):]).resolve()
            if not local.is_relative_to(root):
                page.issues.append(f'link escapes output folder: {raw}')
                continue
            if local.is_dir():
                local /= 'index.html'
            if not local.is_file():
                page.issues.append(f'missing internal target: {raw}')
            elif target.fragment and local in pages and unquote(target.fragment) not in pages[local].ids:
                page.issues.append(f'missing fragment target: {raw}')
        problems.extend(f'{relative}: {issue}' for issue in page.issues)
    if problems:
        print('\n'.join(problems))
        raise SystemExit(1)
    print(f'PASS: {len(pages)} HTML pages, {checked_links} internal references, and HTML accessibility basics.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check a generated static site.')
    parser.add_argument('directory', nargs='?', type=Path, default=Path('public'))
    parser.add_argument('--base-url', default='https://geriskenderi.github.io/')
    options = parser.parse_args()
    check(options.directory, options.base_url)
