import requests
from bs4 import BeautifulSoup
import os
import re
import concurrent.futures
import datetime
import ipaddress

try:
    import cloudscraper
except ImportError:
    cloudscraper = None

def get_client(use_cloudscraper=False):
    if use_cloudscraper and cloudscraper:
        return cloudscraper.create_scraper(browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        })
    return requests.Session()

def get_ip_country_code(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.version == 6:
            return "IPv6"
        url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("country", "XX")
    except:
        return "XX"

def parse_speed(speed_str):
    if not speed_str:
        return 0
    match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|KB)/s', speed_str, re.I)
    if match:
        value = float(match.group(1))
        unit = match.group(2).upper()
        return value * 1024 if unit == 'MB' else value
    return 0

def parse_latency(latency_str):
    if not latency_str:
        return 999999
    match = re.search(r'(\d+(?:\.\d+)?)\s*毫秒', latency_str)
    if match:
        return float(match.group(1))
    match = re.search(r'(\d+(?:\.\d+)?)\s*ms', latency_str, re.I)
    if match:
        return float(match.group(1))
    return 999999

def fetch_text_ips(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return [line.strip() for line in response.text.split('\n')
                if line.strip() and (
                    re.match(r'^\d+\.\d+\.\d+\.\d+$', line.strip()) or ':' in line.strip()
                )]
    except:
        return []

def fetch_ip164746(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            print(f"❌ {url} 未找到表格")
            return []

        ip_data = []
        for row in table.find_all('tr')[1:]:
            cols = row.find_all('td')
            row_text = [c.get_text(" ", strip=True) for c in cols]

            ip = None
            speed = None
            for text in row_text:
                if not ip:
                    ip_match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', text)
                    if ip_match:
                        ip = ip_match.group(1)

                if not speed:
                    speed_match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|KB)/s', text, re.I)
                    if speed_match:
                        speed = speed_match.group(0)

            if ip and speed:
                ip_data.append((ip, speed))

        return sorted(ip_data, key=lambda x: parse_speed(x[1]), reverse=True)[:5]

    except Exception as e:
        print(f"❌ {url} 处理错误: {str(e)}")
        return []

def fetch_wetest_ips(url):
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.wetest.vip/',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            print(f"❌ {url} 未找到表格")
            return []

        carriers = ["移动", "联通", "电信"]
        grouped = {carrier: [] for carrier in carriers}

        for row in table.find_all('tr')[1:]:
            cols = [td.get_text(" ", strip=True) for td in row.find_all('td')]
            carrier = None
            for c in carriers:
                if any(c in col for col in cols):
                    carrier = c
                    break
            if not carrier:
                continue

            ip = None
            speed = None
            latency = None
            datacenter = None

            for text in cols:
                if not ip:
                    ip_match = re.search(r'((?:\d{1,3}\.){3}\d{1,3}|(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F]{0,4})', text)
                    if ip_match:
                        ip = ip_match.group(1)

                if not speed:
                    speed_match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|KB)/s', text, re.I)
                    if speed_match:
                        speed = speed_match.group(0)

                if not latency:
                    latency_match = re.search(r'(\d+(?:\.\d+)?)\s*(毫秒|ms)', text, re.I)
                    if latency_match:
                        latency = latency_match.group(0)

                if not datacenter:
                    dc_match = re.fullmatch(r'[A-Z]{3}', text.strip())
                    if dc_match:
                        datacenter = dc_match.group(0)

            if ip and latency:
                grouped[carrier].append({
                    "ip": ip,
                    "speed": speed or "0KB/s",
                    "latency": latency,
                    "name": f"{datacenter or 'UNK'}-{carrier}"
                })

        results = []
        for carrier in carriers:
            items = grouped.get(carrier, [])
            if not items:
                continue
            items.sort(key=lambda x: (parse_latency(x["latency"]), -parse_speed(x["speed"])))
            best = items[0]
            results.append((best["ip"], best["name"]))

        return results

    except Exception as e:
        print(f"❌ {url} 处理错误: {str(e)}")
        return []

