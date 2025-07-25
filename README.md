# Rust完全理解: 公式ドキュメント網羅とコンピューターサイエンス理論

## はじめに

この書籍は、Rustプログラミング言語を、公式ドキュメントの網羅的な学習とコンピューターサイエンスの理論的背景を組み合わせて学ぶための包括的な学習書です。

## 本書の特徴

- **公式ドキュメントの完全網羅**: The Rust Book、Reference、Rustonomicon等の全学習要素を体系化
- **理論的背景の理解**: メモリ管理、型理論、並行性理論等のCS理論を含む
- **深い理解の提供**: 「なぜそうなっているか」の理論的説明
- **実行可能なコード例**: 理論と実装を結びつける豊富なサンプル

## 対象読者

- Rustを深く理解したいプログラマー
- コンピューターサイエンスの背景を学びたい方
- 他言語からRustに移行したい方
- システムプログラミングに興味がある方

## プロジェクト構造

```
rust-complete-understanding/
├── book.toml              # mdBook設定ファイル
├── SUMMARY.md             # 書籍の目次
├── src/                   # 書籍コンテンツ
├── content_extraction/    # 公式ドキュメント分析
├── theory_integration/    # CS理論統合
├── code_examples/         # コード例
└── assets/                # 図表・画像資料
```

## ビルド方法

```bash
# mdBookのインストール
cargo install mdbook mdbook-epub

# 書籍のビルド
mdbook build

# EPUB形式での出力
mdbook-epub

# 開発サーバーの起動
mdbook serve
```

## コントリビューション

このプロジェクトへの貢献を歓迎します。詳細は[CONTRIBUTING.md](CONTRIBUTING.md)をご覧ください。

## ライセンス

TBD

## 連絡先

TBD