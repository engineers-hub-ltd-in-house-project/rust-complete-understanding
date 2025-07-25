# 高度な型システム機能

## はじめに

Rustの型システムは、基本的な静的型付けを超えて、多くの高度な機能を提供します。これらの機能は、より安全で表現力豊かなコードを書くことを可能にし、多くのバグをコンパイル時に防ぎます。本章では、関連型、型エイリアス、const generics、そして実験的機能など、Rustの型システムの最先端を探求します。

## 関連型（Associated Types）の深い理解

### 関連型の理論的背景

関連型は、型族（type families）の概念に基づいています：

```rust
// 型族の例：コレクションとその要素型の関係
trait Collection {
    type Item;  // 関連型
    
    fn empty() -> Self;
    fn add(&mut self, item: Self::Item);
    fn contains(&self, item: &Self::Item) -> bool;
}

// 具体的な実装
impl Collection for Vec<i32> {
    type Item = i32;
    
    fn empty() -> Self { Vec::new() }
    fn add(&mut self, item: i32) { self.push(item) }
    fn contains(&self, item: &i32) -> bool { self.contains(item) }
}
```

### 関連型 vs 型パラメータ

```rust
// 型パラメータを使った設計（問題あり）
trait GraphParam<N, E> {
    fn nodes(&self) -> Vec<N>;
    fn edges(&self) -> Vec<E>;
}

// 関連型を使った設計（適切）
trait Graph {
    type Node;
    type Edge;
    
    fn nodes(&self) -> Vec<Self::Node>;
    fn edges(&self) -> Vec<Self::Edge>;
}

// 使用時の違い
fn process_param<G, N, E>(graph: G) 
where 
    G: GraphParam<N, E> 
{
    // NとEを明示的に指定する必要がある
}

fn process_assoc<G>(graph: G) 
where 
    G: Graph 
{
    // G::NodeとG::Edgeは自動的に決まる
}
```

### Generic Associated Types (GAT)

Rust 1.65で安定化されたGATは、関連型にジェネリクスを導入します：

```rust
trait Lending {
    type Lend<'a> where Self: 'a;
    
    fn lend(&self) -> Self::Lend<'_>;
}

// 使用例：借用を返すイテレータ
trait LendingIterator {
    type Item<'a> where Self: 'a;
    
    fn next(&mut self) -> Option<Self::Item<'_>>;
}

struct WindowsMut<'t, T> {
    slice: &'t mut [T],
    size: usize,
}

impl<'t, T> LendingIterator for WindowsMut<'t, T> {
    type Item<'a> = &'a mut [T] where Self: 'a;
    
    fn next(&mut self) -> Option<Self::Item<'_>> {
        if self.slice.len() >= self.size {
            let (window, rest) = self.slice.split_at_mut(self.size);
            self.slice = rest;
            Some(window)
        } else {
            None
        }
    }
}
```

## 型エイリアスと不透明型

### 型エイリアスの進化

```rust
// 基本的な型エイリアス
type Kilometers = i32;
type Result<T> = std::result::Result<T, std::io::Error>;

// ジェネリック型エイリアス
type Thunk<T> = Box<dyn Fn() -> T>;

// 関連型を含む型エイリアス
type StringIter = std::vec::IntoIter<String>;

// 高階型エイリアス（現在は不可能）
// type HigherKinded<F> = F<i32>;  // エラー
```

### 存在型（Existential Types）

```rust
// impl Traitによる存在型
fn returns_closure() -> impl Fn(i32) -> i32 {
    |x| x + 1
}

// Type alias impl trait (TAIT) - 実験的機能
#![feature(type_alias_impl_trait)]

type MyIterator = impl Iterator<Item = u32>;

fn create_iterator() -> MyIterator {
    (0..10).map(|x| x * 2)
}

// 不透明型の利点
mod private {
    pub type Handle = impl Send + Sync;
    
    pub fn create_handle() -> Handle {
        // 実装の詳細を隠蔽
        42u64
    }
}
```

## Const Generics

### 基本的なconst generics

