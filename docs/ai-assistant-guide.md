# AI助手项目参考指南

## 🚀 运行环境说明

### Windows环境配置
- **操作系统**: Windows 10/11
- **Python环境**: 项目使用虚拟环境 `.venv`
- **激活命令**: `.venv\Scripts\activate` (Windows批处理)

### 正确的运行流程
1. **进入项目根目录**: `C:\Users\22721\Documents\Codes\Github\DeltaForce-MarketBot`
2. **激活虚拟环境**: `.venv\Scripts\activate`
3. **运行项目**: `python main.py`

### 重要提醒
- ❌ **不要直接运行Python代码** - 缺少依赖环境
- ❌ **不要尝试测试导入** - 会因为缺少easyocr等依赖失败
- ✅ **只进行代码分析和修改** - 这是安全且有效的
- ✅ **使用工具读取文件内容** - 理解代码结构

### 依赖说明
项目依赖包括但不限于：
- `easyocr` - OCR文字识别
- `PySide6` - GUI界面
- `pyautogui` - 自动化操作
- `opencv-python` - 图像处理

### 运行命令模板
```bash
# 正确的运行方式（用户环境中）
cd C:\Users\22721\Documents\Codes\Github\DeltaForce-MarketBot
.venv\Scripts\activate
python main.py
```

### AI助手工作原则
1. **只做代码分析和修改**
2. **不尝试运行或测试代码**
3. **通过读取文件理解项目结构**
4. **基于代码逻辑进行推理**

## 📝 编程规范

### Python文件头部规范
- ❌ **禁止添加Shebang行**: 不要写入 `#!/usr/bin/python` 或 `#!/usr/bin/env python` 等
- ❌ **禁止Unix系统头**: Windows环境不需要任何Unix风格的头文件指示
- ✅ **只保留编码声明**: 仅在必要时使用 `# -*- coding: utf-8 -*-`
- ✅ **直接开始模块文档**: 文档字符串应紧跟编码声明

### 正确的文件头格式
```python
# -*- coding: utf-8 -*-
"""
模块功能描述
"""

import sys
import os
# ... 其他代码
```

### 错误的文件头格式
```python
#!/usr/bin/env python3  # ❌ Windows不需要
#!/usr/bin/python       # ❌ Windows不需要
# -*- coding: utf-8 -*-
"""
模块功能描述
"""
```

## 🔍 窗口验证功能

### 新增功能：verify_window_focus()
为了解决窗口聚焦失败导致操作在错误窗口执行的问题，在 `DeltaForceClass` 中新增了窗口验证功能。

### 使用方法
```python
# 在每个关键行为执行前调用验证
if not delta_instance.verify_window_focus():
    print("❌ 窗口验证失败，拒绝执行后续操作")
    return False

# 验证通过后执行实际操作
delta_instance.click_ratio(0.5, 0.5)
```

### 验证流程
1. 尝试聚焦到绑定的窗口
2. 检测当前前台窗口是否为目标窗口
3. 如果不匹配，打印详细调试信息并发送到GUI
4. 返回验证结果（不会重试）

### 已验证的方法
- `get_ammo_price()` - 价格识别
- `click_ratio()` - 坐标点击
- `click_ammo()` - 子弹按钮点击
- `get_balance()` - 余额识别

### 线程安全
`click_ammo_worker` 线程调用 `aux_delta.click_ammo()`，会自动获得窗口验证保护。

### 调试信息示例
```
🔍 [窗口验证] 开始验证窗口聚焦状态 (目标窗口: 123456)
❌ [窗口验证] 窗口聚焦验证失败!
   目标窗口: 123456
   实际前台: 789012
   建议: 检查窗口是否被其他程序覆盖或最小化
```

---
*此文档仅供AI助手参考，确保正确理解项目运行环境*

## ⚠️ 常见错误与避免方法

### 架构理解错误
- ❌ **重新实现已存在的功能**: 不要重新编写已经测试过的窗口句柄获取逻辑
- ❌ **过度抽象**: 不要创建不必要的基类或抽象层，保持代码简洁
- ❌ **破坏现有接口**: 修改代码时要保持与现有调用方式的兼容性

### 窗口句柄处理错误
- ❌ **重复获取句柄**: UI已经通过 `get_deltaforce_processes()` 获取句柄，不要重新实现
- ❌ **错误的方法调用**: 不要调用不存在的方法如 `get_deltaforce_processes()` (应该是UI的方法)
- ✅ **正确做法**: 使用UI传递的句柄，通过 `BehaviorManager` 统一管理

### 方法名错误
- ❌ **假设方法存在**: 调用方法前要确认方法确实存在于对应的类中
- ❌ **混淆不同类的方法**: 不要把UI的方法当作Delta类的方法
- ✅ **正确做法**: 使用 `grep` 工具确认方法名和所属类

### 文件管理错误
- ❌ **创建不必要的文件**: 如 `BaseBehavior` 基类，当统一管理可以在 `BehaviorManager` 中实现时
- ❌ **创建临时测试文件**: 不要创建 `test_*.py` 文件来调试，直接分析代码
- ✅ **正确做法**: 通过 `BehaviorManager` 统一管理所有行为，避免多余的抽象层

### 缩进和语法错误
- ❌ **缩进不一致**: Python对缩进敏感，混用空格和制表符会导致语法错误
- ❌ **复制粘贴时保留多余空格**: 修改代码时要注意缩进对齐
- ✅ **正确做法**: 使用标准的4个空格缩进，检查语法正确性

### 错误示例记录
```python
# ❌ 错误：重新实现已存在的功能
from DeltaForce.DeltaForceWindow import DeltaForceWindow
window_finder = DeltaForceWindow()
window_handles = window_finder.get_deltaforce_processes()  # 方法不存在

# ✅ 正确：使用UI已有的方法
processes = self.get_deltaforce_processes()  # UI类的方法
window_handles = [process['hwnd'] for process in processes]
```

### 最佳实践
1. **先理解现有架构** - 不要急于重构，先理解现有代码的工作原理
2. **最小化改动** - 能修复就不重写，能复用就不创建
3. **保持接口一致** - 修改内部实现时保持外部接口不变
4. **验证方法存在性** - 调用方法前用 `grep` 确认方法确实存在
5. **统一管理原则** - 通过 `BehaviorManager` 统一管理，避免散乱的抽象
