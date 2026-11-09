# 荷比德冬季旅行手冊

`python3 src/build.py` 以標準函式庫產生 GitHub Pages 使用的 `index.html`，寫入前會檢查公開版隱私規則。不要手改產出檔。

本機預覽：

```sh
python3 src/build.py
python3 -m http.server 8765
```

打開 [本機預覽](http://localhost:8765/)。可直接跳到 [布魯日章節](http://localhost:8765/#c-bru)、[12/14 行程](http://localhost:8765/#d1214) 或 [科隆吃喝](http://localhost:8765/#g-kol)。

- `src/booklet_data.py`：行程資料、章節順序、圖說與替代文字。
- `src/build.py`、`src/book.css`：模板、版面和行程工具。
- `assets/img/photos.json`：照片來源、授權、焦點與裁切；[照片完整署名](assets/img/CREDITS.md) 也可從網頁頁尾打開。
- `assets/fonts/`：隨站字型與 OFL 授權。正文字型依裝置，書名與扉頁使用 Noto Serif TC 子集，數字使用 Source Serif 4 和 Source Code Pro。

需要更新照片時才安裝 Pillow（`python3 -m pip install -r requirements.txt`），執行 `python3 src/images.py [照片代號...]` 重做 WebP 與署名。原始照片不隨站發佈，可由署名連回 Wikimedia Commons。編輯預覽在 PR 驗收後再合併至 Pages 使用的 main。
