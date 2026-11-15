---
name: spring-boot-bug-check
description: 導入中の Spring Boot バージョン（既定 3.1.1）以降に公開された、サーバダウン・プロセスダウン・データ破壊などにつながる重大な非セキュリティ不具合を spring.io / GitHub から調べ、パッチ適用検討用のレポートを作る。CVE と脆弱性情報は対象外。「Spring Boot の不具合チェック」「Spring Boot の重大バグ確認」「SpringBoot パッチ検討」などで使う。
---

# Spring Boot 重大不具合チェック

導入中バージョン以降に見つかった **重大不具合** を洗い出し、パッチ適用要否の判断材料をまとめる。

## パラメータ

- 導入バージョン: 引数で指定があればそれを使う。なければ `3.1.1`。
- 前回チェック日: `reports/` 内の最新レポートの日付。なければスキルディレクトリ直下にある日付付きレポートを確認する。それもなければ導入バージョンのリリース日を起点にする。

以下 `CUR`＝導入バージョン（既定 3.1.1）、`GEN`＝世代（既定 3.1.x）、`GEN_SHORT`＝世代の短縮表記（既定 3.1）、`SINCE`＝起点日（YYYY-MM-DD）とする。

## 前提知識（毎回 API で再確認すること）

- サポート終了日や最新パッチは固定値を使わず、毎回公式 API で GEN の最新情報を確認する。
- `CUR` 以降にリリースされた GEN 内のパッチで修正された不具合を確認する。後継世代で修正された不具合も、変更内容と `CUR` のコード・依存バージョンを照合し、影響可能性があるものを調べる。
- 対象はセキュリティ脆弱性ではなく、サーバダウン、プロセスダウン、データ破壊・消失など運用上の重大な不具合とする。CVE、セキュリティアドバイザリ、脆弱性情報は別調査のため、影響度や修正内容にかかわらず対象外とする。
- Spring Boot 自体に加え、アプリケーションで実際に使用している同梱依存ライブラリの非セキュリティ不具合も確認する。

## 手順

GitHub API は未認証だと 1 時間 60 リクエストまで。`GITHUB_TOKEN` 環境変数があれば `-H "Authorization: Bearer $GITHUB_TOKEN"` を付ける。

### 1. サポート状況と最新パッチを確認

```bash
curl -sL "https://api.spring.io/projects/spring-boot/generations/GEN"
curl -sL "https://api.spring.io/projects/spring-boot/generations" | grep -E '"name"|EndDate|"oss"|"enterprise"'
```

`ossSupportEndDate`、`commercialSupportEndDate`、`latestPatch.oss` / `latestPatch.enterprise` を記録する。CUR より新しいパッチがあれば、入手可能な区分（OSS / 商用）を明記し、そのリリースノートも手順 2 の対象に加える。API で確認できない場合は推測せず「確認できず」とする。

### 2. CUR 以降のリリースとリリースノートを取得

```bash
curl -s "https://api.github.com/repos/spring-projects/spring-boot/releases?per_page=50"
```

- `published_at` が SINCE より後の GA 版（`-M` / `-RC` を除く）を対象にする。ページングが必要な場合は続きも取得する。
- GEN 内の CUR より新しいリリースを優先して確認する。後継世代のリリースノートも、CUR に影響し得る変更を見落とさない範囲で調べる。
- 各リリースの `body` から「Bug Fixes」と「Dependency Upgrades」を読み、セキュリティ修正やCVEに該当する記載は除外する。
- 依存ライブラリのアップグレードは、CUR が管理するバージョンとの差分を把握する。プロジェクトがある場合は実際の依存解決結果を優先し、ない場合は Spring Boot `CUR` の dependency management / BOM を参照する。世代の一覧確認には `https://docs.spring.io/spring-boot/GEN_SHORT/appendix/dependency-versions/coordinates.html` を使う。

### 3. 修正済みバグ issue を検索

