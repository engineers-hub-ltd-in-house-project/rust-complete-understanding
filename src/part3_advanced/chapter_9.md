# マクロとメタプログラミング

## はじめに

メタプログラミングは、プログラムを生成・操作するプログラムを書く技術です。Rustは、強力なマクロシステムを通じてコンパイル時のコード生成を可能にし、ボイラープレートの削減、DSL（ドメイン固有言語）の作成、パフォーマンスの向上を実現します。本章では、Rustのマクロシステムの理論的基礎から実践的な使用方法まで、包括的に探求します。

## メタプログラミングの理論的基礎

### 準引用（Quasiquotation）

LISPから始まったメタプログラミングの概念：

```rust
// 概念的な例（Rustの実際の構文ではない）
// LISPスタイル：
// `(+ 1 2)        ; 式
// '(+ 1 2)        ; 引用（データとしての式）
// `(+ 1 ,x)       ; 準引用（部分的な評価）

// Rustでの対応：
// 1 + 2           // 式
// quote! { 1 + 2 } // 引用（TokenStreamとして）
// quote! { 1 + #x } // 準引用（変数の展開）
```

### 衛生的マクロ（Hygienic Macros）

名前の衝突を防ぐマクロシステム：

```rust
// 非衛生的マクロの問題（仮想的な例）
macro_rules! bad_swap {
    ($a:expr, $b:expr) => {
        let temp = $a;  // tempが外部と衝突する可能性
        $a = $b;
        $b = temp;
    }
}

// Rustの衛生的マクロ
macro_rules! swap {
    ($a:expr, $b:expr) => {
        {
            let temp = $a;  // tempは新しいスコープで隔離
            $a = $b;
            $b = temp;
        }
    }
}

fn hygiene_example() {
    let mut x = 1;
    let mut y = 2;
    let temp = 99;  // 外部のtemp
    
    swap!(x, y);    // マクロ内のtempと衝突しない
    assert_eq!(x, 2);
    assert_eq!(y, 1);
    assert_eq!(temp, 99);  // 変更されない
}
```

## 宣言的マクロ（macro_rules!）

### 基本的なパターンマッチング

```rust
// 単純なマクロ
macro_rules! say_hello {
    () => {
        println!("Hello, world!");
    };
}

// パターンマッチングを使ったマクロ
macro_rules! create_function {
    ($func_name:ident) => {
        fn $func_name() {
            println!("Function {} was called", stringify!($func_name));
        }
    };
}

create_function!(foo);
create_function!(bar);

// 複数のパターン
macro_rules! test_macro {
    // パターン1：引数なし
    () => {
        println!("No arguments");
    };
    
    // パターン2：1つの式
    ($e:expr) => {
        println!("One expression: {}", $e);
    };
    
    // パターン3：複数の式
    ($($e:expr),+) => {
        $(
            println!("Expression: {}", $e);
        )+
    };
}
```

### マクロの引数の種類

```rust
macro_rules! demonstrate_designators {
    // item: 関数、構造体、モジュールなど
    ($i:item) => { $i };
    
    // block: ブロック式
    ($b:block) => { $b };
    
    // stmt: 文
    ($s:stmt) => { $s };
    
    // pat: パターン
    ($p:pat) => { 
        match Some(42) {
            $p => println!("Matched!"),
            _ => println!("Not matched"),
        }
    };
    
    // expr: 式
    ($e:expr) => { $e };
    
    // ty: 型
    ($t:ty) => {
        let _: $t = Default::default();
    };
    
    // ident: 識別子
    ($id:ident) => {
        let $id = 42;
    };
    
    // path: パス
    ($p:path) => {
        use $p;
    };
    
    // tt: トークンツリー
    ($t:tt) => { $t };
    
    // meta: メタアイテム（属性内容）
    (#[$m:meta]) => {
        #[$m]
        struct Attributed;
    };
    
    // lifetime: ライフタイム
    ($lt:lifetime) => {
        struct Ref<$lt> { r: &$lt i32 }
    };
}
```

### 再帰的マクロ

```rust
// ベクトルマクロの簡略版実装
macro_rules! vec_simple {
    // ベースケース：引数なし
    () => {
        ::std::vec::Vec::new()
    };
    
    // 再帰ケース：要素を追加
    ($elem:expr; $n:expr) => {
        ::std::vec::from_elem($elem, $n)
    };
    
    // 可変長引数
    ($($x:expr),+ $(,)?) => {
        {
            let mut temp_vec = ::std::vec::Vec::new();
            $(
                temp_vec.push($x);
            )+
            temp_vec
        }
    };
}

// 複雑な再帰マクロ：カウント機能付き
macro_rules! count_exprs {
    () => (0usize);
    ($head:expr) => (1usize);
    ($head:expr, $($tail:expr),*) => (1usize + count_exprs!($($tail),*));
}

