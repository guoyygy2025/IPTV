import requests
import re
import time
from datetime import datetime

# 配置
BASE_URL = "https://iptv.cqshushu.com"
# 搜索关键词：湖南省长沙市
SEARCH_URL = f"{BASE_URL}/search?q=湖南省长沙市"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': BASE_URL
}

def download_m3u_and_extract(m3u_url):
    """访问接口地址，下载并提取内部所有的 rtp/udp 链接"""
    try:
        print(f"   正在处理接口内容: {m3u_url}")
        resp = requests.get(m3u_url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            # 匹配文件内部真实的组播地址
            links = re.findall(r'((?:rtp|udp)://[\d\.:]+)', resp.text)
            return links
    except Exception as e:
        print(f"      下载失败: {e}")
    return []

def main():
    final_rtp_pool = set()  # 使用集合自动去重地址
    
    try:
        print(f"[{datetime.now()}] 步骤1: 搜索 '湖南省长沙市'...")
        response = requests.get(SEARCH_URL, headers=HEADERS, timeout=20)
        response.encoding = 'utf-8'
        html = response.text

        # 步骤2: 在表格中定位至少存活2天的源
        # 匹配模式说明：捕获 m3u 链接和其对应的存活天数
        # 该网站结构中，m3u链接通常在 <td> 里的 <a> 标签，天数在同行的后续 <td>
        pattern = re.compile(r'href="(/m3u/.*?\.m3u)".*?(\d+)\s*天', re.S)
        matches = pattern.findall(html)
        
        print(f"共发现 {len(matches)} 个潜在记录。")

        for m3u_path, alive_days in matches:
            days = int(alive_days)
            if days >= 2:
                m3u_full_url = BASE_URL + m3u_path
                print(f"发现存活 {days} 天的源，开始提取具体频道...")
                
                # 步骤3: 下载并解析具体的组播地址
                rtp_links = download_m3u_and_extract(m3u_full_url)
                print(f"      提取到 {len(rtp_links)} 个唯一频道地址")
                
                for link in rtp_links:
                    final_rtp_pool.add(link)
                
                # 频率控制，防止被封
                time.sleep(1)

        # 步骤4: 汇总生成去重后的 M3U 文件
        if final_rtp_pool:
            filename = "changsha_live.m3u"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n")
                f.write(f"# 来源: cqshushu | 关键词: 湖南省长沙市 | 存活: >=2天\n")
                f.write(f"# 总计去重后频道数: {len(final_rtp_pool)}\n")
                f.write(f"# 更新日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for i, rtp in enumerate(sorted(list(final_rtp_pool))):
                    f.write(f"#EXTINF:-1 group-title=\"长沙组播汇总\", 频道-{i+1:03d}\n")
                    f.write(f"{rtp}\n")
            print(f"成功！去重后的 M3U 已生成: {filename}，共 {len(final_rtp_pool)} 条地址。")
        else:
            print("未找到符合条件（存活>=2天）的源。")

    except Exception as e:
        print(f"主程序异常: {e}")

if __name__ == "__main__":
    main()