```rust
// 配列のサイズを型パラメータとして扱う
struct Matrix<T, const ROWS: usize, const COLS: usize> {
    data: [[T; COLS]; ROWS],
}

impl<T: Default + Copy, const ROWS: usize, const COLS: usize> 
    Matrix<T, ROWS, COLS> 
{
    fn new() -> Self {
        Matrix {
            data: [[T::default(); COLS]; ROWS],
        }
    }
    
    fn transpose(&self) -> Matrix<T, COLS, ROWS> {
        let mut result = Matrix::<T, COLS, ROWS>::new();
        for i in 0..ROWS {
            for j in 0..COLS {
                result.data[j][i] = self.data[i][j];
            }
        }
        result
    }
}

// 使用例
let matrix: Matrix<f64, 3, 4> = Matrix::new();
let transposed: Matrix<f64, 4, 3> = matrix.transpose();
```

### Const genericsの高度な使用

```rust
// 型レベルでの計算
struct TypeLevelArray<T, const N: usize>([T; N]);

impl<T, const N: usize> TypeLevelArray<T, N> {
    const DOUBLE: usize = N * 2;
    
    fn double_size(self, default: T) -> TypeLevelArray<T, {Self::DOUBLE}> 
    where 
        T: Clone 
    {
        let mut vec = self.0.to_vec();
        vec.resize(Self::DOUBLE, default);
        TypeLevelArray(vec.try_into().unwrap())
    }
}

// const式での制約
fn requires_power_of_two<const N: usize>() 
where
    Assert<{N & (N - 1) == 0}>: IsTrue,
{
    // Nは2の累乗でなければならない
}

// const評価を使った型レベルアサーション
struct Assert<const COND: bool>;
trait IsTrue {}
impl IsTrue for Assert<true> {}
```

## 高階型（Higher-Kinded Types）の模倣

### HKTがない中での工夫

```rust
// Functor抽象化の試み
trait HKT {
    type Wrapped<T>;
}

trait Functor: HKT {
    fn map<A, B, F>(wrapped: Self::Wrapped<A>, f: F) -> Self::Wrapped<B>
    where
        F: FnOnce(A) -> B;
}

// Option用の実装
struct OptionF;

impl HKT for OptionF {
    type Wrapped<T> = Option<T>;
}

impl Functor for OptionF {
    fn map<A, B, F>(wrapped: Option<A>, f: F) -> Option<B>
    where
        F: FnOnce(A) -> B
    {
        wrapped.map(f)
    }
}

// モナド変換子の模倣
trait Monad: Functor {
    fn pure<T>(value: T) -> Self::Wrapped<T>;
    fn flat_map<A, B, F>(
        wrapped: Self::Wrapped<A>, 
        f: F
    ) -> Self::Wrapped<B>
    where
        F: FnOnce(A) -> Self::Wrapped<B>;
}
```

## 型レベルプログラミング

### 型レベル自然数

```rust
use std::marker::PhantomData;

// Peano数
struct Zero;
struct Succ<N>(PhantomData<N>);

// 型レベル演算
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

// 型レベルリスト
struct Nil;
struct Cons<H, T>(PhantomData<(H, T)>);

// 型レベルでのリスト操作
trait Length {
    type Len;
}

impl Length for Nil {
    type Len = Zero;
}

impl<H, T> Length for Cons<H, T>
where
    T: Length,
{
    type Len = Succ<T::Len>;
}
```

### 型レベル状態機械

```rust
// 型で表現された状態
struct Locked;
struct Unlocked;
struct Broken;

// 状態遷移を型で保証
struct Safe<State> {
    _state: PhantomData<State>,
}

impl Safe<Locked> {
    fn new() -> Self {
        Safe { _state: PhantomData }
    }
    
    fn unlock(self) -> Safe<Unlocked> {
        Safe { _state: PhantomData }
    }
    
    fn break_lock(self) -> Safe<Broken> {
        Safe { _state: PhantomData }
    }
}

impl Safe<Unlocked> {
    fn lock(self) -> Safe<Locked> {
        Safe { _state: PhantomData }
    }
    
    fn open(&self) -> &'static str {
        "Safe is open!"
    }
}

impl Safe<Broken> {
    fn repair(self) -> Safe<Locked> {
        Safe { _state: PhantomData }
    }
}
```

## 変位（Variance）の詳細

### 共変性、反変性、不変性

