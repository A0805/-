# -*- coding: utf-8 -*-
"""微博热搜监控脚本：抓取微博热搜 JSON 接口并将结果追加保存到 CSV。"""

import csv
import os
import random
import time
from datetime import datetime

import requests

# 微博热搜 JSON 接口
URL = "https://weibo.com/ajax/side/hotSearch"

# 脚本所在目录（即当前目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Cookie 单独存放在文本文件中，避免修改代码时被误替换或破坏
COOKIE_FILE = os.path.join(SCRIPT_DIR, "weibo_cookie.txt")


def load_cookie():
    """从 weibo_cookie.txt 读取 Cookie；文件不存在或为空时使用占位符。"""
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, "r", encoding="utf-8") as f:
            cookie = f.read().strip()
        if cookie:
            return cookie
    return "YOUR_COOKIE_HERE"


# 请求头：Cookie 从 weibo_cookie.txt 读取
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Cookie": load_cookie(),
    "Referer": "https://weibo.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
}

# CSV 文件路径：保存到脚本所在目录（即当前目录）
CSV_FILE = os.path.join(SCRIPT_DIR, "weibo_data.csv")

# CSV 表头（顺序即写入顺序）
FIELD_NAMES = [
    "抓取时间",
    "HTTP状态码",
    "响应耗时(秒)",
    "内容字节数",
    "热搜第一名",
    "异常类型",
]


def fetch_hot_search():
    """抓取一次微博热搜，返回记录字典。"""
    # 先初始化各字段，保证发生异常时也能完整写入一行数据
    record = {
        "抓取时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "HTTP状态码": "无",
        "响应耗时(秒)": 0.0,
        "内容字节数": "无",
        "热搜第一名": "无",
        "异常类型": "正常",
    }

    start = time.perf_counter()  # 高精度计时，用于计算响应耗时

    try:
        # 发送请求，设置 10 秒超时，避免程序长时间卡住
        response = requests.get(URL, headers=HEADERS, timeout=10)

        # 记录响应耗时（秒，保留 3 位小数）和内容字节大小
        record["响应耗时(秒)"] = round(time.perf_counter() - start, 3)
        record["HTTP状态码"] = response.status_code
        record["内容字节数"] = len(response.content)

        if response.status_code == 200:
            # 解析 JSON，取 realtime 列表第一条的 word 作为热搜第一名
            data = response.json()
            realtime_list = data.get("data", {}).get("realtime", [])
            if realtime_list:
                record["热搜第一名"] = realtime_list[0].get("word", "无")
            else:
                record["热搜第一名"] = "无数据"
            record["异常类型"] = "正常"
        else:
            # 状态码非 200，记录为 HTTP 状态码异常
            record["异常类型"] = f"HTTP状态码异常({response.status_code})"

    except requests.exceptions.Timeout:
        # 请求超时
        record["响应耗时(秒)"] = round(time.perf_counter() - start, 3)
        record["异常类型"] = "Timeout（请求超时）"

    except requests.exceptions.ConnectionError:
        # 网络连接错误，例如断网、DNS 解析失败等
        record["响应耗时(秒)"] = round(time.perf_counter() - start, 3)
        record["异常类型"] = "ConnectionError（连接错误）"

    except Exception as e:
        # 其他异常，例如 JSON 解析失败、字段缺失等
        record["响应耗时(秒)"] = round(time.perf_counter() - start, 3)
        record["异常类型"] = f"{type(e).__name__}: {e}"

    return record


def save_to_csv(record):
    """将一条记录追加写入 CSV；文件不存在或为空时先写入表头。"""
    # 文件不存在或内容为空，说明是首次运行
    file_exists = os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 0

    # utf-8-sig 编码可避免用 Excel 打开时中文乱码
    with open(CSV_FILE, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELD_NAMES)
        if not file_exists:
            writer.writeheader()  # 首次运行写入表头

        writer.writerow(record)


def main():
    """执行一次抓取、保存，并在控制台打印结果。"""
    record = fetch_hot_search()
    save_to_csv(record)

    # 控制台打印本次抓取结果
    print("=" * 40)
    print("本次微博热搜抓取结果：")
    for key, value in record.items():
        print(f"{key}：{value}")
    print(f"数据已追加写入：{CSV_FILE}")
    print("=" * 40)

    # 随机休眠 1~3 秒，模拟真实用户的访问间隔，降低被封风险
    time.sleep(random.uniform(1, 3))


if __name__ == "__main__":
    main()
