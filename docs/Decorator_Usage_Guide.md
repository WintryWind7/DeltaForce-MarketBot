# Delta装饰器使用指南

## 📋 概述

Behavior基类提供了4个装饰器，用于自动注入和验证Delta实例，让代码更加简洁和安全。

## 🎯 可用装饰器

### 1. `@require_any_delta` - 通用装饰器
自动注入任意可用的Delta实例，优先级：单端delta > 主端delta > 辅端delta

```python
@require_any_delta
def get_balance(self, delta):
    """delta参数自动注入，确保可用"""
    balance = delta.get_balance()
    return balance

# 调用时不需要传递delta参数
balance = self.get_balance()
```

### 2. `@require_main_delta` - 主端装饰器
自动注入主端Delta实例（单端模式下就是唯一的delta）

```python
@require_main_delta  
def check_main_balance(self, main_delta):
    """main_delta参数自动注入"""
    balance = main_delta.get_balance()
    self.send_log(LogLevel.INFO, f"主端余额: {balance}")
    return balance

# 调用
balance = self.check_main_balance()
```

### 3. `@require_aux_delta` - 辅端装饰器
自动注入辅端Delta实例（仅双端模式可用）

```python
@require_aux_delta
def refresh_aux_market(self, aux_delta):
    """aux_delta参数自动注入"""
    success = aux_delta.buy_in_market(
        buyin=31, maxin=31, times=1, buy=True, loop=False
    )
    return success

# 调用
success = self.refresh_aux_market()
```

### 4. `@require_dual_delta` - 双端装饰器
自动注入主端和辅端Delta实例（仅双端模式可用）

```python
@require_dual_delta
def coordinate_purchase(self, main_delta, aux_delta):
    """main_delta, aux_delta参数自动注入"""
    # 辅端刷新
    aux_success = aux_delta.buy_in_market(buyin=31, maxin=31, times=1, buy=True, loop=False)
    
    if aux_success:
        # 主端购买
        main_success = main_delta.buy_in_market(buyin=200, maxin=200, times=6, buy=True, loop=False)
        return main_success
    
    return False

# 调用
success = self.coordinate_purchase()
```

## 🔧 装饰器特性

### 自动验证
- 装饰器会自动检查Delta实例是否可用
- 如果实例不可用，会自动记录错误日志并返回`None`
- 无需手动检查`if self.delta:`

### 错误处理
```python
@require_main_delta
def my_operation(self, main_delta):
    # 如果main_delta不可用，这个方法不会被执行
    # 装饰器会自动记录错误并返回None
    return main_delta.get_balance()

# 调用结果
result = self.my_operation()
if result is None:
    # Delta实例不可用或操作失败
    pass
```

### 参数传递
装饰器注入的Delta参数总是在最前面：

```python
@require_main_delta
def operation_with_params(self, main_delta, param1, param2, param3=None):
    # main_delta自动注入
    # param1, param2, param3正常传递
    pass

# 调用时不传递main_delta
self.operation_with_params("value1", "value2", param3="value3")
```

## 📝 实际使用示例

### 单端Behavior示例
```python
class SingleEndBehavior(Behavior):
    
    @require_any_delta
    def check_initial_balance(self, delta):
        """检查初始余额"""
        balance = delta.get_balance()
        if balance is None:
            self.send_log(LogLevel.ERROR, "❌ 无法获取初始余额")
            return False
        
        self.send_log(LogLevel.SUCCESS, f"💰 初始余额: {balance:,}")
        return True
    
    @require_any_delta
    def perform_purchase(self, delta, quantity):
        """执行购买操作"""
        success = delta.buy_in_market(
            buyin=quantity, maxin=quantity, times=1, buy=True, loop=False
        )
        
        if success:
            self.send_log(LogLevel.SUCCESS, f"✅ 购买成功: {quantity}发")
        else:
            self.send_log(LogLevel.ERROR, f"❌ 购买失败: {quantity}发")
        
        return success
    
    def main_logic(self):
        # 检查初始余额
        if not self.check_initial_balance():
            return False
        
        # 执行购买
        return self.perform_purchase(200)
```

### 双端Behavior示例
```python
class DualEndBehavior(Behavior):
    
    @require_dual_delta
    def initialize_both_ends(self, main_delta, aux_delta):
        """初始化双端"""
        main_balance = main_delta.get_balance()
        aux_balance = aux_delta.get_balance()
        
        if main_balance is None or aux_balance is None:
            return False
        
        self.send_log(LogLevel.INFO, f"💰 主端: {main_balance:,}, 辅端: {aux_balance:,}")
        return True
    
    @require_aux_delta
    def aux_refresh_phase(self, aux_delta):
        """辅端刷新阶段"""
        balance_before = aux_delta.get_balance()
        
        success = aux_delta.buy_in_market(
            buyin=31, maxin=31, times=1, buy=True, loop=False
        )
        
        if success:
            balance_after = aux_delta.get_balance()
            price_diff = balance_before - balance_after
            unit_price = price_diff / 31
            
            self.send_log(LogLevel.INFO, f"🔄 辅端刷新: 单价 {unit_price:.1f}")
            return unit_price
        
        return None
    
    @require_main_delta
    def main_purchase_phase(self, main_delta, target_price):
        """主端购买阶段"""
        if target_price <= 500:  # 目标价格
            success = main_delta.buy_in_market(
                buyin=200, maxin=200, times=6, buy=True, loop=False
            )
            
            if success:
                self.send_log(LogLevel.SUCCESS, f"✅ 主端购买成功: {target_price:.1f}")
            
            return success
        
        return False
    
    def main_logic(self):
        # 初始化双端
        if not self.initialize_both_ends():
            return False
        
        while not self.is_stopped():
            # 辅端刷新
            unit_price = self.aux_refresh_phase()
            if unit_price is None:
                continue
            
            # 主端购买
            if self.main_purchase_phase(unit_price):
                break
            
            self.segmented_sleep(1.0)
        
        return True
```

## ⚠️ 注意事项

1. **装饰器顺序**: Delta装饰器应该是最外层的装饰器
2. **参数位置**: 注入的Delta参数总是在方法参数的最前面
3. **返回值**: 如果Delta实例不可用，装饰器会返回`None`
4. **异常处理**: 装饰器只处理Delta实例验证，方法内的异常需要自行处理
5. **性能**: 装饰器会在每次调用时检查Delta实例状态，开销很小

## 🎯 最佳实践

1. **优先使用装饰器**: 比手动检查`if self.delta:`更安全
2. **合理选择装饰器**: 根据实际需要选择合适的装饰器类型
3. **错误处理**: 检查装饰器方法的返回值是否为`None`
4. **日志记录**: 装饰器会自动记录Delta不可用的错误，无需重复记录
