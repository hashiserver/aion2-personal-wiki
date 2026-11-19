# AION2 ポータル

日本・グローバル版AION2の個人用非公式ポータル。公開情報をAIで整理し、やることと参照先を短く案内します。

公開先：https://aion2-personal-wiki.hashimo326.workers.dev/

## ページ構成

主ナビは7項目です。

- `/`：毎日・上限・週課の要点と受取期限を表示。詳しい手順と更新履歴は展開式。
- `/progression/`：IL700〜3000の解放コンテンツと、次に達するための装備・アルカナ・遠征の優先行動。
- `/duty/`：任務と指令書の受け方、報酬選定の手引き。
- `/events/`：イベント、クーポン・受取、更新・メンテナンスを掲載。終了済みとパッチ履歴は展開式。
- `/gear/`：8クラス比較と強化・継承。チャンターはGlobal版の優先・妥協候補を掲載し、各職の韓国PvE採用率は参考資料として扱います。スマホでは部位ごとに表示します。
- `/pets/`：黒雲貿易団の魔族向け購入候補（92種・あいうえお順）。ペット名・よみがな・入手区分・種族で絞り込めます。スマホでは横スクロールなしで入手先まで表示し、チェックはlocalStorageに保存します。
- `/links/`：チャンターを最初に、他7職を展開式で表示。マップと計算機も掲載。

`/gear/transfer/`は低IL唯一装備の強化・継承と良オプション維持の判断表。通常継承・魂魄装備の固定魂刻印ルート・引き継げない成長要素を区別し、台湾公式とGlobal第三者解説の地域差も明記。

`/sources/`はフッターから開くサイト方針です。計17ページ。参照先と重複する17記事は公開本文から外し、旧URLは`_redirects`で関連ページへ302案内します。以前の記事はGit履歴に残ります。

## デザインと情報選択

ui-ux-pro-maxを読み込み、情報階層・最小限のナビ・読みやすい文字・タッチ領域を見直しました。判断の記録は`docs/design-decisions.md`。

大きなヒーロー、二重ナビ、独自ビルド表を置かず、まず行動リストを表示。増え続ける更新履歴は本文ごと消さずに折りたたみ、日々の掲載更新にも追従します。終了済みイベントも折りたたみます。細かな攻略・スキル回し・素材情報は外部ガイドへ任せ、出典は各ページ下部から確認できます。

## 生成・検証

Python3.9以上。

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests -v
python3 build.py
python3 checks/check_site.py dist
```

開閉にはHTML標準の `details` を使います。トップとイベントページは期限判定、ペット購入は完了チェックと絞り込みにページ専用のJavaScriptを使います。ペットのチェックはブラウザのlocalStorageに保存します。

## Workers向けの配信最適化

- サイト内リンクは `/events/` のような公開URLに統一し、`index.html` からの転送を省きます。生成HTMLはHTTP配信向けです。
- CSSは内容ハッシュ付きのファイル名で出力し、生成する `dist/_headers` で1年間のimmutableキャッシュを指定。CSS変更時はURLも変わります。旧 `assets/style.css` は既存ページとの互換用に残します。
- HTMLは毎回再検証し、イベントや週課の更新が古いキャッシュに固定されないようにします。
- 背景色をhead内に指定し、スクロールバーの領域を確保します。対応ブラウザでは、主要ナビや装備メニューのリンクにポインターを置くと、Speculation Rulesで遷移先のHTMLを先読みします。
- Workers Static Assetsで直接配信します。ペットの絞り込みは各行の表示だけを更新し、完了状態を変更したときに対象行を移動します。

Astroは将来の静的生成・コンポーネント管理の候補です。現状は少数ページの静的出力で、移行自体による速度改善は保証されないため今回は維持しています。Svelteは操作が複雑になった部分、HonoはAPI等のリクエスト処理が必要になった場合に検討します。

仕様の参照先：[Workers HTML handling](https://developers.cloudflare.com/workers/static-assets/routing/advanced/html-handling/)、[Workers Headers](https://developers.cloudflare.com/workers/static-assets/headers/)、[View Transition](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API/Using)。

## 更新する場所

`data/portal.json`：日課・週課・イベント・外部リンク。`data/pets.json`：ペット購入優先分類・生息地の根拠（変更時は `tests/test_pets.py` の件数も確認）。`content/progression.md`：IL解放と進行のロードマップ。`content/`：見出しと補足。`data/sources.json`：出典のURL・対象版・確認日。

イベントの `starts_on` と `ends_on` はJSTの日付です。正確な時刻が確認できた場合は、オフセット付きISO 8601の `starts_at` と `ends_at` を指定します。日付だけの場合、当日は「公式で確認」と表示します。地域によって期間が異なる場合は `status_basis` と本文に対象を明記します。

## 公開設定

Cloudflare Workers Static Assetsで`dist`を配信。Git連携は`main`、ルートはリポジトリ直下。

- ビルド：`python3 -m pip install -r requirements.txt && python3 build.py`
- デプロイ：`npx wrangler deploy`

`wrangler.json`の公開先を維持しています。`_redirects`はビルド時に`dist`へコピーされます。

Cloudflare公式：https://developers.cloudflare.com/workers/static-assets/redirects/

## 確認範囲

ユニットテストと全生成ページの内部リンクを検証しています。2026年11月19日の更新では、Chromiumで画面幅320〜1,366pxの表示、期限切り替え、週課への移動、ペットの絞り込みと保存を確認しました。公開環境のCore Web Vitalsは未計測です。

ゲーム情報はページごとに確認日を記録しています。公式ガイドには9月30日時点の説明を含み、現行の残り回数・条件はゲーム内を優先します。最適DPSや全ビルドを実測したサイトではありません。
