# Spring Boot 重大不具合チェック 2026-11-08

- 導入バージョン: Spring Boot 3.1.1
- 調査期間: 2023-06-22 ～ 2026-11-08
- 対象: Spring Boot、Spring Framework 6.0.x、組み込みTomcat 10.1.xの非セキュリティ不具合
- CVE・脆弱性情報: 調査対象外
- 前提: アプリケーションの `pom.xml` / `build.gradle` は提供されていないため、依存関係はSpring Boot標準管理を基準とする。機能の利用有無も未確認。

## 結論

Spring Boot 3.1.xはOSSサポートが2024-06-30、商用サポートも2025-06-30に終了している。API上の最新パッチはOSS 3.1.12、Enterprise 3.1.21だが、現時点でサポート対象の系列ではないため、継続利用よりサポート中の系列への移行を優先して検討する。

3.1.1の標準構成で直ちに発生すると確認できたCritical不具合は特定できなかった。一方、Logbackの並列初期化、Log4j2の共有LoggerContext、Tomcatの永続セッション・WebDAV・Native SSLなど、構成に依存するHigh候補がある。実際の依存バージョンと機能利用を照合し、該当する場合は更新・移行を急ぐことを推奨する。

## サポート状況・標準依存関係

| 項目 | 確認結果 |
|---|---|
| Spring Boot 3.1.1リリース日 | 2023-06-22 |
| 3.1.x最終OSS版 | 3.1.12（2024-05-23） |
| 3.1.x OSSサポート終了 | 2024-06-30 |
| 3.1.x 商用サポート終了 | 2025-06-30 |
| 3.1.x API掲載最新パッチ | OSS: 3.1.12 / Enterprise: 3.1.21 |
| Boot 3.1.1標準 Spring Framework | 6.0.10 |
| Boot 3.1.1標準 Tomcat | 10.1.10 |
| Boot 3.1.12の依存例 | Spring Framework 6.0.21 / Tomcat 10.1.24 |

API掲載のEnterprise最新パッチは、契約上の入手可否や個別修正内容を意味しない。商用サポート期間も終了済みのため、提供元へ確認が必要。

