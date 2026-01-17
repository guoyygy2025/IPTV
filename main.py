import requests
import re
import base64
import time
from datetime import datetime

# --- 配置 ---
BASE_URL = "https://iptv.cqshushu.com"
SEARCH_QUERY = "湖南省长沙市"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': BASE_URL
}

def main():
    session = requests.Session()
    session.headers.update(HEADERS)
    final_pool = {}

    try:
        # 1. 访问首页获取搜索 Token
        print("[*] 正在初始化访问首页...")
        home_resp = session.get(BASE_URL, timeout=15)
        token_match = re.search(r'name="token" value="([^"]+)"', home_resp.text)
        token = token_match.group(1) if token_match else ""
        
        # 2. 执行搜索
        search_params = {'token': token, 'q': SEARCH_QUERY}
        print(f"[*] 正在搜索关键词: {SEARCH_QUERY}")
        search_resp = session.get(BASE_URL, params=search_params, timeout=15)
        
        # 3. 提取所有组播 IP (Base64格式)
        # 匹配 gotoIP('MTc1LjAuNzIuMjIxOjQwMjI=', 'multicast')
        ip_items = re.findall(r"gotoIP\('([^']+)',\s*'multicast'\)", search_resp.text)
        print(f"[*] 搜索完成，找到 {len(ip_items)} 个原始 IP 记录")

        # 4. 遍历提取频道 (仅处理存活率高的前 5 个，防止被封)
        for b64_ip in ip_items[:5]:
            try:
                real_ip = base64.b64decode(b64_ip).decode('utf-8')
                print(f"  [+] 正在解析存活源: {real_ip}")
                
                # 模拟进入详情页建立 Session 权限
                detail_url = f"{BASE_URL}/?s={real_ip}&t=multicast"
                session.get(detail_url, timeout=10)
                
                # 请求 M3U 下载接口
                m3u_url = f"{BASE_URL}/?s={real_ip}&t=multicast&channels=1&download=m3u"
                m3u_resp = session.get(m3u_url, timeout=10)
                
                if "#EXTM3U" in m3u_resp.text:
                    # 正则解析频道名和链接
                    matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?://.*?/rtp/.*)', m3u_resp.text)
                    for name, url in matches:
                        # 以频道名为 Key 去重，确保获取最新链接
                        final_pool[name.strip()] = url.strip()
                
                time.sleep(2) # 礼貌延时
            except Exception as e:
                print(f"    [-] 解析 {b64_ip} 失败: {e}")

        # 5. 生成 M3U 文件
        with open("hunan_iptv.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            if final_pool:
                for name in sorted(final_pool.keys()):
                    f.write(f"#EXTINF:-1, {name}\n{final_pool[name]}\n")
                print(f"[*] 任务成功！共提取 {len(final_pool)} 个频道。")
            else:
                f.write("# 当前未抓取到有效源，可能触发了网站防火墙。\n")
                print("[!] 警告：未发现有效频道，请检查网站访问是否受限。")

    except Exception as e:
        print(f"[!] 脚本运行异常: {e}")
        # 确保文件存在，防止 Actions 报错
        with open("hunan_iptv.m3u", "w") as f: f.write("# Error")

if __name__ == "__main__":
    main()
