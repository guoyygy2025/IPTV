import requests
import re
import base64
import time
from datetime import datetime

# --- 配置信息 ---
BASE_URL = "https://iptv.cqshushu.com"
SEARCH_QUERY = "湖南省长沙市"
SEARCH_URL = f"{BASE_URL}/search?q={SEARCH_QUERY}"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': BASE_URL
}

def get_rtp_from_m3u(m3u_url):
    """下载并解析 M3U 内容中的频道名和组播地址"""
    results = {}
    try:
        resp = requests.get(m3u_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            # 匹配 #EXTINF 中的频道名和下一行的链接
            # 格式兼容：#EXTINF:-1,CCTV-1\nhttp://ip:port/rtp/xxx
            matches = re.findall(r'#EXTINF:.*?,(.*?)\n(http.*?://.*?/rtp/.*)', resp.text)
            for name, url in matches:
                results[name.strip()] = url.strip()
    except Exception as e:
        print(f"      下载失败: {e}")
    return results

def main():
    final_pool = {} # 使用字典按“频道名”去重
    
    try:
        print(f"开始搜索关键词: {SEARCH_QUERY}")
        r = requests.get(SEARCH_URL, headers=HEADERS, timeout=20)
        html = r.text
        
        # 定位组播表格 (Multicast IP)
        multicast_block = re.search(r'组播源列表.*?<tbody>(.*?)</tbody>', html, re.S)
        if not multicast_block:
            print("未能定位到组播数据表格")
            return

        # 匹配：Base64加密的IP、存活天数
        items = re.findall(r"gotoIP\('([^']+)',\s*'multicast'\).*?存活(\d+)天", multicast_block.group(1), re.S)
        print(f"找到 {len(items)} 条初步记录")

        for b64_ip, alive_days in items:
            days = int(alive_days)
            if days >= 2:
                real_ip = base64.b64decode(b64_ip).decode('utf-8')
                # 构造该站的 M3U 下载接口
                m3u_api = f"{BASE_URL}/?s={real_ip}&t=multicast&channels=1&download=m3u"
                
                print(f"--> 提取接口 (存活{days}天): {real_ip}")
                channel_data = get_rtp_from_m3u(m3u_api)
                final_pool.update(channel_data) # 合并并覆盖去重
                
                time.sleep(1.5) # 避免请求过快

        # 生成最终文件
        if final_pool:
            with open("hunan_iptv.m3u", "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write(f"# 更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# 总计去重频道: {len(final_pool)}\n\n")
                for name in sorted(final_pool.keys()):
                    f.write(f"#EXTINF:-1 group-title=\"长沙组播\", {name}\n")
                    f.write(f"{final_pool[name]}\n")
            print(f"任务完成！生成 hunan_iptv.m3u，共 {len(final_pool)} 个频道。")
        else:
            print("未找到满足条件的有效频道。")

    except Exception as e:
        print(f"程序运行错误: {e}")

if __name__ == "__main__":
    main()
