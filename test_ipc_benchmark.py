"""
IPC性能基准测试
测试不同进程间通信方式的实际开销
"""

import time
import numpy as np
import socket
import pickle
import json
from multiprocessing import Process, Queue, Pipe
from threading import Thread
import subprocess

# 模拟图像数据
def generate_test_image(width=1920, height=1080):
    """生成测试图像数据（模拟截图）"""
    # RGB图像，每像素3字节
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

def benchmark_function_call():
    """基准测试：直接函数调用（无IPC）"""
    image = generate_test_image()
    
    def mock_ocr(img):
        # 模拟OCR处理（简单计算）
        return str(np.sum(img))
    
    iterations = 100
    start = time.perf_counter()
    
    for _ in range(iterations):
        result = mock_ocr(image)
    
    elapsed = (time.perf_counter() - start) * 1000 / iterations
    print(f"直接函数调用: {elapsed:.3f}ms/次")
    return elapsed

def benchmark_queue():
    """测试：multiprocessing.Queue"""
    def worker(queue_in, queue_out):
        while True:
            data = queue_in.get()
            if data is None:
                break
            # 模拟处理
            result = str(np.sum(data))
            queue_out.put(result)
    
    queue_in = Queue()
    queue_out = Queue()
    
    p = Process(target=worker, args=(queue_in, queue_out))
    p.start()
    
    image = generate_test_image()
    iterations = 50  # Queue较慢，减少迭代次数
    
    start = time.perf_counter()
    for _ in range(iterations):
        queue_in.put(image)
        result = queue_out.get()
    
    elapsed = (time.perf_counter() - start) * 1000 / iterations
    
    queue_in.put(None)
    p.join()
    
    print(f"multiprocessing.Queue: {elapsed:.3f}ms/次")
    return elapsed

def benchmark_pipe():
    """测试：multiprocessing.Pipe"""
    def worker(conn):
        while True:
            data = conn.recv()
            if data is None:
                break
            result = str(np.sum(data))
            conn.send(result)
    
    parent_conn, child_conn = Pipe()
    p = Process(target=worker, args=(child_conn,))
    p.start()
    
    image = generate_test_image()
    iterations = 50
    
    start = time.perf_counter()
    for _ in range(iterations):
        parent_conn.send(image)
        result = parent_conn.recv()
    
    elapsed = (time.perf_counter() - start) * 1000 / iterations
    
    parent_conn.send(None)
    p.join()
    
    print(f"multiprocessing.Pipe: {elapsed:.3f}ms/次")
    return elapsed

def benchmark_socket():
    """测试：TCP Socket (localhost)"""
    def server():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('localhost', 9999))
        s.listen(1)
        conn, addr = s.accept()
        
        while True:
            # 接收数据大小
            size_data = conn.recv(8)
            if not size_data:
                break
            size = int.from_bytes(size_data, 'big')
            
            # 接收实际数据
            data = b''
            while len(data) < size:
                chunk = conn.recv(min(size - len(data), 65536))
                if not chunk:
                    break
                data += chunk
            
            if not data:
                break
            
            # 反序列化
            image = pickle.loads(data)
            result = str(np.sum(image))
            
            # 发送结果
            result_bytes = result.encode()
            conn.sendall(len(result_bytes).to_bytes(8, 'big'))
            conn.sendall(result_bytes)
        
        conn.close()
        s.close()
    
    # 启动服务器
    server_thread = Thread(target=server, daemon=True)
    server_thread.start()
    time.sleep(0.1)  # 等待服务器启动
    
    # 客户端
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', 9999))
    
    image = generate_test_image()
    iterations = 50
    
    start = time.perf_counter()
    for _ in range(iterations):
        # 序列化并发送
        data = pickle.dumps(image)
        client.sendall(len(data).to_bytes(8, 'big'))
        client.sendall(data)
        
        # 接收结果
        size_data = client.recv(8)
        size = int.from_bytes(size_data, 'big')
        result_data = b''
        while len(result_data) < size:
            chunk = client.recv(size - len(result_data))
            result_data += chunk
        result = result_data.decode()
    
    elapsed = (time.perf_counter() - start) * 1000 / iterations
    
    client.close()
    
    print(f"TCP Socket (localhost): {elapsed:.3f}ms/次")
    return elapsed

def benchmark_serialization():
    """测试：序列化开销"""
    image = generate_test_image()
    iterations = 100
    
    # Pickle
    start = time.perf_counter()
    for _ in range(iterations):
        data = pickle.dumps(image)
        restored = pickle.loads(data)
    elapsed_pickle = (time.perf_counter() - start) * 1000 / iterations
    
    # NumPy tobytes (最快)
    start = time.perf_counter()
    for _ in range(iterations):
        data = image.tobytes()
        restored = np.frombuffer(data, dtype=np.uint8).reshape(image.shape)
    elapsed_bytes = (time.perf_counter() - start) * 1000 / iterations
    
    print(f"\n序列化开销:")
    print(f"  Pickle: {elapsed_pickle:.3f}ms/次 (数据大小: {len(pickle.dumps(image))/1024/1024:.2f}MB)")
    print(f"  tobytes: {elapsed_bytes:.3f}ms/次 (数据大小: {len(image.tobytes())/1024/1024:.2f}MB)")
    
    return elapsed_pickle, elapsed_bytes

if __name__ == "__main__":
    print("=" * 60)
    print("IPC性能基准测试")
    print("图像大小: 1920x1080 RGB (~6MB)")
    print("=" * 60)
    
    print("\n1. 基准测试（无IPC）:")
    baseline = benchmark_function_call()
    
    print("\n2. 序列化测试:")
    ser_pickle, ser_bytes = benchmark_serialization()
    
    print("\n3. IPC方式对比:")
    try:
        pipe_time = benchmark_pipe()
        print(f"   相比基准慢: {pipe_time/baseline:.1f}x")
    except Exception as e:
        print(f"   Pipe测试失败: {e}")
    
    try:
        queue_time = benchmark_queue()
        print(f"   相比基准慢: {queue_time/baseline:.1f}x")
    except Exception as e:
        print(f"   Queue测试失败: {e}")
    
    try:
        socket_time = benchmark_socket()
        print(f"   相比基准慢: {socket_time/baseline:.1f}x")
    except Exception as e:
        print(f"   Socket测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("结论:")
    print(f"  对于6MB图像数据，IPC开销约为 {pipe_time - baseline:.1f}ms")
    print(f"  主要开销来自序列化 ({ser_pickle:.1f}ms) 和数据传输")
    print("=" * 60)
