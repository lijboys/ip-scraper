# GitHub Actions IP地址定时获取脚本

这个项目使用GitHub Actions定时从指定网页抓取IP地址信息，并自动更新到仓库中。无需服务器，完全免费使用！

## 功能特点

- 每4小时自动运行一次（可自定义频率）
- 从指定网页提取IP地址信息
- 自动保存IP地址到文件
- 自动提交更新到GitHub仓库
- 记录详细执行日志，方便排查问题

## 使用方法

### 部署步骤

1. **Fork本仓库**：点击右上角"Fork"按钮，将本仓库复制到你的GitHub账号下

2. **修改配置文件**（可选）：
   - `.github/workflows/ip-scraper.yml`：调整执行频率（默认每4小时一次）
   - `ip_scraper.py`：根据目标网站结构调整IP提取逻辑

3. **启用GitHub Actions**：
   - 进入你的仓库页面
   - 点击"Actions"标签
   - 点击"Enable workflows"按钮启用工作流

4. **查看结果**：
   - 每次执行后，IP地址会保存在`current_ip.txt`文件中
   - 执行日志保存在`ip_scraper.log`文件中

### 自定义设置

1. **调整执行频率**：
   修改`.github/workflows/ip-scraper.yml`文件中的cron表达式：
   ```yaml
   on:
     schedule:
       - cron: '0 */4 * * *'  # 每4小时执行一次
   ```
   例如，修改为`0 */6 * * *`可设置为每6小时执行一次。

2. **修改目标网站**：
   编辑`ip_scraper.py`文件中的URL和解析逻辑：
   ```python
   URL = 'https://ip.164746.xyz/'  # 修改为你想获取IP的网站
   ```

3. **调整日志级别**：
   修改`ip_scraper.py`中的日志配置：
   ```python
   logging.basicConfig(
       filename='ip_scraper.log',
       level=logging.INFO,  # 可调整为DEBUG获取更详细信息
       format='%(asctime)s - %(levelname)s - %(message)s'
   )
   ```

## 文件结构
.github/
└── workflows/
    └── ip-scraper.yml  # GitHub Actions配置文件
ip_scraper.py           # IP地址抓取脚本
current_ip.txt          # 保存最新IP地址
ip_scraper.log          # 执行日志文件
README.md               # 项目说明文档
## 故障排除

1. **查看执行日志**：
   - 进入仓库的"Actions"标签
   - 点击左侧的"IP Scraper"工作流
   - 选择最近一次执行记录
   - 查看详细日志输出

2. **常见问题**：
   - **工作流未运行**：检查是否已启用GitHub Actions，以及cron表达式格式是否正确
   - **IP未更新**：可能目标网站结构发生变化，需要更新解析逻辑
   - **权限错误**：确保仓库设置中允许Actions修改仓库

## 贡献

如果你发现任何问题或有改进建议，请提交Issue或Pull Request。

## 许可证

本项目采用MIT许可证，详情见LICENSE文件。
    
