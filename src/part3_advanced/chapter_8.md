# 並行性理論とRustの並行プログラミング

## はじめに

並行性は現代のコンピューティングにおいて不可欠な要素です。マルチコアプロセッサの普及により、並行プログラミングは高性能アプリケーションの鍵となっています。しかし、並行プログラミングは本質的に困難であり、データ競合、デッドロック、競合状態などの問題を引き起こしやすいです。Rustは、その型システムと所有権モデルを活用して、これらの問題の多くをコンパイル時に防ぐ革新的なアプローチを採用しています。

本章では、並行性の理論的基礎から始めて、Rustがどのようにこれらの理論を実装し、安全な並行プログラミングを実現しているかを探求します。

## 並行性理論の基礎

### 並行性と並列性の違い

```rust
// 並行性（Concurrency）: 複数のタスクが論理的に同時に進行
// 並列性（Parallelism）: 複数のタスクが物理的に同時に実行

use std::thread;
use std::time::Duration;

// 並行的だが必ずしも並列でない例
fn concurrent_not_parallel() {
    // シングルコアでも動作する
    let handle1 = thread::spawn(|| {
        for i in 0..5 {
            println!("Thread 1: {}", i);
            thread::sleep(Duration::from_millis(1));
        }
    });
    
    let handle2 = thread::spawn(|| {
        for i in 0..5 {
            println!("Thread 2: {}", i);
            thread::sleep(Duration::from_millis(1));
        }
    });
    
    handle1.join().unwrap();
    handle2.join().unwrap();
}

// 並列実行の例
use rayon::prelude::*;

fn parallel_computation() {
    let data: Vec<i32> = (0..1000000).collect();
    
    // 並列マップリデュース
    let sum: i32 = data.par_iter()
        .map(|&x| x * 2)
        .sum();
    
    println!("Parallel sum: {}", sum);
}
```

### CSP（Communicating Sequential Processes）

Tony Hoareが提唱したCSPモデルは、Rustのチャネル通信の基礎となっています：

```rust
use std::sync::mpsc;

// CSPモデルに基づくメッセージパッシング
fn csp_example() {
    let (tx, rx) = mpsc::channel();
    
    // プロセス1：数値を送信
    let tx1 = tx.clone();
    thread::spawn(move || {
        for i in 0..10 {
            tx1.send(i).unwrap();
            thread::sleep(Duration::from_millis(100));
        }
    });
    
    // プロセス2：数値を変換して送信
    let tx2 = tx.clone();
    thread::spawn(move || {
        for i in 0..10 {
            tx2.send(i * 2).unwrap();
            thread::sleep(Duration::from_millis(150));
        }
    });
    
    drop(tx); // 元の送信端を閉じる
    
    // 受信プロセス
    for received in rx {
        println!("Received: {}", received);
    }
}
```

### アクターモデル

Carl Hewittのアクターモデルは、状態をカプセル化し、メッセージパッシングで通信します：

```rust
use std::sync::{Arc, Mutex};
use std::collections::HashMap;

// 簡単なアクター実装
struct Actor {
    state: Arc<Mutex<HashMap<String, i32>>>,
    receiver: mpsc::Receiver<Message>,
}

enum Message {
    Get(String, mpsc::Sender<Option<i32>>),
    Set(String, i32),
    Inc(String),
}

impl Actor {
    fn run(self) {
        thread::spawn(move || {
            for msg in self.receiver {
                let mut state = self.state.lock().unwrap();
                match msg {
                    Message::Get(key, sender) => {
                        sender.send(state.get(&key).copied()).unwrap();
                    }
                    Message::Set(key, value) => {
                        state.insert(key, value);
                    }
                    Message::Inc(key) => {
                        state.entry(key).and_modify(|v| *v += 1).or_insert(1);
                    }
                }
            }
        });
    }
}
```

### π計算（Pi-calculus）

プロセス計算の理論的基礎：

```rust
// π計算の概念をRustで表現
// チャネルの動的生成と送信

fn pi_calculus_inspired() {
    // 新しいチャネルの生成（νx in π計算）
    let (tx, rx) = mpsc::channel::<mpsc::Sender<i32>>();
    
    // プロセス1：チャネルを送信
    thread::spawn(move || {
        let (new_tx, new_rx) = mpsc::channel();
        tx.send(new_tx).unwrap();
        
        // 新しいチャネルで値を受信
        if let Ok(value) = new_rx.recv() {
            println!("Process 1 received: {}", value);
        }
    });
    
    // プロセス2：チャネルを受信して使用
    thread::spawn(move || {
        if let Ok(channel) = rx.recv() {
            channel.send(42).unwrap();
        }
    });
    
    thread::sleep(Duration::from_millis(100));
}
```

