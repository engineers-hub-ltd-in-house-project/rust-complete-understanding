# 他言語との比較

## はじめに

Rustの所有権システムは、プログラミング言語史において独特な位置を占めています。本節では、主要なプログラミング言語のメモリ管理手法を体系的に比較し、Rustのアプローチがどのように異なり、なぜ革新的なのかを探求します。

## メモリ管理手法の分類

プログラミング言語のメモリ管理は、大きく以下のカテゴリに分類できます：

1. **手動メモリ管理**: C、C++（スマートポインタ以前）
2. **ガベージコレクション**: Java、Go、Python、JavaScript
3. **参照カウント**: Swift、Python（一部）、Objective-C（ARC）
4. **所有権ベース**: Rust
5. **ハイブリッド**: C++（スマートポインタ）、Swift（一部）

## 各言語の詳細比較

### C言語：完全手動管理

```c
// Cのメモリ管理
#include <stdlib.h>
#include <string.h>

typedef struct {
    char* data;
    size_t size;
} Buffer;

Buffer* create_buffer(size_t size) {
    Buffer* buf = malloc(sizeof(Buffer));
    if (buf) {
        buf->data = malloc(size);
        buf->size = size;
    }
    return buf;
}

void destroy_buffer(Buffer* buf) {
    if (buf) {
        free(buf->data);
        free(buf);
    }
}

// 使用例
int main() {
    Buffer* buf = create_buffer(1024);
    // 使用...
    destroy_buffer(buf);  // 手動で解放
    // buf->data;  // use-after-free（実行時エラー）
    return 0;
}
```

**特徴**：
- 完全な制御が可能
- メモリリークやuse-after-freeのリスク
- プログラマの責任が大きい

### C++：RAIIとスマートポインタ

```cpp
// C++の進化的アプローチ
#include <memory>
#include <vector>

// RAII（C++98から）
class Buffer {
private:
    std::vector<char> data;
public:
    explicit Buffer(size_t size) : data(size) {}
    // デストラクタで自動解放
};

// スマートポインタ（C++11から）
void modern_cpp() {
    // unique_ptr: 単一所有権
    std::unique_ptr<Buffer> buf1 = std::make_unique<Buffer>(1024);
    // std::unique_ptr<Buffer> buf2 = buf1;  // エラー：コピー不可
    std::unique_ptr<Buffer> buf2 = std::move(buf1);  // 移動はOK
    
    // shared_ptr: 共有所有権
    std::shared_ptr<Buffer> shared1 = std::make_shared<Buffer>(512);
    std::shared_ptr<Buffer> shared2 = shared1;  // 参照カウント増加
}
```

**特徴**：
- RAIIによる自動リソース管理
- テンプレートによる汎用性
- 依然として生ポインタの使用が可能

### Java：ガベージコレクション

```java
// Javaのガベージコレクション
public class JavaMemory {
    static class Buffer {
        private byte[] data;
        
        public Buffer(int size) {
            this.data = new byte[size];
        }
        
        // finalize()は廃止予定
        // GCのタイミングは予測不可能
    }
    
    public static void main(String[] args) {
        Buffer buf1 = new Buffer(1024);
        Buffer buf2 = buf1;  // 参照のコピー
        
        buf1 = null;  // 参照を削除
        // buf2がまだ参照しているので、オブジェクトは生存
        
        buf2 = null;  // 最後の参照が削除
        // いつかGCによって回収される
    }
}
```

**特徴**：
- 自動メモリ管理
- GCによる一時停止
- 循環参照も解決可能

### Go：並行GC

```go
// Goの並行ガベージコレクション
package main

import (
    "runtime"
    "time"
)

type Buffer struct {
    data []byte
}

func createBuffer(size int) *Buffer {
    return &Buffer{
        data: make([]byte, size),
    }
}

func main() {
    buf := createBuffer(1024)
    
    // 明示的なGC実行（通常は不要）
    runtime.GC()
    
    // Goの並行GCは低レイテンシを目指す
    go func() {
        largeBuf := createBuffer(1024 * 1024)
        time.Sleep(time.Second)
        // 関数終了時に参照が失われ、GC対象になる
    }()
}
```

**特徴**：
- 並行マーク&スイープGC
- 低レイテンシを重視
- エスケープ解析による改良

### Python：参照カウント＋循環GC

```python
# Pythonの参照カウント
import sys
import gc

class Buffer:
    def __init__(self, size):
        self.data = bytearray(size)
    
    def __del__(self):
        print(f"Buffer of size {len(self.data)} is being deleted")

# 参照カウントのデモ
buf1 = Buffer(1024)
print(f"Reference count: {sys.getrefcount(buf1) - 1}")  # -1は関数引数分

buf2 = buf1  # 参照カウント増加
print(f"Reference count: {sys.getrefcount(buf1) - 1}")

del buf1  # 参照カウント減少
# buf2がまだ参照している

# 循環参照の例
class Node:
    def __init__(self):
        self.ref = None

a = Node()
b = Node()
a.ref = b
b.ref = a  # 循環参照

del a, b  # 参照カウントでは解放されない
gc.collect()  # 循環GCが必要
```

**特徴**：
- 基本は参照カウント
- 循環参照用のGC
- 即座の解放が多い

### Swift：ARC（自動参照カウント）

