import time
from DeltaForce.DeltaForceClass import DeltaForceClass

# 如需绑定窗口，请在此填写正确的窗口句柄（hwnd）
# hwnd = 12345678  # 示例
# delta = DeltaForceClass()
# delta.bind_to_window(hwnd)

def extract_balance_result(result):
    # 提取get_balance返回的余额
    # 兼容protocol对象或直接数字
    if hasattr(result, 'balance'):
        return result.balance
    return result

def main():
    delta = DeltaForceClass()
    print("=============== 31发购买OCR识别延迟测试 ===============")
    # 获取初始余额
    print("[STEP 1] 获取初始余额...")
    bal1_result = delta.get_balance(where="market")
    bal1 = extract_balance_result(bal1_result)
    print("初始余额:", bal1)
    time.sleep(1)

    # 单次购买测试
    print("[STEP 2] 开始一次购买...")
    delta.buy_in_market(31, 200, 1)
    bal2_result = delta.get_balance(where="market")
    bal2 = extract_balance_result(bal2_result)
    print("[Test1] 单次购买 差价:", bal1 - bal2)

    # 连续两次购买测试
    print("[STEP 3] 开始两次购买...")
    delta.buy_in_market(31, 200, 1)
    delta.buy_in_market(31, 200, 1)
    bal3_result = delta.get_balance(where="market")
    bal3 = extract_balance_result(bal3_result)
    print("[Test2] 连续两次购买 差价:", bal1 - bal3)

if __name__ == "__main__":
    main()
