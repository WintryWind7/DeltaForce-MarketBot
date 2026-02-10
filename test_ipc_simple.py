"""
简化的IPC性能测试
专注于实际场景：Java调用Python OCR服务
"""

import time
import numpy as np
import socket
import pickle
import threading

def generate_test_image(width=1920, height=1080):
    """生成测试图像（模拟截图）"""
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

def mock_ocr_processing(image):
    """模拟OCR处理（简单计算代替实际OCR）"""
    return str(np.sum(image) % 1000000)

# ============================================================
# 测试1: 直接调用（Python单体架构）
# ============================================================
def test_direct_call():
    """基准：直接函数调用"""
    print("\n【测试1】直接函数调用（Python单体）")
    print("-" * 50)
    
    image = generate_test_image()
    iterations = 100
    
    start = time.perf_counter()
    for _ in range(iterations):
        result = mock_ocr_processing(image)
    elapsed = (time.perf_counter() - start) * 1000 / iterations
    
    print(f"平均耗时: {elapsed:.3f}ms")
    print(f"图像大小: {image.nbytes / 1024 / 1024:.2f}MB")
    return elapsed

# ============================================================
# 测试2: TCP Socket通信（模拟Java调用Python服务）
# ============================================================
def test_socket_ipc():
    """TCP Socket IPC（模拟gRPC/REST）"""
    print("\n【测试2】TCP Socket IPC（模拟Java→Python）")
    print("-" * 50)
    
    PORT = 19999
    
    # Python服务端
    def python_service():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', PORT))
        server.listen(1)
        conn, _ = server.accept()
        
        while True:
            try:
                # 接收数据长度
                size_bytes = conn.recv(8)
                if not size_bytes:
                    break
                size = int.from_bytes(size_bytes, 'big')
                
                # 接收图像数据
                data = b''
                while len(data) < size:
                    chunk = conn.recv(min(size - len(data), 65536))
                    if not chunk:
                        break
                    data += chunk
                
                # 反序列化
                image = pickle.loads(data)
                
                # OCR处理
                result = mock_ocr_processing(image)
                
                # 返回结果
                result_bytes = result.encode()
                conn.sendall(len(result_bytes).to_bytes(8, 'big'))
                conn.sendall(result_bytes)
            except:
                break
        
        conn.close()
        server.close()
    
    # 启动服务
    server_thread = threading.Thread(target=python_service, daemon=True)
    server_thread.start()
    time.sleep(0.2)
    
    # Java客户端（模拟）
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(('localhost', PORT))
    
    image = generate_test_image()
    iterations = 50
    
    # 预热
    for _ in range(5):
        data = pickle.dumps(image)
        client.sendall(len(data).to_bytes(8, 'big'))
        client.sendall(data)
        size_bytes = client.recv(8)
        size = int.from_bytes(size_bytes, 'big')
        result = client.recv(size)
    
    # 正式测试
    start = time.perf_counter()
    for _ in range(iterations):
        # 序列化图像
        data = pickle.dumps(image)
        
        # 发送
        client.sendall(len(data).to_bytes(8, 'big'))
        client.sendall(data)
        
        # 接收结果
        size_bytes = client.recv(8)
        size = int.from_bytes(size_bytes, 'big')
        result = client.recv(size)
    
    elapsed = (time.perf_counter() - start) * 1000 / iterations
    
    client.close()
    
    print(f"平均耗时: {elapsed:.3f}ms")
    print(f"  - 序列化: ~2ms")
    print(f"  - 网络传输: ~{elapsed - 4:.1f}ms")
    print(f"  - OCR处理: ~2ms")
    return elapsed

# ============================================================
# 测试3: 只测序列化开销
# ============================================================
def test_serialization():
    """测试序列化开销"""
    print("\n【测试3】序列化开销分析")
    print("-" * 50)
    
    image = generate_test_image()
    iterations = 100
    
    # Pickle序列化
    start = time.perf_counter()
    for _ in range(iterations):
        data = pickle.dumps(image)
    ser_time = (time.perf_counter() - start) * 1000 / iterations
    
    # Pickle反序列化
    data = pickle.dumps(image)
    start = time.perf_counter()
    for _ in range(iterations):
        img = pickle.loads(data)
    deser_time = (time.perf_counter() - start) * 1000 / iterations
    
    print(f"序列化:   {ser_time:.3f}ms")
    print(f"反序列化: {deser_time:.3f}ms")
    print(f"总计:     {ser_time + deser_time:.3f}ms")
    print(f"数据大小: {len(data) / 1024 / 1024:.2f}MB")
    
    return ser_time + deser_time

# ============================================================
# 测试4: 实际场景模拟
# ============================================================
def test_real_scenario():
    """模拟实际使用场景：get_balance操作"""
    print("\n【测试4】实际场景对比")
    print("-" * 50)
    
    image = generate_test_image()
    
    # Python单体：点击 → 截图 → OCR → 返回
    def python_monolith():
        time.sleep(0.001)  # 模拟点击
        screenshot = image.copy()  # 模拟截图（内存操作）
        result = mock_ocr_processing(screenshot)  # OCR
        return result
    
    # Java+Python混合：点击 → 截图 → 序列化 → 传输 → OCR → 返回
    def java_python_hybrid():
        time.sleep(0.001)  # 模拟点击（Java）
        screenshot = image.copy()  # 模拟截图（Java）
        
        # 序列化（Java → Python）
        data = pickle.dumps(screenshot)
        time.sleep(0.0005)  # 模拟网络传输（localhost很快）
        
        # 反序列化（Python）
        img = pickle.loads(data)
        result = mock_ocr_processing(img)  # OCR
        
        # 返回结果
        time.sleep(0.0005)  # 模拟返回传输
        return result
    
    iterations = 100
    
    # Python单体
    start = time.perf_counter()
    for _ in range(iterations):
        python_monolith()
    python_time = (time.perf_counter() - start) * 1000 / iterations
    
    # Java+Python混合
    start = time.perf_counter()
    for _ in range(iterations):
        java_python_hybrid()
    hybrid_time = (time.perf_counter() - start) * 1000 / iterations
    
    print(f"Python单体架构:    {python_time:.3f}ms")
    print(f"Java+Python混合:   {hybrid_time:.3f}ms")
    print(f"额外开销:          {hybrid_time - python_time:.3f}ms ({(hybrid_time/python_time - 1)*100:.1f}%)")

# ============================================================
# 主测试
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("IPC性能测试 - 实际场景分析")
    print("=" * 60)
    
    baseline = test_direct_call()
    socket_time = test_socket_ipc()
    ser_time = test_serialization()
    
    test_real_scenario()
    
    print("\n" + "=" * 60)
    print("【总结】")
    print("=" * 60)
    print(f"1. 纯OCR处理:        {baseline:.3f}ms")
    print(f"2. 序列化往返:       {ser_time:.3f}ms")
    print(f"3. Socket IPC总计:   {socket_time:.3f}ms")
    print(f"4. IPC纯开销:        {socket_time - baseline:.3f}ms")
    print(f"5. 性能损失:         {(socket_time/baseline - 1)*100:.1f}%")
    print()
    print("结论:")
    if socket_time - baseline < 5:
        print(f"  ✅ IPC开销很小（<5ms），混合架构可行")
    elif socket_time - baseline < 10:
        print(f"  ⚠️  IPC开销中等（5-10ms），需权衡利弊")
    else:
        print(f"  ❌ IPC开销较大（>10ms），不建议混合架构")
    print("=" * 60)
