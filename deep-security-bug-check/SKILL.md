---
name: deep-security-bug-check
description: 導入中の Trend Micro Deep Security 20 LTS（Agent 既定 20.0.1-14610 / Linux、Manager も対象）以降に公開された重大不具合・脆弱性（サーバダウン、カーネルパニック、プロセスダウン、ハング、データ破壊、メモリリーク、CVE 等）を公式リリースノート・サポート記事・NVD から調べ、パッチ適用検討用のレポートを作る。「Deep Security の不具合チェック」「DSA の重大バグ確認」「Deep Security パッチ検討」などで使う。
---

# Deep Security 重大不具合チェック

導入中ビルド以降に公開された **重大不具合** と **脆弱性** を洗い出し、Agent / Manager の更新要否を判断する材料をまとめる。

## パラメータ

引数で指定があればそれを使い、なければ次の既定値を使う。

| 名前 | 既定値 | 説明 |
|---|---|---|
| `DSA_CUR` | `20.0.1-14610` | Deep Security Agent の導入ビルド（2024-07-17 リリース） |
| `PLATFORM` | `Linux` | Agent の OS。`Linux` / `Windows` / `Unix` のどれか |
| `DSM_CUR` | 未設定 | Deep Security Manager の導入ビルド（形式 `20.0.NNNN`）。未設定ならユーザーに尋ねる。不明と言われたら Manager は最新数件の Critical / High だけ確認し、その旨をレポートに書く |

- `SINCE`（前回チェック日）: `reports/` 内の最新レポートのファイル名の日付。レポートがなければ `DSA_CUR` のリリース日（2024-07-17）を使う。
- ユーザーが導入ビルドを更新したと言った場合は、このファイルの既定値も書き換えるか確認する。

## 前提知識（毎回公式ページで再確認すること）

- Agent のビルドは `20.0.<系列>-<ビルド番号>` 形式（例: `20.0.1-14610`、`20.0.3-31610`）。系列（20.0.1 → 20.0.2 → 20.0.3）をまたいでも同じ 20 LTS 内の更新扱い。Manager のビルドは `20.0.NNNN` 形式。
- サポート期限（2023 年以降の Update）: リリース日から 3 年で標準サポート終了、4 年で延長サポート終了。`DSA_CUR` の期限もレポートに書く。
- 修正は最新ビルドにまとめて入る。個別パッチは基本的に提供されないため、「どのビルドまで上げれば重大不具合が解消されるか」を示すことが目的になる。
- リリースノートには **リコールされたビルド**（例: 20.0.3-14910）がある。推奨先にしないこと。

## 情報源

| 用途 | URL |
|---|---|
| Agent リリースノート（英語版のほうが日本語版より更新が早い） | https://help.deepsecurity.trendmicro.com/20_0/on-premise/release-notes-dsa.html |
| Manager リリースノート | https://help.deepsecurity.trendmicro.com/20_0/on-premise/release-notes-dsm.html |
| ライフサイクル | https://help.deepsecurity.trendmicro.com/dates-lts.html |
| 脆弱性（NVD API） | https://services.nvd.nist.gov/rest/json/cves/2.0 |
| 脆弱性の詳細（Trend Micro Success Portal） | `https://success.trendmicro.com/en-US/solution/KA-XXXXXXX`（curl で取得可） |
| 国内の脆弱性情報 | JVN（https://jvn.jp/） |

## 手順

ダウンロードしたファイルは作業用の空ディレクトリに置き、スクリプトはこのスキルのディレクトリから絶対パスで実行する。`SKILL_DIR` はこの SKILL.md のあるディレクトリ。

```bash
WORK=$(mktemp -d)
curl -sL -o "$WORK/dsa.html" https://help.deepsecurity.trendmicro.com/20_0/on-premise/release-notes-dsa.html
curl -sL -o "$WORK/dsm.html" https://help.deepsecurity.trendmicro.com/20_0/on-premise/release-notes-dsm.html
```

### 1. Agent: 導入ビルドより新しいリリースを抽出

```bash
python -I "$SKILL_DIR/extract_notes.py" dsa "$WORK/dsa.html" DSA_CUR PLATFORM > "$WORK/dsa_new.txt"
grep '^## ' "$WORK/dsa_new.txt"     # 対象ビルドの一覧
```

- ページ全体は 35 万字以上あるため、WebFetch で直接読まずに、このスクリプトで対象プラットフォームの差分だけを取り出す。
- スクリプトがエラーになった場合（ページ構成の変更など）は、エラー内容をレポートに書き、WebFetch で `offset` を進めながら読む方法に切り替える。
- `dsa_new.txt` を **全文** 読む。各ビルドの `Resolved issues` / `Known issues` / `Security updates` / `Enhancements` から、次のキーワードに当たる項目を中心に拾う。grep だけで判断せず、文脈を読んで重大度を判定する。

  `crash`, `kernel panic`, `BSOD`, `reboot`, `restart`, `hang`, `unresponsive`, `freeze`, `deadlock`, `blocked`, `memory leak`, `high CPU`, `100%`, `stopped`, `terminated`, `offline`, `corrupt`, `data loss`, `failed to start`, `network disconnect`, `dropped`, `kill`, `recalled`