```bash
# SINCE 以降に close された非セキュリティ bug
curl -s "https://api.github.com/search/issues?q=repo:spring-projects/spring-boot+is:issue+label:%22type:+bug%22+closed:>SINCE&per_page=100"
# 重大キーワードで絞り込み（キーワードを変えて複数回）
curl -s "https://api.github.com/search/issues?q=repo:spring-projects/spring-boot+is:issue+closed:>SINCE+%22memory+leak%22&per_page=50"
```

キーワード例: `memory leak`, `deadlock`, `OutOfMemoryError`, `hang`, `thread`, `shutdown`, `startup fails`, `data loss`, `corrupt`, `transaction`, `connection pool`, `regression`, `NullPointerException`, `StackOverflowError`, `infinite loop`, `100% CPU`。

各 issue の `milestone.title` を見て、どの版で修正されたか確認する。後継世代でのみ修正された bug は、本文・関連 PR・変更対象ファイルを見て CUR にも該当コードがあるか判断する（判断できなければ「要確認」とする）。脆弱性やCVEに関する issue / PR は調査結果に含めない。

### 4. 主要依存ライブラリ（利用しているもののみ）

利用状況が分からない場合は、カレントディレクトリに `pom.xml` / `build.gradle(.kts)` があれば読み、なければ Spring Framework と組み込みサーバー（既定は Tomcat）を確認して、その制約をレポートに書く。対象ライブラリのセキュリティ情報・CVE は調べない。

- Spring Framework: `https://api.github.com/repos/spring-projects/spring-framework/releases` と非セキュリティ bug issue（Boot と同じ方法）
- Tomcat: https://tomcat.apache.org/tomcat-10.1-doc/changelog.html
- その他は各プロジェクトのリリースノートや bug issue

### 5. 重大度で分類

各非セキュリティ不具合を次の基準で分類する。影響を受ける条件と重大度の根拠を書く。

| 区分 | 基準 |
|---|---|
| **Critical** | サーバダウン / プロセスダウン、データ破壊・消失 |
| **High** | メモリリーク・スレッドリーク、デッドロック・ハング、起動不能、トランザクション不整合など、可用性やデータ整合性に重大な影響を及ぼすもの |
| **Medium** | 特定条件での機能不全、性能劣化など、影響が限定的なもの |
| 対象外 | CVE・脆弱性・セキュリティアドバイザリ、ドキュメント、テスト支援、開発ツール（DevTools、Docker Compose サポート等の開発時専用機能）、軽微な不具合 |

Medium 以下と対象外はレポートに件数だけ書く。Critical / High は個別に記載する。

### 6. レポート作成

`reports/YYYY-MM-DD.md`（このスキルのディレクトリ配下）に保存し、要約をユーザーに表示する。

```markdown
# Spring Boot 重大不具合チェック YYYY-MM-DD

- 導入バージョン: CUR / 調査期間: SINCE 〜 今日
- サポート状況: OSS 終了日 / 商用終了日 / 最新パッチ（確認できた範囲）

## 結論
（パッチ適用またはアップグレードを検討すべきか、1〜3 行で）

## Critical / High
| 区分 | 内容 | 発生条件 | GEN への影響 | 修正版 | 出典 URL |

## 依存ライブラリの不具合
（同じ表形式）

## 対象外・Medium 以下
件数のみ

## 推奨アクション
- 例: 修正済みパッチへの更新可否の検討 / 依存ライブラリのみ個別アップグレード（`<tomcat.version>` 等のプロパティ上書き）/ 回避策の設定 / 後継世代への移行計画
```

## 注意

- 出典 URL を必ず付け、推測と確認済みの事実を区別して書く。
- CUR への影響を確認できなかったものは「影響: 要確認」と書き、確認方法（該当クラス名など）を添える。
- 前回レポートに載せた項目は「既出」と書き、新規分と分けて示す。
- CVE や脆弱性情報は報告しない。別調査の対象である旨も、ユーザーから求められない限り本レポートでは扱わない。
