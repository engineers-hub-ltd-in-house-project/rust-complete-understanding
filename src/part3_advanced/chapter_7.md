# Unsafe Rustとシステムプログラミング

## はじめに

Rustの安全性保証は強力ですが、システムプログラミングの領域では、ハードウェアとの直接的なやり取りや、他言語との相互運用など、コンパイラが安全性を保証できない操作が必要になります。Unsafe Rustは、これらの低レベル操作を可能にしながら、安全性の境界を明確にする仕組みです。本章では、Unsafe Rustの理論的基礎から実践的な使用方法まで、包括的に探求します。

## Unsafe Rustの理論的基礎

### 安全性の境界

Rustの型システムは、以下の不変条件を保証します：

1. **メモリ安全性**: 有効なメモリのみアクセス
2. **スレッド安全性**: データ競合なし
3. **型安全性**: 型の不変条件を維持

Unsafeは、これらの保証を解除します：

```rust
// Safe Rustでは不可能な操作
fn impossible_in_safe_rust() {
    let raw_ptr: *const i32 = 0x12345678 as *const i32;
    // let value = *raw_ptr;  // エラー：生ポインタの参照外し
    
    let mut data = [1, 2, 3, 4];
    let ptr1 = &mut data[0];
    let ptr2 = &mut data[1];
    // 同時に複数の可変参照は作れない（エイリアシングなし）
}

// Unsafe Rustで可能になる
unsafe fn possible_in_unsafe() {
    let raw_ptr: *const i32 = 0x12345678 as *const i32;
    let value = *raw_ptr;  // 危険：任意のメモリアドレスを読む
    
    let mut data = [1, 2, 3, 4];
    let ptr1 = &mut data[0] as *mut i32;
    let ptr2 = &mut data[1] as *mut i32;
    *ptr1 = 10;
    *ptr2 = 20;  // 生ポインタ経由なら可能
}
```

### Unsafeの5つの超能力

Unsafe Rustでのみ可能な5つの操作：

1. **生ポインタの参照外し**
2. **unsafe関数・メソッドの呼び出し**
3. **可変静的変数へのアクセス・変更**
4. **unsafeトレイトの実装**
5. **共用体のフィールドへのアクセス**

## 生ポインタ（Raw Pointers）

### 生ポインタの基礎

```rust
// 生ポインタの型
let mut num = 5;
let r1 = &num as *const i32;      // 不変生ポインタ
let r2 = &mut num as *mut i32;    // 可変生ポインタ

// 生ポインタの特徴
// 1. 借用規則を回避できる
// 2. nullかもしれない
// 3. 自動的な解放はない
// 4. 有効性の保証がない

// 生ポインタの操作
unsafe {
    println!("r1の値: {}", *r1);
    *r2 = 10;
    println!("変更後: {}", *r1);
}
```

### ポインタ演算

```rust
use std::mem;

fn pointer_arithmetic() {
    let arr = [1, 2, 3, 4, 5];
    let ptr = arr.as_ptr();
    
    unsafe {
        // ポインタのオフセット計算
        let second = ptr.offset(1);
        let third = ptr.add(2);
        
        println!("second: {}", *second);  // 2
        println!("third: {}", *third);     // 3
        
        // 逆方向のオフセット
        let back = third.sub(1);
        println!("back: {}", *back);       // 2
        
        // バイト単位のオフセット
        let bytes_ptr = ptr as *const u8;
        let next_elem = bytes_ptr.add(mem::size_of::<i32>()) as *const i32;
        println!("next via bytes: {}", *next_elem);  // 2
    }
}
```

### Nullポインタ処理

