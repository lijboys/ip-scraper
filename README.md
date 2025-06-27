IP 地址采集与筛选工具
 
本工具通过 GitHub Actions 定时从多个网页采集 IP 地址，对第一个网页的 IP 按速度筛选出最优 5 个，第二个网页的 IP 全部采集，并为所有 IP 添加国家代码，最终保存到文件中。
 
功能特点
 
- 多源采集：同时从两个不同结构的网页采集 IP 地址
- 第一个网页：从表格中提取 IP 及速度信息，筛选速度最快的 5 个（示例网址： https://example.com/ip-source1 ）
- 第二个网页：直接提取纯文本格式的所有 IP（示例网址： https://example.com/ip-source2 ）
- 国家代码标注：为所有采集到的 IP 标注国家代码（如  CN 、 US ）
- 自动定时执行：通过 GitHub Actions 实现每 4 小时自动运行
- 结果合并保存：将两个网页的结果合并保存到  89.txt  文件
 
目录结构
 
.
├── ip_scraper.py       # 核心脚本，负责 IP 采集与处理
├── 89.txt              # 保存最终 IP 结果的文件
└── .github/
    └── workflows/
        └── ip-scraper.yml  # GitHub Actions 配置文件
 
 
使用方法
 
部署步骤
 
1. Fork 仓库：点击右上角 "Fork" 按钮，将本仓库复制到你的 GitHub 账号下。
2. 启用 GitHub Actions：
- 进入仓库页面 → 点击 "Actions" 标签 → 点击 "Enable workflows" 启用工作流。
3. 查看结果：
- 每次执行后，IP 地址会保存在  89.txt  中，可在 Actions 运行记录中查看日志。
 
配置说明
 
1. 采集网页配置（修改  ip_scraper.py ）
 
html_url = "https://example.com/ip-source1"  # 含 IP 速度信息的网页（示例）
text_url = "https://example.com/ip-source2"  # 纯文本 IP 网页（示例）
 
 
2. 定时执行频率（修改  .github/workflows/ip-scraper.yml ）
 
on:
  schedule:
    - cron: '0 */4 * * *'  # 每 4 小时执行一次（示例）
 
 
结果格式说明
 
 89.txt  文件内容示例：
 
1. 第一个网页的最优 5 个 IP（带速度）：
192.168.1.100#US-25.5MB/s
192.168.1.101#CA-24.8MB/s
192.168.1.102#DE-23.7MB/s
192.168.1.103#UK-22.9MB/s
192.168.1.104#FR-21.5MB/s
 
2. 第二个网页的所有 IP（仅国家代码）：
10.0.0.1#CN
10.0.0.2#JP
10.0.0.3#KR
10.0.0.4#RU
10.0.0.5#IT
 
 
技术实现
 
核心依赖
 
- Python 3.10+
- 第三方库： requests ,  beautifulsoup4 
 
关键逻辑
 
1. IP 采集：使用 BeautifulSoup 解析 HTML 表格或纯文本内容。
2. 速度筛选：将速度统一转换为 KB/s 后排序，取前 5 个。
3. 国家代码获取：调用  ipinfo.io  API（示例），失败时返回  XX 。
 
Telegram 通知功能
 
配置步骤
 
1. 创建 Bot：
- 搜索 @BotFather，发送  /newbot  创建 Bot，获取 Token（示例： 123456:ABC-DEF1234ghIkl-zyx57W2v1u ）。
2. 获取聊天 ID：
- 搜索 @getchatid_echo_bot，发送消息获取 ID（示例： 123456789 ）。
3. 配置仓库秘密：
- 在仓库  Settings → Secrets  中添加：
-  TELEGRAM_BOT_TOKEN ：填入 Bot 的 Token
-  TELEGRAM_CHAT_ID ：填入你的聊天 ID
 
通知示例
 
⏰ 2023-01-01 12:00:00  
开始运行项目脚本，解析以下网页：  
1. https://example.com/ip-source1  
2. https://example.com/ip-source2  
已保存 IP 到 `89.txt`  
 
 
（附带  89.txt  文件作为附件）
 
常见问题
 
1. 国家代码查询失败：
- 原因：示例 API 有请求限制，实际使用需更换为有效服务。
- 解决方案：注册付费 API 或使用本地 IP 库。
2. 网页结构变化：
- 原因：目标网页 HTML 结构更新（如表格列数变化）。
- 解决方案：修改  ip_scraper.py  中解析表格的列索引（如  cols[0]  改为对应列）。
 
许可证
 
本项目采用 MIT 许可证。
 
注意：README 中的所有网址、IP 地址、Token 均为虚构示例，使用时请替换为真实配置。