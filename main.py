import requests
import re
import base64
import time
import random
import os
from datetime import datetime

# 模拟真实浏览器
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

def main():
    filename = "hunan_iptv.m3u"
    final_pool = {}
    session = requests.Session()
    session.headers.update({'User-Agent': random.choice(UA_LIST)})

    try:
        # 第一步：访问首页拿 Cookie
        print("[*] 正在初始化连接...")
        home = session.get("https://iptv.cqshushu.com", timeout=15)
        time.sleep(random.uniform(2, 5)) # 模拟真人停顿

        # 第二步：搜索
        print("[*] 正在检索长沙组播源...")
        search_url = "https://iptv.cqshushu.com/?q=湖南省长沙市"
        resp = session.get(search_url, headers={'Referer': 'https://iptv.cqshushu.com/'}, timeout=15)
        
        # 提取 Base64 IP
        ips = re.findall(r"gotoIP\('([^']+)',\s*'multicast'\)", resp.text)
        
        if not ips:
            print("[!] 未能获取到 IP，可能触发了防火墙验证。")
            # 这里可以输出部分 HTML 内容到 Action 日志协助排查
            print(f"DEBUG: 页面内容前200字符: {resp.text[:200]}")
        else:
            for b64 in ips[:3]: # 仅取前3个最稳的源
                ip = base64.b64decode(b64).decode('utf-8')
                # 再次随机等待
                time.sleep(random.uniform(3, 6))
                m3u_url = f"https://iptv.cqshushu.com/?s={ip}&t=multicast&channels=1&download=m3u"
                m3u_data = session.get(m3u_url, headers={'Referer': search_url}, timeout=15).text
                
                if "#EXTM3U" in m3u_data:
                    channels = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?/rtp/.*)', m3u_data)
                    for name, url in channels:
                        final_pool[name.strip()] = url.strip()

    except Exception as e:
        print(f"[!] 发生异常: {e}")

    # 关键点：无论如何都要写文件
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Updated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if final_pool:
            for name, url in sorted(final_pool.items()):
                f.write(f"#EXTINF:-1, {name}\n{url}\n")
            print(f"[*] 成功导出 {len(final_pool)} 个频道")
        else:
            f.write("# Warning: No sources found due to firewall or connection issues\n")

if __name__ == "__main__":
    main()
