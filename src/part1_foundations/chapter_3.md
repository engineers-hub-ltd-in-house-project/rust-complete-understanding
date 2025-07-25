# 借用システムとライフタイム

## はじめに

前章で学んだ所有権システムは、メモリ安全性を保証する強力な仕組みですが、それだけでは実用的なプログラムを書くことは困難です。なぜなら、所有権の移動だけでは、複数の場所から同じデータを参照したり、短期間データを使用したりすることができないからです。Rustは「借用（Borrowing）」と「ライフタイム（Lifetime）」という概念を導入することで、この問題を解決しています。

## 借用システムの基礎

### 借用とは何か

借用は、所有権を移動せずに値への参照を作成する仕組みです：

```rust
fn main() {
    let s = String::from("hello");
    let len = calculate_length(&s);  // sを借用
    println!("The length of '{}' is {}.", s, len);  // sはまだ使える
}

fn calculate_length(s: &String) -> usize {
    s.len()  // 借用した値を読み取り
}
```

### 借用の2つのルール

Rustの借用システムには、2つの基本的なルールがあります：

1. **任意の時点で、1つの可変参照か、任意個の不変参照のどちらかを持てる（両方は不可）**
2. **参照は常に有効でなければならない**

```rust
fn borrowing_rules() {
    let mut s = String::from("hello");
    
    // ルール1: 複数の不変参照はOK
    let r1 = &s;
    let r2 = &s;
    println!("{} and {}", r1, r2);
    
    // ルール1: 可変参照は1つだけ
    let r3 = &mut s;
    // let r4 = &mut s;  // エラー：2つ目の可変参照
    
    // ルール2: 参照は有効でなければならない
    let r;
    {
        let x = 5;
        r = &x;  // xのライフタイムはこのスコープ内
    }
    // println!("{}", r);  // エラー：xはスコープ外
}
```

## 理論的基礎：読み書きロックとの対応

借用システムは、並行プログラミングの読み書きロック（RWLock）と同じ原理に基づいています：

```rust
// 概念的な対応関係
// &T    ≈ 読み取りロック（共有可能）
// &mut T ≈ 書き込みロック（排他的）

use std::sync::RwLock;

fn rwlock_analogy() {
    let data = RwLock::new(5);
    
    // 複数の読み取りロック
    let r1 = data.read().unwrap();
    let r2 = data.read().unwrap();
    println!("{} {}", *r1, *r2);
    drop(r1);
    drop(r2);
    
    // 排他的な書き込みロック
    let mut w = data.write().unwrap();
    *w += 1;
}
```

## ライフタイムの概念

### ライフタイムとは

ライフタイムは、参照が有効である期間を表す概念です。Rustコンパイラは、すべての参照にライフタイムを割り当て、参照が常に有効であることを保証します。

```rust
// ライフタイムの明示的な注釈
fn longest<'a>(x: &'a str, y: &'a str) -> &'a str {
    if x.len() > y.len() {
        x
    } else {
        y
    }
}
```

### ライフタイムの推論

多くの場合、コンパイラはライフタイムを自動的に推論します：

```rust
// ライフタイム省略規則が適用される
fn first_word(s: &str) -> &str {
    let bytes = s.as_bytes();
    
    for (i, &item) in bytes.iter().enumerate() {
        if item == b' ' {
            return &s[0..i];
        }
    }
    
    &s[..]
}
```

## 借用チェッカーの仕組み

### Non-Lexical Lifetimes (NLL)

Rust 2018で導入されたNLLにより、借用チェッカーはより賢くなりました：

```rust
fn nll_example() {
    let mut x = 5;
    let r1 = &x;        // 不変借用開始
    println!("{}", r1); // 最後の使用
    // NLL以前: ここで借用が終了しない
    // NLL以降: ここで借用が終了
    
    let r2 = &mut x;    // 可変借用が可能
    *r2 += 1;
}
```

### 借用の分割

構造体のフィールドは個別に借用できます：

```rust
struct Point {
    x: i32,
    y: i32,
}

fn split_borrowing() {
    let mut point = Point { x: 0, y: 0 };
    
    let r1 = &point.x;      // xフィールドの不変借用
    let r2 = &mut point.y;  // yフィールドの可変借用
    
    println!("x: {}", r1);
    *r2 += 1;
}
```

## 高度なライフタイムパターン

### 複数のライフタイムパラメータ

異なるライフタイムを持つ参照を扱う場合：

```rust
fn complex_lifetimes<'a, 'b>(x: &'a str, y: &'b str) -> &'a str {
    println!("y: {}", y);
    x  // xのライフタイムを返す
}
```

