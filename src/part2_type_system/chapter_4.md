# 型理論の基礎とRustの型システム

## はじめに

型システムは、プログラミング言語の安全性と表現力を決定する重要な要素です。Rustの型システムは、MLファミリーの言語から影響を受けた強力な静的型システムに、所有権という独自の概念を統合したものです。本章では、型理論の基礎から始め、Rustがどのようにこれらの理論を実装し、拡張しているかを探求します。

## 型理論の歴史と基礎

### ラムダ計算から型付きラムダ計算へ

1930年代、Alonzo Churchが考案したラムダ計算は、計算の数学的モデルです：

```
λ計算の構文:
e ::= x         // 変数
    | λx.e      // 抽象（関数）
    | e₁ e₂     // 適用
```

しかし、純粋なラムダ計算には「型」の概念がありません。1940年、Churchは単純型付きラムダ計算を導入しました：

```
型の構文:
τ ::= α         // 基本型
    | τ₁ → τ₂   // 関数型

型付け規則:
Γ, x:τ ⊢ x:τ   // 変数

Γ, x:τ₁ ⊢ e:τ₂
─────────────── // 抽象
Γ ⊢ λx.e : τ₁→τ₂

Γ ⊢ e₁:τ₁→τ₂   Γ ⊢ e₂:τ₁
────────────────────────── // 適用
Γ ⊢ e₁ e₂ : τ₂
```

### Curry-Howard対応

型システムと論理の深い関係を示すCurry-Howard対応：

```
型          ≈ 命題
プログラム   ≈ 証明
関数型 A→B  ≈ 含意 A⇒B
積型 A×B    ≈ 連言 A∧B
和型 A+B    ≈ 選言 A∨B
```

この対応により、「型安全なプログラムを書く」ことは「数学的証明を構築する」ことと等価になります。

## Rustの型システムの特徴

### 静的型付けと型推論

Rustは静的型付け言語ですが、強力な型推論により多くの場合型注釈が不要です：

```rust
// 型推論の例
fn type_inference_example() {
    let x = 42;           // i32と推論
    let y = 3.14;         // f64と推論
    let z = x as f64 + y; // f64と推論
    
    // ジェネリクスでの型推論
    let vec = vec![1, 2, 3];  // Vec<i32>と推論
    let first = vec.first();   // Option<&i32>と推論
}
```

### 代数的データ型（ADT）

Rustは直積型（struct）と直和型（enum）をサポート：

```rust
// 直積型（Product Type）
struct Point {
    x: f64,
    y: f64,
}

// 直和型（Sum Type）
enum Shape {
    Circle { radius: f64 },
    Rectangle { width: f64, height: f64 },
    Triangle { base: f64, height: f64 },
}

// パターンマッチングによる分解
fn area(shape: &Shape) -> f64 {
    match shape {
        Shape::Circle { radius } => std::f64::consts::PI * radius * radius,
        Shape::Rectangle { width, height } => width * height,
        Shape::Triangle { base, height } => 0.5 * base * height,
    }
}
```

### 型の代数的性質

型を代数的に理解すると：

```rust
// 和型の値の数 = 各バリアントの値の数の和
enum Bool { True, False }  // 2 = 1 + 1

// 積型の値の数 = 各フィールドの値の数の積
struct Pair(bool, bool);   // 4 = 2 × 2

// Option<T> = 1 + T （NoneとSome(T)）
// Result<T, E> = T + E （Ok(T)とErr(E)）
```

## 高度な型システム機能

### 型レベルプログラミング

Rustでは、型レベルで計算を表現できます：

```rust
use std::marker::PhantomData;

// 型レベル自然数
struct Zero;
struct Succ<N>(PhantomData<N>);

// 型レベル加算
trait Add<B> {
    type Output;
}

impl<B> Add<B> for Zero {
    type Output = B;
}

impl<A, B> Add<B> for Succ<A>
where
    A: Add<B>,
{
    type Output = Succ<A::Output>;
}

// 使用例
type One = Succ<Zero>;
type Two = Succ<One>;
type Three = <One as Add<Two>>::Output;
```

### 高階型（Higher-Kinded Types）の模倣

Rustは直接的にHKTをサポートしませんが、トレイトで模倣できます：

```rust
// Functorパターン
trait Functor {
    type Wrapped<T>;
    
    fn map<A, B, F>(self, f: F) -> Self::Wrapped<B>
    where
        F: FnOnce(A) -> B;
}

// Generic Associated Types (GAT)を使用
trait Container {
    type Item<'a> where Self: 'a;
    
    fn get<'a>(&'a self) -> Self::Item<'a>;
}
```

### 幽霊型（Phantom Types）

コンパイル時の型安全性を向上させる技法：

```rust
use std::marker::PhantomData;

// 状態を型で表現
struct Locked;
struct Unlocked;

struct Door<State> {
    _phantom: PhantomData<State>,
}

impl Door<Locked> {
    fn unlock(self) -> Door<Unlocked> {
        Door { _phantom: PhantomData }
    }
}

impl Door<Unlocked> {
    fn lock(self) -> Door<Locked> {
        Door { _phantom: PhantomData }
    }
    
    fn open(&self) {
        println!("Door opened!");
    }
}

// 使用例
fn door_example() {
    let door = Door::<Locked> { _phantom: PhantomData };
    // door.open();  // コンパイルエラー：Locked状態では開けない
    
    let door = door.unlock();
    door.open();  // OK：Unlocked状態なので開ける
}
```

## 型システムと所有権の統合

### アフィン型としての所有権

Rustの所有権システムは、型システムに統合されています：

