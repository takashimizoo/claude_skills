# Spring Boot 3.1.1 重大不具合チェックレポート

> このレポートは旧版です。Tomcatの一部候補に出典で裏付けられない記載が含まれていたため、参照せず、更新版 [reports/2026-11-08.md](reports/2026-11-08.md) を使用してください。

- 調査基準日: 2026-11-08
- 導入バージョン: Spring Boot 3.1.1
- 調査期間: 2023-06-22 ～ 2026-11-08
- 対象: Spring Boot / Spring Framework / 組み込みTomcatを中心とした重大な製品不具合
- CVE・脆弱性情報: ユーザー指定により調査対象外
- 判定上の注意: 本レポートは公開情報の一次調査。3.1.1の実環境での再現確認、ソースコード差分の全件照合、pom.xml / build.gradleとの依存照合は未実施。

## 1. 結論

Spring Boot 3.1.xのOSSサポートは3.1.12をもって終了している。3.1.1の標準依存関係にはSpring Framework 6.0.10、Tomcat 10.1.10が含まれる。

今回の公開情報調査では、Tomcat 10.1系の後続リリースで、HTTP/2アップロード時のデータ破損、HTTP/2のメモリリーク、セッション処理のデッドロック、WebSocketエンドポイントの失敗時メモリリーク等の修正が確認できた。これらは3.1.1の標準Tomcatと同じ10.1系統に属するため、利用機能・修正導入バージョン・コードの該当性を確認する価値がある。

ただし、Tomcat公式変更履歴の記述だけでは各不具合の正確な影響開始バージョンが確定できない項目がある。したがって「3.1.1で発生する」と断定せず、現時点では影響可能性あり／要確認として扱う。CVE情報は本調査から除外している。

## 2. サポート状況・標準依存関係

| 項目 | 確認結果 |
|---|---|
| Spring Boot 3.1.1リリース日 | 2023-06-22 |
| 3.1.x最終OSSリリース | 3.1.12（2024-05-23） |
| 3.1.x OSSサポート | 終了 |
| 商用サポート | Spring商用サポートの提供あり。契約・対象パッチは提供元に確認が必要 |
| Spring Framework標準版 | 6.0.10 |
| 組み込みTomcat標準版 | 10.1.10 |
| Logback標準版 | 1.4.8 |
| Spring Security標準版 | 6.1.1 |

出典:
- https://spring.io/blog/2023/06/22/spring-boot-3-1-1-available-now
- https://spring.io/blog/2024/05/23/spring-boot-3-1-12-available-now/
- https://docs.spring.io/spring-boot/docs/3.1.1/reference/html/dependency-versions.html
- https://spring.io/blog/2023/06/15/spring-framework-5-3-28-and-6-0-10-available-now/
- https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-Versions

## 3. Critical / High候補

### 3.1 Tomcat: HTTP/2 + 非同期アップロード時のデータ破損

| 項目 | 内容 |
|---|---|
| 暫定重大度 | Critical候補（データ破損の可能性） |
| 対象コンポーネント | Apache Tomcat 10.1系 |
| 公式修正記載 | Tomcat 10.1.61 |
| 不具合概要 | HTTP/2と非同期I/Oを使用したアップロードでデータ破損が発生し得る問題を修正 |
| 発生条件 | HTTP/2経由のアップロードで非同期I/Oを使用する場合 |
| 3.1.1への影響 | 要確認。3.1.1標準Tomcatは10.1.10。同じ10.1系だが、影響開始バージョンは変更履歴だけでは確定できない |
| 推奨確認 | HTTP/2有効化の有無、アップロード処理が非同期I/Oを使用するか、Tomcat修正コミットと10.1.10の実装を比較 |
| 出典 | https://tomcat.apache.org/tomcat-10.1-doc/changelog.html |

### 3.2 Tomcat: HTTP/2フロー制御ウィンドウのリーク

| 項目 | 内容 |
|---|---|
| 暫定重大度 | High候補 |
| 対象コンポーネント | Apache Tomcat 10.1系 |
| 公式修正記載 | Tomcat 10.1.61 |
| 不具合概要 | HTTPリクエスト本文の一部を受信したものの読み取らない場合、HTTP/2接続のフロー制御ウィンドウにリークが発生する問題を修正 |
| 発生条件 | HTTP/2でリクエスト本文の一部が未読のままになる処理 |
| 想定影響 | 接続資源の消費・通信処理への影響。実際の停止条件は要確認 |
| 3.1.1への影響 | 要確認。10.1.10からの影響有無を修正コミットで確認する必要あり |
| 推奨確認 | HTTP/2利用有無、リクエスト中断・本文未読となるアプリケーション処理を確認 |
| 出典 | https://tomcat.apache.org/tomcat-10.1-doc/changelog.html |

### 3.3 Tomcat: DeltaSessionのデッドロック

