import requests
from bs4 import BeautifulSoup
import os
import re
import concurrent.futures
import time
import random

def get_ip_country_code(ip):
    """通过ipinfo.io接口查询IP所属国家代码"""
    try:
        url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("country", "XX")  # 默认返回XX表示未知
    except requests.RequestException as e:
        print(f"查询IP {ip} 国家代码失败: {str(e)}")
        return "XX"

def fetch_html_ips_with_speed(url):
    """从HTML表格网页提取速度最快的5个IP（针对不同网页结构优化）"""
    # 增强请求头，模拟真实浏览器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        # 发送请求并处理可能的编码问题
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding  # 自动识别编码
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            print(f"❌ {url} 中未找到表格，可能网页结构变化")
            return []
        
        ip_data = []
        rows = table.find_all('tr')[1:]  # 跳过表头
        if not rows:
            print(f"❌ {url} 表格中无数据行")
            return []
        
        # 根据网页URL选择对应的列索引（精确适配）
        if "cf.090227.xyz" in url:
            # 从截图可知：IP在第2列（索引1），速度在第5列（索引4）
            ip_col_index = 1
            speed_col_index = 4
            print(f"ℹ️ 检测到cf.090227.xyz，使用专用列索引规则：IP列={ip_col_index}，速度列={speed_col_index}")
        elif "ip.164746.xyz" in url:
            # 假设原网页IP在第1列，速度在第6列
            ip_col_index = 0
            speed_col_index = 5
            print(f"ℹ️ 检测到ip.164746.xyz，使用专用列索引规则：IP列={ip_col_index}，速度列={speed_col_index}")
        else:
            # 默认规则（备用）
            ip_col_index = 0
            speed_col_index = 5
            print(f"ℹ️ 使用默认列索引规则：IP列={ip_col_index}，速度列={speed_col_index}")
        
        # 提取IP和速度数据
        for row in rows:
            cols = row.find_all('td')
            # 确保列数足够
            if len(cols) <= max(ip_col_index, speed_col_index):
                continue
            
            # 提取IP地址
            ip_text = cols[ip_col_index].text.strip()
            ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ip_text)
            if not ip_match:
                continue  # 跳过非IP格式
            ip = ip_match.group(1)
            
            # 提取速度信息
            speed = cols[speed_col_index].text.strip()
            if re.search(r'\d+\.\d+\s*(MB|KB)/s', speed):
                ip_data.append((ip, speed))
        
        if not ip_data:
            print(f"❌ {url} 未提取到有效IP和速度数据")
            return []
        
        # 按速度排序并取前5个
        sorted_ips = sorted(ip_data, key=lambda x: parse_speed(x[1]), reverse=True)[:5]
        print(f"✅ {url} 成功提取5个最快IP")
        return sorted_ips
        
    except requests.RequestException as e:
        print(f"❌ 请求 {url} 失败: {str(e)}（可能被拦截或网络问题）")
    except Exception as e:
        print(f"❌ 处理 {url} 时出错: {str(e)}")
    return []

def fetch_text_ips(url):
    """从纯文本网页提取所有IP"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        ips = [line.strip() for line in response.text.split('\n') if line.strip() and re.match(r'^\d+\.\d+\.\d+\.\d+$', line.strip())]
        print(f"✅ {url} 提取到 {len(ips)} 个IP")
        return ips
    except Exception as e:
        print(f"❌ 处理文本网页 {url} 时出错: {str(e)}")
        return []

def parse_speed(speed_str):
    """解析速度字符串为数值"""
    try:
        match = re.search(r'(\d+\.\d+)\s*(MB|KB)/s', speed_str)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            return value * (1024 if unit == 'MB' else 1)
        return 0
    except:
        return 0

def send_telegram_notification(bot_token, chat_id, message, file_path=None):
    """发送Telegram通知"""
    if not bot_token or not chat_id:
        print("⚠️ Telegram配置缺失，跳过通知")
        return False
    
    try:
        # 先发送文本消息
        text_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        response = requests.post(text_url, data=payload, timeout=15)
        response.raise_for_status()
        print("✅ Telegram文本消息发送成功")
        
        # 等待后发送文件
        if file_path and os.path.exists(file_path):
            time.sleep(random.uniform(1, 2))
            file_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            with open(file_path, 'rb') as f:
                files = {'document': (os.path.basename(file_path), f)}
                response = requests.post(file_url, data={"chat_id": chat_id}, files=files, timeout=15)
                response.raise_for_status()
            print("✅ Telegram文件发送成功")
        return True
    except Exception as e:
        print(f"❌ Telegram发送失败: {str(e)}")
        return False

def extract_fastest_ips():
    """主函数：采集并处理所有IP"""
    # 配置网页
    speed_urls = [
        "https://ip.164746.xyz/",
        "https://cf.090227.xyz/"  # 重点适配此网页
    ]
    text_url = "https://ipdb.api.030101.xyz/?type=bestcf&country=true"
    
    # 采集带速度的IP（并发处理）
    speed_ips_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(fetch_html_ips_with_speed, speed_urls))
        for i, result in enumerate(results):
            if not result:
                print(f"⚠️ {speed_urls[i]} 未返回有效数据，已跳过")
            speed_ips_list.extend(result)
    
    # 采集纯文本IP
    text_ips = fetch_text_ips(text_url)
    
    # 处理结果
    all_results = []
    # 处理带速度的IP
    for ip, speed in speed_ips_list:
        country_code = get_ip_country_code(ip)
        all_results.append(f"{ip}#{country_code}-{speed}")
    # 处理纯文本IP
    for ip in text_ips:
        country_code = get_ip_country_code(ip)
        all_results.append(f"{ip}#{country_code}")
    
    # 保存到文件
    file_path = '89.txt'
    if all_results:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_results))
        print(f"✅ 已保存 {len(all_results)} 个IP到 {file_path}")
    else:
        print("⚠️ 未提取到任何有效IP，不生成文件")
    
    # 生成通知消息
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    message = f"⏰ {timestamp}\n\nIP采集结果：\n"
    for i, url in enumerate(speed_urls, 1):
        count = len([x for x in speed_ips_list if x in [item for sublist in results[i-1:i] for item in sublist]])
        message += f"{i}. {url}：{count}个IP\n"
    message += f"{len(speed_urls)+1}. {text_url}：{len(text_ips)}个IP\n"
    message += f"\n总计：{len(all_results)}个IP"
    
    # 发送Telegram通知
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    send_telegram_notification(bot_token, chat_id, message, file_path if all_results else None)

if __name__ == "__main__":
    print("===== 开始执行IP采集任务 =====")
    extract_fastest_ips()
    print("===== 任务执行完毕 =====")
    
