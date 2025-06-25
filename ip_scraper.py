import requests
from bs4 import BeautifulSoup
import time
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ip_scraper.log"),
        logging.StreamHandler()
    ]
)

def get_ip_from_webpage():
    """从指定网页获取IP地址"""
    url = "https://ip.164746.xyz/"
    
    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 发送HTTP请求
        response = requests.get(url, headers=headers, timeout=10)
        
        # 检查响应状态码
        if response.status_code == 200:
            # 使用BeautifulSoup解析HTML内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 这里需要根据网页实际结构调整选择器
            # 以下为示例，假设IP地址在某个具有特定class的元素中
            ip_element = soup.find('div', class_='ip-address')
            
            if ip_element:
                ip_address = ip_element.text.strip()
                logging.info(f"成功获取IP地址: {ip_address}")
                return ip_address
            else:
                logging.error("未在网页中找到IP地址元素")
                return None
        else:
            logging.error(f"请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"发生异常: {str(e)}")
        return None

def save_ip_to_file(ip_address):
    """将IP地址保存到文件"""
    if ip_address:
        try:
            with open("current_ip.txt", "w") as f:
                f.write(ip_address)
            logging.info("IP地址已保存到文件")
        except Exception as e:
            logging.error(f"保存文件失败: {str(e)}")

def main():
    """主函数，定时执行IP获取任务"""
    logging.info("IP地址定时获取脚本启动")
    
    # 首次运行
    ip = get_ip_from_webpage()
    if ip:
        save_ip_to_file(ip)
    
    # 设置定时任务（每4小时执行一次）
    interval = 4 * 60 * 60  # 4小时，单位：秒
    
    while True:
        logging.info(f"等待下一次执行，间隔: {interval/3600}小时")
        time.sleep(interval)
        
        # 执行获取IP任务
        ip = get_ip_from_webpage()
        if ip:
            save_ip_to_file(ip)

if __name__ == "__main__":
    main()    