## Rustの並行性モデル

### Send と Sync トレイト

Rustの並行性安全性の中核：

```rust
// Send: スレッド間で所有権を転送可能
// Sync: スレッド間で参照を共有可能

use std::rc::Rc;

// SendでもSyncでもない型
struct NotThreadSafe {
    data: Rc<Vec<i32>>, // RcはSendでない
}

// Sendだが Syncでない型
struct SendNotSync {
    data: Vec<i32>,
    _not_sync: std::cell::Cell<i32>, // CellはSyncでない
}

// SendかつSync型
struct ThreadSafe {
    data: Arc<Mutex<Vec<i32>>>,
}

// 自動的な導出と明示的な実装
struct CustomType {
    data: Vec<i32>,
}

// 自動的にSendとSyncが導出される
// unsafe impl Send for CustomType {}
// unsafe impl Sync for CustomType {}

// Sendでないことを明示
struct ExplicitlyNotSend {
    _marker: std::marker::PhantomData<*const u8>,
}

// コンパイラによる安全性保証
fn compile_time_safety() {
    let not_send = Rc::new(42);
    
    // コンパイルエラー：RcはSendでない
    // thread::spawn(move || {
    //     println!("{}", not_send);
    // });
    
    let send = Arc::new(42);
    
    // OK：ArcはSend
    thread::spawn(move || {
        println!("{}", send);
    });
}
```

### 所有権による並行性制御

```rust
// 所有権システムが並行性バグを防ぐ
fn ownership_prevents_races() {
    let mut data = vec![1, 2, 3];
    
    // moveセマンティクスによるデータ競合防止
    let handle = thread::spawn(move || {
        data.push(4); // データの所有権を取得
        data
    });
    
    // data.push(5); // エラー：dataはmoveされた
    
    let result = handle.join().unwrap();
    println!("{:?}", result);
}

// 借用チェッカーによる保護
fn borrow_checker_protection() {
    let data = Arc::new(Mutex::new(vec![1, 2, 3]));
    let data_clone = Arc::clone(&data);
    
    let handle = thread::spawn(move || {
        let mut vec = data_clone.lock().unwrap();
        vec.push(4);
    });
    
    // 別スレッドでも安全にアクセス
    {
        let mut vec = data.lock().unwrap();
        vec.push(5);
    }
    
    handle.join().unwrap();
}
```

## スレッドとメッセージパッシング

### スレッドの作成と管理

```rust
use std::thread::{self, JoinHandle};

// スレッドプールパターン
struct ThreadPool {
    workers: Vec<Worker>,
    sender: mpsc::Sender<Job>,
}

type Job = Box<dyn FnOnce() + Send + 'static>;

struct Worker {
    id: usize,
    thread: Option<JoinHandle<()>>,
}

impl ThreadPool {
    fn new(size: usize) -> Self {
        assert!(size > 0);
        
        let (sender, receiver) = mpsc::channel();
        let receiver = Arc::new(Mutex::new(receiver));
        
        let mut workers = Vec::with_capacity(size);
        
        for id in 0..size {
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }
        
        ThreadPool { workers, sender }
    }
    
    fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        let job = Box::new(f);
        self.sender.send(job).unwrap();
    }
}

impl Worker {
    fn new(id: usize, receiver: Arc<Mutex<mpsc::Receiver<Job>>>) -> Self {
        let thread = thread::spawn(move || loop {
            let job = receiver.lock().unwrap().recv().unwrap();
            println!("Worker {} executing job", id);
            job();
        });
        
        Worker {
            id,
            thread: Some(thread),
        }
    }
}
```

### チャネルの種類と使い分け

