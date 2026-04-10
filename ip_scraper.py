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
        return cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    return requests.Session()

def get_ip_country_code(ip):
    """ip.164746 和 ipdb.api 专用：查不到就返回 CF"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.version == 6:
            return "IPv6"
        url = f"https://ipinfo.io/{ip}/json"
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        country = response.json().get("country")
        return country if country and country != "XX" else "CF"
    except:
        return "CF"

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
    match = re.search(r'(\d+(?:\.\d+)?)\s*(毫秒|ms)', latency_str, re.I)
    if match:
        return float(match.group(1))
    return 999999

def fetch_text_ips(url):
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return [line.strip() for line in response.text.split('\n')
                if line.strip() and (re.match(r'^\d+\.\d+\.\d+\.\d+$', line.strip()) or ':' in line.strip())]
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
    except:
        return []

def fetch_wetest_ips(url):
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.wetest.vip/', 'Accept-Language': 'zh-CN,zh;q=0.9'}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            return []
        carriers = ["移动", "联通", "电信"]
        grouped = {carrier: [] for carrier in carriers}
        for row in table.find_all('tr')[1:]:
            cols = [td.get_text(" ", strip=True) for td in row.find_all('td')]
            carrier = next((c for c in carriers if any(c in col for col in cols)), None)
            if not carrier:
                continue
            ip = speed = latency = datacenter = None
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
            if items:
                items.sort(key=lambda x: (parse_latency(x["latency"]), -parse_speed(x["speed"])))
                best = items[0]
                results.append((best["ip"], best["name"]))
        return results
    except:
        return []

def fetch_vps789_ips():
    """vps789 双官方API（分开统计计数，两个链接单独显示）"""
    cf_api_ips = []
    cf_top_ips = []

    # 1. cfIpApi
    url_api = "https://vps789.com/openApi/cfIpApi"
    try:
        response = requests.get(url_api, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            carrier_map = {"CM": "移动", "CU": "联通", "CT": "电信"}
            for carrier_code, items in data.get("data", {}).items():
                carrier_name = carrier_map.get(carrier_code, carrier_code)
                if items:
                    item = items[0]
                    ip = item.get("ip")
                    if ip:
                        cf_api_ips.append((ip, carrier_name))
    except Exception as e:
        print(f"❌ vps789 cfIpApi 失败: {e}")

    # 2. cfIpTop20
    url_top20 = "https://vps789.com/openApi/cfIpTop20"
    try:
        response = requests.get(url_top20, timeout=15)
        response.raise_for_status()
        data = response.json()
        if data.get("code") == 0:
            good_list = data.get("data", {}).get("good", [])[:3]
            seen = set()
            for item in good_list:
                entry = item.get("ip")
                if not entry or entry in seen:
                    continue
                seen.add(entry)
                cf_top_ips.append((entry, "优选"))
    except Exception as e:
        print(f"❌ vps789 cfIpTop20 失败: {e}")

    all_vps = cf_api_ips + cf_top_ips
    print(f"✅ vps789 双API成功（含域名）获取 {len(all_vps)} 个条目 (cfIpApi: {len(cf_api_ips)}, cfIpTop20: {len(cf_top_ips)})")
    return {
        "all": all_vps,
        "cfIpApi_count": len(cf_api_ips),
        "cfIpTop20_count": len(cf_top_ips),
        "cfIpApi_url": url_api,
        "cfIpTop20_url": url_top20
    }

def fetch_hostmonit_ips(url):
    """已适配当前 markdown 表格"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,*/*',
        'Referer': 'https://stock.hostmonit.com/'
    }
    client = get_client(True)
    try:
        response = client.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        text = response.text
        records = []
        for line in text.splitlines():
            line = line.strip()
            if '|' not in line or '---' in line or 'Line' in line or 'IP' in line.upper():
                continue
            parts = [p.strip() for p in line.split('|') if p.strip()]
            if len(parts) < 6:
                continue
            carrier = parts[0]
            ip = next((p for p in parts if re.match(r'(\d{1,3}\.){3}\d{1,3}|:', p)), None)
            latency = next((p for p in parts if 'ms' in p.lower()), None)
            speed = next((p for p in parts if re.search(r'KB/s|MB/s', p, re.I)), None)
            colo = next((p for p in parts if re.fullmatch(r'[A-Z]{3}', p)), None)
            if ip and latency:
                records.append({
                    "ip": ip,
                    "speed": speed or "0KB/s",
                    "latency": latency,
                    "name": f"{colo or 'HM'}-{carrier}"
                })
        records.sort(key=lambda x: (parse_latency(x["latency"]), -parse_speed(x["speed"])))
        selected = records[:2]
        if selected:
            print(f"✅ hostmonit 成功: {url}（{len(selected)}个）")
            return [(x["ip"], x["name"]) for x in selected]
        else:
            print(f"⚠️ hostmonit 解析到0个（格式可能再次变化）")
            return []
    except Exception as e:
        print(f"❌ {url} 处理错误: {e}")
        return []

