"""
演示为什么TCP Socket传输大数据会慢
"""

import socket
import threading
import time

# ============================================================
# 演示1：传输小数据（快）
# ============================================================
def demo_small_data():
    print("\n【演示1】传输小数据（100字节）")
    print("-" * 50)
    
    def server():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 9001))
        s.listen(1)
        conn, _ = s.accept()
        
        start = time.perf_counter()
        data = conn.recv(1024)
        elapsed = (time.perf_counter() - start) * 1000
        
        print(f"  服务器接收: {len(data)}字节, 耗时: {elapsed:.3f}ms")
        conn.close()
        s.close()
    
    def client():
        time.sleep(0.1)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 9001))
        
        # 发送100字节
        data = b'x' * 100
        start = time.perf_counter()
        s.sendall(data)
        elapsed = (time.perf_counter() - start) * 1000
        
        print(f"  客户端发送: {len(data)}字节, 耗时: {elapsed:.3f}ms")
        s.close()
    
    t1 = threading.Thread(target=server)
    t2 = threading.Thread(target=client)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

# ============================================================
# 演示2：传输大数据（慢）
# ============================================================
def demo_large_data():
    print("\n【演示2】传输大数据（6MB）")
    print("-" * 50)
    
    def server():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 9002))
        s.listen(1)
        conn, _ = s.accept()
        
        # 接收6MB数据
        total = 0
        target = 6 * 1024 * 1024
        start = time.perf_counter()
        recv_count = 0
        
        while total < target:
            chunk = conn.recv(65536)  # 每次最多64KB
            if not chunk:
                break
            total += len(chunk)
            recv_count += 1
        
        elapsed = (time.perf_counter() - start) * 1000
        
        print(f"  服务器接收: {total/1024/1024:.2f}MB")
        print(f"  recv()调用次数: {recv_count}次")
        print(f"  总耗时: {elapsed:.3f}ms")
        print(f"  平均每次recv: {elapsed/recv_count:.3f}ms")
        
        conn.close()
        s.close()
    
    def client():
        time.sleep(0.1)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('localhost', 9002))
        
        # 发送6MB数据
        data = b'x' * (6 * 1024 * 1024)
        start = time.perf_counter()
        s.sendall(data)
        elapsed = (time.perf_counter() - start) * 1000
        
        print(f"  客户端发送: {len(data)/1024/1024:.2f}MB, 耗时: {elapsed:.3f}ms")
        s.close()
    
    t1 = threading.Thread(target=server)
    t2 = threading.Thread(target=client)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

# ============================================================
# 演示3：为什么慢？
# ============================================================
def explain_why_slow():
    print("\n【解释】为什么传输6MB需要这么久？")
    print("-" * 50)
    print("""
TCP Socket传输大数据的过程：

1. 应用层（你的程序）
   sendall(6MB数据)
   ↓
2. 系统调用
   write() → 拷贝到内核缓冲区
   ↓
3. TCP协议栈
   ├─ 分包：6MB ÷ 64KB = 约100个包
   ├─ 每个包：添加TCP头、IP头
   ├─ 发送：逐个发送
   └─ 确认：等待ACK确认
   ↓
4. Loopback接口（本地回环）
   虽然是本地，但仍走完整TCP流程
   ↓
5. 接收端TCP协议栈
   ├─ 接收包
   ├─ 发送ACK
   ├─ 重组数据
   └─ 拷贝到接收缓冲区
   ↓
6. 应用层（接收程序）
   recv() 循环调用约100次
   每次从内核拷贝数据到用户空间

关键问题：
❌ 多次系统调用（~100次）
❌ 多次内存拷贝（内核↔用户空间）
❌ TCP协议开销（分包、确认、重组）
❌ 即使是localhost，也要走完整流程

结果：6MB数据传输需要 30-40ms
    """)

# ============================================================
# 运行演示
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TCP Socket 性能分析")
    print("=" * 60)
    
    demo_small_data()
    demo_large_data()
    explain_why_slow()
    
    print("\n" + "=" * 60)
    print("结论：")
    print("  小数据（<1KB）：TCP Socket很快（<1ms）")
    print("  大数据（6MB）：TCP Socket很慢（30-40ms）")
    print("  原因：多次系统调用 + 内存拷贝 + 协议开销")
    print("=" * 60)
