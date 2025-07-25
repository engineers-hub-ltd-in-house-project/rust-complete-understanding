# ジェネリクスとトレイト

## はじめに

ジェネリクスとトレイトは、Rustの型システムの中核を成す機能です。ジェネリクスは型の抽象化を可能にし、トレイトは振る舞いの抽象化を提供します。これらは単なる便利な機能ではなく、Rustの「ゼロコスト抽象化」と「型安全性」を実現する基盤技術です。本章では、これらの機能の理論的背景から実装詳細まで、包括的に探求します。

## ジェネリクスの理論的基礎

### パラメトリック多相性

ジェネリクスは、型理論における「パラメトリック多相性」の実装です：

```rust
// 恒等関数：任意の型Tに対して動作
fn identity<T>(x: T) -> T {
    x
}

// 型理論的表現：∀T. T → T
// これは「すべての型Tに対して、TからTへの関数」を意味
```

### パラメトリシティ定理

パラメトリック多相関数には重要な性質があります：

```rust
// この関数は、型Tの値の内部を観察できない
fn mystery<T>(x: T, y: T) -> T {
    // xかyのどちらかを返すしかない
    // Tの具体的な値に依存した処理は不可能
    x  // またはy
}

// 自由定理（Free Theorem）：
// ∀f: A → B, ∀x: A. 
// map(f, identity(x)) = identity(map(f, x))
```

## Rustにおけるジェネリクスの実装

### 単相化（Monomorphization）

Rustはコンパイル時にジェネリック関数を具体的な型で特殊化します：

```rust
// ジェネリック関数
fn add<T: std::ops::Add<Output = T>>(a: T, b: T) -> T {
    a + b
}

// 使用例
let int_result = add(5, 3);      // add::<i32>が生成
let float_result = add(5.0, 3.0); // add::<f64>が生成

// コンパイラは以下のような特殊化されたコードを生成
// fn add_i32(a: i32, b: i32) -> i32 { a + b }
// fn add_f64(a: f64, b: f64) -> f64 { a + b }
```

### ジェネリック構造体と列挙型

```rust
// ジェネリック構造体
struct Point<T> {
    x: T,
    y: T,
}

// 複数の型パラメータ
struct Pair<T, U> {
    first: T,
    second: U,
}

// ジェネリック列挙型
enum Option<T> {
    Some(T),
    None,
}

enum Result<T, E> {
    Ok(T),
    Err(E),
}

// 実装例
impl<T> Point<T> {
    fn new(x: T, y: T) -> Self {
        Point { x, y }
    }
}

impl<T: Clone> Point<T> {
    fn duplicate(&self) -> Self {
        Point {
            x: self.x.clone(),
            y: self.y.clone(),
        }
    }
}
```

## トレイトの理論的基礎

### 型クラスとの関係

トレイトは、Haskellの型クラスに影響を受けた概念です：

```rust
// Rustのトレイト
trait Show {
    fn show(&self) -> String;
}

// Haskellの型クラス（参考）
// class Show a where
//     show :: a -> String
```

### トレイトの意味論

トレイトは「型が満たすべき契約」を定義します：

```rust
// 数学的な群の性質をトレイトで表現
trait Group {
    // 単位元
    fn identity() -> Self;
    
    // 二項演算
    fn compose(&self, other: &Self) -> Self;
    
    // 逆元
    fn inverse(&self) -> Self;
}

// 整数の加法群
impl Group for i32 {
    fn identity() -> Self { 0 }
    fn compose(&self, other: &Self) -> Self { self + other }
    fn inverse(&self) -> Self { -self }
}
```

## トレイトの高度な機能

### 関連型（Associated Types）

```rust
// 関連型を持つトレイト
trait Iterator {
    type Item;  // 関連型
    
    fn next(&mut self) -> Option<Self::Item>;
}

// 実装例
struct Counter {
    count: u32,
}

impl Iterator for Counter {
    type Item = u32;  // 関連型の具体化
    
    fn next(&mut self) -> Option<Self::Item> {
        self.count += 1;
        Some(self.count)
    }
}

// 関連型 vs 型パラメータ
// 型パラメータ版（良くない設計）
trait IteratorParam<T> {
    fn next(&mut self) -> Option<T>;
}
// 問題：同じ型に対して複数の実装が可能になる
```

