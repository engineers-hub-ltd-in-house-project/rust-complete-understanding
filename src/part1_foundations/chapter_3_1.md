# アフィン型理論と借用

## はじめに

前章で学んだ借用システムは、実はアフィン型理論の巧妙な応用です。所有権がアフィン型（最大1回使用）であるのに対し、借用は「短期間の読み取り専用アクセス」または「短期間の排他的アクセス」を提供します。本節では、この借用メカニズムがどのようにアフィン型理論から導かれるか、その数学的基礎を探求します。

## アフィン型理論の復習

### 基本概念

アフィン型システムでは、値は**最大1回**使用できます：

```
構造規則:
- 弱化（Weakening）: OK - 値を使わないことは許される
- 縮約（Contraction）: NG - 値を複製することは許されない
```

### 型理論的表現

```
Γ ⊢ e : τ
───────── (Affine-Use)
Γ \ {x:τ} ⊢ e'

ここで、Γ \ {x:τ} は環境Γからx:τを除去
```

## 借用の型理論的基礎

### 借用型の導入

Rustの借用は、型理論的には以下のように表現できます：

```
τ ::= T           // 所有型
    | &τ          // 共有参照（不変借用）
    | &mut τ      // 排他参照（可変借用）
```

### 借用の生成規則

```
Γ ⊢ e : τ
─────────── (&-intro)
Γ ⊢ &e : &τ

Γ ⊢ e : τ
──────────────── (&mut-intro)
Γ ⊢ &mut e : &mut τ
```

## 借用とアフィン性の調和

### 問題：アフィン型では値の共有ができない

純粋なアフィン型システムでは、値を複数回使用できません：

```rust
// 純粋なアフィン型では不可能
let x = String::from("hello");
print_string(x);      // xの所有権が移動
print_string(x);      // エラー：xは既に使用済み
```

### 解決：借用による短期間アクセス権

借用は、所有権を移動せずに値へのアクセスを提供します：

```rust
let x = String::from("hello");
print_string(&x);     // xを借用
print_string(&x);     // 再度借用可能
// xの所有権は維持される
```

## 借用の数学的モデル

### 能力（Capability）ベースの形式化

借用は「能力」として形式化できます：

```
能力の種類:
- own(τ): τの所有権
- &shared(τ): τへの共有アクセス権
- &unique(τ): τへの排他アクセス権
```

### 分割可能性（Fractional Permissions）

共有借用は「分数的許可」として理解できます：

```
own(τ) = 1         // 完全な所有権
&shared(τ) = 1/n   // n個に分割可能な読み取り権
&unique(τ) = 1     // 分割不可能な書き込み権
```

実装例：

```rust
// 所有権の分割と再結合のデモ
fn demonstrate_fractional_permissions() {
    let mut data = vec![1, 2, 3];  // own(Vec<i32>) = 1
    
    {
        let r1 = &data;  // &shared = 1/2
        let r2 = &data;  // &shared = 1/2
        // 合計: 1/2 + 1/2 = 1（ただし読み取りのみ）
        println!("{:?} {:?}", r1, r2);
    }  // 借用終了、所有権が戻る
    
    data.push(4);  // own = 1 が復活
}
```

## 借用チェッカーの理論

### 領域（Region）ベースの型システム

借用チェッカーは、各借用に「領域」を割り当てます：

```
型の拡張:
τ ::= T | &'r τ | &'r mut τ

ここで 'r は領域（ライフタイム）
```

### 領域の包含関係

```
'a ⊆ 'b は「領域'aは領域'bに含まれる」を意味

推論規則:
Γ ⊢ e : &'a τ    'a ⊆ 'b
────────────────────────── (Sub-Region)
Γ ⊢ e : &'b τ
```

## 借用の実装メカニズム

### コンパイル時の借用追跡

```rust
// 借用チェッカーの内部動作を示す擬似コード
struct BorrowChecker {
    // 各変数の借用状態
    borrows: HashMap<Variable, BorrowState>,
}

enum BorrowState {
    NotBorrowed,
    SharedBorrow(Vec<Region>),  // 複数の共有借用
    UniqueBorrow(Region),       // 単一の排他借用
}

impl BorrowChecker {
    fn check_borrow(&mut self, var: Variable, kind: BorrowKind, region: Region) -> Result<(), Error> {
        match (self.borrows.get(&var), kind) {
            (Some(SharedBorrow(regions)), BorrowKind::Shared) => {
                // 共有借用の追加はOK
                regions.push(region);
                Ok(())
            }
            (Some(NotBorrowed), _) => {
                // 新規借用はOK
                self.borrows.insert(var, kind.to_state(region));
                Ok(())
            }
            _ => Err(Error::ConflictingBorrow),
        }
    }
}
```