def fetch_vps789_ips():
    candidate_urls = [
        "https://vps789.com/cfip",
        "https://vps789.com/cfip/",
        "https://vps789.com/cfip/?remarks=ip"
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Referer': 'https://vps789.com/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1'
    }

    clients = []
    if cloudscraper:
        clients.append(("cloudscraper", get_client(True)))
    clients.append(("requests", get_client(False)))

    last_error = None

    for client_name, client in clients:
        for url in candidate_urls:
            try:
                response = client.get(url, headers=headers, timeout=20)
                response.raise_for_status()
                response.encoding = response.apparent_encoding

                soup = BeautifulSoup(response.text, 'html.parser')
                table = soup.find('table')
                if not table:
                    continue

                records = []
                for row in table.find_all('tr')[1:]:
                    cols = [td.get_text(" ", strip=True) for td in row.find_all('td')]
                    if len(cols) < 2:
                        continue

                        # 注意：这里保持你的原样逻辑
                    ip = None
                    speed = None
                    best_latency = 999999

                    for text in cols:
                        if not ip:
                            ip_match = re.search(r'(\d{1,3}(?:\.\d{1,3}){3})', text)
                            if ip_match:
                                ip = ip_match.group(1)

                        speed_match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|KB)/s', text, re.I)
                        if speed_match:
                            speed = speed_match.group(0)

                        for lm in re.findall(r'(\d+(?:\.\d+)?)\s*ms', text, re.I):
                            try:
                                best_latency = min(best_latency, float(lm))
                            except:
                                pass

                    if ip and speed:
                        records.append({
                            "ip": ip,
                            "speed": speed,
                            "latency": f"{int(best_latency)}ms" if best_latency != 999999 else "未知"
                        })

                records.sort(key=lambda x: (parse_latency(x["latency"]), -parse_speed(x["speed"])))
                selected = records[:3]
                if selected:
                    print(f"✅ vps789 使用 {client_name} 成功: {url}")
                    return [(x["ip"], x["speed"], x["latency"]) for x in selected]

            except Exception as e:
                last_error = e
                continue

    print(f"❌ vps789 所有方式都失败: {last_error}")
    if not cloudscraper:
        print("⚠️ 建议安装 cloudscraper 以提升成功率")
    return []

def fetch_hostmonit_ips(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'application/json,text/plain,text/html,*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://stock.hostmonit.com/',
        'Origin': 'https://stock.hostmonit.com'
    }

    clients = []
    if cloudscraper:
        clients.append(get_client(True))
    clients.append(get_client(False))

    last_error = None
    for client in clients:
        try:
            response = client.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            text = response.text.strip()

            records = []

            try:
                data = response.json()
                if isinstance(data, list):
                    for item in data:
                        if not isinstance(item, dict):
                            continue

                        ip = item.get("ip") or item.get("host") or item.get("address") or item.get("ipv4") or item.get("ipv6")
                        speed = str(item.get("download_speed") or item.get("speed") or item.get("avg_speed") or "")
                        latency = str(item.get("latency") or item.get("delay") or item.get("ping") or "")
                        datacenter = item.get("colo") or item.get("datacenter") or item.get("city") or "HM"
                        carrier = item.get("isp") or item.get("carrier") or item.get("line") or "优选"

                        if ip:
                            if re.fullmatch(r'\d+(?:\.\d+)?', speed):
                                speed = f"{speed}KB/s"
                            if re.fullmatch(r'\d+(?:\.\d+)?', latency):
                                latency = f"{latency}ms"

                            records.append({
                                "ip": ip,
                                "speed": speed if speed else "0KB/s",
                                "latency": latency if latency else "999999ms",
                                "name": f"{datacenter}-{carrier}"
                            })
            except:
                pass

            if not records:
                temp = []
                for line in text.splitlines():
                    ip_match = re.search(r'((?:\d{1,3}\.){3}\d{1,3}|(?:[0-9a-fA-F]{0,4}:){2,}[0-9a-fA-F]{0,4})', line)
                    speed_match = re.search(r'(\d+(?:\.\d+)?)\s*(MB|KB)/s', line, re.I)
                    latency_match = re.search(r'(\d+(?:\.\d+)?)\s*(ms|毫秒)', line, re.I)
                    dc_match = re.search(r'\b([A-Z]{3})\b', line)

                    carrier = None
                    for c in ["移动", "联通", "电信"]:
                        if c in line:
                            carrier = c
                            break

                    if ip_match:
                        datacenter = dc_match.group(1) if dc_match else "HM"
                        temp.append({
                            "ip": ip_match.group(1),
                            "speed": speed_match.group(0) if speed_match else "0KB/s",
                            "latency": latency_match.group(0) if latency_match else "999999ms",
                            "name": f"{datacenter}-{carrier or '优选'}"
                        })

                records = temp

            records = [x for x in records if x.get("ip")]
            records.sort(key=lambda x: (parse_latency(x["latency"]), -parse_speed(x["speed"])))
            selected = records[:2]
            if selected:
                return [(x["ip"], x["name"]) for x in selected]

        except Exception as e:
            last_error = e
            continue

    print(f"❌ {url} 处理错误: {str(last_error)}")
    if not cloudscraper:
        print("⚠️ 建议安装 cloudscraper 以提升成功率")
    return []