- 導入ビルドの **Known issues** と、導入ビルドより後のビルドに書かれた不具合のうち、`DSA_CUR` にも当てはまりそうなもの（「〜 and earlier」「since 20.0.1-xxxx」などの記載）を特に重視する。

### 2. Manager: 導入ビルドより新しいリリースを抽出

```bash
python -I "$SKILL_DIR/extract_notes.py" dsm "$WORK/dsm.html" DSM_CUR > "$WORK/dsm_new.txt"
```

Agent と同じ観点で読む。Manager の場合は、DB 関連の不具合（データ不整合、DB 肥大化、マイグレーション失敗）、サービス停止、Java ヒープ不足、Agent との通信断なども重大として扱う。`Security updates` の「Highest CVSS score」を必ず記録する。

### 3. 脆弱性（CVE）

NVD API で SINCE 以降に公開された CVE を検索する。期間指定は最大 120 日なので、区切って繰り返す。未認証の場合、30 秒あたり 5 リクエストまでに抑える。

```bash
curl -s "https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=Trend%20Micro%20Deep%20Security&pubStartDate=YYYY-MM-DDT00:00:00.000&pubEndDate=YYYY-MM-DDT00:00:00.000"
```

- CVSS は `metrics` の各要素の `cvssData.baseScore` を見る（`cvssData` がない要素もあるため、キーの存在を確認してから読む）。
- 説明文から Agent / Manager、対象 OS（Windows のみ、など）を判断し、`PLATFORM` に関係ないものは対象外に分類する。
- 参照 URL に Success Portal の KA があれば curl で取得し、**修正ビルド** を確認する。
- WebSearch で `"Deep Security" vulnerability site:success.trendmicro.com` や `"Deep Security" site:jvn.jp` も検索し、NVD に未登録のアドバイザリを補う。

### 4. ライフサイクル

https://help.deepsecurity.trendmicro.com/dates-lts.html を WebFetch で確認し、`DSA_CUR` と `DSM_CUR` の標準サポート終了日と延長サポート終了日を記録する。終了まで 1 年を切っている場合は結論に書く。

### 5. 重大度で分類

迷ったら上位に分類し、理由を書く。

| 区分 | 基準 |
|---|---|
| **Critical** | OS のクラッシュ・カーネルパニック・BSOD・意図しない再起動、Agent / Manager プロセスのダウン、サーバ全体のハング、通信の全断、データ破壊・消失、無関係なプロセスの強制終了、CVSS 9.0 以上 |
| **High** | メモリリーク、デッドロック、CPU 100% 張り付き、一時的なシステムブロック、保護機能の停止（Anti-Malware がオフラインになる、など）、起動・アップグレードの失敗、CVSS 7.0〜8.9 |
| **Medium** | 特定条件での機能不全、誤検知、性能劣化、CVSS 4.0〜6.9 |
| 対象外 | 別プラットフォーム専用、UI 表示、ドキュメント、新機能・対応 OS の追加 |

Critical / High は個別に記載する。Medium 以下と対象外は件数だけ書く。

### 6. レポート作成

`$SKILL_DIR/reports/YYYY-MM-DD.md` に保存し、要約をユーザーに表示する。作業ディレクトリ（`$WORK`）は最後に削除する。

```markdown
# Deep Security 重大不具合チェック YYYY-MM-DD

- Agent: DSA_CUR（PLATFORM）/ 最新: 20.0.x-xxxxx（YYYY-MM-DD）/ 差分ビルド数: N
- Manager: DSM_CUR / 最新: 20.0.xxxx（YYYY-MM-DD）
- 調査期間: SINCE 〜 今日
- サポート期限: Agent 標準 YYYY-MM-DD・延長 YYYY-MM-DD / Manager 同様

## 結論
（パッチ適用を検討すべきか、推奨ビルドとその理由を 1〜3 行で）

## Agent: Critical / High
| 区分 | 内容（日本語要約） | 発生条件・対象機能 | 修正ビルド | ID（V1E-/DSA-/SEG- 等） | 新規/既出 |

## Manager: Critical / High
（同じ形式）

## 脆弱性（CVE）
| CVE | CVSS | 内容 | 対象（Agent/Manager・OS） | 修正ビルド | 出典 URL |

## 導入ビルドの既知の問題（Known issues）で未解決のもの

## Medium 以下・対象外
件数のみ

## 推奨アクション
- 例: Agent を 20.0.x-xxxxx 以上に更新（リコールされたビルドは除外）/ 該当機能（Application Control など）を使っているか確認 / 回避策 / Manager の先行アップグレード（Agent より新しい Manager が必要）
```

## 注意

- 出典 URL と、リリースノートの課題 ID（`V1E-`、`DSA-`、`SEG-`、`PCT-` など）を必ず書く。推測と確認済みの事実を区別する。
- 不具合がどの機能（Anti-Malware、Intrusion Prevention、Firewall、Application Control、Integrity Monitoring、Web Reputation、Log Inspection など）に関係するかを書き、ユーザーが使っていない機能なら影響が下がることを添える。
- 前回レポートに載せた項目は「既出」とし、新規分と分けて示す。
- Agent を更新する場合、Manager のバージョンが Agent 以上である必要がある。推奨アクションでは更新の順番にも触れる。