### トレイト境界（Trait Bounds）

```rust
// 基本的なトレイト境界
fn print_debug<T: std::fmt::Debug>(value: &T) {
    println!("{:?}", value);
}

// 複数のトレイト境界
fn compare_and_print<T: PartialOrd + std::fmt::Display>(a: &T, b: &T) {
    if a < b {
        println!("{} < {}", a, b);
    } else {
        println!("{} >= {}", a, b);
    }
}

// where句による読みやすい記法
fn complex_function<T, U, V>(t: T, u: U) -> V
where
    T: Clone + std::fmt::Debug,
    U: Iterator<Item = T>,
    V: Default + From<T>,
{
    // 実装
    V::default()
}
```

### 高階トレイト境界（HRTB）

```rust
// ライフタイムに対する高階境界
fn higher_ranked<F>(f: F) 
where
    F: for<'a> Fn(&'a str) -> &'a str
{
    let s = String::from("hello");
    let result = f(&s);
    println!("{}", result);
}

// クロージャトレイトの階層
// Fn: 不変借用で呼び出し可能
// FnMut: 可変借用で呼び出し可能
// FnOnce: 所有権を取って一度だけ呼び出し可能

fn closure_traits_demo() {
    // Fn
    let immutable = |x: &i32| x + 1;
    
    // FnMut
    let mut counter = 0;
    let mut mutable = |x: i32| {
        counter += x;
        counter
    };
    
    // FnOnce
    let s = String::from("hello");
    let once = move || s;  // sの所有権を取る
}
```

## トレイトオブジェクトと動的ディスパッチ

### 静的ディスパッチ vs 動的ディスパッチ

```rust
// 静的ディスパッチ（コンパイル時に解決）
fn static_dispatch<T: std::fmt::Display>(value: &T) {
    println!("{}", value);
}

// 動的ディスパッチ（実行時に解決）
fn dynamic_dispatch(value: &dyn std::fmt::Display) {
    println!("{}", value);
}

// トレイトオブジェクトの内部表現
// &dyn Trait = データポインタ + vtableポインタ（ファットポインタ）

struct TraitObject {
    data: *const (),
    vtable: *const VTable,
}

struct VTable {
    destructor: fn(*mut ()),
    size: usize,
    align: usize,
    method1: fn(*const ()) -> ReturnType,
    // ... 他のメソッド
}
```

### オブジェクト安全性

```rust
// オブジェクト安全なトレイト
trait Draw {
    fn draw(&self);
}

// オブジェクト安全でないトレイト
trait NotObjectSafe {
    // Selfを返すメソッド
    fn clone_self(&self) -> Self;
    
    // ジェネリックメソッド
    fn generic_method<T>(&self, x: T);
    
    // 関連関数（selfを取らない）
    fn associated_function();
}

// トレイトオブジェクトの使用例
struct Screen {
    components: Vec<Box<dyn Draw>>,
}

impl Screen {
    fn run(&self) {
        for component in &self.components {
            component.draw();  // 動的ディスパッチ
        }
    }
}
```

## 高度なトレイトパターン

### トレイトの継承

```rust
// スーパートレイト
trait Animal {
    fn name(&self) -> &str;
}

trait Dog: Animal {  // DogはAnimalを継承
    fn bark(&self);
}

struct Beagle {
    name: String,
}

impl Animal for Beagle {
    fn name(&self) -> &str {
        &self.name
    }
}

impl Dog for Beagle {
    fn bark(&self) {
        println!("{} says: Woof!", self.name());
    }
}
```

### デフォルト実装とオーバーライド

```rust
trait Summary {
    fn summarize_author(&self) -> String;
    
    // デフォルト実装
    fn summarize(&self) -> String {
        format!("(Read more from {}...)", self.summarize_author())
    }
}

struct Tweet {
    username: String,
    content: String,
}

impl Summary for Tweet {
    fn summarize_author(&self) -> String {
        format!("@{}", self.username)
    }
    
    // デフォルト実装をオーバーライド
    fn summarize(&self) -> String {
        format!("{}: {}", self.username, self.content)
    }
}
```

### 拡張トレイト（Extension Traits）