```rust
use std::sync::mpsc;
use crossbeam_channel;

// 標準ライブラリのmpsc（multiple producer, single consumer）
fn std_channel_example() {
    let (tx, rx) = mpsc::channel();
    
    // 複数の送信者
    for i in 0..5 {
        let tx_clone = tx.clone();
        thread::spawn(move || {
            tx_clone.send(i).unwrap();
        });
    }
    
    drop(tx); // 元の送信端を閉じる
    
    // 単一の受信者
    for received in rx {
        println!("Received: {}", received);
    }
}

// Crossbeamの高性能チャネル
fn crossbeam_channel_example() {
    // 有界チャネル（バックプレッシャー付き）
    let (tx, rx) = crossbeam_channel::bounded(10);
    
    thread::spawn(move || {
        for i in 0..100 {
            tx.send(i).unwrap();
            println!("Sent: {}", i);
        }
    });
    
    thread::spawn(move || {
        for msg in rx {
            println!("Processing: {}", msg);
            thread::sleep(Duration::from_millis(100));
        }
    });
    
    thread::sleep(Duration::from_secs(2));
}

// セレクト操作
fn select_example() {
    let (tx1, rx1) = crossbeam_channel::unbounded();
    let (tx2, rx2) = crossbeam_channel::unbounded();
    
    thread::spawn(move || {
        for i in 0..10 {
            tx1.send(format!("Channel 1: {}", i)).unwrap();
            thread::sleep(Duration::from_millis(100));
        }
    });
    
    thread::spawn(move || {
        for i in 0..10 {
            tx2.send(format!("Channel 2: {}", i)).unwrap();
            thread::sleep(Duration::from_millis(150));
        }
    });
    
    loop {
        crossbeam_channel::select! {
            recv(rx1) -> msg => {
                if let Ok(msg) = msg {
                    println!("{}", msg);
                } else {
                    break;
                }
            }
            recv(rx2) -> msg => {
                if let Ok(msg) = msg {
                    println!("{}", msg);
                } else {
                    break;
                }
            }
        }
    }
}
```

## 共有状態と同期プリミティブ

### Mutex（相互排他）

```rust
use std::sync::{Mutex, Arc};
use std::thread;

// 基本的なMutexの使用
fn basic_mutex() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Result: {}", *counter.lock().unwrap());
}

// ポイズニング（poisoning）の処理
fn mutex_poisoning() {
    let data = Arc::new(Mutex::new(vec![1, 2, 3]));
    let data_clone = Arc::clone(&data);
    
    let handle = thread::spawn(move || {
        let mut vec = data_clone.lock().unwrap();
        vec.push(4);
        panic!("Oops!"); // パニックでMutexがポイズン状態に
    });
    
    let _ = handle.join(); // パニックを処理しない
    
    // ポイズン状態のMutexへのアクセス
    match data.lock() {
        Ok(vec) => println!("Data: {:?}", vec),
        Err(poisoned) => {
            println!("Mutex was poisoned!");
            // into_inner()で内部データを取得可能
            let vec = poisoned.into_inner();
            println!("Recovered data: {:?}", vec);
        }
    }
}
```

### RwLock（読み書きロック）

```rust
use std::sync::RwLock;

// 読み込み優先の同期
fn rwlock_example() {
    let data = Arc::new(RwLock::new(HashMap::new()));
    
    // 複数の読み込みスレッド
    for i in 0..5 {
        let data = Arc::clone(&data);
        thread::spawn(move || {
            loop {
                let map = data.read().unwrap();
                println!("Reader {}: {:?}", i, map.get("key"));
                drop(map); // 明示的に読み込みロックを解放
                thread::sleep(Duration::from_millis(100));
            }
        });
    }
    
    // 書き込みスレッド
    let data_write = Arc::clone(&data);
    thread::spawn(move || {
        let mut count = 0;
        loop {
            let mut map = data_write.write().unwrap();
            map.insert("key".to_string(), count);
            count += 1;
            println!("Writer updated: {}", count);
            drop(map); // 明示的に書き込みロックを解放
            thread::sleep(Duration::from_millis(500));
        }
    });
    
    thread::sleep(Duration::from_secs(3));
}
```

### Atomic型

