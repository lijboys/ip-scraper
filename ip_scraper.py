import requests
from bs4 import BeautifulSoup
import time
import logging
import os
import re
import concurrent.futures

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ip_scraper.log"),
        logging.StreamHandler()
    ]
)

def get_ip_list_from_webpage():
    """从指定网页获取IP地址和速度列表"""
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
            # 以下为示例，假设IP和速度在表格中
            ip_speed_list = []
            # 查找所有包含IP的行
            ip_elements = soup.find_all('tr')
            
            for element in ip_elements:
                # 提取IP地址、端口和速度
                columns = element.find_all('td')
                if len(columns) >= 3:  # 假设第三列是速度信息
                    ip = columns[0].text.strip()
                    port = columns[1].text.strip()
                    speed = columns[2].text.strip()
                    
                    # 验证速度格式是否包含单位
                    if re.search(r'\d+\.?\d*\s*(KB|MB|GB)?/s', speed):
                        ip_speed_list.append((f"{ip}:{port}", speed))
            
            logging.info(f"成功获取{len(ip_speed_list)}个IP地址和速度信息")
            return ip_speed_list
        else:
            logging.error(f"请求失败，状态码: {response.status_code}")
            return []
            
    except Exception as e:
        logging.error(f"发生异常: {str(e)}")
        return []

def parse_speed(speed_str):
    """将速度字符串转换为数值以便排序"""
    try:
        # 提取数值和单位
        match = re.search(r'(\d+\.?\d*)\s*([KMGT]?B)?/s', speed_str)
        if match:
            value = float(match.group(1))
            unit = match.group(2) or 'B'  # 默认单位为B/s
            
            # 转换为相同单位（KB/s）便于比较
            if unit == 'B':
                return value / 1024
            elif unit == 'KB':
                return value
            elif unit == 'MB':
                return value * 1024
            elif unit == 'GB':
                return value * 1024 * 1024
            elif unit == 'TB':
                return value * 1024 * 1024 * 1024
        return 0
    except Exception as e:
        logging.error(f"解析速度失败: {speed_str}, 错误: {str(e)}")
        return 0

def save_top_ips_to_file(ip_speed_list, count=5):
    """将速度最快的前N个IP保存到文件"""
    if not ip_speed_list:
        logging.error("没有可用的IP地址")
        return
    
    # 按速度排序（降序，速度越快越靠前）
    sorted_ips = sorted(ip_speed_list, key=lambda x: parse_speed(x[1]), reverse=True)
    
    # 取前N个
    top_ips = sorted_ips[:count]
    
    # 保存到文件
    try:
        with open("ip.txt", "w") as f:
            for ip, speed in top_ips:
                f.write(f"{ip}#{speed}\n")
        logging.info(f"已保存{len(top_ips)}个最快的IP到文件")
        
        # 打印结果
        print("\n速度最快的IP地址:")
        print("排名\tIP地址\t\t速度")
        for i, (ip, speed) in enumerate(top_ips, 1):
            print(f"{i}\t{ip}\t{speed}")
            
    except Exception as e:
        logging.error(f"保存文件失败: {str(e)}")

def main():
    """主函数，执行IP获取和保存任务"""
    logging.info("IP地址定时获取脚本启动")
    
    # 获取IP和速度列表
    ip_speed_list = get_ip_list_from_webpage()
    
    if ip_speed_list:
        # 保存速度最快的IP
        save_top_ips_to_file(ip_speed_list, 5)
    else:
        logging.error("未能获取到任何IP地址")

if __name__ == "__main__":
    main()    