fn recursive_macro_example() {
    let v1 = vec_simple![1, 2, 3];
    let v2 = vec_simple![0; 10];
    
    let count = count_exprs!(a, b, c, d);
    assert_eq!(count, 4);
}
```

### 内部ルールとマクロの構造化

```rust
macro_rules! implement_arithmetic {
    // 公開インターフェース
    ($type:ty) => {
        implement_arithmetic!(@impl $type);
    };
    
    // 内部実装（@プレフィックスは慣例）
    (@impl $type:ty) => {
        impl $type {
            implement_arithmetic!(@method add);
            implement_arithmetic!(@method sub);
            implement_arithmetic!(@method mul);
        }
    };
    
    // メソッド生成
    (@method add) => {
        pub fn add(self, other: Self) -> Self {
            Self(self.0 + other.0)
        }
    };
    
    (@method sub) => {
        pub fn sub(self, other: Self) -> Self {
            Self(self.0 - other.0)
        }
    };
    
    (@method mul) => {
        pub fn mul(self, other: Self) -> Self {
            Self(self.0 * other.0)
        }
    };
}

// 使用例
struct Wrapper(i32);
implement_arithmetic!(Wrapper);
```

## 手続き的マクロ（Procedural Macros）

### derive マクロ

```rust
use proc_macro::TokenStream;
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

// Cargo.toml:
// [lib]
// proc-macro = true
//
// [dependencies]
// syn = "1.0"
// quote = "1.0"
// proc-macro2 = "1.0"

#[proc_macro_derive(MyDebug)]
pub fn my_debug_derive(input: TokenStream) -> TokenStream {
    // 入力をパース
    let input = parse_macro_input!(input as DeriveInput);
    
    // 型名を取得
    let name = &input.ident;
    
    // ジェネリクスを処理
    let generics = &input.generics;
    let (impl_generics, ty_generics, where_clause) = generics.split_for_impl();
    
    // 実装を生成
    let expanded = quote! {
        impl #impl_generics std::fmt::Debug for #name #ty_generics #where_clause {
            fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
                write!(f, "MyDebug instance of {}", stringify!(#name))
            }
        }
    };
    
    TokenStream::from(expanded)
}

// 使用例
#[derive(MyDebug)]
struct Point {
    x: i32,
    y: i32,
}
```

### 属性マクロ

```rust
#[proc_macro_attribute]
pub fn route(args: TokenStream, input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as syn::ItemFn);
    let args = parse_macro_input!(args as syn::AttributeArgs);
    
    // HTTPメソッドとパスを解析
    let method = // ... 解析ロジック
    let path = // ... 解析ロジック
    
    let fn_name = &input.sig.ident;
    let fn_block = &input.block;
    
    let expanded = quote! {
        fn #fn_name() {
            // ルート登録コード
            ROUTER.register(#method, #path, || {
                #fn_block
            });
        }
    };
    
    TokenStream::from(expanded)
}

