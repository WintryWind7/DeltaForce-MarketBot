import time
import re
import os
from paddleocr import PaddleOCR
import easyocr

# 测试图片列表
test_images = [
    '2829979.png',
    '2842317.png', 
    '2857185.png',
    '2871693.png',
    '2888991.png'
]

# 字符替换映射 - 常见OCR错误纠正
char_replacements = {
    'O': '0', 'o': '0', 'B': '8',
    'l': '1', 'I': '1', 'i': '1',
    'S': '5', 's': '5',
    'Z': '2', 'z': '2',
    ' ': '', ',': ''  # 移除空格和逗号
}

print("=" * 80)
print("EasyOCR vs PaddleOCR 性能对比测试 (PaddleOCR 3.3.1)")
print("=" * 80)

# ==================== EasyOCR 测试 ====================
print("\n【EasyOCR 测试】")
print("-" * 80)

print("正在初始化 EasyOCR...")
start_time = time.time()
model_dir = os.path.expanduser("~/.EasyOCR/model")
easy_reader = easyocr.Reader(['en'], gpu=True, 
                              model_storage_directory=model_dir, 
                              download_enabled=False)
easy_init_time = time.time() - start_time
print(f"✓ EasyOCR 初始化耗时: {easy_init_time:.4f} 秒")

# 识别测试
easy_results = []
easy_times = []

for img_path in test_images:
    start_time = time.time()
    
    results = easy_reader.readtext(
        img_path,
        allowlist='1234567890,',
        width_ths=0.7,
        height_ths=0.7,
        text_threshold=0.5,
        decoder='greedy'
    )
    
    recognized_text = ''.join([text for _, text, _ in results])
    recognized_text = recognized_text.replace(',', '')
    
    ocr_time = time.time() - start_time
    easy_times.append(ocr_time)
    easy_results.append(recognized_text)
    
    print(f"  {img_path}: {recognized_text} ({ocr_time:.4f}秒)")

easy_avg_time = sum(easy_times) / len(easy_times)
print(f"\n✓ EasyOCR 平均识别耗时: {easy_avg_time:.4f} 秒")

# ==================== PaddleOCR 3.3.1 测试 ====================
print("\n【PaddleOCR 测试 (v3.3.1)】")
print("-" * 80)

print("正在初始化 PaddleOCR...")
start_time = time.time()

# PaddleOCR 3.3.1 配置
paddle_ocr = PaddleOCR(
    use_angle_cls=False,  # 不使用文本方向分类
    lang='en'
)

paddle_init_time = time.time() - start_time
print(f"✓ PaddleOCR 初始化耗时: {paddle_init_time:.4f} 秒")

# 识别测试
paddle_results = []
paddle_times = []

for img_path in test_images:
    start_time = time.time()
    
    try:
        # PaddleOCR 3.3.1 - 返回 OCRResult 对象
        result = paddle_ocr.ocr(img_path)
        
        digits_only = ''
        raw_texts = []
        confidences = []
        
        if result and len(result) > 0:
            ocr_result = result[0]  # OCRResult 对象(字典)
            
            # 从 rec_texts 字段提取识别文本
            if 'rec_texts' in ocr_result:
                raw_texts = ocr_result['rec_texts']
                confidences = ocr_result.get('rec_scores', [])
                
                for text in raw_texts:
                    # 使用字符替换映射纠正常见OCR错误
                    cleaned = str(text)
                    for wrong, correct in char_replacements.items():
                        cleaned = cleaned.replace(wrong, correct)
                    
                    # 只保留数字
                    digits = re.sub(r'[^0-9]', '', cleaned)
                    digits_only += digits
        
        # 打印原始识别数据用于分析
        print(f"  {img_path}:")
        print(f"    原始文本: {raw_texts}")
        if confidences:
            print(f"    置信度: {[f'{c:.3f}' for c in confidences]}")
        print(f"    提取数字: {digits_only} ({ocr_time:.4f}秒)")
                    
    except Exception as e:
        print(f"识别错误: {e}")
        import traceback
        traceback.print_exc()
        digits_only = ''
    
    ocr_time = time.time() - start_time
    paddle_times.append(ocr_time)
    paddle_results.append(digits_only)

paddle_avg_time = sum(paddle_times) / len(paddle_times)
print(f"\n✓ PaddleOCR 平均识别耗时: {paddle_avg_time:.4f} 秒")

# ==================== 对比结果 ====================
print("\n" + "=" * 80)
print("对比结果")
print("=" * 80)

print(f"\n【初始化时间对比】")
print(f"  EasyOCR:   {easy_init_time:.4f} 秒")
print(f"  PaddleOCR: {paddle_init_time:.4f} 秒")
print(f"  差异: {abs(easy_init_time - paddle_init_time):.4f} 秒 ", end="")
if paddle_init_time < easy_init_time:
    print(f"(PaddleOCR 快 {easy_init_time/paddle_init_time:.2f}x)")
else:
    print(f"(EasyOCR 快 {paddle_init_time/easy_init_time:.2f}x)")

print(f"\n【平均识别时间对比】")
print(f"  EasyOCR:   {easy_avg_time:.4f} 秒")
print(f"  PaddleOCR: {paddle_avg_time:.4f} 秒")
print(f"  差异: {abs(easy_avg_time - paddle_avg_time):.4f} 秒 ", end="")
if paddle_avg_time < easy_avg_time:
    print(f"(PaddleOCR 快 {easy_avg_time/paddle_avg_time:.2f}x)")
else:
    print(f"(EasyOCR 快 {paddle_avg_time/easy_avg_time:.2f}x)")

print(f"\n【识别结果对比】")
match_count = 0
for i, img_path in enumerate(test_images):
    match = "✓" if easy_results[i] == paddle_results[i] else "✗"
    if easy_results[i] == paddle_results[i]:
        match_count += 1
    print(f"  {img_path}:")
    print(f"    EasyOCR:   {easy_results[i]}")
    print(f"    PaddleOCR: {paddle_results[i]} {match}")

print(f"\n一致性: {match_count}/{len(test_images)} ({match_count/len(test_images)*100:.1f}%)")

print("\n" + "=" * 80)