# 协议装饰器使用指南

## 协议装饰器 (自动计时)

```python
from base import protocol_handler

class MyService:
    @protocol_handler()
    def get_balance(self, protocol):
        balance = 64498254
        protocol.balance = balance  # 只允许使用直接赋值
        return True  # 必须返回 True 或 False

# 使用
service = MyService()
protocol = service.get_balance()  # 返回协议实例
print(f"成功: {protocol.success}")  # True
print(f"余额: {protocol.balance}")  # 64498254
```

**重要变化：**
- 函数必须返回 `True` 或 `False`
- 装饰器返回协议实例，不是函数原返回值
- `protocol.success` 根据函数返回值自动设置
- 自动计时和错误处理

## 计时器

```python
from base import Timer

with Timer() as timer:
    # 执行操作
    result = some_function()

print(f"耗时: {timer.elapsed_time:.4f}秒")
```
