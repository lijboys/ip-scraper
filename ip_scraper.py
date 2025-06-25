import requests
from bs4 import BeautifulSoup
import logging
import os
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ip_scraper.log"),
        logging.StreamHandler()
    ]
)

def extract_fastest_ips():
    """从网页提取速度最快的5个IP，按'ip#速度'格式保存到ip.txt"""
    url = "https://ip.164746.xyz/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    try:
        # 发送请求获取网页内容
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # 抛出HTTP错误
        
        # 解析HTML表格
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        ip_data = []
        
        # 遍历表格行（跳过表头）
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) >= 6:  # 确保包含IP和下载速度列
                ip = cols[0].text.strip()
                speed = cols[5].text.strip()  # 下载速度在第6列（索引5）
                
                # 验证速度格式（包含数字和单位）
                if re.search(r'\d+\.\d+\s*(MB|KB)/s', speed):
                    ip_data.append((ip, speed))
        
        if not ip_data:
            logging.error("未提取到有效IP速度数据")
            return
        
        # 按速度降序排序（MB/s > KB/s，数值大的优先）
        def sort_key(item):
            speed_str = item[1]
            num = float(re.search(r'(\d+\.\d+)', speed_str).group(1))
            unit = re.search(r'([KM]B)/s', speed_str).group(1)
            return num * (1024 if unit == 'MB' else 1)  # MB转KB统一单位比较
        
        top_5 = sorted(ip_data, key=sort_key, reverse=True)[:5]
        
        # 保存到文件
        with open('ip.txt', 'w', encoding='utf-8') as f:
            for ip, speed in top_5:
                f.write(f"{ip}#{speed}\n")
        logging.info(f"已成功保存5个最快的IP地址到ip.txt文件")
        
        # 打印结果
        print("\n检测到速度最快的5个IP地址：")
        print("排名\tIP地址\t\t\t速度")
        print("-" * 40)
        for i, (ip, speed) in enumerate(top_5, 1):
            print(f"{i}\t{ip}\t{speed}")
        print("-" * 40)
        print(f"完整结果已保存至: {os.path.abspath('ip.txt')}")
            
    except requests.exceptions.RequestException as e:
        logging.error(f"网络请求失败: {str(e)}")
    except Exception as e:
        logging.error(f"程序运行异常: {str(e)}")

if __name__ == "__main__":
    print("正在执行IP速度检测任务...")
    extract_fastest_ips()
    print("任务执行完毕！")