```rust
use std::ptr;

fn null_pointer_handling() {
    // nullポインタの作成
    let null_ptr: *const i32 = ptr::null();
    let null_mut: *mut i32 = ptr::null_mut();
    
    // null チェック
    if null_ptr.is_null() {
        println!("ポインタはnull");
    }
    
    // Option<&T>のnull pointer optimization
    assert_eq!(mem::size_of::<Option<&i32>>(), mem::size_of::<*const i32>());
    
    // NonNullによる非nullポインタ
    use std::ptr::NonNull;
    let mut x = 5;
    let ptr = NonNull::new(&mut x as *mut i32).unwrap();
    
    unsafe {
        *ptr.as_mut() = 10;
    }
}
```

## FFI（Foreign Function Interface）

### C言語との相互運用

```rust
// Cの関数を宣言
extern "C" {
    fn abs(input: i32) -> i32;
    fn sqrt(input: f64) -> f64;
    
    // Cの構造体
    fn malloc(size: usize) -> *mut u8;
    fn free(ptr: *mut u8);
}

// Rustの関数をCから呼べるようにする
#[no_mangle]
pub extern "C" fn rust_function(x: i32) -> i32 {
    x * 2
}

// FFIの使用例
fn ffi_example() {
    unsafe {
        println!("abs(-5) = {}", abs(-5));
        println!("sqrt(2.0) = {}", sqrt(2.0));
        
        // 手動メモリ管理
        let ptr = malloc(100);
        if !ptr.is_null() {
            // メモリを使用
            free(ptr);
        }
    }
}
```

### 構造体のレイアウト

```rust
// C互換の構造体
#[repr(C)]
struct CCompatible {
    x: i32,
    y: i32,
}

// パディングとアライメント
#[repr(C, packed)]
struct Packed {
    a: u8,
    b: u32,
    c: u8,
}

#[repr(C, align(16))]
struct Aligned {
    data: [u8; 10],
}

// 共用体（Union）
#[repr(C)]
union MyUnion {
    i: i32,
    f: f32,
}

fn layout_example() {
    println!("CCompatible size: {}", mem::size_of::<CCompatible>());
    println!("Packed size: {}", mem::size_of::<Packed>());
    println!("Aligned size: {}", mem::size_of::<Aligned>());
    
    let u = MyUnion { i: 42 };
    unsafe {
        println!("As int: {}", u.i);
        println!("As float: {}", u.f);  // 再解釈
    }
}
```

## メモリ管理の低レベル操作

### アロケータAPI

```rust
use std::alloc::{GlobalAlloc, Layout, alloc, dealloc};
use std::ptr;

// カスタムアロケータの実装
struct MyAllocator;

unsafe impl GlobalAlloc for MyAllocator {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let ptr = alloc(layout);
        if !ptr.is_null() {
            println!("Allocated {} bytes at {:p}", layout.size(), ptr);
        }
        ptr
    }
    
    unsafe fn dealloc(&self, ptr: *mut u8, layout: Layout) {
        println!("Deallocating {} bytes at {:p}", layout.size(), ptr);
        dealloc(ptr, layout);
    }
}

#[global_allocator]
static ALLOCATOR: MyAllocator = MyAllocator;

// 手動メモリ管理
fn manual_memory_management() {
    unsafe {
        let layout = Layout::array::<i32>(10).unwrap();
        let ptr = alloc(layout) as *mut i32;
        
        if ptr.is_null() {
            panic!("アロケーション失敗");
        }
        
        // メモリの初期化
        for i in 0..10 {
            ptr.add(i).write(i as i32);
        }
        
        // メモリの読み取り
        for i in 0..10 {
            println!("ptr[{}] = {}", i, *ptr.add(i));
        }
        
        // メモリの解放
        dealloc(ptr as *mut u8, layout);
    }
}
```

### メモリマップドI/O

