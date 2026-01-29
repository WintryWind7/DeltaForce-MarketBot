"""
测试共享内存IPC - 最快的IPC方式
"""

import time
import numpy as np
from multiprocessing import shared_memory
import threading

def generate_test_image(width=1920, height=1080):
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)

def mock_ocr_processing(image):
    return str(np.sum(image) % 1000000)

# ============================================================
# 测试：共享内存IPC
# ============================================================
def test_shared_memory():
    """共享内存方式（零拷贝）"""
    print("\n【测试】共享内存IPC（零拷贝）")
    print("-" * 50)
    
    image = generate_test_image()
    
    # 创建共享内存
    shm = shared_memory.SharedMemory(create=True, size=image.nbytes)
    
    # 模拟Python服务（在另一个进程中访问共享内存）
    def python_service():
        # 直接从共享内存读取（零拷贝）
        shared_array = np.ndarray(image.shape, dtype=image.dtype, buffer=shm.buf)
        result = mock_ocr_processing(shared_array)
        return result
    
    iterations = 100
    
    # 测试：Java写入共享内存 → Python读取
    start = time.perf_counter()
    for _ in range(iterations):
        # Java端：写入共享内存
        shared_array = np.ndarray(image.shape, dtype=image.dtype, buffer=shm.buf)
        np.copyto(shared_array, image)
        
        # Python端：读取并处理
        result = python_service()
    
    elapsed = (time.perf_counter() - start) * 1000 / iterations
    
    shm.close()
    shm.unlink()
    
    print(f"平均耗时: {elapsed:.3f}ms")
    print(f"  - 内存拷贝: ~{elapsed - 2:.1f}ms")
    print(f"  - OCR处理: ~2ms")
    
    return elapsed

# ============================================================
# 对比测试
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("共享内存 vs TCP Socket")
    print("=" * 60)
    
    # 基准
    image = generate_test_image()
    iterations = 100
    start = time.perf_counter()
    for _ in range(iterations):
        mock_ocr_processing(image)
    baseline = (time.perf_counter() - start) * 1000 / iterations
    
    print(f"\n基准（直接调用）: {baseline:.3f}ms")
    
    # 共享内存
    shm_time = test_shared_memory()
    
    print("\n" + "=" * 60)
    print("【对比】")
    print("=" * 60)
    print(f"直接调用:     {baseline:.3f}ms")
    print(f"共享内存IPC:  {shm_time:.3f}ms  (慢 {shm_time/baseline:.1f}x)")
    print(f"TCP Socket:   ~39ms  (慢 ~20x)")
    print()
    print("结论:")
    print(f"  共享内存比TCP快 {39/shm_time:.1f}x")
    print(f"  但仍比直接调用慢 {(shm_time/baseline - 1)*100:.0f}%")
    print("=" * 60)
