# 565software.github.io

## クロール・検索インデックス制御方針
- 本サイトの HTML ページは `_layouts/default.html` で `<meta name="robots" content="noindex, nofollow, noarchive">` を指定し、検索エンジンへのインデックスを抑止しています。
- Googlebot 等のクローラーが `noindex` タグを読み取れるよう、`robots.txt` でサイト全体（`Disallow: /`）をブロックしないでください（ブロックすると HTML 内の `noindex` が検出されず、「robots.txt によりブロックされましたが、インデックスに登録しました」として URL のみインデックスされてしまいます）。
- ただし画像ファイル（特商法画像 `tokushoho.png` など）は meta タグで保護できないため、`robots.txt` にて `Disallow: /assets/images/` を設定して画像検索や OCR から保護しています。