def send_telegram_combined_message(bot_token, chat_id, caption, file_path):
    if not all([bot_token, chat_id, file_path, os.path.exists(file_path)]):
        print("⚠️ Telegram参数缺失或文件不存在")
        return False
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': (os.path.basename(file_path), f)}
            data = {'chat_id': chat_id, 'caption': caption[:1024], 'parse_mode': 'Markdown'}
            response = requests.post(url, data=data, files=files, timeout=20)
            response.raise_for_status()
            if response.json().get('ok'):
                print("✅ Telegram 通知发送成功")
                return True
        return False
    except Exception as e:
        print(f"❌ 发送失败: {e}")
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
    # 1. ip.164746.xyz → IP#CF-速度
    for ip, speed in speed_ips_dict.get(normal_speed_url, []):
        all_ips.append(f"{ip}#{get_ip_country_code(ip)}-{speed}")
    # 2. wetest
    for url in wetest_urls:
        for ip, name in speed_ips_dict.get(url, []):
            all_ips.append(f"{ip}#{name}")
    # 3. vps789（双API）
    vps_data = speed_ips_dict.get("vps789", {"all": []})
    for ip, name in vps_data.get("all", []):
        all_ips.append(f"{ip}#{name}")
    # 4. hostmonit
    for url in hostmonit_urls:
        for ip, name in speed_ips_dict.get(url, []):
            all_ips.append(f"{ip}#{name}")
    # 5. ipdb.api → IP#CF
    all_ips += [f"{ip}#{get_ip_country_code(ip)}" for ip in text_ips]

    # 去重
    seen = set()
    deduped_ips = []
    for line in all_ips:
        entry = line.split('#')[0].strip()
        if entry not in seen:
            seen.add(entry)
            deduped_ips.append(line)

    file_path = '89.txt'
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(deduped_ips))
    print(f"✅ 已保存 {len(deduped_ips)} 个条目到 {file_path}")

    # ==================== 新 TG 来源详情（完全按你指定的格式） ====================
    source_stats = []

    # ip.164746
    ip164_count = len(speed_ips_dict.get(normal_speed_url, []))
    source_stats.append(f"ip.164746.xyz ({normal_speed_url}): {ip164_count}个")

    # wetest（精确匹配你想要的短名称 + 空格）
    for url in wetest_urls:
        count = len(speed_ips_dict.get(url, []))
        if 'cloudflare' in url.lower():
            short = f"address_{url.split('address_')[-1].replace('.html', '')}"
        else:
            short = f"cloudfront_{url.split('address_')[-1].replace('.html', '')}"
        source_stats.append(f"wetest {short}   {count}个")

    # vps789（两个链接单独显示，完全按你要求）
    vps_data = speed_ips_dict.get("vps789", {"cfIpApi_count": 0, "cfIpTop20_count": 0, "cfIpApi_url": "", "cfIpTop20_url": ""})
    cf_api_count = vps_data.get("cfIpApi_count", 0)
    cf_top_count = vps_data.get("cfIpTop20_count", 0)
    source_stats.append(f"vps789 cfIpApi ({vps_data.get('cfIpApi_url')}): {cf_api_count}个")
    source_stats.append(f"vps789 cfIpTop20 ({vps_data.get('cfIpTop20_url')}): {cf_top_count}个")

    # hostmonit
    for url in hostmonit_urls:
        count = len(speed_ips_dict.get(url, []))
        short = url.split('/')[-1]
        source_stats.append(f"hostmonit {short}   {count}个")

    # ipdb.api
    ipdb_count = len(text_ips)
    source_stats.append(f"ipdb.api ({text_url}): {ipdb_count}个")

    # 异常列表
    failed_sources = []
    if ip164_count == 0:
        failed_sources.append("ip.164746.xyz")
    for url in wetest_urls:
        if len(speed_ips_dict.get(url, [])) == 0:
            failed_sources.append(url.split('/')[-1])
    if cf_api_count == 0 and cf_top_count == 0:
        failed_sources.append("vps789")
    for url in hostmonit_urls:
        if len(speed_ips_dict.get(url, [])) == 0:
            failed_sources.append(url.split('/')[-1])
    if ipdb_count == 0:
        failed_sources.append("ipdb.api")

    # ==================== TG 通知（精确按你指定的格式） ====================
    caption = "IP-scraper运行完成\n\n"
    caption += "📊 采集情况：\n" + "\n".join([f"• {stat}" for stat in source_stats]) + "\n\n"
    caption += f"✅ 本次共采集 (去重后)：{len(deduped_ips)}个\n"
    if failed_sources:
        caption += f"⚠️ 异常（0个）：{'、'.join(failed_sources)}\n"
    caption += "\n文件地址：\nhttps://raw.githubusercontent.com/lijboys/ip-scraper/refs/heads/main/89.txt\n"
    caption += f"⏰ {get_china_time()}"

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    send_telegram_combined_message(bot_token, chat_id, caption, file_path)

if __name__ == "__main__":
    print("===== 开始执行IP采集任务 =====")
    extract_fastest_ips()
    print("===== 任务执行完毕 =====")
