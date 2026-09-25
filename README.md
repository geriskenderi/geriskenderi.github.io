# Geri Skenderi — personal website

The Hugo source lives at the repository root. GitHub Actions builds and checks the site before deploying it to GitHub Pages.

## GitHub Pages setup

1. Commit and push this source to `geriskenderi/geriskenderi.github.io` on `master` (the current default branch).
2. In the repository's **Settings → Pages → Build and deployment**, set **Source** to **GitHub Actions**.
3. In **Actions**, open **Build and deploy Hugo site** and select **Run workflow** on the default branch if the initial push ran before Pages was enabled.
4. Wait for both **Build and check** and **Deploy to GitHub Pages** to pass. The deployment links to the published site.

The workflow runs on pushes to `master` or `main`, pull requests, and manual dispatch. Only the default branch can deploy. If the `github-pages` environment has branch restrictions, allow that branch in **Settings → Environments**. A personal access token is not required.

Pull requests build and check the site without publishing. Checks cover internal links, assets, fragments, canonical URLs, and basic HTML accessibility. A second build checks paths under a project subdirectory. Deployment uses the URL supplied by GitHub Pages, including any configured custom domain.

Commit the source directories, `hugo.toml`, `scripts`, and `.github`. Hugo generates `public/` and `resources/`; both are ignored. Keep only this Pages deployment workflow when replacing the previous site.

## Local development

Use Hugo Extended **0.115.3**, matching the workflow, and Python **3.9 or later**. This site does not require Node.js, Sass, or a theme download.

```sh
hugo server
```

To run the production build and checks:

```sh
hugo --gc --minify
python scripts/check_site.py public --base-url https://geriskenderi.github.io/
```

The workflow verifies the downloaded Hugo archive against the release checksums. Update `HUGO_VERSION` deliberately and run the checks when upgrading.