```rust
use std::sync::atomic::{AtomicUsize, AtomicBool, Ordering};

// ロックフリーな同期
fn atomic_example() {
    static COUNTER: AtomicUsize = AtomicUsize::new(0);
    static READY: AtomicBool = AtomicBool::new(false);
    
    // カウンタの更新
    let handle1 = thread::spawn(|| {
        for _ in 0..1000 {
            COUNTER.fetch_add(1, Ordering::SeqCst);
        }
        READY.store(true, Ordering::Release);
    });
    
    // フラグの監視
    let handle2 = thread::spawn(|| {
        while !READY.load(Ordering::Acquire) {
            thread::yield_now();
        }
        println!("Final count: {}", COUNTER.load(Ordering::SeqCst));
    });
    
    handle1.join().unwrap();
    handle2.join().unwrap();
}

// メモリ順序（Memory Ordering）
fn memory_ordering_example() {
    let x = Arc::new(AtomicUsize::new(0));
    let y = Arc::new(AtomicUsize::new(0));
    
    let x1 = Arc::clone(&x);
    let y1 = Arc::clone(&y);
    
    let handle1 = thread::spawn(move || {
        x1.store(1, Ordering::Release);
        y1.store(1, Ordering::Release);
    });
    
    let x2 = Arc::clone(&x);
    let y2 = Arc::clone(&y);
    
    let handle2 = thread::spawn(move || {
        while y2.load(Ordering::Acquire) == 0 {}
        assert_eq!(x2.load(Ordering::Acquire), 1);
    });
    
    handle1.join().unwrap();
    handle2.join().unwrap();
}
```

## 非同期プログラミング

### async/await の基礎

```rust
use std::future::Future;
use std::pin::Pin;
use std::task::{Context, Poll};

// 基本的な非同期関数
async fn async_function() -> i32 {
    42
}

// Futureトレイトの手動実装
struct MyFuture {
    count: u32,
}

impl Future for MyFuture {
    type Output = i32;
    
    fn poll(mut self: Pin<&mut Self>, cx: &mut Context<'_>) -> Poll<Self::Output> {
        self.count += 1;
        if self.count < 3 {
            cx.waker().wake_by_ref();
            Poll::Pending
        } else {
            Poll::Ready(42)
        }
    }
}

// async/awaitの変換
async fn composed_async() {
    let result = async_function().await;
    println!("Result: {}", result);
    
    let custom = MyFuture { count: 0 }.await;
    println!("Custom: {}", custom);
}
```

### 非同期ランタイム

```rust
// Tokioランタイムの使用
use tokio;

#[tokio::main]
async fn tokio_example() {
    // 非同期タスクのスポーン
    let handle = tokio::spawn(async {
        tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
        "Task completed"
    });
    
    let result = handle.await.unwrap();
    println!("{}", result);
}

// 非同期I/O
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;

async fn async_tcp_server() -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind("127.0.0.1:8080").await?;
    
    loop {
        let (mut socket, _) = listener.accept().await?;
        
        tokio::spawn(async move {
            let mut buf = [0; 1024];
            
            loop {
                let n = match socket.read(&mut buf).await {
                    Ok(n) if n == 0 => return,
                    Ok(n) => n,
                    Err(_) => return,
                };
                
                if let Err(_) = socket.write_all(&buf[0..n]).await {
                    return;
                }
            }
        });
    }
}
```

### 非同期並行性パターン

```rust
use futures::future;
use futures::stream::{self, StreamExt};

// 並行実行
async fn concurrent_execution() {
    // 複数の非同期タスクを並行実行
    let (result1, result2, result3) = tokio::join!(
        async { compute_1().await },
        async { compute_2().await },
        async { compute_3().await }
    );
    
    println!("Results: {}, {}, {}", result1, result2, result3);
}

async fn compute_1() -> i32 { 1 }
async fn compute_2() -> i32 { 2 }
async fn compute_3() -> i32 { 3 }

// ストリーム処理
async fn stream_processing() {
    let stream = stream::iter(vec![1, 2, 3, 4, 5]);
    
    let processed = stream
        .map(|x| async move { x * 2 })
        .buffer_unordered(3)
        .collect::<Vec<_>>()
        .await;
    
    println!("Processed: {:?}", processed);
}

// セレクト操作
use tokio::select;

async fn async_select() {
    let mut interval = tokio::time::interval(tokio::time::Duration::from_secs(1));
    let mut count = 0;
    
    loop {
        select! {
            _ = interval.tick() => {
                count += 1;
                println!("Tick {}", count);
                if count >= 5 {
                    break;
                }
            }
            _ = tokio::signal::ctrl_c() => {
                println!("Interrupted!");
                break;
            }
        }
    }
}
```

## 高度な並行性パターン

### ロックフリーデータ構造

