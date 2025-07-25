#!/usr/bin/env python3
"""
公式ドキュメント解析ツール

Rust公式ドキュメントから学習要素を抽出し、
構造化されたデータとして出力します。
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class LearningElement:
    """学習要素のデータクラス"""
    id: str
    source: str
    chapter: str
    title: str
    concepts: List[str]
    prerequisites: List[str]
    difficulty: str
    cs_theory: List[str]
    

class OfficialDocsParser:
    """公式ドキュメント解析クラス"""
    
    def __init__(self):
        self.learning_elements: List[LearningElement] = []
        
    def parse_the_book(self) -> List[LearningElement]:
        """
        The Rust Programming Languageから学習要素を抽出
        
        注: 実際の実装では、公式ドキュメントのHTML/Markdownを
        パースして情報を抽出します
        """
        # サンプルデータ
        elements = [
            LearningElement(
                id="ownership_basic",
                source="the_book",
                chapter="4",
                title="Understanding Ownership",
                concepts=["ownership_rules", "move_semantics", "copy_trait"],
                prerequisites=["variables", "functions"],
                difficulty="beginner",
                cs_theory=["memory_management", "resource_management"]
            ),
            LearningElement(
                id="borrowing_basic",
                source="the_book",
                chapter="4.2",
                title="References and Borrowing",
                concepts=["references", "mutable_references", "borrowing_rules"],
                prerequisites=["ownership_basic"],
                difficulty="beginner",
                cs_theory=["pointer_semantics", "memory_safety"]
            ),
        ]
        return elements
        
    def parse_reference(self) -> List[LearningElement]:
        """
        The Rust Referenceから学習要素を抽出
        """
        elements = [
            LearningElement(
                id="type_system_advanced",
                source="reference",
                chapter="3",
                title="Type System",
                concepts=["type_inference", "type_coercion", "subtyping"],
                prerequisites=["type_basics"],
                difficulty="intermediate",
                cs_theory=["type_theory", "type_inference_algorithms"]
            ),
        ]
        return elements
        
    def parse_rustonomicon(self) -> List[LearningElement]:
        """
        The Rustonomiconから学習要素を抽出
        """
        elements = [
            LearningElement(
                id="lifetimes_advanced",
                source="rustonomicon",
                chapter="3",
                title="Lifetime Subtyping",
                concepts=["variance", "higher_ranked_trait_bounds"],
                prerequisites=["lifetimes_basic", "traits"],
                difficulty="advanced",
                cs_theory=["type_theory", "subtyping"]
            ),
        ]
        return elements
        
    def extract_all(self) -> Dict[str, List[Dict]]:
        """
        すべての公式ドキュメントから学習要素を抽出
        """
        self.learning_elements.extend(self.parse_the_book())
        self.learning_elements.extend(self.parse_reference())
        self.learning_elements.extend(self.parse_rustonomicon())
        
        return {
            "learning_elements": [asdict(elem) for elem in self.learning_elements]
        }
        
    def save_to_yaml(self, output_path: Path):
        """
        抽出したデータをYAML形式で保存
        """
        data = self.extract_all()
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
    def save_to_json(self, output_path: Path):
        """
        抽出したデータをJSON形式で保存
        """
        data = self.extract_all()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    parser = OfficialDocsParser()
    
    # YAML形式で保存
    parser.save_to_yaml(Path("learning_elements.yaml"))
    
    # JSON形式で保存
    parser.save_to_json(Path("learning_elements.json"))
    
    print("学習要素の抽出が完了しました。")