### ライフタイムの境界

ジェネリック型にライフタイムの制約を設定：

```rust
use std::fmt::Display;

fn longest_with_announcement<'a, T>(
    x: &'a str,
    y: &'a str,
    ann: T,
) -> &'a str
where
    T: Display,
{
    println!("Announcement: {}", ann);
    if x.len() > y.len() {
        x
    } else {
        y
    }
}
```

### 構造体のライフタイム

参照を含む構造体では、ライフタイムの注釈が必要：

```rust
struct ImportantExcerpt<'a> {
    part: &'a str,
}

impl<'a> ImportantExcerpt<'a> {
    fn level(&self) -> i32 {
        3
    }
    
    fn announce_and_return_part(&self, announcement: &str) -> &str {
        println!("Attention please: {}", announcement);
        self.part
    }
}

fn struct_lifetime_example() {
    let novel = String::from("Call me Ishmael. Some years ago...");
    let first_sentence = novel.split('.').next().expect("Could not find a '.'");
    let i = ImportantExcerpt {
        part: first_sentence,
    };
    
    println!("Important part: {}", i.part);
}
```

## 実践的な借用パターン

### イテレータと借用

```rust
fn iterator_borrowing() {
    let vec = vec![1, 2, 3, 4, 5];
    
    // 不変借用によるイテレーション
    for item in &vec {
        println!("{}", item);
    }
    
    // 可変借用によるイテレーション
    let mut vec_mut = vec![1, 2, 3];
    for item in &mut vec_mut {
        *item *= 2;
    }
}
```

### メソッドレシーバーの借用

```rust
struct Counter {
    value: i32,
}

impl Counter {
    // 不変借用
    fn get(&self) -> i32 {
        self.value
    }
    
    // 可変借用
    fn increment(&mut self) {
        self.value += 1;
    }
    
    // 所有権を取得
    fn into_value(self) -> i32 {
        self.value
    }
}
```

### Interior Mutability パターン

`RefCell`を使用した実行時借用チェック：

```rust
use std::cell::RefCell;

struct Cache {
    data: RefCell<Option<String>>,
}

impl Cache {
    fn new() -> Self {
        Cache {
            data: RefCell::new(None),
        }
    }
    
    fn get_or_compute(&self, compute: impl FnOnce() -> String) -> String {
        let mut data = self.data.borrow_mut();
        match data.as_ref() {
            Some(value) => value.clone(),
            None => {
                let value = compute();
                *data = Some(value.clone());
                value
            }
        }
    }
}
```

## 借用とライフタイムの数学的モデル

### 領域推論（Region Inference）

ライフタイムは、数学的には「領域」として表現されます：

```
'a: {L1, L2, ..., Ln}
```

ここで、各Liはプログラムの位置を表します。

### 制約システム

借用チェッカーは、以下のような制約を解きます：

```
'a: 'b  // 'aは'bより長く生きる
'a = 'b  // 'aと'bは同じライフタイム
```

## エラーパターンと解決方法

### よくあるエラー1：ダングリング参照

```rust
fn dangling_reference() -> &String {  // エラー
    let s = String::from("hello");
    &s  // sはこの関数の終了時に破棄される
}

// 解決方法：所有権を返す
fn fixed_dangling() -> String {
    let s = String::from("hello");
    s  // 所有権を移動
}
```

### よくあるエラー2：可変参照の競合

```rust
fn mutable_conflict() {
    let mut s = String::from("hello");
    let r1 = &mut s;
    let r2 = &mut s;  // エラー：2つの可変参照
    
    // 解決方法：スコープを分ける
    {
        let r1 = &mut s;
        // r1を使用
    }  // r1のスコープ終了
    let r2 = &mut s;  // OK
}
```

## まとめ

借用とライフタイムは、Rustのメモリ安全性を支える重要な概念です：

1. **借用**により、所有権を移動せずにデータへのアクセスが可能
2. **ライフタイム**により、参照の有効性がコンパイル時に保証される
3. **借用チェッカー**が、これらのルールを強制する

これらの仕組みにより、Rustは実行時オーバーヘッドなしに、メモリ安全性と並行性の安全性を実現しています。

次節では、借用システムの理論的基礎であるアフィン型理論との関係について、より詳しく見ていきます。

## 公式ドキュメント参照

- **The Book**: Chapter 4.2 - References and Borrowing
- **The Book**: Chapter 10.3 - Lifetime Syntax
- **Reference**: Section 10.3 - Lifetimes
- **Rustonomicon**: Chapter 3 - Lifetimes