import requests
from bs4 import BeautifulSoup
import os
import re
import concurrent.futures
import time
import datetime  # 新增：用于时区处理
import random

def get_ip_country_code(ip):
    """查询IP所属国家代码"""
    try:
        url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("country", "XX")
    except:
        return "XX"

def fetch_html_ips_with_speed(url):
    """提取网页中的IP和速度信息"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            print(f"❌ {url} 未找到表格")
            return []
        
        # 根据域名选择列索引
        if "cf.090227.xyz" in url:
            ip_col, speed_col = 1, 4
        elif "ip.164746.xyz" in url:
            ip_col, speed_col = 0, 5
        else:
            ip_col, speed_col = 0, 5
            
        ip_data = []
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) <= max(ip_col, speed_col):
                continue
                
            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', cols[ip_col].text)
            if not ip_match:
                continue
                
            speed = cols[speed_col].text.strip()
            if re.search(r'\d+\.\d+\s*(MB|KB)/s', speed):
                ip_data.append((ip_match.group(1), speed))
                
        return sorted(ip_data, key=lambda x: parse_speed(x[1]), reverse=True)[:5]
        
    except Exception as e:
        print(f"❌ {url} 处理错误: {str(e)}")
        return []

def fetch_text_ips(url):
    """提取文本网页中的IP"""
    try:
        response = requests.get(url, timeout=15)
        return [line.strip() for line in response.text.split('\n') 
                if line.strip() and re.match(r'^\d+\.\d+\.\d+\.\d+$', line.strip())]
    except:
        return []

def parse_speed(speed_str):
    """解析速度字符串"""
    match = re.search(r'(\d+\.\d+)\s*(MB|KB)/s', speed_str)
    if match:
        value = float(match.group(1))
        return value * 1024 if match.group(2) == 'MB' else value
    return 0

def send_telegram_combined_message(bot_token, chat_id, caption, file_path):
    """将文本说明作为文件的caption一起发送"""
    if not all([bot_token, chat_id, file_path, os.path.exists(file_path)]):
        print("⚠️ 缺少必要参数或文件不存在，无法发送通知")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        
        with open(file_path, 'rb') as f:
            files = {'document': (os.path.basename(file_path), f)}
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, files=files, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                print("✅ 文本和文件已合并发送成功")
                return True
            else:
                print(f"❌ API返回错误: {result.get('description')}")
                return False
                
    except Exception as e:
        print(f"❌ 发送失败: {str(e)}")
        return False

def get_china_time():
    """获取中国标准时间(UTC+8)"""
    # 计算UTC时间与北京时间的时差（+8小时）
    utc_now = datetime.datetime.utcnow()
    china_time = utc_now + datetime.timedelta(hours=8)
    # 格式化输出：年-月-日 时:分:秒
    return china_time.strftime("%Y-%m-%d %H:%M:%S")

def extract_fastest_ips():
    """主函数"""
    speed_urls = [
        "https://ip.164746.xyz/",
        "https://cf.090227.xyz/"
    ]
    text_url = "https://ipdb.api.030101.xyz/?type=bestcf&country=true"
    
    # 采集IP，区分来源
    speed_ips_dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(fetch_html_ips_with_speed, speed_urls))
        for url, ips in zip(speed_urls, results):
            speed_ips_dict[url] = ips
    text_ips = fetch_text_ips(text_url)
    
    # 保存结果
    all_ips = []
    for url in speed_urls:
        all_ips += [f"{ip}#{get_ip_country_code(ip)}-{speed}" for ip, speed in speed_ips_dict[url]]
    all_ips += [f"{ip}#{get_ip_country_code(ip)}" for ip in text_ips]
    
    file_path = '89.txt'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_ips))
    print(f"✅ 已保存 {len(all_ips)} 个IP到 {file_path}")
    
    # 生成合并发送的文本内容
    caption = "IP采集结果：\n"
    for i, url in enumerate(speed_urls, 1):
        count = len(speed_ips_dict[url])
        caption += f"{i}. {url}：{count}个IP\n"
    caption += f"{len(speed_urls)+1}. {text_url}：{len(text_ips)}个IP\n"
    caption += f"\n总计：{len(all_ips)}个IP\n"
    
    # GitHub Raw地址
    caption += "https://raw.githubusercontent.com/lijboys/ip-scraper/refs/heads/main/89.txt\n"
    
    # 空行分隔
    caption += "\n"
    
    # 中国时间戳（关键修改）
    caption += f"⏰ {get_china_time()}"
    
    # 发送合并消息
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    send_telegram_combined_message(bot_token, chat_id, caption, file_path)

if __name__ == "__main__":
    print("===== 开始执行IP采集任务 =====")
    extract_fastest_ips()
    print("===== 任务执行完毕 =====")
    
