import requests
import re
import os
from datetime import datetime

# 搜索参数：湖南电信 组播
SEARCH_URL = "https://iptv.cqshushu.com/search?q=湖南电信+组播"
OUTPUT_FILE = "hunan.m3u"

def get_iptv_sources():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(SEARCH_URL, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        html = response.text
        
        # 匹配规则（根据网站结构提取：名称、地址、存活天数）
        # 注意：网站结构可能变化，需根据实际HTML调整正则
        # 这里模拟提取逻辑
        sources = []
        
        # 假设提取到的数据块中包含存活时间信息
        # 逻辑：筛选关键词包含“湖南电信”、“组播”，且存活天数 > 2
        pattern = re.compile(r'<tr>.*?<td>(.*?)</td>.*?<td>(rtp://.*?)</td>.*?<td>(.*?)天</td>', re.S)
        matches = pattern.findall(html)
        
        for name, url, alive_days in matches:
            if int(alive_days) >= 2:
                sources.append(f"#EXTINF:-1, {name} (存活{alive_days}天)\n{url}")
        
        return sources
    except Exception as e:
        print(f"抓取失败: {e}")
        return []

def main():
    sources = get_iptv_sources()
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        if sources:
            f.write("\n".join(sources))
        else:
            f.write("# 暂未找到符合条件的源\n")
    print(f"已生成 {len(sources)} 个源至 {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
