# 分发说明

## 📦 给其他用户的安装指南

### **系统要求**
- Windows 64位系统
- Python 3.10 或更高版本（推荐 3.11）

⚠️ **注意：** 
- 如果你的 Python 版本不是 3.11，需要按照"开发者编译指南"重新编译 `.pyd` 文件
- 或者从发布页面下载对应你 Python 版本的 `.pyd` 文件

### **安装步骤**

1. **安装 Python 依赖**
```bash
pip install -r requirements.txt
```

2. **放置 `.pyd` 文件**
将 `window_func.cp311-win_amd64.pyd` 文件放在：
```
DeltaForce-MarketBot/
└── core/
    └── dist/
        └── window_func.cp311-win_amd64.pyd  ← 必须在这里
```

⚠️ **注意：** 必须保持 `core/dist/` 目录结构，不要直接放在根目录

3. **运行程序**
```bash
python main.py
```

---

## 🔧 开发者编译指南

如果你需要重新编译 `.pyx` 文件或适配不同的 Python 版本：

### **1. 安装编译工具**
```bash
pip install cython
```

### **2. 安装 C++ 编译器**
- 下载并安装 [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- 安装时选择 "C++ 生成工具"

### **3. 编译 Cython 扩展**
```bash
cd core
python setup.py build_ext --inplace
```

编译完成后，`.pyd` 文件会生成在 `core/dist/` 目录。

---

## 📋 兼容性说明

- ✅ **当前编译版本：** Python 3.11 + Windows 64位
- ⚠️ **其他 Python 版本：** 需要重新编译
- ⚠️ **Linux/Mac：** 需要重新编译（会生成 `.so` 文件）

---

## ❓ 常见问题

### Q: 提示找不到 `window_func` 模块？
**A:** 
1. 检查文件是否存在：`core/dist/window_func.cp311-win_amd64.pyd`
2. 确认目录结构完整：必须保持 `core/dist/` 路径
3. 如果文件存在但仍报错，可能是 Python 版本不匹配（见下一个问题）

### Q: 我的 Python 版本是 3.10/3.12，可以用吗？
**A:** 
- 当前提供的 `.pyd` 文件是为 Python 3.11 编译的
- **方案1（推荐）：** 重新编译（5分钟，需要 C++ 环境）
  ```bash
  pip install cython
  cd core
  python setup.py build_ext
  ```
- **方案2：** 安装 Python 3.11 并使用
- **方案3：** 联系作者获取对应版本的 `.pyd` 文件

### Q: 可以在 Linux 上运行吗？
**A:** 需要在 Linux 上重新编译，会生成 `.so` 文件而不是 `.pyd` 文件。