```rust
// 型が所有権を表現
fn ownership_in_types() {
    // T: 所有された値
    let owned: String = String::from("hello");
    
    // &T: 不変借用
    let borrowed: &String = &owned;
    
    // &mut T: 可変借用
    let mut owned_mut = String::from("world");
    let borrowed_mut: &mut String = &mut owned_mut;
}

// 型によって異なる所有権セマンティクス
fn type_based_ownership<T: Clone>(x: T) -> (T, T) {
    (x.clone(), x)  // Cloneトレイトが必要
}
```

### 型による並行性の保証

`Send`と`Sync`トレイトによる型レベルの並行性制御：

```rust
use std::rc::Rc;
use std::sync::Arc;
use std::thread;

// Sendでない型
fn not_send() {
    let rc = Rc::new(42);
    // thread::spawn(move || {
    //     println!("{}", rc);  // エラー：RcはSendでない
    // });
}

// Sendな型
fn is_send() {
    let arc = Arc::new(42);
    thread::spawn(move || {
        println!("{}", arc);  // OK：ArcはSend
    });
}
```

## 型推論アルゴリズム

### Hindley-Milner型推論

Rustの型推論は、Hindley-Milner型推論の拡張です：

```rust
// 型推論の過程を示す例
fn hindley_milner_example() {
    let id = |x| x;  // ∀α. α → α と推論
    
    let x = id(42);      // α = i32 と単一化
    let y = id("hello"); // 別のインスタンス：α = &str
    
    // 多相関数
    fn identity<T>(x: T) -> T { x }
    
    // 型推論の制約収集
    let result = identity(vec![1, 2, 3]);  // T = Vec<i32>
}
```

### 双方向型検査

Rustは型推論と型検査を組み合わせます：

```rust
// 上向き推論（synthesis）
fn upward() -> i32 {
    42  // 型を推論：i32
}

// 下向き検査（checking）
fn downward() {
    let x: i32 = 42;  // 期待される型に対して検査
    
    // 型強制（coercion）
    let y: &str = "hello";  // &'static str から &str へ
}
```

## 実用的な型パターン

### ニュータイプパターン

型安全性を高める軽量な抽象化：

```rust
// 単位を型で表現
struct Meters(f64);
struct Feet(f64);

impl Meters {
    fn to_feet(&self) -> Feet {
        Feet(self.0 * 3.28084)
    }
}

fn calculate_distance() {
    let distance = Meters(100.0);
    // let wrong = distance + Feet(50.0);  // エラー：型が異なる
    
    let in_feet = distance.to_feet();
    println!("{} feet", in_feet.0);
}
```

### 型状態パターン

プロトコルや状態遷移を型で表現：

```rust
// TCPコネクションの状態
struct Closed;
struct Connected;
struct Listening;

struct TcpStream<State> {
    _state: PhantomData<State>,
}

impl TcpStream<Closed> {
    fn connect(self) -> Result<TcpStream<Connected>, Error> {
        // 接続処理
        Ok(TcpStream { _state: PhantomData })
    }
}

impl TcpStream<Connected> {
    fn send(&mut self, data: &[u8]) -> Result<(), Error> {
        // データ送信
        Ok(())
    }
}
```

### ビルダーパターンと型安全性

```rust
struct Builder<HasName, HasAge> {
    name: Option<String>,
    age: Option<u32>,
    _phantom: PhantomData<(HasName, HasAge)>,
}

struct Yes;
struct No;

impl Builder<No, No> {
    fn new() -> Self {
        Builder {
            name: None,
            age: None,
            _phantom: PhantomData,
        }
    }
}

impl<HasAge> Builder<No, HasAge> {
    fn name(self, name: String) -> Builder<Yes, HasAge> {
        Builder {
            name: Some(name),
            age: self.age,
            _phantom: PhantomData,
        }
    }
}

impl<HasName> Builder<HasName, No> {
    fn age(self, age: u32) -> Builder<HasName, Yes> {
        Builder {
            name: self.name,
            age: Some(age),
            _phantom: PhantomData,
        }
    }
}

impl Builder<Yes, Yes> {
    fn build(self) -> Person {
        Person {
            name: self.name.unwrap(),
            age: self.age.unwrap(),
        }
    }
}

struct Person {
    name: String,
    age: u32,
}
```

## 型システムの限界と将来

### 現在の限界

1. **高階型の直接サポートなし**
2. **依存型の欠如**
3. **型レベル計算の制限**

### 将来の拡張可能性

```rust
// 将来可能になるかもしれない機能の例

// const generics（既に部分的にサポート）
struct Array<T, const N: usize> {
    data: [T; N],
}

// 型族（type families）の可能性
// type family Add a b where
//     Add Zero b = b
//     Add (Succ a) b = Succ (Add a b)
```

## まとめ

Rustの型システムは、以下の特徴を持ちます：

1. **理論的基礎**: ラムダ計算と型理論に基づく健全な設計
2. **実用性**: 型推論による使いやすさと表現力
3. **安全性**: 所有権と型システムの統合によるメモリ安全性
4. **拡張性**: トレイトシステムによる柔軟な抽象化

この強力な型システムにより、Rustは「高速」「安全」「並行」という目標を達成しています。

次章では、このトレイトシステムとジェネリクスについて、より詳しく見ていきます。

## 公式ドキュメント参照

- **The Book**: Chapter 10 - Generic Types, Traits, and Lifetimes
- **Reference**: Chapter 8 - Type system
- **Rustonomicon**: Chapter 6 - Type Conversions
- **RFC 1598**: Generic Associated Types