出典:
- [Spring Boot generation API 3.1.x](https://api.spring.io/projects/spring-boot/generations/3.1.x)
- [Spring Boot 3.1.12 OSSサポート終了告知](https://spring.io/blog/2024/05/23/spring-boot-3-1-12-available-now/)
- [Spring Boot 3.1.1依存バージョン一覧](https://docs.spring.io/spring-boot/docs/3.1.1/reference/html/dependency-versions.html)
- [Spring Boot 3.1.12リリースノート](https://github.com/spring-projects/spring-boot/releases/tag/v3.1.12)

## Critical / High候補

「影響可能性」は公開情報に基づく判定であり、実環境での再現確認を意味しない。影響開始バージョンを公式情報から確認できない場合は、その旨を明記した。

| 区分 | 不具合と条件 | 3.1.1への影響・修正版 | 推奨確認 | 出典 |
|---|---|---|---|---|
| High | **起動時のLogback/SLF4J並列初期化でアプリ起動に失敗**。複数スレッドが初期化を競合し、`SubstituteLoggerFactory` が競合LoggerFactoryと判定される条件。 | 3.1.xでは3.1.4に修正が取り込まれた。3.1.1が影響する可能性があるが、公式 issue は3.1.1を影響版として明示していないため要確認。 | 起動時に複数スレッドからLoggerFactoryを初期化する独自処理・ライブラリがあるか確認。 | [3.1.x issue #37484](https://github.com/spring-projects/spring-boot/issues/37484)、[3.1.4リリースノート](https://github.com/spring-projects/spring-boot/releases/tag/v3.1.4) |
| High | **TomcatへのWAR配置時にLog4j2のLoggerContext共有構成でStackOverflowError**。Spring Boot独自Filterが、TomcatクラスローダーからJVM全体共有のLog4j2 LoggerContextに登録される条件。 | 3.1.1の `Log4J2LoggingSystem` は独自 `AbstractFilter` を使用し、3.1.11ではLog4j2標準 `DenyAllFilter` に置き換えられたことをソースで確認。該当構成なら3.1.1への影響可能性が高い。 | WAR配置、Log4j2利用、単一JVM-wide LoggerContext設定の3点を確認。 | [修正PR #40235](https://github.com/spring-projects/spring-boot/pull/40235)、[3.1.11リリースノート](https://github.com/spring-projects/spring-boot/releases/tag/v3.1.11)、[3.1.1の実装](https://github.com/spring-projects/spring-boot/blob/v3.1.1/spring-boot-project/spring-boot/src/main/java/org/springframework/boot/logging/log4j2/Log4J2LoggingSystem.java)、[3.1.11の実装](https://github.com/spring-projects/spring-boot/blob/v3.1.11/spring-boot-project/spring-boot/src/main/java/org/springframework/boot/logging/log4j2/Log4J2LoggingSystem.java) |
| High候補 | **Tomcat永続セッションの保存エラー時にセッション状態が失われる可能性**。Tomcat 10.1.56の変更履歴はDataSourceStoreの例外握りつぶし除去とFileStoreでのアトミック保存を記載。 | Boot 3.1.1の標準Tomcatは10.1.10で、3.1.x OSS最終版も10.1.24。修正が含まれない。10.1.10で同じ欠陥が存在するか、開始バージョンは変更履歴だけでは確定できない。業務DBデータではなく、永続化対象のTomcatセッション状態に関する候補。 | Tomcat PersistentManagerのDataSourceStore/FileStore利用、セッションに重要状態を保持しているか、保存障害時のログと復旧方法を確認。 | [Tomcat 10.1変更履歴](https://tomcat.apache.org/tomcat-10.1-doc/changelog.html)、[FileStore atomic保存PR #1016](https://github.com/apache/tomcat/pull/1016) |
| High候補 | **WebDAVのリソースコピー時のデッドロック**。 | Tomcat 10.1.56の変更履歴に修正あり。10.1.10が影響するかは修正記載だけでは断定できない。WebDAVを使わない構成では該当しない。 | WebDAV Servlet / WebDAVアクセスおよびリソースコピーの利用有無を確認。 | [Tomcat 10.1変更履歴](https://tomcat.apache.org/tomcat-10.1-doc/changelog.html) |
| High候補 | **JVMクラッシュの可能性**。Tomcat Nativeの適合バージョンがない状態で、ConnectorにTomcat Native/OpenSSLを明示指定する条件。 | Tomcat 10.1.57の変更履歴にクラッシュ回避修正あり。10.1.10への影響開始版は未確認。標準NIOコネクタでTomcat Nativeを指定していない場合は該当しない。 | ConnectorのTLS実装、Tomcat Native/OpenSSLの明示設定、Nativeライブラリのバージョンを確認。 | [Tomcat 10.1変更履歴](https://tomcat.apache.org/tomcat-10.1-doc/changelog.html) |

## 3.1.x内の更新時注意（3.1.1での既知不具合とは区別）

以下は3.1.1で発生する不具合ではなく、途中のパッチ版で導入された回帰または特定構成の問題。更新先を選ぶ際の注意事項として記録する。

| 対象版 | 内容 | 対応 |
|---|---|---|
| 3.1.2 | 外部TomcatへWARを繰り返しデプロイ／アンデプロイすると、7～8回程度でMetaspace不足になるとの報告。Issue本文は3.1.2を明示。3.1.4で修正。3.1.1自体への影響は報告されていない。 | 3.1.2を更新先にしない。3.1.4以降を候補とし、外部Tomcat運用では再デプロイ試験を行う。 |
| 3.1.9 | Hibernate 6.2.22.Finalへの更新はGraalVM native imageで正しく動作しない旨、公式リリースノートが注意喚起。 | native image利用時は3.1.9のHibernate設定を避けるか、互換性を確認した後続パッチを選択する。 |

出典:
- [Metaspace issue #37096](https://github.com/spring-projects/spring-boot/issues/37096)、[3.1.4リリースノート](https://github.com/spring-projects/spring-boot/releases/tag/v3.1.4)
- [3.1.9リリースノート](https://github.com/spring-projects/spring-boot/releases/tag/v3.1.9)

## 後継世代で見つかった要確認項目

- Boot 4.0.9 / 4.1.2のリリースノートに、Graceful shutdown直後に呼ばれた場合のNettyWebServer停止ハングが記載されている（各系列issue #52119 / #52196）。3.1.1のNetty/Reactor Netty実装への修正適用有無は未確認。Reactive Nettyを使用する場合、移行先のコードまたは依存側修正と3.1.1の実装を比較する。
- 後続世代のIssueや修正は、同じクラス・同じ処理経路が3.1.1にあると確認できるまで、3.1.1の影響ありとは判定しない。

出典:
- [Boot 4.0.9リリースノート](https://github.com/spring-projects/spring-boot/releases/tag/v4.0.9)
- [Boot 4.1.2リリースノート](https://github.com/spring-projects/spring-boot/releases/tag/v4.1.2)

## Spring Framework

3.1.1の管理バージョンはSpring Framework 6.0.10、3.1.x OSS最終版3.1.12では6.0.21。確認したFramework 6.0.xのリリース情報から、Spring Boot 3.1.1に直接結びつくCritical/Highの障害は今回確定できなかった。アプリケーション固有の利用APIや実依存関係の照合は未実施であり、「重大不具合なし」を意味しない。

参考:
- [Spring Framework 6.0.21リリース](https://github.com/spring-projects/spring-framework/releases/tag/v6.0.21)
- [Spring Framework 6.0リリースノート](https://github.com/spring-projects/spring-framework/wiki/Spring-Framework-6.0-Release-Notes)

## 対象外・Medium以下

- CVE・脆弱性情報: 対象外のため調査・件数集計を実施していない。
- Medium以下、ドキュメント、テスト・開発専用機能: 個別報告を省略。リリースノート全件の件数集計は未実施。

## 推奨アクション

1. `mvn dependency:tree` または `gradlew dependencies --configuration runtimeClasspath` で実依存関係を取得し、Tomcat / Spring Framework / Log4j2 / Logback / Reactor Nettyの実バージョンを確定する。
2. WAR外部Tomcat配置、Log4j2のJVM-wide LoggerContext、並列ロギング初期化、Tomcat永続セッション、WebDAV、Tomcat Native/OpenSSL、Reactive Nettyの利用有無を確認する。
3. 該当するHigh候補があれば、サポート対象のSpring Boot系列への移行を優先する。依存ライブラリだけを個別に上書きする場合は、Spring Bootの依存管理から外れるため、互換性・回帰・停止／再起動試験を行う。
4. 3.1.x継続が必要な場合、3.1.21の契約上の入手可否、修正内容、サポート条件を提供元に確認する。ただし、3.1.xのサポート期限を過ぎているため恒久対応とは見なさない。

## 調査範囲・制約

- 公式のSpring Boot 3.1.xリリースノート、Spring Boot issue/PR、Spring Frameworkリリース情報、Tomcat 10.1変更履歴を中心に一次調査した。
- GitHubの全Issue/PRを全ページ取得していないため、網羅的な不具合不存在の証明ではない。
- 一部Tomcat修正は影響開始バージョンが公式変更履歴に記載されていない。Tomcat 10.1.10への影響を推定で断定していない。
- `pom.xml` / `build.gradle`、Tomcat設定、ログ設定、本番構成、再現試験は未提供・未実施。
- CVE・脆弱性情報は依頼どおり調査対象外。