```rust
// メモリマップドI/Oの例（組み込みシステム）
const GPIO_BASE: usize = 0x40020000;
const GPIO_MODER: usize = GPIO_BASE + 0x00;
const GPIO_ODR: usize = GPIO_BASE + 0x14;

fn mmio_example() {
    unsafe {
        // GPIOモードレジスタの設定
        let moder = GPIO_MODER as *mut u32;
        *moder = (*moder & !(0b11 << 10)) | (0b01 << 10);
        
        // GPIO出力データレジスタの操作
        let odr = GPIO_ODR as *mut u32;
        *odr |= 1 << 5;  // ピン5をHIGHに
    }
}

// Volatile読み書き
use std::ptr::{read_volatile, write_volatile};

fn volatile_operations() {
    let mut value = 42;
    let ptr = &mut value as *mut i32;
    
    unsafe {
        // コンパイラの変更を防ぐ
        write_volatile(ptr, 100);
        let read = read_volatile(ptr);
        println!("Volatile read: {}", read);
    }
}
```

## Unsafeトレイト

### SendとSync

```rust
// Sendトレイト：スレッド間で所有権を転送可能
// Syncトレイト：スレッド間で参照を共有可能

use std::cell::UnsafeCell;

// 手動でSend/Syncを実装
struct MyBox<T> {
    data: UnsafeCell<T>,
}

unsafe impl<T: Send> Send for MyBox<T> {}
unsafe impl<T: Sync> Sync for MyBox<T> {}

impl<T> MyBox<T> {
    fn new(value: T) -> Self {
        MyBox {
            data: UnsafeCell::new(value),
        }
    }
    
    fn get(&self) -> &T {
        unsafe { &*self.data.get() }
    }
    
    fn get_mut(&self) -> &mut T {
        unsafe { &mut *self.data.get() }
    }
}
```

### カスタムスマートポインタ

```rust
use std::ops::{Deref, DerefMut};
use std::marker::PhantomData;

// 独自のBoxの実装
struct MyOwnBox<T> {
    ptr: NonNull<T>,
    _phantom: PhantomData<T>,
}

impl<T> MyOwnBox<T> {
    fn new(value: T) -> Self {
        let layout = Layout::new::<T>();
        unsafe {
            let ptr = alloc(layout) as *mut T;
            if ptr.is_null() {
                std::alloc::handle_alloc_error(layout);
            }
            ptr.write(value);
            
            MyOwnBox {
                ptr: NonNull::new_unchecked(ptr),
                _phantom: PhantomData,
            }
        }
    }
}

impl<T> Deref for MyOwnBox<T> {
    type Target = T;
    
    fn deref(&self) -> &T {
        unsafe { self.ptr.as_ref() }
    }
}

impl<T> DerefMut for MyOwnBox<T> {
    fn deref_mut(&mut self) -> &mut T {
        unsafe { self.ptr.as_mut() }
    }
}

impl<T> Drop for MyOwnBox<T> {
    fn drop(&mut self) {
        unsafe {
            let layout = Layout::new::<T>();
            ptr::drop_in_place(self.ptr.as_ptr());
            dealloc(self.ptr.as_ptr() as *mut u8, layout);
        }
    }
}
```

## インラインアセンブリ

### 基本的なインラインアセンブリ

```rust
use std::arch::asm;

fn inline_assembly_examples() {
    let mut x: u64 = 3;
    let y: u64 = 5;
    
    unsafe {
        // 基本的な算術演算
        asm!(
            "add {}, {}",
            inout(reg) x,
            in(reg) y,
        );
        println!("3 + 5 = {}", x);
        
        // 複数の命令
        let mut a: u32 = 10;
        let b: u32 = 20;
        let mut result: u32;
        
        asm!(
            "mov {result}, {a}",
            "add {result}, {b}",
            a = in(reg) a,
            b = in(reg) b,
            result = out(reg) result,
        );
        println!("10 + 20 = {}", result);
    }
}

// CPU機能の直接利用
#[cfg(target_arch = "x86_64")]
fn cpuid_example() {
    unsafe {
        let mut eax: u32;
        let mut ebx: u32;
        let mut ecx: u32;
        let mut edx: u32;
        
        // CPUID命令の実行
        asm!(
            "cpuid",
            inout("eax") 0 => eax,
            out("ebx") ebx,
            out("ecx") ecx,
            out("edx") edx,
        );
        
        println!("CPU Vendor ID: {:x} {:x} {:x} {:x}", eax, ebx, ecx, edx);
    }
}
```

