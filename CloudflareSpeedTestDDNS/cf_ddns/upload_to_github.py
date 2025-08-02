import requests
import base64
from datetime import datetime
import os

# 配置文件路径
config_path = '/pac/config.conf'

# 初始化变量
github_token = None
github_repo = None
bot_token = None
chat_id = None

try:
    # 打开配置文件，逐行读取并处理
    with open(config_path, 'r') as file:
        for line in file:
            # 去除行两端的空白字符（空格、制表符、换行符等）
            line = line.strip()
            
            # 跳过空行和注释行（以#开头的行）
            if not line or line.startswith('#'):
                continue
            
            # 解析键值对
            key, value = line.split('=', 1)
            
            # 去除键和值两端的空白字符
            key = key.strip()
            value = value.strip()
            
            # 根据键设置相应的变量
            if key == 'github_token':
                github_token = value
            elif key == 'github_repo':
                github_repo = value
            elif key == 'telegramBotToken':
                bot_token = value
            elif key == 'telegramBotUserId':
                chat_id = value

    # 如果需要通过环境变量覆盖配置文件中的值，可以在这里进行处理
    github_token = os.getenv('github_token') or github_token
    github_repo = os.getenv('github_repo') or github_repo
    bot_token = os.getenv('bot_token') or bot_token
    chat_id = os.getenv('chat_id') or chat_id

except Exception as e:
    print(f"Error reading configuration: {e}")

# 获取当前脚本的绝对路径
script_path = os.path.abspath(__file__)

# 获取脚本所在目录的路径
script_dir_path = os.path.dirname(script_path)

# 获取脚本所在目录的上一级目录的路径
parent_dir_path = os.path.dirname(script_dir_path)

# 获取脚本所在的上一级目录的名称 (例如: "ceshi" 或 "pa")
parent_dir_name = os.path.basename(parent_dir_path)

# 根据上一级目录名称生成 GitHub 中的目标文件名
github_file_name = f"{parent_dir_name}_ip"  # GitHub 仓库中的文件名

# 构造本地文件路径，假设与脚本在同一目录
local_file_path = os.path.join(script_dir_path, 'ips.txt')  # 本地文件路径

# 提交信息使用脚本路径作为 Commit message
commit_message = f"Update IPs from script {script_path}"

# 获取当前时间
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 从 result.csv 中提取内容并写入 ips.txt
result_csv_path = os.path.join(script_dir_path, 'result.csv')
try:
    with open(result_csv_path, 'r') as csv_file:
        lines = csv_file.readlines()
        with open(local_file_path, 'w') as ips_file:
            for line in lines[1:]:  # 跳过标题行
                ip = line.split(',')[0]  # 仅提取逗号前的IP地址
                ips_file.write(ip + '\n')
except FileNotFoundError:
    print(f"File not found: {result_csv_path}")
except Exception as e:
    print(f"An error occurred while processing result.csv: {e}")

# 定义 Telegram 发送文件和消息的函数
def send_to_telegram(file_path, message):
    try:
        # 构造 Telegram API 请求
        telegram_url = f'https://api.telegram.org/bot{bot_token}/sendDocument'
        with open(file_path, 'rb') as file:
            files = {'document': (github_file_name, file)}  # 设置文件名为 github_file_name
            payload = {
                'chat_id': chat_id,
                'caption': message,
            }
            response = requests.post(telegram_url, files=files, data=payload)
            response.raise_for_status()  # 检查响应状态码
            print("File and message successfully sent to Telegram")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send file and message to Telegram: {e}")

# 获取文件的 SHA 值
def get_file_sha(repo, path, token):
    try:
        url = f"https://api.github.com/repos/{repo}/contents/{path}"
        headers = {'Authorization': f'token {token}'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查响应状态码
        return response.json().get('sha')
    except requests.exceptions.RequestException as e:
        print(f"Failed to get SHA from GitHub: {e}")
        return None

# 上传文件到 GitHub，并发送到 Telegram
def upload_to_github_and_telegram(file_path, message):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        github_file_path = github_file_name  # GitHub 中的文件路径，只是文件名
        sha = get_file_sha(github_repo, github_file_path, github_token)
        url = f'https://api.github.com/repos/{github_repo}/contents/{github_file_path}'
        headers = {
            'Authorization': f'token {github_token}',
            'Content-Type': 'application/json'
        }
        data = {
            'message': message,
            'content': base64.b64encode(content.encode()).decode('utf-8'),
            'sha': sha if sha else None  # 添加 sha 值，如果文件存在则用于覆盖
        }
        response = requests.put(url, json=data, headers=headers)
        response.raise_for_status()  # 检查响应状态码
        if response.status_code in (201, 200):
            success_message = f"❇️上传优选IP到Github脚本执行完毕\n❇执行时间：{current_time} \n❇文件 {github_file_name} 已成功上传到 GitHub 仓库 {github_repo} 中"
            print(success_message)
            send_to_telegram(file_path, success_message)  # 发送成功信息到 Telegram
        else:
            error_message = f"❇️上传优选IP到Github脚本执行完毕\n❇执行时间：{current_time} \n❇文件 {github_file_name} 上传到 GitHub 仓库 {github_repo} 失败. HTTP 状态码: {response.status_code}"
            print(error_message)
            send_to_telegram(file_path, error_message)  # 发送失败信息到 Telegram
    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

# 调用上传到 GitHub 和发送到 Telegram 的函数
upload_to_github_and_telegram(local_file_path, commit_message)
