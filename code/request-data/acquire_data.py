from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

# 设置 ChromeDriver 路径
chromedriver_path = '/usr/local/bin/chromedriver'
if not os.path.exists(chromedriver_path):
    raise FileNotFoundError(f"未找到 ChromeDriver：{chromedriver_path}。请确保 ChromeDriver 135.0.7049.84 已安装。")
service = Service(chromedriver_path)
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')  # Linux 必需
options.add_argument('--disable-dev-shm-usage')  # 避免内存问题
# options.add_argument('--headless')  # 无头模式，取消注释以隐藏浏览器窗口
driver = webdriver.Chrome(service=service, options=options)

try:
    # 访问小红书并手动登录
    driver.get('https://www.xiaohongshu.com')
    print("请在30秒内手动登录小红书（确保网络正常）...")
    time.sleep(30)

    # 搜索“求脱单”帖子
    search_url = 'https://www.xiaohongshu.com/search_result?keyword=求脱单'
    driver.get(search_url)
    time.sleep(5)  # 等待页面加载

    # 收集帖子
    posts = []
    max_posts = 5000
    scroll_pause = random.uniform(2, 4)  # 随机延时防反爬

    while len(posts) < max_posts:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # 更新 class 名：需检查小红书网页源码（右键 > 检查）
        post_elements = soup.find_all('div', class_='note-item')  # 可能为 'note-card' 或其他
        for post in post_elements:
            try:
                content = post.find('div', class_='content').text.strip() if post.find('div', class_='content') else ''
                user_info = post.find('div', class_='author-wrapper') or post.find('div', class_='user-info') or ''
                gender = '未知'  # 后续推断
                education = '未知'  # 后续提取
                if any(keyword in content for keyword in ['求脱单', '相亲', '恋爱']):
                    posts.append({
                        'content': content,
                        'gender': gender,
                        'education': education,
                        'standards': content  # 择偶标准
                    })
            except Exception as e:
                print(f"帖子解析错误: {e}")
                continue
        
        # 滚动加载更多
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)
        print(f"已收集 {len(posts)} 条帖子...")
        
        if len(posts) >= max_posts:
            break

    # 保存数据
    df = pd.DataFrame(posts)
    df.to_csv('xiaohongshu_posts.csv', index=False, encoding='utf-8-sig')
    print(f"已保存 {len(posts)} 条帖子至 xiaohongshu_posts.csv")

finally:
    driver.quit()