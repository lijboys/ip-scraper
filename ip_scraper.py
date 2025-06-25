import requests
from bs4 import BeautifulSoup
import os
import re

def get_ip_country(ip):
    """通过 ipinfo.io 接口查询 IP 所属国家"""
    try:
        url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("country", "未知国家")
    except requests.RequestException as e:
        print(f"查询 {ip} 国家信息失败: {e}")
        return "未知国家"

def extract_fastest_ips():
    """从网页提取速度最快的 5 个 IP，按 'ip#国家-速度' 格式保存到 89.txt"""
    url = "https://ip.164746.xyz/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    }
    
    try:
        # 发送请求获取网页内容
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # 抛出 HTTP 错误
        
        # 解析 HTML 表格
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        ip_data = []
        
        # 遍历表格行（跳过表头）
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            if len(cols) >= 6:  # 确保包含 IP 和下载速度列
                # 提取并清理 IP 地址，只保留数字和点
                ip_text = cols[0].text.strip()
                ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', ip_text)
                if not ip_match:
                    continue  # 如果没有匹配到 IP 格式，则跳过此行
                ip = ip_match.group(1)
                
                speed = cols[5].text.strip()  # 下载速度在第 6 列（索引 5）
                
                # 验证速度格式（包含数字和单位）
                if re.search(r'\d+\.\d+\s*(MB|KB)/s', speed):
                    country = get_ip_country(ip)
                    ip_data.append((ip, country, speed))
        
        if not ip_data:
            print("未提取到有效 IP 速度数据")
            return
        
        # 按速度降序排序（MB/s > KB/s，数值大的优先）
        def sort_key(item):
            speed_str = item[2]
            num = float(re.search(r'(\d+\.\d+)', speed_str).group(1))
            unit = re.search(r'([KM]B)/s', speed_str).group(1)
            return num * (1024 if unit == 'MB' else 1)  # MB 转 KB 统一单位比较
        
        top_5 = sorted(ip_data, key=sort_key, reverse=True)[:5]
        
        # 保存到文件
        with open('89.txt', 'w', encoding='utf-8') as f:
            for ip, country, speed in top_5:
                f.write(f"{ip}#{country}-{speed}\n")
        print(f"已成功保存 5 个最快的 IP 地址到 89.txt 文件")
        
        # 打印结果
        print("\n检测到速度最快的 5 个 IP 地址：")
        print("排名\tIP 地址\t\t\t国家\t\t速度")
        print("-" * 50)
        for i, (ip, country, speed) in enumerate(top_5, 1):
            print(f"{i}\t{ip}\t{country}\t{speed}")
        print("-" * 50)
            
    except requests.exceptions.RequestException as e:
        print(f"网络请求失败: {str(e)}")
    except Exception as e:
        print(f"程序运行异常: {str(e)}")

if __name__ == "__main__":
    print("正在执行 IP 速度检测任务...")
    extract_fastest_ips()
    print("任务执行完毕！")
