import requests
import re
import base64
import time
import random
from datetime import datetime

# --- 增强版配置 ---
BASE_URL = "https://iptv.cqshushu.com"
SEARCH_QUERY = "湖南省长沙市"

# 模拟不同浏览器的 User-Agent 池
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def main():
    session = requests.Session()
    # 随机选择一个 UA
    current_ua = random.choice(UA_LIST)
    session.headers.update({
        'User-Agent': current_ua,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'max-age=0',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Upgrade-Insecure-Requests': '1'
    })

    final_pool = {}

    try:
        # 1. 访问首页（获取必要的安全 Cookie）
        print(f"[*] 正在建立安全连接 (UA: {current_ua[:30]}...)")
        home_resp = session.get(BASE_URL, timeout=20)
        time.sleep(random.uniform(2, 4)) # 随机等待，模拟真人阅读首页

        # 2. 提取搜索 Token（如果存在）
        token_match = re.search(r'name="token" value="([^"]+)"', home_resp.text)
        token = token_match.group(1) if token_match else ""

        # 3. 执行搜索（带上 Referer）
        search_url = f"{BASE_URL}/?q={SEARCH_QUERY}"
        print(f"[*] 正在模拟人工搜索: {SEARCH_QUERY}")
        search_resp = session.get(search_url, headers={'Referer': BASE_URL}, timeout=20)
        
        # 4. 解析 IP
        ip_items = re.findall(r"gotoIP\('([^']+)',\s*'multicast'\)", search_resp.text)
        
        if not ip_items:
            print("[!] 警告：未发现 IP。可能是 IP 被屏蔽，或者页面结构变化。")
            if "Cloudflare" in search_resp.text:
                print("[!!!] 触发了 Cloudflare 五秒盾，脚本无法自动绕过。")

        # 5. 极慢速抓取
        for b64_ip in ip_items[:3]: # 减少单次抓取数量，降低风险
            real_ip = base64.b64decode(b64_ip).decode('utf-8')
            print(f"  [+] 正在低频解析: {real_ip}")
            
            # 访问详情页（伪造来源）
            detail_url = f"{BASE_URL}/?s={real_ip}&t=multicast"
            session.get(detail_url, headers={'Referer': search_url}, timeout=15)
            
            # 随机延迟 3-7 秒
            time.sleep(random.uniform(3, 7))
            
            m3u_url = f"{BASE_URL}/?s={real_ip}&t=multicast&channels=1&download=m3u"
            m3u_resp = session.get(m3u_url, headers={'Referer': detail_url}, timeout=15)
            
            if "#EXTM3U" in m3u_resp.text:
                matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?/rtp/.*)', m3u_resp.text)
                for name, url in matches:
                    final_pool[name.strip()] = url.strip()
            
            time.sleep(random.uniform(2, 5))

        # 6. 保存结果
        with open("hunan_iptv.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"# 自动更新于: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            for name in sorted(final_pool.keys()):
                f.write(f"#EXTINF:-1, {name}\n{final_pool[name]}\n")
        
        print(f"[*] 任务结束，成功获取 {len(final_pool)} 个频道")

    except Exception as e:
        print(f"[!] 错误: {e}")

if __name__ == "__main__":
    main()
