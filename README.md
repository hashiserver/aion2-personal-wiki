# AION2 プレイポータル

日本・グローバル版の個人利用向け非公式ポータル。イベント・日課・週課と外部ツールを中心に、初心者メモと8職のガイド比較をまとめます。AIを活用した公開情報の整理、情報源タグ、確認日、対象地域を各ページに表示します。ポータルの確認日：2026年10月19日（JST）。既存の初心者メモはページごとに確認日が異なります。

## すぐ読む

`dist/index.html`をブラウザで開くと、ネット接続なしでも本文・表・ページ移動を使えます。外部の出典リンクを開くときのみネット接続が必要です。ZIPを展開してから開いてください。

## 現在の公開サイト（Workers Static Assets）

https://aion2-personal-wiki.hashimo326.workers.dev/

2026年10月6日に公開済みです。現在はCloudflare Workersの静的アセット配信で動いています。`wrangler.json`で`dist`の配信と末尾スラッシュ付きURLを指定しています。Workerの実行コードは含めていません。

Git連携の設定は、ブランチ`main`、ルートはリポジトリ直下、ビルドコマンド`python3 -m pip install -r requirements.txt && python3 build.py`、デプロイコマンド`npx wrangler deploy`です。Cloudflare側でこのリポジトリのGit連携が有効なら、push後に再ビルド・公開されます。

公式手順：https://developers.cloudflare.com/workers/static-assets/

## Cloudflare Pagesで公開する場合

以下は別途Pagesを作成する場合の手順です。現在のWorkers公開には使用しません。

1. Cloudflareダッシュボードで「Workers & Pages」を開きます。
2. Pagesのプロジェクトを作成し、静的ファイルを直接アップロードする方法を選びます。画面のラベルは更新で変わる場合があります。
3. `dist`の中身（`index.html`、`assets`、各ページのフォルダ）をアップロードします。`dist`自体を上位階層として含めないでください。
4. 公開するとCloudflareが`<プロジェクト名>.pages.dev`のURLを発行します。トップと職業ページが開けることを確認します。

アップロード専用ZIP `aion2-wiki-pages.zip` は `index.html`を最上位に置いています。ダッシュボードからこのZIPを使えます。

公式手順：https://developers.cloudflare.com/pages/get-started/direct-upload/

静的ファイルへのアクセスは無料・無制限です。Functionsは使っていません。独自ドメインを購入しない限りドメイン費用も不要です。Git連携の無料枠は月500ビルド。最新条件は公式をご確認ください。

- https://developers.cloudflare.com/pages/functions/pricing/
- https://developers.cloudflare.com/pages/platform/limits/

### Gitで更新する場合

このフォルダをGitHubリポジトリとして管理し、Cloudflare PagesのGit連携を使用します。ルートディレクトリはこのREADMEのあるフォルダ、ビルドコマンドは`python3 -m pip install -r requirements.txt && python3 build.py`、公開ディレクトリは`dist`です。

直接アップロードからGit連携へは後で切り替えられないため、Git連携を希望する場合は最初からその方法でプロジェクトを作成してください。利用するPython版は3.9以上を指定します。

## ローカルで生成・確認

Python 3.9以上で実行します。

```bash
python3 -m pip install -r requirements.txt
python3 build.py
python3 -m unittest discover -s tests -v
python3 checks/check_site.py dist
python3 -m http.server 8080 --directory dist
```

## 記事の更新

トップのカード・日課要約は`data/portal.json`、詳細記事は`content/`のMarkdownを編集し、必要な出典を`data/sources.json`へ追加します。記事の先頭行はJSONメタデータで、`slug`、`title`、`checked_at`、`source_ids`を指定します。トップの`slug`は空文字です。

本文では`[[source:出典ID]]`を使うと、その情報源タグとページ内の出典リンクになります。表の行ごとに付けられます。参照IDは記事の`source_ids`にも登録してください。

公開日が不明な出典は`published_at: null`にします。確認日と公開日を混同せず、`scope`に対象パッチや未照合の範囲を書きます。更新後は生成・リンク検証を行い、`dist`を再公開します。内容は自動で収集・更新されません。`portal.json`の`checked_at`はトップ記事の確認日と一致させてください。イベント状態は確認日を基準に生成し、終了日は「終了日・公式確認」として正確な終了時刻を捏造しません。現在日の自動判定や期限後の自動再収集はありません。

## 確認範囲

- 初心者の進行、日課・週課、職業比較、8職の育成ビルド、装備、ダンジョン、差分、用語、カバン整理、ディーヴァニオン、イベント、リンク集、ビルド比較の21ページ。
- 67件の出典・参考リンクを管理。全67件を検証済み攻略根拠として扱っているわけではありません。
- 日本公式の報酬期限と国内記事に1時間の差があるため、日本公式の15:30 JSTを採用。
- 職業別ガイドは育成・Lv45・用途別にリンク。gaming.toolsの初期ソロ周回表示と、装備完成後の作者ガイドを同じ条件として比較しません。旧Lv22配分は10月6日・2.0.5.0の参考記録として区別。
- イベント3件は日本語公式本文を参照し、開催期間とアイテム期限を区別。新規出席、ハロウィン、サービス開始記念報酬を掲載。
- 日課・週課は公式ガイドとGlobal解析を区別。公式の使命クエスト5個は同時進行数であり日次上限とは扱いません。
- 全8職の育成ガイドをLv22に切り替え、盤面の取得済み表示と追加ノードを集計。レベル報酬44ポイントを基準にした参考配分を掲載。ソーサラーは43使用・1残し。初期化費用と返還量は日本版未確認。
- 日本版の全職最終ビルド、同条件DPS、職業別PvP、全ボスの攻撃順は未確定。
- Xの取得不能な投稿と本文取得不能な台湾公式ガイドからは、仕様・性能を確定していません。
- 他サイトの画像・記事本文をまとめて転載していません。要約や表示内容の出典は各ページに掲載しています。

## 検証結果

生成・検証テスト15項目と、21ページの内部リンク・出典アンカー検証に合格しました。スマホ・200%拡大時の実機確認は未完了です。2026年10月6日に公開サイトのPC表示、育成ページから職業ページへの移動、情報源タグから出典への移動をブラウザで確認しました。CSS上はレスポンシブ表示と表内スクロールを実装していますが、実機での見え方は公開前に確認してください。

## 構成

`build.py`：静的HTML生成と記事・出典の検証。`portal.py`：トップ用カードの安全なHTML生成。`assets/style.css`：共通スタイル。`templates/page.html`：共通レイアウト。`checks/check_site.py`：リンク確認。閲覧側にJavaScript、DB、API、外部フォントはありません。
