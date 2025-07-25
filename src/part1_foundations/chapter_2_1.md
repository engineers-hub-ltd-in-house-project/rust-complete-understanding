# 線形型理論と所有権

## はじめに

Rustの所有権システムを深く理解するためには、その理論的基礎である線形型理論（Linear Type Theory）を理解することが重要です。本節では、数学的な観点から線形型理論を解説し、それがどのようにRustの所有権システムに実装されているかを探求します。

## 線形論理の基礎

### 線形論理とは

線形論理は、1987年にフランスの論理学者Jean-Yves Girardによって提唱されました。従来の論理では、命題は何度でも使用できる（構造規則の弱化と縮約）のに対し、線形論理では**リソースとしての命題**という概念を導入しました。

#### 従来の論理の構造規則

```
弱化（Weakening）:
Γ ⊢ B
───────
Γ, A ⊢ B

縮約（Contraction）:
Γ, A, A ⊢ B
───────────
Γ, A ⊢ B
```

これらの規則により、命題Aは0回でも複数回でも使用できます。

#### 線形論理での制限

線形論理では、これらの構造規則を制限します：

```
線形含意（Linear Implication）: A ⊸ B
「AというリソースをちょうどB」

乗法的結合（Multiplicative Conjunction）: A ⊗ B
「AとBの両方のリソース」

加法的選択（Additive Disjunction）: A ⊕ B
「AまたはBのどちらか一方」
```

### 線形型システム

線形型システムでは、各値は**正確に一度**使用されなければなりません：

```
型付け規則:
Γ₁ ⊢ e₁ : τ₁    Γ₂ ⊢ e₂ : τ₂
─────────────────────────────── (⊗-intro)
    Γ₁, Γ₂ ⊢ (e₁, e₂) : τ₁ ⊗ τ₂
```

ここで、環境Γ₁とΓ₂は分離されており、変数の重複使用を防ぎます。

## アフィン型理論への拡張

### アフィン論理

アフィン論理は線形論理の緩和版で、**弱化は許すが縮約は許さない**システムです：

```
アフィン論理での規則:
弱化: OK（リソースを使わないことは許される）
縮約: NG（リソースを複製することは許されない）
```

これは実用的なプログラミングにおいて重要です。すべての値を必ず使用しなければならないのは制約が強すぎるからです。

### Rustにおけるアフィン型

Rustの所有権システムは、アフィン型システムの実装です：

```rust
fn affine_example() {
    let x = String::from("hello");  // xがリソースを所有
    
    // 選択1: 使用する
    println!("{}", x);
    
    // 選択2: 使用しない（弱化）
    // xは自動的にドロップされる
    
    // 不可能: 複製（縮約）
    // let y = x;
    // let z = x;  // エラー！
}
```

## 数学的定式化

### 型システムの形式化

Rustの所有権システムを形式的に表現すると：

```
型環境: Γ ::= ∅ | Γ, x:τ
型:     τ ::= T | &τ | &mut τ | Box<τ>

所有権の判定:
─────────── (Var-Own)
Γ, x:τ ⊢ x : τ

Γ ⊢ e : τ
─────────────── (Move)
Γ ⊢ move e : τ

Γ ⊢ e : τ    x ∉ dom(Γ)
──────────────────────── (Let-Move)
Γ ⊢ let x = e : unit
```

### 借用の形式化

借用は、所有権を移動せずに値への参照を作成します：

```
Γ ⊢ e : τ
──────────── (Borrow)
Γ ⊢ &e : &τ

Γ ⊢ e : &τ
─────────── (Deref)
Γ ⊢ *e : τ
```

## 実装例：線形型の動作

### 基本的な線形型の動作

```rust
// 線形型的な動作を示す構造体
struct LinearResource {
    id: u32,
    data: Vec<u8>,
}

impl LinearResource {
    fn new(id: u32, size: usize) -> Self {
        println!("リソース {} を作成", id);
        LinearResource {
            id,
            data: vec![0; size],
        }
    }
    
    // リソースを消費するメソッド
    fn consume(self) -> Vec<u8> {
        println!("リソース {} を消費", self.id);
        self.data  // 所有権を移動
    }
}

impl Drop for LinearResource {
    fn drop(&mut self) {
        println!("リソース {} を解放", self.id);
    }
}

fn demonstrate_linearity() {
    let resource = LinearResource::new(1, 100);
    
    // 一度だけ使用可能
    let data = resource.consume();
    
    // resource.consume();  // エラー：すでに移動済み
    
    println!("データサイズ: {}", data.len());
}
```

### アフィン型の実用例

```rust
use std::sync::mpsc;
use std::thread;

// 送信端は一度しか使えない（アフィン型）
fn channel_example() {
    let (tx, rx) = mpsc::channel();
    
    thread::spawn(move || {
        tx.send(42).unwrap();  // txの所有権が移動
        // tx.send(43);  // エラー：txはすでに移動済み
    });
    
    let received = rx.recv().unwrap();
    println!("受信: {}", received);
}
```

## 理論と実装の対応

### 型レベルでの保証

Rustのマーカートレイトは、型レベルで線形性を保証します：

```rust
// Copyトレイトを実装しない型は自動的にアフィン型
struct NonCopyable {
    data: String,
}

// Copyトレイトを実装する型は自由に複製可能
#[derive(Copy, Clone)]
struct Copyable {
    value: i32,
}

fn type_level_guarantees() {
    let nc = NonCopyable { data: String::from("unique") };
    let c = Copyable { value: 42 };
    
    let nc2 = nc;  // 移動（アフィン型）
    // let nc3 = nc;  // エラー
    
    let c2 = c;   // コピー
    let c3 = c;   // OK：何度でもコピー可能
}
```

### 借用検査器の役割

借用検査器（Borrow Checker）は、アフィン型の規則を実行時ではなくコンパイル時に検証します：

```rust
fn borrow_checker_example() {
    let mut data = vec![1, 2, 3];
    
    // 不変借用は複数可能（読み取り専用）
    let r1 = &data;
    let r2 = &data;
    println!("{:?} {:?}", r1, r2);
    
    // 可変借用は一つだけ（排他的アクセス）
    let m1 = &mut data;
    // let m2 = &mut data;  // エラー：既に可変借用されている
    m1.push(4);
}
```

## 高度な型理論的概念

### 部分構造型理論

Rustの型システムは、部分構造型理論（Substructural Type Theory）の一種です：

```
部分構造型の分類:
- 線形型（Linear）: 正確に1回使用
- アフィン型（Affine）: 最大1回使用  ← Rust
- 関連型（Relevant）: 最低1回使用
- 通常型（Normal）: 任意回使用
```

### ライフタイムと型理論

ライフタイムは、借用の有効期間を型レベルで追跡します：

```rust
// ライフタイムパラメータ 'a は型理論での時相論理に対応
fn lifetime_theory<'a, T>(x: &'a T) -> &'a T {
    x  // 入力と同じライフタイムを保持
}
```

## まとめ

線形型理論とアフィン型理論は、Rustの所有権システムの数学的基礎を提供します。これらの理論により、メモリ安全性が型システムのレベルで保証され、実行時オーバーヘッドなしに安全なシステムプログラミングが可能になります。

次節では、この理論的基礎の上に構築された「moveセマンティクス」の詳細な動作を見ていきます。

## 公式ドキュメント参照

- **Reference**: Section 15.2 - Subtyping and Variance
- **Rustonomicon**: Chapter 3.2 - Ownership and Lifetimes
- **RFC 1238**: Nonparametric dropck