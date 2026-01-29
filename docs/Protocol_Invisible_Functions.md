# 协议不可见函数（is_invisible）使用指南

## 📚 概述

在 DeltaProtocol 系统中，现在支持三种函数追踪模式：

| 模式 | 标记 | timing_record | 显示 | 净时间计算 |
|------|------|---------------|------|-----------|
| **普通函数** | 默认 | ✅ 创建 | 根据 debug 模式 | 总时间 - 子函数时间 |
| **底层函数** | `is_base_function = True` | ✅ 创建 | 总是显示 | 总时间 - 子函数时间 |
| **不可见函数** | `is_invisible = True` | ❌ 不创建 | 永不显示 | 耗时融入父函数 |

---

## 🎯 不可见函数的用途

不可见函数适用于：
- ✅ 纯工具类函数（如坐标转换、数据格式化）
- ✅ 非常频繁调用的底层函数
- ✅ 不需要单独追踪的辅助函数
- ✅ 需要使用 protocol 但不想显示在调用链中的函数

---

## 💡 使用示例

### **示例1：坐标转换函数**

```python
@protocol_handler()
def ratio_to_screen_coords(self, protocol, x_ratio, y_ratio):
    """将比例坐标转换为屏幕坐标 - 不可见函数"""
    protocol.is_invisible = True  # 标记为不可见
    
    # 验证坐标范围
    if not (0.0 <= x_ratio <= 1.0 and 0.0 <= y_ratio <= 1.0):
        protocol.error_message = f"坐标超出范围"
        return False
    
    # 执行转换
    screen_x = self.window_left + int(self.window_width * x_ratio)
    screen_y = self.window_top + int(self.window_height * y_ratio)
    
    protocol.screen_x = screen_x
    protocol.screen_y = screen_y
    return True

@protocol_handler()
def move_ratio(self, protocol, x_ratio, y_ratio):
    """移动鼠标到比例坐标位置"""
    # 调用不可见函数
    coords_result = self.ratio_to_screen_coords(x_ratio, y_ratio)
    if not coords_result.success:
        return False
    
    # 执行移动
    pyautogui.moveTo(coords_result.screen_x, coords_result.screen_y)
    return True
```

**调用链显示：**
```
move_ratio: 11ms  ← ratio_to_screen_coords 的 1ms 已融入这里
```

---

### **示例2：数据验证函数**

```python
@protocol_handler()
def _validate_price(self, protocol, price):
    """验证价格范围 - 不可见函数"""
    protocol.is_invisible = True
    
    if price < 0:
        protocol.error_message = "价格不能为负数"
        return False
    
    if price > 999999:
        protocol.error_message = "价格超出最大值"
        return False
    
    protocol.validated_price = price
    return True

@protocol_handler()
def set_price(self, protocol, price):
    """设置价格"""
    # 验证价格
    validate_result = self._validate_price(price)
    if not validate_result.success:
        return False
    
    # 设置价格
    self.current_price = validate_result.validated_price
    return True
```

**调用链显示：**
```
set_price: 5ms  ← _validate_price 不显示，耗时已融入
```

---

## ⚠️ 注意事项

### **1. 仍然可以检查 success**
```python
result = self.ratio_to_screen_coords(0.5, 0.5)
if not result.success:  # ✅ 仍然可以检查
    return False
```

### **2. 仍然可以传递数据**
```python
coords_result = self.ratio_to_screen_coords(x, y)
x_screen = coords_result.screen_x  # ✅ 仍然可以获取数据
y_screen = coords_result.screen_y
```

### **3. 错误会自动传播**
```python
# 不可见函数失败时，父函数也会自动失败
result = self.move_ratio(0.5, 0.5)
# 如果 ratio_to_screen_coords 失败，move_ratio 也会失败
```

### **4. 不要过度使用**
- ❌ 不要将所有函数都标记为 `is_invisible`
- ✅ 只对纯工具类、非常频繁调用的函数使用
- ✅ 业务逻辑函数应该保持可见

---

## 📊 性能对比

### **使用装饰器（可见）：**
```
click_ratio: 0.05ms
└── move_ratio: 10ms
    └── ratio_to_screen_coords: 1ms
```

### **使用装饰器 + is_invisible：**
```
click_ratio: 0.05ms
└── move_ratio: 11ms  ← ratio_to_screen_coords 融入这里
```

### **不使用装饰器（普通函数）：**
```
click_ratio: 0.05ms
└── move_ratio: 11ms  ← 无法使用 protocol 传递数据
```

---

## 🎯 最佳实践

1. **命名约定：** 不可见函数建议以 `_` 开头（如 `_validate`, `_convert`）
2. **标记位置：** 在函数开头立即标记 `protocol.is_invisible = True`
3. **文档注释：** 在函数文档中注明 "不可见函数"
4. **错误处理：** 仍然需要设置 `protocol.error_message` 便于调试

---

## ✅ 总结

`is_invisible` 提供了一种**既能使用 protocol 又不污染调用链**的方式，适合那些频繁调用的工具函数。它让你在保持代码一致性的同时，获得更清晰的性能分析输出。

