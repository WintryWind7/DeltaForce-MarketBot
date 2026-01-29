# Delta实例使用指南

## 📋 概述

Behavior基类现在自动管理Delta实例，根据窗口数量自动选择单端或双端模式。

## 🎯 可用的Delta实例

### 单端模式 (1个窗口)
```python
self.delta          # DeltaForceClass实例，绑定到唯一窗口
self.manager         # None
self.main_delta      # None  
self.auxiliary_delta # None
```

### 双端模式 (2+个窗口)
```python
self.delta           # DeltaForceClass实例，等同于main_delta (兼容性)
self.manager         # DeltaForceManager实例
self.main_delta      # 主端DeltaForceClass实例
self.auxiliary_delta # 辅端DeltaForceClass实例
```

## 🔧 使用方法

### 检查Delta状态
```python
# 检查Delta是否就绪
if self.is_delta_ready():
    # 可以安全使用Delta实例
    pass

# 获取Delta信息
delta_info = self.get_delta_info()
self.send_log(LogLevel.INFO, f"Delta状态: {delta_info}")
```

### 单端操作示例
```python
def main_logic(self):
    if not self.is_delta_ready():
        self.send_log(LogLevel.ERROR, "❌ Delta实例未就绪")
        return False
    
    # 获取余额
    balance = self.delta.get_balance()
    if balance is not None:
        self.send_log(LogLevel.INFO, f"💰 当前余额: {balance:,}")
    
    # 点击操作
    self.delta.click_ratio(0.5, 0.5)  # 点击屏幕中心
    
    # OCR识别
    result = self.delta.recognize(
        (0.1, 0.1), (0.9, 0.9),  # 识别区域
        save=False,
        allow_list=None
    )
    
    return True
```

### 双端操作示例
```python
def main_logic(self):
    if not self.is_delta_ready():
        self.send_log(LogLevel.ERROR, "❌ 双端Delta实例未就绪")
        return False
    
    # 使用管理器切换窗口
    self.manager.focus_main()      # 切换到主端
    main_balance = self.main_delta.get_balance()
    
    self.manager.focus_aux()       # 切换到辅端  
    aux_balance = self.auxiliary_delta.get_balance()
    
    self.send_log(LogLevel.INFO, f"💰 主端余额: {main_balance:,}, 辅端余额: {aux_balance:,}")
    
    # 辅端刷新操作
    self.manager.focus_aux()
    success = self.auxiliary_delta.buy_in_market(
        buyin=31, maxin=31, times=1, buy=True, loop=False
    )
    
    if success:
        # 主端购买操作
        self.manager.focus_main()
        success = self.main_delta.buy_in_market(
            buyin=200, maxin=200, times=6, buy=True, loop=False
        )
    
    return success
```

## ⚠️ 注意事项

1. **线程安全**: Delta操作在主逻辑线程中执行，无需额外同步
2. **异常处理**: Delta操作可能抛出异常，建议使用try-catch
3. **窗口焦点**: 双端模式下记得使用manager切换窗口焦点
4. **资源清理**: Behavior基类会自动清理Delta实例
5. **兼容性**: 双端模式下`self.delta`等同于`self.main_delta`

## 🎮 常用Delta方法

### 基础操作
- `get_balance(where="market", loop=False)` - 获取余额
- `click_ratio(x_ratio, y_ratio)` - 按比例点击
- `focus_window()` - 聚焦窗口

### 购买操作  
- `buy_in_market(buyin, maxin, times, buy, loop)` - 市场购买

### OCR识别
- `recognize(top_left, bottom_right, save, allow_list)` - OCR识别

### 双端管理 (DeltaForceManager)
- `focus_main()` - 切换到主端
- `focus_aux()` - 切换到辅端
- `get_main()` - 获取主端实例
- `get_auxiliary()` - 获取辅端实例
