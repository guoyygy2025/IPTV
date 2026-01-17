import requests
import re
import base64
import time
import random
from datetime import datetime

# --- 增强版伪装头 ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Referer': 'https://iptv.cqshushu.com/',
    'Connection': 'keep-alive'
}

def fetch_cqshushu(session):
    """尝试从 cqshushu 获取源"""
    links = {}
    try:
        print("[*] 正在尝试源 A (cqshushu)...")
        # 1. 获取首页 Token
        home = session.get("https://iptv.cqshushu.com", timeout=15)
        token = re.search(r'name="token" value="([^"]+)"', home.text)
        token_val = token.group(1) if token else ""
        
        # 2. 搜索长沙组播
        search_url = f"https://iptv.cqshushu.com/?token={token_val}&q=湖南省长沙市"
        resp = session.get(search_url, timeout=15)
        
        # 3. 提取 Base64 IP
        ips = re.findall(r"gotoIP\('([^']+)',\s*'multicast'\)", resp.text)
        for b64 in ips[:3]:
            ip = base64.b64decode(b64).decode('utf-8')
            m3u_url = f"https://iptv.cqshushu.com/?s={ip}&t=multicast&channels=1&download=m3u"
            m3u_data = session.get(m3u_url, timeout=15).text
            if "#EXTM3U" in m3u_data:
                items = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?/rtp/.*)', m3u_data)
                for name, url in items:
                    links[name.strip()] = url.strip()
            time.sleep(random.uniform(3, 5))
    except Exception as e:
        print(f"[!] 源 A 抓取失败: {e}")
    return links

def fetch_tonkiang():
    """备选源：从 tonkiang.us 获取（作为备份）"""
    links = {}
    try:
        print("[*] 正在尝试源 B (tonkiang)...")
        # Tonkiang 搜索长沙电信组播的接口
        url = "http://tonkiang.us/hoteliptv.php?q=长沙电信" 
        resp = requests.get(url, headers=HEADERS, timeout=15)
        # 简单的正则提取
        urls = re.findall(r'rtp://(\d+\.\d+\.\d+\.\d+:\d+)', resp.text)
        for i, rtp_url in enumerate(urls[:20]):
            links[f"长沙备用-{i}"] = f"http://{rtp_url}"
    except Exception as e:
        print(f"[!] 源 B 抓取失败: {e}")
    return links

def main():
    final_pool = {}
    session = requests.Session()
    session.headers.update(HEADERS)

    # 尝试两个源
    res_a = fetch_cqshushu(session)
    final_pool.update(res_a)
    
    if not res_a:
        res_b = fetch_tonkiang()
        final_pool.update(res_b)

    # 无论结果如何，写入文件
    with open("hunan_iptv.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if final_pool:
            for name in sorted(final_pool.keys()):
                f.write(f"#EXTINF:-1, {name}\n{final_pool[name]}\n")
            print(f"[*] 任务成功，共捕获 {len(final_pool)} 个链接")
        else:
            f.write("# Warning: All sources blocked by WAF. Please try again later.\n")

if __name__ == "__main__":
    main()
