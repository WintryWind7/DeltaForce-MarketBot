import paddleocr
import pkg_resources

# 正确检查版本的方法
try:
    version = pkg_resources.get_distribution("paddleocr").version
    print(f"PaddleOCR 版本: {version}")
except:
    print("无法获取版本信息")

# 检查PaddlePaddle版本
try:
    import paddle
    print(f"PaddlePaddle 版本: {paddle.__version__}")
except ImportError:
    print("PaddlePaddle 未安装")