```rust
// 既存の型に新しいメソッドを追加
trait VecExt<T> {
    fn second(&self) -> Option<&T>;
}

impl<T> VecExt<T> for Vec<T> {
    fn second(&self) -> Option<&T> {
        self.get(1)
    }
}

// 使用例
fn extension_example() {
    let vec = vec![1, 2, 3];
    println!("{:?}", vec.second());  // Some(&2)
}
```

## マーカートレイト

### コンパイラ組み込みトレイト

```rust
// Send: スレッド間で所有権を転送可能
// Sync: スレッド間で参照を共有可能
// Copy: ビットコピーで複製可能
// Sized: コンパイル時にサイズが既知

// 自動実装の制御
struct NotSend {
    _marker: std::marker::PhantomData<*const u8>,
}

// Sendでないことを明示
impl !Send for NotSend {}

// PhantomDataを使った型の調整
struct PhantomExample<T> {
    // Tを「所有している」ように見せる
    _phantom: std::marker::PhantomData<T>,
}
```

### カスタムマーカートレイト

```rust
// 独自のマーカートレイト
trait Serializable {}
trait Validated {}

// 型レベルでの保証
struct User<T = ()> {
    name: String,
    email: String,
    _state: std::marker::PhantomData<T>,
}

impl User {
    fn new(name: String, email: String) -> User<()> {
        User {
            name,
            email,
            _state: std::marker::PhantomData,
        }
    }
}

impl User<()> {
    fn validate(self) -> Result<User<Validated>, String> {
        if self.email.contains('@') {
            Ok(User {
                name: self.name,
                email: self.email,
                _state: std::marker::PhantomData,
            })
        } else {
            Err("Invalid email".to_string())
        }
    }
}

impl User<Validated> {
    fn save(&self) {
        // 検証済みのユーザーのみ保存可能
        println!("Saving user: {}", self.name);
    }
}
```

## トレイトとジェネリクスの相互作用

### impl Trait構文

```rust
// 引数位置でのimpl Trait
fn accept_displayable(item: impl std::fmt::Display) {
    println!("{}", item);
}

// 戻り値位置でのimpl Trait
fn return_iterator() -> impl Iterator<Item = i32> {
    vec![1, 2, 3].into_iter()
}

// impl Traitの制限
// fn invalid() -> impl Display {
//     if condition {
//         "string"  // &str
//     } else {
//         42        // i32 - エラー：異なる型
//     }
// }
```

### トレイトエイリアス（実験的機能）

```rust
// 将来のRustで可能になるかもしれない機能
// trait Draw = std::fmt::Debug + std::fmt::Display;

// 現在の回避策
trait DrawAlias: std::fmt::Debug + std::fmt::Display {}
impl<T: std::fmt::Debug + std::fmt::Display> DrawAlias for T {}
```

## パフォーマンスへの影響

### ゼロコスト抽象化の実現

```rust
// ジェネリクスは単相化によりゼロコスト
fn generic_sum<T: std::ops::Add<Output = T> + Default + Copy>(slice: &[T]) -> T {
    let mut sum = T::default();
    for &item in slice {
        sum = sum + item;
    }
    sum
}

// トレイトオブジェクトは間接参照のコスト
fn dynamic_sum(slice: &[Box<dyn std::ops::Add<Output = i32>>]) -> i32 {
    // vtable経由の呼び出し
    0  // 簡略化
}

// インライン化の例
#[inline]
fn small_function<T: Display>(x: T) {
    println!("{}", x);
}
```

## まとめ

ジェネリクスとトレイトは、Rustの型システムの表現力を大幅に拡張する機能です：

1. **ジェネリクス**: パラメトリック多相性による型の抽象化
2. **トレイト**: アドホック多相性による振る舞いの抽象化
3. **単相化**: コンパイル時の特殊化によるゼロコスト実現
4. **トレイトオブジェクト**: 必要に応じた動的ディスパッチ

これらの機能により、Rustは型安全性を保ちながら、高度な抽象化と高性能を両立させています。

次章では、さらに高度な型システム機能について探求します。

## 公式ドキュメント参照

- **The Book**: Chapter 10 - Generic Types, Traits, and Lifetimes
- **Reference**: Chapter 9 - Traits
- **RFC 1522**: Conservative impl trait
- **RFC 1598**: Generic Associated Types