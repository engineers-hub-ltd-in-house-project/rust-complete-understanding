#!/usr/bin/env python3
"""
Rust公式ドキュメント解析スクリプト

このスクリプトは、Rust公式ドキュメントの構造を解析し、
本書の内容との対応関係を分析します。
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict

class RustDocAnalyzer:
    """Rust公式ドキュメントの構造を解析するクラス"""
    
    def __init__(self):
        self.doc_categories = {
            "the_book": "The Rust Programming Language",
            "reference": "The Rust Reference",
            "rustonomicon": "The Rustonomicon",
            "async_book": "Asynchronous Programming in Rust",
            "embedded_book": "The Embedded Rust Book",
            "rust_by_example": "Rust by Example",
            "std": "Standard Library Documentation",
            "compiler": "Rustc Book",
            "cargo": "The Cargo Book",
            "rustdoc": "The rustdoc Book",
            "clippy": "Clippy Documentation",
            "error_index": "Rust Compiler Error Index"
        }
        
        self.topic_mapping = {
            "ownership": ["the_book:ch04", "reference:ch4.1", "rustonomicon:ch3"],
            "borrowing": ["the_book:ch04.2", "reference:ch4.2", "rustonomicon:ch3.2"],
            "lifetimes": ["the_book:ch10.3", "reference:ch10.3", "rustonomicon:ch3.6"],
            "traits": ["the_book:ch10", "reference:ch9"],
            "generics": ["the_book:ch10", "reference:ch9.2"],
            "unsafe": ["the_book:ch19.1", "reference:ch16", "rustonomicon:all"],
            "concurrency": ["the_book:ch16", "reference:ch15", "async_book:all"],
            "macros": ["the_book:ch19.5", "reference:ch3", "little_book_of_macros:all"],
            "type_system": ["reference:ch8", "rustonomicon:ch6"],
            "memory": ["rustonomicon:ch2", "reference:ch4"],
            "async": ["async_book:all", "the_book:ch17"],
            "ffi": ["rustonomicon:ch10", "reference:ch18"],
            "error_handling": ["the_book:ch09", "rust_by_example:ch18"],
            "testing": ["the_book:ch11", "cargo:ch12"],
            "modules": ["the_book:ch07", "reference:ch6"],
            "patterns": ["the_book:ch18", "reference:ch11"],
            "smart_pointers": ["the_book:ch15", "rustonomicon:ch7"],
            "iterators": ["the_book:ch13", "std:iter"],
            "closures": ["the_book:ch13", "reference:ch9.1"],
            "cargo": ["cargo:all", "the_book:ch01.3"],
            "documentation": ["rustdoc:all", "the_book:ch14.2"]
        }
    
    def analyze_book_structure(self, book_path: Path) -> Dict[str, List[str]]:
        """書籍の構造を解析"""
        structure = defaultdict(list)
        
        summary_path = book_path / "src" / "SUMMARY.md"
        if not summary_path.exists():
            return structure
        
        with open(summary_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # パートごとに分類
        current_part = "Introduction"
        for line in content.split('\n'):
            if line.startswith('# Part'):
                current_part = line.strip('# ').strip()
            elif line.strip().startswith('- ['):
                # 章のタイトルとパスを抽出
                match = re.match(r'.*\[(.*?)\]\((.*?)\)', line)
                if match:
                    title = match.group(1)
                    path = match.group(2)
                    structure[current_part].append({
                        'title': title,
                        'path': path,
                        'level': line.count('  ')
                    })
        
        return dict(structure)
    
    def map_to_official_docs(self, book_structure: Dict) -> Dict[str, List[str]]:
        """書籍の内容を公式ドキュメントにマッピング"""
        mapping = defaultdict(list)
        
        # キーワードベースでマッピング
        keywords_to_topics = {
            "メモリ": ["memory", "ownership"],
            "所有権": ["ownership"],
            "借用": ["borrowing"],
            "ライフタイム": ["lifetimes"],
            "型": ["type_system", "generics"],
            "トレイト": ["traits"],
            "ジェネリクス": ["generics"],
            "unsafe": ["unsafe", "ffi"],
            "並行": ["concurrency", "async"],
            "マクロ": ["macros"],
            "エラー": ["error_handling"],
            "テスト": ["testing"],
            "モジュール": ["modules"],
            "パターン": ["patterns"],
            "スマートポインタ": ["smart_pointers"],
            "イテレータ": ["iterators"],
            "クロージャ": ["closures"]
        }
        
        for part, chapters in book_structure.items():
            for chapter in chapters:
                title = chapter['title']
                
                # キーワードマッチング
                for keyword, topics in keywords_to_topics.items():
                    if keyword in title:
                        for topic in topics:
                            if topic in self.topic_mapping:
                                mapping[chapter['path']].extend(self.topic_mapping[topic])
        
        # 重複を削除
        for path in mapping:
            mapping[path] = list(set(mapping[path]))
        
        return dict(mapping)
    
    def generate_coverage_report(self, mapping: Dict[str, List[str]]) -> str:
        """カバレッジレポートを生成"""
        report = []
        report.append("# Rust公式ドキュメントカバレッジレポート\n")
        report.append("## 概要\n")
        
        # 公式ドキュメントごとのカバー率を計算
        doc_coverage = defaultdict(int)
        total_refs = 0
        
        for chapter, refs in mapping.items():
            for ref in refs:
                doc_name = ref.split(':')[0]
                doc_coverage[doc_name] += 1
                total_refs += 1
        
        report.append(f"総参照数: {total_refs}\n")
        report.append("## ドキュメント別カバレッジ\n")
        
        for doc_key, count in sorted(doc_coverage.items(), key=lambda x: x[1], reverse=True):
            if doc_key in self.doc_categories:
                doc_name = self.doc_categories[doc_key]
                percentage = (count / total_refs * 100) if total_refs > 0 else 0
                report.append(f"- {doc_name}: {count}回参照 ({percentage:.1f}%)")
        
        report.append("\n## トピック別カバレッジ\n")
        
        topic_coverage = defaultdict(int)
        for chapter, refs in mapping.items():
            topics_covered = set()
            for ref in refs:
                for topic, topic_refs in self.topic_mapping.items():
                    if ref in topic_refs:
                        topics_covered.add(topic)
            
            for topic in topics_covered:
                topic_coverage[topic] += 1
        
        total_chapters = len(mapping)
        for topic, count in sorted(topic_coverage.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_chapters * 100) if total_chapters > 0 else 0
            report.append(f"- {topic}: {count}章でカバー ({percentage:.1f}%)")
        
        return '\n'.join(report)
    
    def generate_mapping_table(self, book_structure: Dict, mapping: Dict) -> str:
        """マッピングテーブルを生成"""
        table = []
        table.append("# 章と公式ドキュメントの対応表\n")
        
        for part, chapters in book_structure.items():
            table.append(f"\n## {part}\n")
            table.append("| 章 | 公式ドキュメント参照 |")
            table.append("|---|---|")
            
            for chapter in chapters:
                path = chapter['path']
                title = chapter['title']
                refs = mapping.get(path, [])
                
                if refs:
                    ref_links = []
                    for ref in refs:
                        doc_key, section = ref.split(':') if ':' in ref else (ref, '')
                        if doc_key in self.doc_categories:
                            doc_name = self.doc_categories[doc_key]
                            ref_links.append(f"{doc_name} {section}")
                    
                    ref_str = ', '.join(ref_links)
                else:
                    ref_str = "独自コンテンツ"
                
                indent = '  ' * chapter['level']
                table.append(f"| {indent}{title} | {ref_str} |")
        
        return '\n'.join(table)
    
    def export_json(self, data: Dict, output_path: Path):
        """データをJSON形式でエクスポート"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    """メイン処理"""
    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent
    
    analyzer = RustDocAnalyzer()
    
    # 書籍構造を解析
    print("書籍構造を解析中...")
    book_structure = analyzer.analyze_book_structure(project_root)
    
    # 公式ドキュメントへのマッピング
    print("公式ドキュメントへマッピング中...")
    mapping = analyzer.map_to_official_docs(book_structure)
    
    # レポート生成
    print("レポートを生成中...")
    coverage_report = analyzer.generate_coverage_report(mapping)
    mapping_table = analyzer.generate_mapping_table(book_structure, mapping)
    
    # 結果を保存
    output_dir = project_root / "analysis"
    output_dir.mkdir(exist_ok=True)
    
    # カバレッジレポート
    with open(output_dir / "coverage_report.md", 'w', encoding='utf-8') as f:
        f.write(coverage_report)
    
    # マッピングテーブル
    with open(output_dir / "mapping_table.md", 'w', encoding='utf-8') as f:
        f.write(mapping_table)
    
    # JSON形式でもエクスポート
    analyzer.export_json({
        'book_structure': book_structure,
        'mapping': mapping,
        'doc_categories': analyzer.doc_categories,
        'topic_mapping': analyzer.topic_mapping
    }, output_dir / "analysis_data.json")
    
    print(f"\n解析完了！")
    print(f"カバレッジレポート: {output_dir / 'coverage_report.md'}")
    print(f"マッピングテーブル: {output_dir / 'mapping_table.md'}")
    print(f"解析データ: {output_dir / 'analysis_data.json'}")

if __name__ == "__main__":
    main()