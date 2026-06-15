# Future Work

## Requires A Valid Census API Key

- Regenerate ACS-normalized resident and household request rates.
- Add demographic context overlays for poverty rate, no-vehicle households, and median household income.
- Compare area-density rankings against population-normalized rankings.

## Requires More Data Pulls

- Extend the analysis to a full year.
- Add quarter-over-quarter and month-over-month trend comparisons.
- Add persistence flags for districts or categories that remain high burden across time.

## Optional Analytical Enhancements

- Replace rounded-coordinate repeat screening with DBSCAN or H3 grid clustering.
- Add category-specific burden scores.
- Add confidence or data-quality notation to every district ranking.
- Move large generated datasets to GitHub Releases if repository size becomes a concern.

## Static GIS Presentation Enhancements

- Export the Markdown report to a paginated PDF after a visual QA pass.
- Add a second formal map plate for repeat-location clusters.
- Add static small-multiple plates for unresolved share, long-resolution share, and repeat-cluster share.
