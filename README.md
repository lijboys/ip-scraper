# IP 地址采集与筛选工具

本工具通过 GitHub Actions 定时从多个网页采集 IP 地址，对第一个网页的 IP 按速度筛选出最优 5 个，第二个网页的 IP 全部采集，并为所有 IP 添加国家代码，最终保存到文件中。

## 功能特点

- **多源采集**：同时从两个不同结构的网页采集 IP 地址
  - 第一个网页：从表格中提取 IP 及速度信息，筛选速度最快的 5 个（示例网址：`https://example.com/ip-source1`）
  - 第二个网页：直接提取纯文本格式的所有 IP（示例网址：`https://example.com/ip-source2`）
- **国家代码标注**：为所有采集到的 IP 标注国家代码（如 `CN`、`US`）
- **自动定时执行**：通过 GitHub Actions 实现每 4 小时自动运行
- **结果合并保存**：将两个网页的结果合并保存到 `89.txt` 文件

## 目录结构

```
.
├── ip_scraper.py       # 核心脚本，负责 IP 采集与处理
├── 89.txt              # 保存最终 IP 结果的文件
└── .github/
    └── workflows/
        └── ip-scraper.yml  # GitHub Actions 配置文件
```

## 使用方法

### 部署步骤

1. **Fork 仓库**：点击右上角 "Fork" 按钮，将本仓库复制到你的 GitHub 账号下

2. **启用 GitHub Actions**：
   - 进入你的仓库页面
   - 点击 "Actions" 标签
   - 点击 "Enable workflows" 按钮启用工作流

3. **查看结果**：
   - 每次执行后，IP 地址会保存在 `89.txt` 文件中
   - 执行日志可在 GitHub Actions 运行记录中查看

### 配置说明

#### 1. 采集网页配置

在 `ip_scraper.py` 中可修改采集的网页 URL（示例为虚构地址，需替换为真实网址）：

```python
html_url = "https://example.com/ip-source1"  # 第一个网页，含 IP 速度信息
text_url = "https://example.com/ip-source2"  # 第二个网页，纯文本 IP
```

#### 2. 定时执行频率

在 `.github/workflows/ip-scraper.yml` 中修改 cron 表达式（示例为每 4 小时执行一次）：

```yaml
on:
  schedule:
    - cron: '0 */4 * * *'  # 每 4 小时执行一次
```

## 结果格式说明

`89.txt` 文件中包含两部分内容：

1. **第一个网页的最优 5 个 IP**（带速度信息，示例 IP 为虚构）：
   ```
   192.168.1.100#US-25.50MB/s
   192.168.1.101#US-24.80MB/s
   192.168.1.102#CA-23.70MB/s
   192.168.1.103#DE-22.90MB/s
   192.168.1.104#UK-21.50MB/s
   ```

2. **第二个网页的所有 IP**（只有国家代码，示例 IP 为虚构）：
   ```
   10.0.0.1#CN
   10.0.0.2#JP
   10.0.0.3#KR
   10.0.0.4#FR
   10.0.0.5#IT
   ```

## 技术实现

### 核心逻辑

1. **IP 采集**：
   - 第一个网页：使用 BeautifulSoup 解析 HTML 表格，提取 IP 和速度
   - 第二个网页：直接读取纯文本内容，按行分割获取 IP

2. **速度筛选**：
   - 将速度单位统一转换为 KB/s 进行比较
   - 按速度从快到慢排序，取前 5 个

3. **国家代码获取**：
   - 调用 `ipinfo.io` API 查询 IP 所属国家代码
   - 查询失败时默认返回 `XX`

### 依赖环境

- Python 3.10+
- 第三方库：`requests`, `beautifulsoup4`

## Telegram 通知功能

### 配置方法

1. **创建 Telegram Bot**：
   - 搜索 @BotFather 并发送 `/newbot`
   - 创建 Bot 后获取 API Token（示例：`123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`）

2. **获取聊天 ID**：
   - 搜索 @getchatid_echo_bot 并发送任意消息
   - 机器人会回复你的聊天 ID（示例：`123456789`）

3. **配置仓库秘密**：
   - 在仓库 Settings → Secrets 中添加：
     - `TELEGRAM_BOT_TOKEN`：Bot 的 API Token
     - `TELEGRAM_CHAT_ID`：你的聊天 ID

### 通知效果示例

#### 文本通知内容（示例时间与项目为虚构）：
```
⏰ 2023-01-01 12:00:00

开始运行 *IP采集工具* 项目脚本，对以下网页解析：
1. https://example.com/ip-source1
2. https://example.com/ip-source2

已获取优选IP并保存到文件：`89.txt`
```

#### 附件：
- `89.txt` 文件会作为附件显示在通知下方

## 常见问题

### 1. 国家代码查询失败

- **原因**：`ipinfo.io` 免费 API 有每日请求限制（约 1000 次）
- **解决方案**：可注册账号获取付费 API 密钥，或更换为其他 IP 地理位置查询服务

### 2. 网页结构变化导致采集失败

- **原因**：目标网页的 HTML 结构发生变化
- **解决方案**：修改 `ip_scraper.py` 中的解析逻辑，适配新的网页结构

### 3. GitHub Actions 执行失败

- **原因**：可能是权限问题或依赖安装失败
- **解决方案**：
  - 确保仓库有写入权限
  - 检查 `ip-scraper.yml` 配置是否正确
  - 查看 Actions 运行日志，排查具体错误

## 许可证

本项目采用 MIT 许可证，详情见 LICENSE 文件。

## Stars 增长趋势

以下是本项目 Stars 数量随时间的变化趋势（自动更新）：

![Stars 增长趋势](https://starchart.cc/lijboys/ip-scraper.svg)

> 注：将 `fakeusername/fake-repo-name` 替换为你的 GitHub 用户名和仓库名，即可显示真实数据。例如：`https://starchart.cc/yourusername/your-repo.svg`。该图表由 [starchart.cc](https://starchart.cc/) 自动生成并更新。
