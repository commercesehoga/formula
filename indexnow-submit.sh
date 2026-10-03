#!/usr/bin/env bash
# Submit all sitemap URLs to IndexNow (Bing, Yandex and other participating engines).
# Usage: ./indexnow-submit.sh   (run from the project root, after deploying)
set -euo pipefail

HOST="formula.thunderstudy.indevs.in"
KEY="74b39007c625b7ee839013b618e29a79"
KEY_LOCATION="https://$HOST/$KEY.txt"
SITEMAP="${1:-sitemap.xml}"

[ -f "$SITEMAP" ] || { echo "Cannot find $SITEMAP" >&2; exit 1; }

URLS=$(grep -o '<loc>[^<]*</loc>' "$SITEMAP" | sed -e 's#<loc>##' -e 's#</loc>##')
[ -n "$URLS" ] || { echo "No URLs found in $SITEMAP" >&2; exit 1; }

URL_JSON=$(printf '%s\n' "$URLS" | sed 's#.*#    "&"#' | paste -sd, - | sed 's#,#,\n#g')

BODY=$(cat <<JSON
{
  "host": "$HOST",
  "key": "$KEY",
  "keyLocation": "$KEY_LOCATION",
  "urlList": [
$URL_JSON
  ]
}
JSON
)

echo "Submitting $(printf '%s\n' "$URLS" | wc -l | tr -d ' ') URLs to IndexNow..."
curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
  -X POST "https://api.indexnow.org/indexnow" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$BODY"
echo "200 or 202 means accepted."
