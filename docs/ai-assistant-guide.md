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