def send_telegram_combined_message(bot_token, chat_id, caption, file_path):
    if not all([bot_token, chat_id, file_path, os.path.exists(file_path)]):
        print("⚠️ 缺少必要参数或文件不存在，无法发送通知")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': (os.path.basename(file_path), f)}
            data = {
                'chat_id': chat_id,
                'caption': caption[:1024],
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, data=data, files=files, timeout=20)
            response.raise_for_status()
            result = response.json()
            if result.get('ok'):
                print("✅ Telegram 通知发送成功")
                return True
            print(f"❌ Telegram API错误: {result}")
            return False
    except Exception as e:
        print(f"❌ 发送失败: {str(e)}")
        return False

def get_china_time():
    utc_now = datetime.datetime.utcnow()
    china_time = utc_now + datetime.timedelta(hours=8)
    return china_time.strftime("%Y-%m-%d %H:%M:%S")

def extract_fastest_ips():
    normal_speed_url = "https://ip.164746.xyz/"
    wetest_urls = [
        "https://www.wetest.vip/page/cloudflare/address_v4.html",
        "https://www.wetest.vip/page/cloudflare/address_v6.html",
        "https://www.wetest.vip/page/cloudfront/address_v4.html",
        "https://www.wetest.vip/page/cloudfront/address_v6.html",
    ]
    hostmonit_urls = [
        "https://stock.hostmonit.com/CloudFlareYes",
        "https://stock.hostmonit.com/CloudFlareYesV6"
    ]
    text_url = "https://ipdb.api.030101.xyz/?type=bestcf&country=true"

    speed_ips_dict = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_ip164746, normal_speed_url): normal_speed_url,
            executor.submit(fetch_vps789_ips): "vps789"
        }

        for url in wetest_urls:
            futures[executor.submit(fetch_wetest_ips, url)] = url

        for url in hostmonit_urls:
            futures[executor.submit(fetch_hostmonit_ips, url)] = url

        for future in concurrent.futures.as_completed(futures):
            url = futures[future]
            try:
                speed_ips_dict[url] = future.result()
            except Exception as e:
                print(f"❌ {url} 抓取失败: {e}")
                speed_ips_dict[url] = []

    text_ips = fetch_text_ips(text_url)

    all_ips = []

    # 1. ip.164746.xyz 保持原样
    for item in speed_ips_dict.get(normal_speed_url, []):
        ip, speed = item
        all_ips.append(f"{ip}#{get_ip_country_code(ip)}-{speed}")

    # 2. wetest 新增来源：只保留 IP#数据中心-线路
    for url in wetest_urls:
        for item in speed_ips_dict.get(url, []):
            ip, name = item
            all_ips.append(f"{ip}#{name}")

    # 3. vps789 保持原样
    for item in speed_ips_dict.get("vps789", []):
        ip, speed, latency = item
        all_ips.append(f"{ip}#{latency}-{speed}")

    # 4. hostmonit 新增来源：只保留 IP#数据中心-线路
    for url in hostmonit_urls:
        for item in speed_ips_dict.get(url, []):
            ip, name = item
            all_ips.append(f"{ip}#{name}")

    # 5. ipdb.api.030101.xyz 保持原样
    all_ips += [f"{ip}#{get_ip_country_code(ip)}" for ip in text_ips]

    # 去重保序
    seen = set()
    deduped_ips = []
    for line in all_ips:
        ip_only = line.split('#')[0].strip()
        if ip_only not in seen:
            seen.add(ip_only)
            deduped_ips.append(line)

    file_path = '89.txt'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(deduped_ips))
    print(f"✅ 已保存 {len(deduped_ips)} 个IP到 {file_path}")

    # 精简通知
    failed_sources = []

    if len(speed_ips_dict.get(normal_speed_url, [])) == 0:
        failed_sources.append("ip.164746.xyz")

    for url in wetest_urls:
        if len(speed_ips_dict.get(url, [])) == 0:
            failed_sources.append(url.split('/')[-1])

    if len(speed_ips_dict.get("vps789", [])) == 0:
        failed_sources.append("vps789")

    for url in hostmonit_urls:
        if len(speed_ips_dict.get(url, [])) == 0:
            failed_sources.append(url.split('/')[-1])

    if len(text_ips) == 0:
        failed_sources.append("ipdb.api")

    caption = "IP采集完成\n"
    caption += f"总计：{len(deduped_ips)}个IP\n"

    if failed_sources:
        caption += f"异常：{'、'.join(failed_sources)}\n"

    caption += "下载：\n"
    caption += "https://raw.githubusercontent.com/lijboys/ip-scraper/refs/heads/main/89.txt\n"
    caption += f"⏰ {get_china_time()}"

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    send_telegram_combined_message(bot_token, chat_id, caption, file_path)

if __name__ == "__main__":
    print("===== 开始执行IP采集任务 =====")
    extract_fastest_ips()
    print("===== 任务执行完毕 =====")