// 使用例
#[route(GET, "/users")]
fn get_users() {
    // ハンドラーの実装
}
```

### 関数風マクロ

```rust
#[proc_macro]
pub fn sql(input: TokenStream) -> TokenStream {
    let input_str = input.to_string();
    
    // SQL文法の検証
    validate_sql(&input_str);
    
    // SQLを構造体に変換
    let query = parse_sql(&input_str);
    
    let expanded = quote! {
        Query::new(#input_str)
            .validate()
            .prepare()
    };
    
    TokenStream::from(expanded)
}

// 使用例
fn database_example() {
    let query = sql!(SELECT * FROM users WHERE age > 18);
    let results = query.execute();
}
```

## 高度なマクロテクニック

### トークン操作とAST変換

```rust
use syn::{parse_quote, Expr, Stmt};
use quote::quote;

// AST変換の例
fn transform_expression(expr: Expr) -> Expr {
    match expr {
        Expr::Binary(mut bin_expr) => {
            // 二項演算を変換
            bin_expr.left = Box::new(transform_expression(*bin_expr.left));
            bin_expr.right = Box::new(transform_expression(*bin_expr.right));
            Expr::Binary(bin_expr)
        }
        Expr::Call(mut call_expr) => {
            // 関数呼び出しにログを追加
            let func = &call_expr.func;
            parse_quote! {
                {
                    println!("Calling function");
                    #call_expr
                }
            }
        }
        _ => expr,
    }
}

// ビジターパターンの実装
struct MyVisitor;

impl syn::visit_mut::VisitMut for MyVisitor {
    fn visit_expr_mut(&mut self, expr: &mut Expr) {
        // 式を訪問して変換
        match expr {
            Expr::Lit(lit) => {
                // リテラルを変換
            }
            _ => {
                // 再帰的に訪問
                syn::visit_mut::visit_expr_mut(self, expr);
            }
        }
    }
}
```

### コード生成の実践例

```rust
// ビルダーパターンの自動生成
#[proc_macro_derive(Builder)]
pub fn builder_derive(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);
    let name = &input.ident;
    let builder_name = quote::format_ident!("{}Builder", name);
    
    let fields = match &input.data {
        syn::Data::Struct(data) => &data.fields,
        _ => panic!("Builder can only be derived for structs"),
    };
    
    let field_names: Vec<_> = fields.iter()
        .filter_map(|f| f.ident.as_ref())
        .collect();
    
    let field_types: Vec<_> = fields.iter()
        .map(|f| &f.ty)
        .collect();
    
    let builder_fields = field_names.iter()
        .zip(field_types.iter())
        .map(|(name, ty)| {
            quote! { #name: Option<#ty> }
        });
    
    let builder_methods = field_names.iter()
        .zip(field_types.iter())
        .map(|(name, ty)| {
            quote! {
                pub fn #name(mut self, value: #ty) -> Self {
                    self.#name = Some(value);
                    self
                }
            }
        });
    
    let build_fields = field_names.iter()
        .map(|name| {
            quote! {
                #name: self.#name.ok_or(concat!(stringify!(#name), " is not set"))?
            }
        });
    
    let expanded = quote! {
        pub struct #builder_name {
            #(#builder_fields,)*
        }
        
        impl #builder_name {
            pub fn new() -> Self {
                Self {
                    #(#field_names: None,)*
                }
            }
            
            #(#builder_methods)*
            
            pub fn build(self) -> Result<#name, &'static str> {
                Ok(#name {
                    #(#build_fields,)*
                })
            }
        }
        
        impl #name {
            pub fn builder() -> #builder_name {
                #builder_name::new()
            }
        }
    };
    
    TokenStream::from(expanded)
}
```

### マクロのデバッグとテスト

```rust
// cargo-expand を使用したマクロ展開の確認
// $ cargo install cargo-expand
// $ cargo expand

// マクロのテスト
#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_macro_expansion() {
        // マクロの出力を文字列として検証
        let expanded = quote! {
            test_macro!(42)
        };
        
        let expected = quote! {
            println!("Value: {}", 42);
        };
        
        assert_eq!(expanded.to_string(), expected.to_string());
    }
    
    // コンパイルテスト
    #[test]
    fn ui_test() {
        let t = trybuild::TestCases::new();
        t.pass("tests/01-parse-struct.rs");
        t.compile_fail("tests/02-parse-enum.rs");
    }
}

// デバッグ用マクロ
macro_rules! dbg_macro {
    ($val:expr) => {
        match $val {
            tmp => {
                eprintln!("[{}:{}:{}] {} = {:#?}",
                    file!(), line!(), column!(), 
                    stringify!($val), &tmp);
                tmp
            }
        }
    };
}
```

## DSL（ドメイン固有言語）の作成

### 内部DSLの設計

```rust
// HTMLテンプレートDSL
macro_rules! html {
    // 要素の開始
    ($tag:ident { $($inner:tt)* }) => {
        {
            let mut element = Element::new(stringify!($tag));
            html!(@element element, $($inner)*);
            element
        }
    };
    
    // 属性の処理
    (@element $el:ident, $attr:ident = $value:expr, $($rest:tt)*) => {
        $el.set_attribute(stringify!($attr), $value);
        html!(@element $el, $($rest)*);
    };
    
    // 子要素の処理
    (@element $el:ident, $child:ident { $($inner:tt)* }, $($rest:tt)*) => {
        $el.add_child(html!($child { $($inner)* }));
        html!(@element $el, $($rest)*);
    };
    
    // テキストコンテンツ
    (@element $el:ident, $text:expr, $($rest:tt)*) => {
        $el.add_text($text);
        html!(@element $el, $($rest)*);
    };
    
    // 終了条件
    (@element $el:ident,) => {};
}

// 使用例
fn html_dsl_example() {
    let page = html! {
        div {
            class = "container",
            h1 { "Welcome" },
            p {
                "This is a ",
                strong { "DSL" },
                " example"
            }
        }
    };
}

// 状態機械DSL
macro_rules! state_machine {
    (
        $name:ident {
            states: [$($state:ident),*],
            transitions: [
                $($from:ident -> $to:ident on $event:ident),*
            ],
            initial: $initial:ident
        }
    ) => {
        mod $name {
            #[derive(Debug, Clone, Copy, PartialEq)]
            pub enum State {
                $($state,)*
            }
            
            #[derive(Debug, Clone, Copy)]
            pub enum Event {
                $($event,)*
            }
            
            pub struct StateMachine {
                state: State,
            }
            
            impl StateMachine {
                pub fn new() -> Self {
                    Self { state: State::$initial }
                }
                
                pub fn transition(&mut self, event: Event) {
                    self.state = match (self.state, event) {
                        $(
                            (State::$from, Event::$event) => State::$to,
                        )*
                        _ => self.state,
                    };
                }
            }
        }
    };
}

