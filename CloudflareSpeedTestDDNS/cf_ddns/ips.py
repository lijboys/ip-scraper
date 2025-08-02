import requests
import os

# 定义URL和目标文件路径
url = "https://raw.githubusercontent.com/lijboy/CloudflareCDNFission/main/Fission_ip.txt"
script_dir = os.path.dirname(os.path.abspath(__file__))  # 获取脚本所在目录
target_file = os.path.join(script_dir, "ip.txt")  # 使用绝对路径

try:
    # 发送GET请求获取内容
    response = requests.get(url)
    response.raise_for_status()  # 如果请求不成功，将引发异常

    # 获取内容
    content = response.text
    
    # 将内容写入文件
    with open(target_file, 'w', encoding='utf-8') as file:
        file.write(content)
    
    print(f"内容已成功写入 {target_file}")
    
    # 验证文件是否被创建和写入
    if os.path.exists(target_file):
        print(f"文件已成功创建。大小: {os.path.getsize(target_file)} 字节")
    else:
        print("文件未能成功创建")

except requests.RequestException as e:
    print(f"请求错误: {e}")
except IOError as e:
    print(f"IO错误: {e}")
except Exception as e:
    print(f"发生未知错误: {e}")

# 打印文件的绝对路径
print(f"预期的文件保存位置: {target_file}")