### 実際の借用チェックの例

```rust
fn borrow_checking_example() {
    let mut x = 5;
    
    // フェーズ1: 共有借用
    let r1 = &x;        // 借用開始: SharedBorrow(['a])
    let r2 = &x;        // OK: SharedBorrow(['a, 'b])
    println!("{} {}", r1, r2);
    // r1, r2のスコープ終了 → NotBorrowed
    
    // フェーズ2: 排他借用
    let r3 = &mut x;    // OK: UniqueBorrow(['c])
    *r3 += 1;
    // r3のスコープ終了 → NotBorrowed
    
    // フェーズ3: 再び使用可能
    println!("{}", x);
}
```

## 高度な借用パターン

### リバース借用（Reborrowing）

```rust
fn reborrowing_demo() {
    let mut x = vec![1, 2, 3];
    let r1 = &mut x;
    
    // リバース借用：r1から新しい借用を作成
    let r2 = &mut *r1;
    r2.push(4);
    
    // r2のスコープ終了後、r1が再び使用可能
    r1.push(5);
}
```

### 分割借用（Split Borrowing）

```rust
struct Pair {
    first: String,
    second: String,
}

fn split_borrow_demo() {
    let mut pair = Pair {
        first: String::from("hello"),
        second: String::from("world"),
    };
    
    // 異なるフィールドの同時借用
    let r1 = &mut pair.first;
    let r2 = &pair.second;  // OK: 異なるフィールド
    
    r1.push_str(" rust");
    println!("{}", r2);
}
```

## 理論と実装の橋渡し

### コンパイラの改良

借用チェッカーは、理論的な正しさを保ちながら実用性を追求：

```rust
// Non-Lexical Lifetimes (NLL) の効果
fn nll_improvement() {
    let mut vec = vec![1, 2, 3];
    
    let r = &vec[0];
    println!("{}", r);  // rの最後の使用
    
    // NLL以前: ここでエラー
    // NLL以降: rのライフタイムが終了しているのでOK
    vec.push(4);
}
```

### Two-Phase Borrowing

```rust
fn two_phase_borrowing() {
    let mut vec = vec![1, 2, 3];
    
    // フェーズ1: 予約（まだ排他的アクセスしない）
    // フェーズ2: 活性化（実際に使用）
    vec.push(vec.len());  // vec.len()は共有借用、pushは可変借用
}
```

## 借用とスレッド安全性

### Send と Sync トレイト

```rust
// Sendトレイト: 所有権の転送が安全
// Syncトレイト: 共有参照(&T)の共有が安全

use std::thread;
use std::sync::Arc;

fn thread_safety_demo() {
    let data = Arc::new(vec![1, 2, 3]);
    let data_clone = Arc::clone(&data);
    
    thread::spawn(move || {
        // Arcは共有参照を安全に共有
        println!("{:?}", data_clone);
    });
    
    println!("{:?}", data);
}
```

## 形式的検証

### 借用チェッカーの健全性

借用チェッカーは以下を保証：

1. **メモリ安全性**: ダングリング参照なし
2. **データ競合なし**: 可変参照の排他性
3. **型安全性**: 借用を通じた型の保持

形式的には：

```
定理（借用の健全性）:
プログラムPが借用チェッカーを通過するならば、
Pの実行中に以下が成立：
1. すべての参照は有効なメモリを指す
2. 可変参照を通じたアクセスは排他的
3. 型の不変条件が保持される
```

## まとめ

借用システムは、アフィン型理論を実用的に拡張したものです：

1. **理論的基礎**: アフィン型に「短期間アクセス」の概念を追加
2. **実装**: コンパイル時の静的解析による安全性保証
3. **実用性**: 分割借用、リバース借用などの高度なパターン

この巧妙な設計により、Rustは「所有権による安全性」と「借用による柔軟性」を両立させています。

次節では、借用と密接に関連する「ライフタイム」の理論的基礎について詳しく見ていきます。

## 公式ドキュメント参照

- **Reference**: Section 10.3 - Reference types
- **Rustonomicon**: Chapter 3.4 - Splitting Borrows
- **RFC 2094**: Non-lexical lifetimes
- **RFC 2025**: Two-phase borrows