```rust
use crossbeam_epoch as epoch;
use std::sync::atomic::{AtomicPtr, Ordering};

// 簡単なロックフリースタック
struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}

struct Node<T> {
    data: T,
    next: *mut Node<T>,
}

impl<T> LockFreeStack<T> {
    fn new() -> Self {
        LockFreeStack {
            head: AtomicPtr::new(std::ptr::null_mut()),
        }
    }
    
    fn push(&self, data: T) {
        let new_node = Box::into_raw(Box::new(Node {
            data,
            next: std::ptr::null_mut(),
        }));
        
        loop {
            let head = self.head.load(Ordering::Acquire);
            unsafe {
                (*new_node).next = head;
            }
            
            if self.head.compare_exchange_weak(
                head,
                new_node,
                Ordering::Release,
                Ordering::Acquire,
            ).is_ok() {
                break;
            }
        }
    }
    
    fn pop(&self) -> Option<T> {
        let guard = &epoch::pin();
        
        loop {
            let head = self.head.load(Ordering::Acquire);
            if head.is_null() {
                return None;
            }
            
            let next = unsafe { (*head).next };
            
            if self.head.compare_exchange_weak(
                head,
                next,
                Ordering::Release,
                Ordering::Acquire,
            ).is_ok() {
                unsafe {
                    guard.defer_destroy(head);
                    return Some(std::ptr::read(&(*head).data));
                }
            }
        }
    }
}
```

### 並行性デバッグ

```rust
// Loomを使った並行性テスト
#[cfg(test)]
mod tests {
    use loom::sync::Arc;
    use loom::sync::atomic::{AtomicUsize, Ordering};
    use loom::thread;
    
    #[test]
    #[cfg(loom)]
    fn concurrent_counter() {
        let mut config = loom::model::Config::default();
        config.preemption_bound = Some(3);
        
        loom::model_with_config(config, || {
            let counter = Arc::new(AtomicUsize::new(0));
            let counter1 = counter.clone();
            let counter2 = counter.clone();
            
            let t1 = thread::spawn(move || {
                counter1.fetch_add(1, Ordering::SeqCst);
            });
            
            let t2 = thread::spawn(move || {
                counter2.fetch_add(1, Ordering::SeqCst);
            });
            
            t1.join().unwrap();
            t2.join().unwrap();
            
            assert_eq!(counter.load(Ordering::SeqCst), 2);
        });
    }
}
```

## パフォーマンス考慮事項

### 並行性のオーバーヘッド

```rust
use std::time::Instant;

// スレッド生成のコスト測定
fn thread_overhead_benchmark() {
    let start = Instant::now();
    
    // シーケンシャル実行
    let mut sum = 0;
    for i in 0..1000 {
        sum += i;
    }
    
    let sequential_time = start.elapsed();
    
    let start = Instant::now();
    
    // 並行実行（オーバーヘッドあり）
    let handles: Vec<_> = (0..1000)
        .map(|i| thread::spawn(move || i))
        .collect();
    
    let sum: i32 = handles.into_iter()
        .map(|h| h.join().unwrap())
        .sum();
    
    let parallel_time = start.elapsed();
    
    println!("Sequential: {:?}", sequential_time);
    println!("Parallel: {:?}", parallel_time);
    println!("Speedup: {:.2}x", parallel_time.as_secs_f64() / sequential_time.as_secs_f64());
}

// 適切な粒度の選択
fn granularity_example() {
    use rayon::prelude::*;
    
    let data: Vec<i32> = (0..10_000_000).collect();
    
    // 細かすぎる粒度（非効率）
    let start = Instant::now();
    let sum1: i32 = data.par_iter()
        .map(|&x| x)
        .sum();
    println!("Fine-grained: {:?}", start.elapsed());
    
    // 適切な粒度（高性能）
    let start = Instant::now();
    let chunk_size = 1000;
    let sum2: i32 = data.par_chunks(chunk_size)
        .map(|chunk| chunk.iter().sum::<i32>())
        .sum();
    println!("Coarse-grained: {:?}", start.elapsed());
}
```

## まとめ

Rustの並行性モデルは、以下の特徴を持ちます：

1. **型システムによる安全性**: Send/Syncトレイトによるコンパイル時保証
2. **所有権による競合防止**: データ競合を静的に防ぐ
3. **豊富な抽象化**: チャネル、Mutex、async/awaitなど
4. **ゼロコスト**: 必要な機能のみのオーバーヘッド
5. **理論的基礎**: CSP、アクターモデルなどの確立された理論

これらの機能により、Rustは「恐れることなく並行性を扱える」言語となっています。

次章では、マクロとメタプログラミングについて探求します。

## 公式ドキュメント参照

- **The Book**: Chapter 16 - Fearless Concurrency
- **Async Book**: Asynchronous Programming in Rust
- **Reference**: Chapter 15 - Concurrency
- **RFC 2033**: Async/await syntax