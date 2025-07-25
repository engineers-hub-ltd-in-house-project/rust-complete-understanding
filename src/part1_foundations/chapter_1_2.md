# Rustが解決しようとした問題

## はじめに

プログラミング言語の歴史は、常に「安全性」と「性能」のトレードオフとの戦いでした。Rustは2006年、Mozilla研究員のGraydon Hoareによって、このトレードオフを打破する野心的な目標を持って誕生しました。本節では、Rustが解決しようとした具体的な問題と、その背景にある歴史的経緯を探ります。

## システムプログラミングの歴史的課題

### 1960年代〜1970年代：アセンブリ言語からCへ

システムプログラミングは、当初アセンブリ言語で行われていました：

```assembly
; x86アセンブリの例
mov eax, 1
mov ebx, 42
int 0x80
```

**問題点**：
- ハードウェア依存性が高い
- 可読性が低い
- 保守が困難
- バグが混入しやすい

C言語（1972年）の登場により、ポータビリティと抽象化が実現されましたが、新たな問題も生まれました。

### 1980年代〜1990年代：C++の挑戦

C++（1985年）は、オブジェクト指向とゼロコスト抽象化を目指しました：

```cpp
// RAIIパターン
class FileHandle {
    FILE* file;
public:
    FileHandle(const char* name) : file(fopen(name, "r")) {}
    ~FileHandle() { if (file) fclose(file); }
};
```

**進歩**：
- RAII（Resource Acquisition Is Initialization）
- テンプレートによる汎用プログラミング
- 例外処理

**残された問題**：
- 複雑な言語仕様
- 未定義動作の多さ
- メモリ安全性の保証なし

### 2000年代：管理言語の台頭

Java（1995年）、C#（2000年）などの管理言語が登場：

```java
// Javaのガベージコレクション
public class Example {
    public static void main(String[] args) {
        List<String> list = new ArrayList<>();
        // メモリ管理は自動
    }
}
```

**利点**：
- 自動メモリ管理
- メモリ安全性
- 開発生産性の向上

**新たな問題**：
- GCによる予測不可能な一時停止
- ランタイムオーバーヘッド
- システムプログラミングには不適

## Mozillaが直面した現実的な問題

### Firefoxの開発における課題

Mozillaは、数千万行のC++コードベースを持つFirefoxの開発で、深刻な問題に直面していました：

1. **セキュリティ脆弱性の70%以上がメモリ安全性に起因**
   - バッファオーバーフロー
   - use-after-free
   - データ競合

2. **並行処理の困難さ**
   - マルチコアCPUの活用が困難
   - スレッド間のデータ共有が危険

3. **大規模リファクタリングの恐怖**
   - 型システムが弱く、変更の影響範囲が不明
   - 実行時まで多くのバグが発見されない

### Servo プロジェクトの野望

MozillaはServoという新しいWebレンダリングエンジンの開発を開始し、以下の目標を掲げました：

- **並列処理を前提とした設計**
- **メモリ安全性の保証**
- **C++並みのパフォーマンス**

これらの要求を満たす既存の言語は存在しませんでした。

## Rustが解決を目指した具体的な問題

### 1. メモリ安全性の問題

**従来の問題**：
```c
// Cでの典型的なバグ
char* get_string() {
    char buffer[100];
    strcpy(buffer, "Hello");
    return buffer; // スタック上のデータを返す！
}

void use_after_free() {
    int* ptr = malloc(sizeof(int));
    free(ptr);
    *ptr = 42; // 解放済みメモリへのアクセス！
}
```

**Rustの解決策**：
```rust
// コンパイルエラーになる
fn get_string() -> &str {
    let buffer = "Hello";
    &buffer // ライフタイムエラー
}

// 所有権システムにより防止
fn no_use_after_free() {
    let ptr = Box::new(42);
    drop(ptr);
    // *ptr; // コンパイルエラー：moveされた値の使用
}
```

### 2. データ競合の問題

**従来の問題**：
```cpp
// C++での危険な並行処理
std::vector<int> data;
std::thread t1([&]() { data.push_back(1); });
std::thread t2([&]() { data.push_back(2); });
// データ競合！
```

**Rustの解決策**：
```rust
// Rustではコンパイルエラー
let mut data = vec![];
let t1 = thread::spawn(|| {
    data.push(1); // エラー：mutableな参照を複数作れない
});
```

### 3. ヌルポインタの問題

**従来の問題**：
```java
// Javaでの悪名高いNullPointerException
String str = null;
str.length(); // 実行時エラー！
```

**Rustの解決策**：
```rust
// Optionによる明示的なnull可能性
let str: Option<String> = None;
match str {
    Some(s) => println!("Length: {}", s.len()),
    None => println!("No string"),
}
```

### 4. エラー処理の問題

**従来の問題**：
```c
// Cでのエラー処理
FILE* file = fopen("data.txt", "r");
if (file == NULL) {
    // エラー処理を忘れやすい
}
```

**Rustの解決策**：
```rust
// Result型による強制的なエラー処理
let file = File::open("data.txt");
match file {
    Ok(f) => { /* ファイルを使用 */ },
    Err(e) => { /* エラー処理 */ },
}
```

## Rustの設計哲学

### ゼロコスト抽象化

「使わない機能にはコストを払わない」というC++の哲学を継承：

```rust
// イテレータはコンパイル後、手書きループと同等の性能
let sum: i32 = vec![1, 2, 3, 4, 5]
    .iter()
    .filter(|&&x| x % 2 == 0)
    .sum();
```

### 型による保証

実行時チェックではなく、コンパイル時の型チェックで安全性を保証：

```rust
// Send/Syncトレイトによるスレッド安全性の保証
fn send_between_threads<T: Send>(data: T) {
    thread::spawn(move || {
        // Tが Sendを実装している場合のみコンパイル可能
    });
}
```

### 人間工学的設計

開発者の生産性も重視：

```rust
// 型推論により冗長な記述を削減
let vec = vec![1, 2, 3]; // Vec<i32>と推論される
let doubled: Vec<_> = vec.iter().map(|x| x * 2).collect();
```

## 産業界への影響

Rustの登場は、システムプログラミング業界に大きな影響を与えました：

### 採用企業の増加

- **Microsoft**: Windows の一部をRustで書き換え
- **Google**: Android OSへのRust導入
- **Amazon**: クリティカルなインフラストラクチャでの採用
- **Discord**: 高性能なバックエンドシステムの構築

### 新しいプロジェクトの誕生

- **Deno**: Node.jsの作者によるJavaScriptランタイム
- **Firecracker**: AWSのマイクロVM
- **TiKV**: 分散型Key-Valueストア

## まとめ

Rustは、50年にわたるシステムプログラミングの歴史から学び、現代のハードウェアとソフトウェア要求に応える言語として設計されました。メモリ安全性、並行性、パフォーマンスという、従来は相反すると考えられていた要素を、所有権システムという革新的なアプローチで統合しました。

次章では、この所有権システムがどのような理論的基礎に基づいているか、そしてどのように実装されているかを詳しく見ていきます。

## 公式ドキュメント参照

- **The Book**: Foreword, Introduction
- **Reference**: Section 1 - Introduction
- **RFC 1**: Rust Design Philosophy