```swift
// SwiftのARC
class Buffer {
    var data: [UInt8]
    
    init(size: Int) {
        self.data = Array(repeating: 0, count: size)
        print("Buffer allocated")
    }
    
    deinit {
        print("Buffer deallocated")
    }
}

// 強参照
var buffer1: Buffer? = Buffer(size: 1024)
var buffer2 = buffer1  // 参照カウント増加

buffer1 = nil  // 参照カウント減少
// buffer2がまだ参照している

buffer2 = nil  // 最後の参照が削除、即座に解放

// 弱参照で循環参照を防ぐ
class Node {
    var next: Node?
    weak var prev: Node?  // 弱参照
}
```

**特徴**：
- コンパイル時に参照カウント操作を挿入
- 即座の解放
- 循環参照は手動で防ぐ必要

### Rust：所有権システム

```rust
// Rustの所有権システム
struct Buffer {
    data: Vec<u8>,
}

impl Buffer {
    fn new(size: usize) -> Self {
        println!("Buffer allocated");
        Buffer {
            data: vec![0; size],
        }
    }
}

impl Drop for Buffer {
    fn drop(&mut self) {
        println!("Buffer deallocated");
    }
}

fn rust_ownership() {
    let buffer1 = Buffer::new(1024);
    let buffer2 = buffer1;  // 所有権の移動
    // println!("{:?}", buffer1);  // コンパイルエラー
    
    // 借用による共有
    let buffer3 = Buffer::new(512);
    let ref1 = &buffer3;
    let ref2 = &buffer3;
    println!("Multiple immutable borrows OK");
    
    // スコープ終了時に自動解放
}
```

**特徴**：
- コンパイル時にメモリ安全性を保証
- 実行時オーバーヘッドなし
- 所有権の明確な追跡

## 比較表

| 言語 | メモリ管理 | 実行時コスト | 安全性 | 決定論的解放 | 並行性 |
|------|-----------|-------------|--------|--------------|--------|
| C | 手動 | なし | 低 | 可能 | 危険 |
| C++ | RAII/スマートポインタ | 低 | 中 | 可能 | 注意必要 |
| Java | GC | 高 | 高 | 不可能 | 安全 |
| Go | 並行GC | 中 | 高 | 不可能 | 安全 |
| Python | RefCount+GC | 中 | 高 | 部分的 | GILあり |
| Swift | ARC | 低 | 高 | 可能 | 注意必要 |
| Rust | 所有権 | なし | 最高 | 可能 | 安全 |

## 実践的な比較例

### タスク：大量のデータ処理

各言語で同じタスクを実装し、メモリ管理の違いを見てみましょう：

```rust
// Rust版
use std::collections::HashMap;

fn process_data(data: Vec<String>) -> HashMap<String, usize> {
    let mut counts = HashMap::new();
    
    for item in data {  // dataの所有権を取得
        *counts.entry(item).or_insert(0) += 1;
    }
    
    counts  // 所有権を返す
}
```

```java
// Java版
import java.util.*;

public Map<String, Integer> processData(List<String> data) {
    Map<String, Integer> counts = new HashMap<>();
    
    for (String item : data) {  // dataは参照のまま
        counts.merge(item, 1, Integer::sum);
    }
    
    return counts;  // 参照を返す
    // dataもcountsもGC対象
}
```

```cpp
// C++版
#include <unordered_map>
#include <vector>
#include <string>

std::unordered_map<std::string, size_t> 
process_data(std::vector<std::string> data) {  // 値渡し（コピー）
    std::unordered_map<std::string, size_t> counts;
    
    for (auto& item : data) {
        counts[item]++;
    }
    
    return counts;  // RVOによる改良
}
```

## Rustの独自性

### 1. コンパイル時保証

他の言語が実行時に行うチェックを、Rustはコンパイル時に行います：

```rust
fn compile_time_safety() {
    let mut vec = vec![1, 2, 3];
    let r1 = &vec[0];
    // vec.push(4);  // エラー：可変参照と不変参照の共存不可
    println!("{}", r1);
}
```

### 2. ゼロコスト抽象化

高レベルの抽象化が実行時コストを持たない：

```rust
// イテレータチェーン
let sum: i32 = (0..1000)
    .filter(|x| x % 2 == 0)
    .map(|x| x * x)
    .sum();
// 手書きループと同等の性能
```

### 3. 並行性の安全性

データ競合をコンパイル時に防ぐ：

```rust
use std::thread;

fn concurrency_safety() {
    let data = vec![1, 2, 3];
    
    // Sendトレイトにより安全な共有
    thread::spawn(move || {
        println!("{:?}", data);
    });
    
    // println!("{:?}", data);  // エラー：dataは移動済み
}
```

## まとめ

各言語のメモリ管理手法には、それぞれトレードオフがあります：

- **C/C++**: 最大の制御と性能、しかし安全性が犠牲
- **GC言語**: 安全性と利便性、しかし性能と予測可能性が犠牲
- **ARC**: バランスの取れたアプローチ、しかし循環参照の問題
- **Rust**: 安全性、性能、予測可能性をすべて実現

Rustの所有権システムは、50年にわたるプログラミング言語の進化の集大成として、これまで不可能と思われていた「安全性と性能の両立」を実現しました。

次章では、この所有権システムを補完する「借用とライフタイム」について詳しく見ていきます。

## 公式ドキュメント参照

- **The Book**: Chapter 4.1 - What is Ownership? (他言語との比較)
- **Reference**: Section 10.1 - Memory model
- **Rust Blog**: "Rust's Ownership System" (設計決定の背景)