// 使用例
state_machine! {
    tcp_connection {
        states: [Closed, Listen, SynReceived, Established],
        transitions: [
            Closed -> Listen on Open,
            Listen -> SynReceived on SynReceived,
            SynReceived -> Established on AckReceived
        ],
        initial: Closed
    }
}
```

## コンパイル時計算とconst評価

### const関数とコンパイル時評価

```rust
// const関数による計算
const fn fibonacci(n: u32) -> u32 {
    match n {
        0 => 0,
        1 => 1,
        _ => fibonacci(n - 1) + fibonacci(n - 2),
    }
}

const FIB_10: u32 = fibonacci(10);

// コンパイル時の型レベル計算
trait TypeLevel {
    type Output;
}

struct Zero;
struct Succ<N>(std::marker::PhantomData<N>);

// マクロでの型レベル計算
macro_rules! type_level_add {
    ($a:ty, Zero) => { $a };
    ($a:ty, Succ<$b:ty>) => { Succ<type_level_add!($a, $b)> };
}

// コンパイル時アサーション
macro_rules! const_assert {
    ($cond:expr) => {
        const _: () = assert!($cond);
    };
}

const_assert!(std::mem::size_of::<u32>() == 4);
```

### Build.rsとコード生成

```rust
// build.rs
use std::env;
use std::fs::File;
use std::io::Write;
use std::path::Path;

fn main() {
    let out_dir = env::var("OUT_DIR").unwrap();
    let dest_path = Path::new(&out_dir).join("generated.rs");
    let mut f = File::create(&dest_path).unwrap();
    
    // 環境に基づいてコードを生成
    writeln!(f, "pub const VERSION: &str = {:?};", 
             env::var("CARGO_PKG_VERSION").unwrap()).unwrap();
    
    // 大規模な定数テーブルの生成
    writeln!(f, "pub const LOOKUP_TABLE: &[u32] = &[").unwrap();
    for i in 0..1000 {
        writeln!(f, "    {},", i * i).unwrap();
    }
    writeln!(f, "];").unwrap();
}

// src/main.rs
include!(concat!(env!("OUT_DIR"), "/generated.rs"));

fn use_generated() {
    println!("Version: {}", VERSION);
    println!("Square of 42: {}", LOOKUP_TABLE[42]);
}
```

## マクロのパフォーマンスと向上

### コンパイル時の向上

```rust
// インライン展開による向上
macro_rules! unroll_loop {
    ($n:expr, $body:expr) => {
        unroll_loop!(@unroll $n, $body,)
    };
    
    (@unroll 0, $body:expr, $($code:tt)*) => {
        $($code)*
    };
    
    (@unroll $n:expr, $body:expr, $($code:tt)*) => {
        unroll_loop!(@unroll $n - 1, $body, $($code)* $body)
    };
}

// 使用例：ループアンローリング
fn optimized_sum(arr: &[i32; 8]) -> i32 {
    let mut sum = 0;
    unroll_loop!(8, sum += arr[i]; i += 1);
    sum
}

// SIMD操作の生成
macro_rules! simd_op {
    ($op:tt, $a:expr, $b:expr) => {
        unsafe {
            use std::arch::x86_64::*;
            let a_vec = _mm256_loadu_ps($a.as_ptr());
            let b_vec = _mm256_loadu_ps($b.as_ptr());
            let result = concat_idents!(_mm256_, $op, _ps)(a_vec, b_vec);
            let mut output = [0.0; 8];
            _mm256_storeu_ps(output.as_mut_ptr(), result);
            output
        }
    };
}
```

## まとめ

Rustのマクロシステムは、以下の特徴を持ちます：

1. **衛生的**: 名前の衝突を防ぐ安全な展開
2. **強力**: 宣言的・手続き的の両方のアプローチ
3. **型安全**: コンパイル時の型チェック
4. **拡張可能**: カスタムDSLの作成が可能
5. **向上**: ゼロコスト抽象化の実現

マクロは強力なツールですが、適切に使用することが重要です。コードの可読性とメンテナンス性を考慮し、より単純な解決策がない場合にのみ使用することが望ましいです。

## 公式ドキュメント参照

- **The Book**: Chapter 19.5 - Macros
- **Reference**: Chapter 3 - Macros
- **The Little Book of Rust Macros**: 詳細なマクロガイド
- **Procedural Macros Workshop**: 実践的なチュートリアル