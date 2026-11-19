# 565software.github.io

## クロール・検索インデックス制御方針
- 本サイトの公開ページは既定で検索エンジンへのインデックスを許可し、`sitemap.xml` に自動で列挙されます。
- 検索エンジンへ掲載したくないページ（特定商取引法に基づく表記 `tokushoho.md` など）は、front matter で `noindex: true` を指定して `_layouts/default.html` から `<meta name="robots" content="noindex, nofollow, noarchive">` を出力し、`sitemap.xml` からも除外します。
- Googlebot 等のクローラーが `noindex` タグを読み取れるよう、`robots.txt` でサイト全体（`Disallow: /`）をブロックしないでください（ブロックすると HTML 内の `noindex` が検出されず、「robots.txt によりブロックされましたが、インデックスに登録しました」として URL のみインデックスされてしまいます）。
- ただし画像ファイル（特商法画像 `tokushoho.png` など）は meta タグで保護できないため、`robots.txt` にて `Disallow: /assets/images/` を設定して画像検索や OCR から保護しています。製品ページ用の公開画像は `assets/mvsync/` など別ディレクトリに配置してください。

## 製品アセットの更新（MVsync）
- `mvsync` リポジトリで `STORE_DEVICE=phone npm run store` を実行してスクリーンショット等を生成したあと、本リポジトリで以下を実行すると、LP 用の画像を取り込んで WebP 変換・軽量化します。
  ```bash
  python3 scripts/sync_mvsync_assets.py
  ```
