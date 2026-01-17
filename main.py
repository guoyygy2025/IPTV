import requests
import re
from datetime import datetime

# 搜索关键词：湖南电信 组播
# cqshushu 的搜索 URL 结构通常是这样
SEARCH_URL = "https://iptv.cqshushu.com/search?q=湖南电信+组播"

def get_iptv_sources():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://iptv.cqshushu.com/',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    
    try:
        print(f"正在访问: {SEARCH_URL}")
        response = requests.get(SEARCH_URL, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        html = response.text
        
        # --- 调试信息：如果还是搜不到，取消下面一行的注释，在Actions日志里看输出了什么 ---
        # print(html)

        sources = []
        
        # cqshushu 的结构通常在 <tbody> 的 <tr> 中
        # 我们用更通用的正则来捕获每一行数据
        # 匹配逻辑：名称 -> 包含 rtp/udp 的链接 -> 存活时间数字
        # 注意：这里需要根据网页实际 HTML 源码微调
        # 下面是一个兼容性较强的匹配模式
        items = re.findall(r'<tr>(.*?)</tr>', html, re.S)
        print(f"抓取到 {len(items)} 行原始数据")

        for item in items:
            # 提取包含 rtp 或 udp 的链接
            url_match = re.search(r'((rtp|udp)://[\d\.:]+)', item)
            # 提取名称（通常在链接前后的第一个 td）
            name_match = re.search(r'<td>(.*?)</td>', item)
            # 提取存活天数（通常包含“天”字）
            alive_match = re.search(r'(\d+)\s*天', item)

            if url_match:
                url = url_match.group(1)
                name = name_match.group(1) if name_match else "湖南电信频道"
                alive_days = int(alive_match.group(1)) if alive_match else 0
                
                # 核心过滤条件：湖南、电信、且存活 >= 2天
                if alive_days >= 2:
                    sources.append(f"#EXTINF:-1 group-title=\"湖南电信\", {name} (存活{alive_days}天)\n{url}")

        # 去重处理
        return list(set(sources))

    except Exception as e:
        print(f"抓取过程中出现错误: {e}")
        return []

def main():
    sources = get_iptv_sources()
    
    with open("hunan.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        if sources:
            f.write("\n".join(sources))
        else:
            f.write("# 暂未找到符合条件的源（存活>=2天且为湖南电信组播）\n")
            
    print(f"处理完成，符合条件并保存的源数量: {len(sources)}")

if __name__ == "__main__":
    main()
