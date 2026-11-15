---
name: spring-boot-bug-check
description: 導入中の Spring Boot バージョン（既定 3.5.16）以降に公開された重大不具合・脆弱性（サーバダウン、プロセスダウン、データ破壊、メモリリーク、デッドロック、CVE 等）を spring.io / GitHub から調べ、パッチ適用検討用のレポートを作る。「Spring Boot の不具合チェック」「Spring Boot の重大バグ確認」「SpringBoot パッチ検討」などで使う。
---

# Spring Boot 重大不具合チェック

導入中バージョン以降に見つかった **重大不具合** を洗い出し、パッチ適用要否の判断材料をまとめる。

## パラメータ

- 導入バージョン: 引数で指定があればそれを使う。なければ `3.5.16`。
- 前回チェック日: `reports/` 内の最新レポートのファイル名の日付。なければ導入バージョンのリリース日を起点にする。

以下 `CUR`＝導入バージョン（例 3.5.16）、`GEN`＝世代（例 3.5.x）、`SINCE`＝起点日（YYYY-MM-DD）とする。

## 前提知識（毎回 API で再確認すること）

- 3.5.x の OSS サポートは **2026-06-30 で終了**。OSS 最終版は 3.5.16 で、以降のパッチ（3.5.17〜）は商用版（Tanzu Spring / Enterprise）でのみ提供される。商用版のリリースノートは公開されていないことが多い。
- そのため、**後継世代（4.0.x / 4.1.x など）で修正されたバグのうち、3.5 にも同じコードがあって影響しそうなもの** を拾うことがチェックの中心になる。
- Spring Boot 自体よりも、同梱の依存ライブラリ（Spring Framework 6.2.x、Tomcat 10.1、Jetty、Undertow、Netty、Reactor、Hibernate、HikariCP、Jackson、Logback 等）の不具合や CVE のほうが重大なケースが多い。

## 手順

GitHub API は未認証だと 1 時間 60 リクエストまで。`GITHUB_TOKEN` 環境変数があれば `-H "Authorization: Bearer $GITHUB_TOKEN"` を付ける。

### 1. サポート状況と最新パッチを確認

```bash
curl -sL "https://api.spring.io/projects/spring-boot/generations/GEN"
curl -sL "https://api.spring.io/projects/spring-boot/generations" | grep -E '"name"|EndDate|"oss"|"enterprise"'
```

`ossSupportEndDate`、`commercialSupportEndDate`、`latestPatch.oss` / `latestPatch.enterprise` を記録する。CUR より新しい OSS 版があれば、そのリリースノートも手順 2 の対象に加える。

### 2. CUR 以降のリリースとリリースノートを取得

```bash
curl -s "https://api.github.com/repos/spring-projects/spring-boot/releases?per_page=50"
```

- `published_at` が SINCE より後の GA 版（`-M` / `-RC` を除く）を対象にする。
- 各リリースの `body` から「Bug Fixes」と「Dependency Upgrades」を読む。
- 依存ライブラリのアップグレードは、CUR 時点のバージョンとの差分を把握する（CUR のバージョンは `https://docs.spring.io/spring-boot/GEN_SHORT/appendix/dependency-versions/coordinates.html`（例: `3.5`）で確認）。

### 3. 修正済みバグ issue を検索

```bash
# SINCE 以降に close された bug
curl -s "https://api.github.com/search/issues?q=repo:spring-projects/spring-boot+is:issue+label:%22type:+bug%22+closed:>SINCE&per_page=100"
# 重大キーワードで絞り込み（キーワードを変えて複数回）
curl -s "https://api.github.com/search/issues?q=repo:spring-projects/spring-boot+is:issue+closed:>SINCE+%22memory+leak%22&per_page=50"
```

キーワード例: `memory leak`, `deadlock`, `OutOfMemoryError`, `hang`, `thread`, `shutdown`, `startup fails`, `data loss`, `corrupt`, `transaction`, `connection pool`, `regression`, `NullPointerException`, `StackOverflowError`, `infinite loop`, `100% CPU`。

各 issue の `milestone.title` を見て、どの版で修正されたか確認する。後継世代でのみ修正された bug は、本文・関連 PR・変更対象ファイルを見て GEN にも該当コードがあるか判断する（判断できなければ「要確認」とする）。

### 4. セキュリティアドバイザリ

- https://spring.io/security を WebFetch で取得し、SINCE 以降のアドバイザリを確認。影響バージョンに GEN（または Spring Framework 6.2.x 等の対応世代）が含まれるものを抽出する。
- GitHub Security Advisories も確認:
  ```bash
  curl -s "https://api.github.com/repos/spring-projects/spring-boot/security-advisories?per_page=30"
  curl -s "https://api.github.com/repos/spring-projects/spring-framework/security-advisories?per_page=30"
  ```

### 5. 主要依存ライブラリ（利用しているもののみ）

利用状況が分からない場合は、カレントディレクトリに `pom.xml` / `build.gradle(.kts)` があれば読み、なければ Tomcat と Spring Framework だけ確認してその旨をレポートに書く。

- Spring Framework: `https://api.github.com/repos/spring-projects/spring-framework/releases` と bug issue（Boot と同じ方法）
- Tomcat: https://tomcat.apache.org/security-10.html 、https://tomcat.apache.org/tomcat-10.1-doc/changelog.html
- その他は各プロジェクトのセキュリティページ / リリースノート

### 6. 重大度で分類

各項目を次の基準で分類する。迷ったら上位に倒し、理由を書く。

| 区分 | 基準 |
|---|---|
| **Critical** | サーバダウン / プロセスダウン、データ破壊・消失、認証回避、リモートコード実行、CVSS 9.0 以上 |
| **High** | メモリリーク・スレッドリーク、デッドロック・ハング、起動不能、トランザクション不整合、CVSS 7.0〜8.9 |
| **Medium** | 特定条件での機能不全、性能劣化、CVSS 4.0〜6.9 |
| 対象外 | ドキュメント、テスト支援、開発ツール（DevTools、Docker Compose サポート等の開発時専用機能）、軽微な不具合 |

Medium 以下と対象外はレポートに件数だけ書く。Critical / High は個別に記載する。

### 7. レポート作成

`reports/YYYY-MM-DD.md`（このスキルのディレクトリ配下）に保存し、要約をユーザーに表示する。

```markdown
# Spring Boot 重大不具合チェック YYYY-MM-DD

- 導入バージョン: CUR / 調査期間: SINCE 〜 今日
- サポート状況: OSS 終了日 / 商用終了日 / 最新パッチ（OSS・Enterprise）

## 結論
（パッチ適用またはアップグレードを検討すべきか、1〜3 行で）

## Critical / High
| 区分 | 内容 | 発生条件 | GEN への影響 | 修正版 | 出典 URL |

## 依存ライブラリ・CVE
（同じ表形式）

## 対象外・Medium 以下
件数のみ

## 推奨アクション
- 例: 商用版 3.5.17 の入手検討 / 依存ライブラリのみ個別アップグレード（`<tomcat.version>` 等のプロパティ上書き）/ 回避策の設定 / 4.0.x への移行計画
```

## 注意

- 出典 URL を必ず付け、推測と確認済みの事実を区別して書く。
- GEN への影響を確認できなかったものは「影響: 要確認」と書き、確認方法（該当クラス名など）を添える。
- 前回レポートに載せた項目は「既出」と書き、新規分と分けて示す。