## 安全な抽象化の構築

### Unsafe実装の安全なラッパー

```rust
// 内部でunsafeを使用する安全なAPI
pub struct SafeVec<T> {
    ptr: NonNull<T>,
    cap: usize,
    len: usize,
}

impl<T> SafeVec<T> {
    pub fn new() -> Self {
        SafeVec {
            ptr: NonNull::dangling(),
            cap: 0,
            len: 0,
        }
    }
    
    pub fn push(&mut self, value: T) {
        if self.len == self.cap {
            self.grow();
        }
        
        unsafe {
            self.ptr.as_ptr().add(self.len).write(value);
        }
        self.len += 1;
    }
    
    pub fn pop(&mut self) -> Option<T> {
        if self.len == 0 {
            return None;
        }
        
        self.len -= 1;
        unsafe {
            Some(self.ptr.as_ptr().add(self.len).read())
        }
    }
    
    fn grow(&mut self) {
        let new_cap = if self.cap == 0 { 1 } else { self.cap * 2 };
        let layout = Layout::array::<T>(new_cap).unwrap();
        
        let new_ptr = if self.cap == 0 {
            unsafe { alloc(layout) }
        } else {
            let old_layout = Layout::array::<T>(self.cap).unwrap();
            unsafe {
                std::alloc::realloc(
                    self.ptr.as_ptr() as *mut u8,
                    old_layout,
                    layout.size(),
                )
            }
        };
        
        self.ptr = NonNull::new(new_ptr as *mut T)
            .expect("アロケーション失敗");
        self.cap = new_cap;
    }
}

impl<T> Drop for SafeVec<T> {
    fn drop(&mut self) {
        if self.cap != 0 {
            unsafe {
                // 要素のドロップ
                for i in 0..self.len {
                    ptr::drop_in_place(self.ptr.as_ptr().add(i));
                }
                // メモリの解放
                let layout = Layout::array::<T>(self.cap).unwrap();
                dealloc(self.ptr.as_ptr() as *mut u8, layout);
            }
        }
    }
}
```

## Unsafeコードの検証

### 不変条件の文書化

```rust
/// # Safety
/// 
/// この関数を呼び出すには以下の条件を満たす必要があります：
/// - `ptr`は有効な`T`型の値を指している
/// - `ptr`は適切にアラインされている
/// - `ptr`が指すメモリは少なくとも`count`個の要素を含む
/// - 返されたスライスの生存期間中、他のコードがこのメモリを変更しない
unsafe fn slice_from_raw_parts<'a, T>(ptr: *const T, count: usize) -> &'a [T] {
    std::slice::from_raw_parts(ptr, count)
}
```

### Miriによる検証

```bash
# Miriをインストール
rustup +nightly component add miri

# Unsafeコードの検証
cargo +nightly miri test
```

## まとめ

Unsafe Rustは、システムプログラミングに必要な低レベル操作を可能にしながら、安全性の境界を明確にします：

1. **限定的な使用**: Unsafeは必要最小限に
2. **安全な抽象化**: Unsafe実装を安全なAPIでラップ
3. **文書化**: 安全性の前提条件を明確に
4. **検証**: ツールとテストによる確認

適切に使用されたUnsafe Rustは、システムの性能と安全性を両立させる強力なツールです。

次章では、並行性理論とRustの並行プログラミングについて探求します。

## 公式ドキュメント参照

- **The Book**: Chapter 19 - Advanced Features (Unsafe Rust)
- **Rustonomicon**: The Dark Arts of Advanced and Unsafe Rust
- **Reference**: Chapter 16 - Unsafe blocks
- **RFC 2585**: Inline assembly