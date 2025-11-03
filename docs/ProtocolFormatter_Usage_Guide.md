# ProtocolFormatter 使用指南

`ProtocolFormatter` 用于格式化 `DeltaProtocol` 对象，将性能追踪数据转换为可读的调用链字符串。

---

## 基本用法

```python
from base import ProtocolFormatter

# 创建格式化器
formatter = ProtocolFormatter()

# 格式化 protocol
lines = formatter.format_timing_records(
    protocol,
    title="调用链",
    show_total=True,
    mode="detail"
)

# 打印结果
for line in lines:
    print(line)
```

---

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `protocol` | DeltaProtocol | 必需 | 要格式化的协议对象 |
| `title` | str | `"调用链"` | 标题文本 |
| `show_total` | bool | `True` | 是否显示总执行时间 |
| `mode` | str | `"detail"` | `"detail"` 或 `"simple"` |

---

## 显示模式

### detail 模式（详细）

显示所有函数，包括底层函数。

```
📊 调用链:
  1. get_balance: 5.000ms
    - click_ratio: 0.500ms
      - sleep: 9.000ms
    - screenshot_region: 2.000ms
      - _capture_screenshot_win32api: 8.000ms
    - ocr_readtext: 89.000ms
  总执行时间: 123.500ms
```

### simple 模式（简化）

隐藏底层函数（`is_base_function=True`），时间合并到父函数。

```
📊 调用链:
  1. get_balance: 5.000ms
    - click_ratio: 9.500ms
    - screenshot_region: 10.000ms
    - ocr_readtext: 89.000ms
  总执行时间: 123.500ms
```

---

## 使用示例

### 在 Behavior 类中使用

```python
class MyBehavior(Behavior):
    def __init__(self):
        super().__init__()
        self.formatter = ProtocolFormatter()
    
    def some_operation(self):
        result = self.delta.get_balance(where="market")
        
        mode = "simple" if self.debug_mode == 1 else "detail"
        
        lines = self.formatter.format_timing_records(
            result,
            title=f"余额获取 (余额: {result.balance})",
            mode=mode
        )
        
        for line in lines:
            self.debug_log(LogLevel.INFO, line)
```

### 根据调试级别选择模式

```python
# debug_mode = 1: 简化模式
# debug_mode = 2: 详细模式

if self.debug_mode > 0:
    mode = "simple" if self.debug_mode == 1 else "detail"
    lines = self.formatter.format_timing_records(protocol, mode=mode)
    for line in lines:
        self.debug_log(LogLevel.INFO, line)
```

### 自定义标题

```python
lines = formatter.format_timing_records(
    protocol,
    title="第3次刷新操作",
    show_total=False,
    mode="simple"
)
```

---

## 输出格式

- **顶层函数**: `1. function_name: 5.000ms`
- **子函数**: `  - function_name: 10.000ms`
- **嵌套子函数**: `    - function_name: 2.000ms`
- **总时间**: `总执行时间: 123.500ms`

**时间说明**:
- 每个函数显示的是**自身耗时**（不包括子函数）
- 总执行时间是所有顶层函数的总耗时（包括所有子函数）

---

## 最佳实践

```python
# 在 __init__ 中初始化一次
self.formatter = ProtocolFormatter()

# 在需要的地方复用
lines = self.formatter.format_timing_records(protocol, mode="simple")
```

