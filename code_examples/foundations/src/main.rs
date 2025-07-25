//! # メモリ管理の比較デモンストレーション
//! 
//! このプログラムは、異なるプログラミング言語のメモリ管理手法を
//! Rustで模擬的に実装し、それぞれの特徴を比較します。

use std::alloc::{alloc, dealloc, Layout};
use std::ptr;
use std::mem;

/// C言語スタイルの手動メモリ管理を模擬
mod c_style {
    use super::*;
    
    pub struct Buffer {
        ptr: *mut u8,
        size: usize,
    }
    
    impl Buffer {
        /// malloc相当の操作
        pub unsafe fn malloc(size: usize) -> Self {
            let layout = Layout::from_size_align(size, 8).unwrap();
            let ptr = alloc(layout);
            if ptr.is_null() {
                panic!("メモリ割り当て失敗");
            }
            println!("C-style: {}バイトをアドレス {:p} に割り当て", size, ptr);
            Buffer { ptr, size }
        }
        
        /// free相当の操作
        pub unsafe fn free(&mut self) {
            if !self.ptr.is_null() {
                let layout = Layout::from_size_align(self.size, 8).unwrap();
                println!("C-style: アドレス {:p} を解放", self.ptr);
                dealloc(self.ptr, layout);
                self.ptr = ptr::null_mut();
            }
        }
        
        /// use-after-freeバグのデモ（危険！）
        pub unsafe fn demonstrate_use_after_free() {
            println!("\n=== C言語スタイル: use-after-freeバグのデモ ===");
            let mut buffer = Buffer::malloc(100);
            
            // データを書き込み
            for i in 0..10 {
                *buffer.ptr.add(i) = i as u8;
            }
            
            // メモリを解放
            buffer.free();
            
            // 解放後のアクセス（実際のCではクラッシュの可能性）
            println!("警告: 解放済みメモリへのアクセスを試行（Rustでは安全に制御）");
            // *buffer.ptr = 42; // 実際に実行すると未定義動作
        }
    }
}

/// ガベージコレクションを模擬（簡略化）
mod gc_style {
    use std::rc::Rc;
    use std::cell::RefCell;
    
    /// GC管理されるオブジェクト
    pub struct GcObject {
        data: Vec<u8>,
        allocated_at: std::time::Instant,
    }
    
    impl GcObject {
        pub fn new(size: usize) -> Rc<RefCell<Self>> {
            let obj = GcObject {
                data: vec![0u8; size],
                allocated_at: std::time::Instant::now(),
            };
            println!("GC-style: {}バイトのオブジェクトを作成", size);
            Rc::new(RefCell::new(obj))
        }
        
        /// GCの動作を模擬（実際のGCはもっと複雑）
        pub fn demonstrate_gc() {
            println!("\n=== ガベージコレクションスタイルのデモ ===");
            
            let obj1 = GcObject::new(1000);
            let obj2 = obj1.clone(); // 参照カウント増加
            
            println!("参照カウント: {}", Rc::strong_count(&obj1));
            
            drop(obj2); // 参照カウント減少
            println!("obj2をドロップ後の参照カウント: {}", Rc::strong_count(&obj1));
            
            // obj1がスコープを抜けるときに自動的に解放される
        }
    }
}

/// Rust所有権システムのデモ
mod rust_style {
    use std::time::Instant;
    
    pub struct RustBuffer {
        pub data: Vec<u8>,
        created_at: Instant,
    }
    
    impl RustBuffer {
        pub fn new(size: usize) -> Self {
            println!("Rust-style: {}バイトのバッファを作成", size);
            RustBuffer {
                data: vec![0u8; size],
                created_at: Instant::now(),
            }
        }
        
        /// 所有権の移動を示すデモ
        pub fn demonstrate_ownership() {
            println!("\n=== Rust所有権システムのデモ ===");
            
            let buffer1 = RustBuffer::new(100);
            println!("buffer1が所有権を持つ");
            
            let _buffer2 = buffer1; // 所有権の移動
            println!("所有権がbuffer2に移動");
            
            // println!("{:?}", buffer1.data); // コンパイルエラー！
            println!("buffer1はもう使用できない（コンパイル時に検出）");
            
            // buffer2がスコープを抜けるときに自動的に解放
        }
        
        /// 借用のデモ
        pub fn demonstrate_borrowing() {
            println!("\n=== Rust借用システムのデモ ===");
            
            let mut buffer = RustBuffer::new(50);
            
            // 不変借用
            let len = read_buffer(&buffer);
            println!("読み取り: バッファサイズ = {}", len);
            
            // 可変借用
            modify_buffer(&mut buffer);
            println!("バッファを変更");
            
            // 所有権は維持される
            println!("所有権は維持される: サイズ = {}", buffer.data.len());
        }
    }
    
    fn read_buffer(buffer: &RustBuffer) -> usize {
        buffer.data.len()
    }
    
    fn modify_buffer(buffer: &mut RustBuffer) {
        buffer.data[0] = 42;
    }
    
    impl Drop for RustBuffer {
        fn drop(&mut self) {
            let lifetime = self.created_at.elapsed();
            println!("Rust-style: バッファを自動解放（生存時間: {:?}）", lifetime);
        }
    }
}

/// メモリ使用量の統計を表示
fn print_memory_stats() {
    println!("\n=== メモリレイアウト情報 ===");
    println!("usize: {}バイト", mem::size_of::<usize>());
    println!("Vec<u8>: {}バイト（メタデータ）", mem::size_of::<Vec<u8>>());
    println!("Box<[u8; 1024]>: {}バイト（ポインタ）", mem::size_of::<Box<[u8; 1024]>>());
    println!("String: {}バイト（メタデータ）", mem::size_of::<String>());
}

fn main() {
    println!("===== メモリ管理手法の比較デモンストレーション =====\n");
    
    // メモリ統計を表示
    print_memory_stats();
    
    // 各スタイルのデモを実行
    unsafe {
        c_style::Buffer::demonstrate_use_after_free();
    }
    
    gc_style::GcObject::demonstrate_gc();
    
    rust_style::RustBuffer::demonstrate_ownership();
    rust_style::RustBuffer::demonstrate_borrowing();
    
    println!("\n===== デモンストレーション完了 =====");
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_rust_ownership() {
        let buffer = rust_style::RustBuffer::new(100);
        assert_eq!(buffer.data.len(), 100);
        // 所有権の移動後はアクセスできないことをテスト
        let _buffer2 = buffer;
        // assert_eq!(buffer.data.len(), 100); // コンパイルエラー
    }
    
    #[test]
    fn test_memory_layout() {
        // ポインタサイズの確認
        assert_eq!(mem::size_of::<*const u8>(), mem::size_of::<usize>());
        
        // Vecのメタデータサイズ確認
        assert_eq!(mem::size_of::<Vec<u8>>(), 3 * mem::size_of::<usize>());
    }
}