# AION2 ポータル

日本・グローバル版AION2の個人用非公式ポータル。公開情報をAIで整理し、やることと参照先を短く案内します。

公開先：https://aion2-personal-wiki.hashimo326.workers.dev/

## ページ構成

主ナビは3項目だけです。

- `/`：日課・週課。行動の要約、蓄積上限・週制限の確認。
- `/events/`：イベント期間・やること・受取期限。詳細は公式へ。
- `/links/`：ビルド・ツール。8職の育成/Lv45配分、マップ・計算機などへ直接リンク。

`/sources/`はフッターから開くサイト方針です。計4ページ。参照先と重複する17記事は公開本文から外し、旧URLは`_redirects`で関連ページへ302案内します。以前の記事はGit履歴に残ります。

## デザインと情報選択

ui-ux-pro-maxを読み込み、情報階層・最小限のナビ・読みやすい文字・タッチ領域を見直しました。判断の記録は`docs/design-decisions.md`。

大きなヒーロー、二重ナビ、独自ビルド表、長い比較文を廃止。細かな攻略・スキル回し・素材情報は外部ガイドへ任せます。情報源は各ページ下部から開けます。

## 生成・検証

Python3.9以上。

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 build.py
python3 checks/check_site.py dist
```

閲覧時のJavaScript、DB、API、外部フォント、画像リソースはありません。

## 更新する場所

`data/portal.json`：日課・週課・イベント・外部リンク。`content/`：見出しと短い補足。`data/sources.json`：出典のURL・対象版・確認日。トップとデータの確認日を一致させてください。イベント状態は確認日時点の記録で、自動更新ではありません。

## 公開設定

Cloudflare Workers Static Assetsで`dist`を配信。Git連携は`main`、ルートはリポジトリ直下。

- ビルド：`python3 -m pip install -r requirements.txt && python3 build.py`
- デプロイ：`npx wrangler deploy`

`wrangler.json`の公開先を維持しています。`_redirects`はビルド時に`dist`へコピーされます。

Cloudflare公式：https://developers.cloudflare.com/workers/static-assets/redirects/

## 確認範囲

16テストと4ページの内部リンク検証。ゲーム情報は2026年10月19日確認時点。公式ガイドには9月30日時点の説明を含み、現行の残り回数・条件はゲーム内を優先します。最適DPSや全ビルドを実測したサイトではありません。
