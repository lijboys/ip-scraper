import requests
from bs4 import BeautifulSoup
import os
import re
import concurrent.futures
import time

def get_ip_country_code(ip):
    """通过ipinfo.io接口查询IP所属国家代码"""
    try:
        url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("country", "XX")  # 默认返回XX表示未知
    except requests.RequestException:
        return "XX"  # 查询失败时返回XX

def fetch_html_ips(url):
    """从HTML表格网页提取速度最快的5个IP"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            print(f"未在{url}中找到表格数据")
            return []
        
        ip_data = []
        for row in table.find_all('tr')[1:]:  # 跳过表头
            cols = row.find_all('td')
            if len(cols) < 6:  # 确保至少有IP和速度列
                continue
                
            # 提取IP地址
            ip_text = cols[0].text.strip()
            ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ip_text)
            if not ip_match:
                continue  # 跳过非IP格式的行
            ip = ip_match.group(1)
            
            # 提取速度（假设在第6列）
            speed = cols[5].text.strip()
            
            # 验证速度格式
            if re.search(r'\d+\.\d+\s*(MB|KB)/s', speed):
                ip_data.append((ip, speed))
        
        # 按速度排序并取前5个
        if ip_data:
            sorted_ips = sorted(ip_data, key=lambda x: parse_speed(x[1]), reverse=True)[:5]
            print(f"从{url}成功获取{len(sorted_ips)}个最快IP")
            return sorted_ips
        else:
            print(f"在{url}中未找到有效IP速度数据")
            return []
        
    except Exception as e:
        print(f"处理HTML网页 {url} 时出错: {str(e)}")
        return []

def fetch_text_ips(url):
    """从纯文本网页提取所有IP（每行一个IP）"""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        # 按行分割并过滤空行
        ip_text = response.text
        ips = [line.strip() for line in ip_text.split('\n') if line.strip()]
        
        print(f"从{url}成功获取{len(ips)}个IP")
        return ips
        
    except Exception as e:
        print(f"处理文本网页 {url} 时出错: {str(e)}")
        return []

def parse_speed(speed_str):
    """将速度字符串转换为数值以便排序"""
    try:
        match = re.search(r'(\d+\.\d+)\s*(MB|KB)/s', speed_str)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            return value * (1024 if unit == 'MB' else 1)  # 统一转换为KB/s
        return 0
    except:
        return 0

def send_telegram_notification(bot_token, chat_id, message, file_path=None):
    """发送Telegram通知（文件+消息合并发送）"""
    try:
        if not bot_token or not chat_id:
            print("Telegram配置参数缺失，跳过通知")
            return False
            
        # 合并发送文件和消息（通过caption参数）
        if file_path and os.path.exists(file_path):
            file_url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
            with open(file_path, 'rb') as f:
                files = {'document': (os.path.basename(file_path), f)}
                payload = {
                    "chat_id": chat_id,
                    "caption": message,  # 消息作为文件的标题
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                }
                response = requests.post(file_url, data=payload, files=files)
                response.raise_for_status()
                print("Telegram通知发送成功")
                return True
        else:
            # 无文件时仅发送消息（作为备用）
            text_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            response = requests.post(text_url, data=payload)
            response.raise_for_status()
            print("Telegram消息发送成功")
            return True
            
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP错误 {e.response.status_code}: {e.response.text}"
        print(f"Telegram通知发送失败: {error_msg}")
    except Exception as e:
        print(f"Telegram通知发送失败: {str(e)}")
    return False

def extract_fastest_ips():
    """从多个网页提取IP并按要求保存到89.txt"""
    # 定义两个网页（HTML表格和纯文本）
    html_url = "https://ip.164746.xyz/"
    text_url = "https://ipdb.api.030101.xyz/?type=bestcf&country=true"
    
    # 获取第一个网页的前5个最快IP
    html_ips = fetch_html_ips(html_url)
    
    # 获取第二个网页的所有IP
    text_ips = fetch_text_ips(text_url)
    
    # 处理结果
    all_results = []
    
    # 处理第一个网页的IP（格式: ip#国家代码-速度）
    for ip, speed in html_ips:
        country_code = get_ip_country_code(ip)
        all_results.append(f"{ip}#{country_code}-{speed}")
    
    # 处理第二个网页的IP（格式: ip#国家代码）
    for ip in text_ips:
        country_code = get_ip_country_code(ip)
        all_results.append(f"{ip}#{country_code}")
    
    # 保存到文件
    file_path = '89.txt'
    if all_results:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_results))
        print(f"已成功保存{len(all_results)}个IP到{file_path}文件")
        
        # 生成Telegram通知内容
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        project_name = "IP采集与筛选工具"
        webpages = [html_url, text_url]
        file_name = os.path.basename(file_path)
        
        # 格式化通知消息（作为文件的caption）
        message = f"⏰ {timestamp}\n\n"
        message += f"开始运行 *{project_name}* 项目脚本，对以下网页解析：\n"
        for i, url in enumerate(webpages, 1):
            message += f"{i}. {url}\n"
        message += f"\n已获取优选IP并保存到文件：`{file_name}`"
        
        # 发送Telegram通知（文件+消息合并）
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        send_telegram_notification(bot_token, chat_id, message, file_path)
    else:
        print("未从任何网页提取到有效IP")

if __name__ == "__main__":
    print("正在执行IP采集任务...")
    extract_fastest_ips()
    print("任务执行完毕！")