```rust
// 共変性（Covariant）: 'a ⊆ 'b ⇒ F<'a> ⊆ F<'b>
struct Covariant<'a> {
    data: &'a str,
}

// 反変性（Contravariant）: 'a ⊆ 'b ⇒ F<'b> ⊆ F<'a>
struct Contravariant<'a> {
    f: fn(&'a str),
}

// 不変性（Invariant）: 部分型関係なし
struct Invariant<'a> {
    data: &'a mut str,
}

// 変位の組み合わせ
struct Complex<'a, T> {
    // &'a T は 'a に対して共変、T に対して共変
    shared: &'a T,
    
    // &'a mut T は 'a に対して共変、T に対して不変
    exclusive: &'a mut T,
    
    // fn(T) は T に対して反変
    consumer: fn(T),
    
    // fn() -> T は T に対して共変
    producer: fn() -> T,
}
```

### PhantomDataによる変位の制御

```rust
use std::marker::PhantomData;

// 共変性を強制
struct ForceCovariant<'a, T> {
    _phantom: PhantomData<&'a T>,
}

// 反変性を強制
struct ForceContravariant<'a, T> {
    _phantom: PhantomData<fn(&'a T)>,
}

// 不変性を強制
struct ForceInvariant<'a, T> {
    _phantom: PhantomData<&'a mut T>,
}
```

## 実験的機能と将来の型システム

### 特殊化（Specialization）

```rust
#![feature(specialization)]

trait Example {
    fn method(&self);
}

// デフォルト実装
impl<T> Example for T {
    default fn method(&self) {
        println!("Default implementation");
    }
}

// 特殊化された実装
impl Example for String {
    fn method(&self) {
        println!("Specialized for String: {}", self);
    }
}
```

### 効果システム（Effect System）の可能性

```rust
// 将来の可能性：効果を型で表現
// #[effect(async, try, const)]
// fn complex_function() -> Result<i32> {
//     let x = async_operation().await?;
//     const_computation(x)
// }

// 現在の回避策：トレイトで効果を模倣
trait Effect {
    type Output<T>;
    
    fn pure<T>(value: T) -> Self::Output<T>;
    fn map<A, B, F>(effect: Self::Output<A>, f: F) -> Self::Output<B>
    where
        F: FnOnce(A) -> B;
}
```

## 型推論の限界と回避策

### 型推論の失敗パターン

```rust
// 推論できないケース
fn inference_failure() {
    let numbers = vec![1, 2, 3];
    let strings = numbers.iter()
        .map(ToString::to_string)
        .collect();  // エラー：収集先の型が不明
    
    // 解決策1：型注釈
    let strings: Vec<String> = numbers.iter()
        .map(ToString::to_string)
        .collect();
    
    // 解決策2：ターボフィッシュ構文
    let strings = numbers.iter()
        .map(ToString::to_string)
        .collect::<Vec<_>>();
}

// 高階型推論の限界
fn higher_order_inference<F, G>(f: F, g: G)
where
    F: Fn(i32) -> i32,
    G: Fn(i32) -> i32,
{
    // コンパイラは f と g の関係を推論できない
}
```

## 実践的な型設計パターン

### 型駆動開発

```rust
// 不正な状態を表現不可能にする
enum EmailState {
    Unverified(String),
    Verified(String),
}

struct User {
    id: u64,
    email: EmailState,
}

impl User {
    fn new(id: u64, email: String) -> Self {
        User {
            id,
            email: EmailState::Unverified(email),
        }
    }
    
    fn verify_email(mut self) -> Result<Self, &'static str> {
        match self.email {
            EmailState::Unverified(email) => {
                // 検証ロジック
                self.email = EmailState::Verified(email);
                Ok(self)
            }
            EmailState::Verified(_) => {
                Err("Email already verified")
            }
        }
    }
    
    fn send_notification(&self) -> Result<(), &'static str> {
        match &self.email {
            EmailState::Verified(email) => {
                println!("Sending to {}", email);
                Ok(())
            }
            EmailState::Unverified(_) => {
                Err("Cannot send to unverified email")
            }
        }
    }
}
```

## まとめ

Rustの高度な型システム機能は、以下の利点を提供します：

1. **コンパイル時保証**: 多くのバグを実行前に防ぐ
2. **表現力**: 複雑な不変条件を型で表現
3. **抽象化**: 高レベルの抽象化を実現
4. **拡張性**: 将来の機能拡張への道筋

これらの機能を適切に活用することで、より安全で保守性の高いコードを書くことができます。

次章では、これらの型システムの知識を活かした、Unsafe Rustとシステムプログラミングについて探求します。

## 公式ドキュメント参照

- **Reference**: Chapter 8.5 - Associated Items
- **RFC 1598**: Generic Associated Types
- **RFC 2000**: Const generics
- **RFC 1210**: Specialization