| 項目 | 内容 |
|---|---|
| 暫定重大度 | High候補 |
| 対象コンポーネント | Tomcat Cluster / DeltaSession |
| 公式修正記載 | Tomcat 10.1.61 |
| 不具合概要 | セッション属性リスナー等が関係するロック取得順序により、DeltaSession処理でデッドロックが発生する可能性を修正 |
| 発生条件 | Tomcatのクラスタセッション機能（DeltaSession）を利用し、セッション属性リスナー等が競合する場合 |
| 3.1.1への影響 | 標準の単一組み込みTomcat構成では該当しない可能性。Tomcat Cluster利用時のみ要確認 |
| 推奨確認 | Tomcat Cluster / DeltaManager / BackupManager等の利用有無、セッション属性リスナーの実装を確認 |
| 出典 | https://tomcat.apache.org/tomcat-10.1-doc/changelog.html |

### 3.4 Tomcat: WebSocket Endpoint.onOpen失敗時のメモリリーク

| 項目 | 内容 |
|---|---|
| 暫定重大度 | High候補 |
| 対象コンポーネント | Tomcat WebSocket |
| 公式修正記載 | Tomcat 10.1.57 |
| 不具合概要 | プログラム型WebSocketエンドポイントのonOpen()呼び出しが失敗した場合にメモリリークする問題を修正 |
| 発生条件 | プログラム型Endpointを利用し、onOpen()が例外等で失敗する場合 |
| 3.1.1への影響 | 要確認。WebSocket利用方式と影響開始バージョンを確認する必要あり |
| 推奨確認 | jakarta.websocketのEndpoint実装、onOpen()内の例外経路、接続失敗の頻度を確認 |
| 出典 | https://tomcat.apache.org/tomcat-10.1-doc/changelog.html |

### 3.5 Tomcat: WebDAVリソースコピー時のデッドロック

| 項目 | 内容 |
|---|---|
| 暫定重大度 | High候補 |
| 対象コンポーネント | Tomcat WebDAV |
| 公式修正記載 | Tomcat 10.1.57 |
| 不具合概要 | WebDAVによるリソースコピー時に発生し得るデッドロックを修正 |
| 発生条件 | WebDAV機能を利用し、リソースコピー処理を実行する場合 |
| 3.1.1への影響 | WebDAVを使用していなければ原則対象外。使用時は要確認 |
| 推奨確認 | WebDAV Servlet / WebDAVアクセスの有無 |
| 出典 | https://tomcat.apache.org/tomcat-10.1-doc/changelog.html |

## 4. Spring Boot / Spring Framework

- Spring Boot 3.1.1以降の公式リリースには多数のバグ修正が含まれる。3.1.12は49件の修正等を含むが、今回取得できた公開情報だけでは、サーバ停止・プロセス停止・データ破損に直結し、かつ3.1.1に影響すると確証できる個別項目を確定できなかった。
- Spring Framework 6.0.10以降のリリースにも継続的な修正がある。今回の一次調査では、3.1.1に対する重大障害として確定できる個別項目は抽出できていない。
- 後続世代（Spring Boot 4.x等）の修正を3.1.1へ外挿する場合、同一クラス・同一処理経路が存在することをソースコードで確認する必要がある。バージョンが異なるという理由だけで影響あり／なしを断定しない。

参考:
- https://github.com/spring-projects/spring-boot/releases
- https://github.com/spring-projects/spring-framework/releases
- https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-6.0-Release-Notes

## 5. 対象外・Medium以下

- CVE・脆弱性情報: ユーザー指定により調査対象外（件数集計にも含めない）。
- ドキュメント、テスト専用機能、開発ツールの不具合: 個別評価対象外。
- その他の軽微な機能不全・性能改善: 今回は個別列挙を省略。
- 本調査で「重大不具合なし」とは結論づけない。GitHub APIの全Issue・全PRのページネーションを伴う網羅的取得、コメント・関連コミットの追跡は未完了。

## 6. 推奨アクション

1. 本番アプリケーションの実依存関係を `mvn dependency:tree` または `gradlew dependencies --configuration runtimeClasspath` で取得し、Tomcatが実際に10.1.10か確認する。
2. HTTP/2、非同期アップロード、WebSocket、WebDAV、Tomcat Cluster/DeltaSessionの利用有無を確認する。
3. 該当機能を利用している場合、Tomcat公式変更履歴の該当修正コミットを確認し、10.1.10に不具合コードが存在するか比較する。
4. Spring Boot 3.1.xおよびSpring Framework 6.0.xはOSSサポート終了済みのため、商用サポート契約の有無と、より新しいサポート対象系列への移行計画を確認する。
5. 依存ライブラリ単独更新を行う場合は、Spring Bootの依存管理から外れるため、互換性確認と回帰試験を実施する。

## 7. 調査上の制約

- 本レポートは公開Web情報に基づく一次調査であり、GitHub APIを用いた全件検索・ページネーションを完遂したものではない。
- `pom.xml` / `build.gradle` が提供されていないため、標準依存関係を基準にしている。実際の本番依存関係とは異なる可能性がある。
- Tomcatの一部修正について、公式変更履歴に影響開始バージョンが明記されていないため、3.1.1（Tomcat 10.1.10）への該当性は未確定。
- CVE・セキュリティアドバイザリは意図的に調査していない。
