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
# options.add_argument('--headless')  # 无头模式，取消注释以隐藏窗口
driver = webdriver.Chrome(service=service, options=options)

try:
    # 访问小红书并手动登录
    driver.get('https://www.xiaohongshu.com')
    print("请在30秒内手动登录小红书（确保网络正常）...")
    time.sleep(30)

    # 验证登录
    if 'xiaohongshu.com' not in driver.current_url:
        print("登录失败，请检查网络或手动登录操作")
        raise Exception("登录失败")

    # 搜索“求脱单”帖子
    search_url = 'https://www.xiaohongshu.com/search_result?keyword=求脱单'
    driver.get(search_url)
    time.sleep(10)  # 等待页面加载

    # 模拟用户行为：向下滚动
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(2)

    # 收集帖子
    posts = []
    max_posts = 10
    scroll_pause = random.uniform(5, 7)  # 防反爬延时
    visited_urls = set()  # 避免重复爬取

    while len(posts) < max_posts:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # 搜索页帖子容器
        post_elements = soup.find_all('section', class_='note-item')
        print(f"找到 {len(post_elements)} 个帖子元素")

        for post in post_elements:
            try:
                # 获取标题
                title_elem = post.find('span', class_='title')
                title = title_elem.text.strip() if title_elem else ''
                # 获取帖子链接
                link_elem = post.find('a', class_='cover mask ld')
                post_url = link_elem['href'] if link_elem else ''
                full_url = f"https://www.xiaohongshu.com{post_url}" if post_url else ''

                # 跳过已访问的帖子
                if full_url in visited_urls:
                    continue
                visited_urls.add(full_url)

                # 进入详情页获取完整内容
                content = title  # 默认使用标题
                if full_url:
                    driver.get(full_url)
                    time.sleep(random.uniform(3, 5))  # 等待详情页
                    detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    # 详情页正文
                    content_elem = detail_soup.find('div', class_='desc')
                    content = content_elem.text.strip() if content_elem else title
                    driver.back()  # 返回搜索页
                    time.sleep(random.uniform(2, 4))

                user_info = post.find('div', class_='author-wrapper') or post.find('div', class_='user-info') or ''
                gender = '未知'  # 后续推断
                education = '未知'  # 后续提取

                # 严格过滤相关帖子
                if any(keyword in content.lower() for keyword in ['求脱单', '相亲', '恋爱', '脱单']):
                    posts.append({
                        'content': content,
                        'gender': gender,
                        'education': education,
                        'standards': content
                    })
            except Exception as e:
                print(f"帖子解析错误: {e}")
                continue
        
        # 滚动加载更多
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)
        print(f"已收集 {len(posts)} 条帖子...")

        # 检查反爬
        if '请稍后再试' in driver.page_source:
            print("可能被反爬限制，尝试延长延时或使用 VPN")
            break
        
        if len(posts) >= max_posts:
            break

    # 保存数据
    df = pd.DataFrame(posts)
    df.to_csv('xiaohongshu_posts.csv', index=False, encoding='utf-8-sig')
    print(f"已保存 {len(posts)} 条帖子至 xiaohongshu_posts.csv")

finally:
    driver.quit()