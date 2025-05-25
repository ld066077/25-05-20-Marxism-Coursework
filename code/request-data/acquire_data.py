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

    # 读取现有数据（若存在且有效）
    data_file = 'xiaohongshu_posts.csv'
    visited_urls = set()
    posts = []
    if os.path.exists(data_file):
        try:
            # 检查文件是否为空
            with open(data_file, 'r', encoding='utf-8-sig') as f:
                content = f.read().strip()
                if content and 'url' in content:  # 检查是否有数据和 URL 列
                    existing_df = pd.read_csv(data_file)
                    if not existing_df.empty:
                        visited_urls = set(existing_df['url'].values)
                        posts = existing_df.to_dict('records')
                        print(f"已加载 {len(posts)} 条历史数据")
                    else:
                        print("现有 CSV 文件为空，初始化为空数据集")
                else:
                    print("现有 CSV 文件无效或为空，初始化为空数据集")
        except Exception as e:
            print(f"读取 CSV 文件失败: {e}，初始化为空数据集")
    else:
        print("未找到 CSV 文件，初始化为空数据集")

    # 搜索“求脱单”帖子
    search_url = 'https://www.xiaohongshu.com/search_result?keyword=求脱单'
    driver.get(search_url)
    time.sleep(10)  # 等待页面加载

    # 模拟用户行为：向下滚动
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(2)

    max_posts = 3000
    scroll_pause = random.uniform(10, 15)  # 增加延时防反爬

    while len(posts) < max_posts:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        post_elements = soup.find_all('section', class_='note-item')
        print(f"找到 {len(post_elements)} 个帖子元素")

        new_posts = 0  # 记录本次循环新增帖子
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
                if full_url in visited_urls or not full_url:
                    continue
                visited_urls.add(full_url)

                # 进入详情页获取完整内容
                content = title
                driver.get(full_url)
                time.sleep(random.uniform(7, 10))  # 增加详情页延时
                detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
                content_elem = detail_soup.find('div', class_='desc')
                content = content_elem.text.strip() if content_elem else title
                driver.back()
                time.sleep(random.uniform(3, 5))

                user_info = post.find('div', class_='author-wrapper') or post.find('div', class_='user-info') or ''
                gender = '未知'
                education = '未知'

                # 放宽关键词过滤
                if any(keyword in content.lower() for keyword in ['求脱单', '相亲', '恋爱', '脱单', '找对象', '单身', '择偶']):
                    posts.append({
                        'url': full_url,  # 记录唯一标识码
                        'content': content,
                        'gender': gender,
                        'education': education,
                        'standards': content
                    })
                    new_posts += 1
            except Exception as e:
                print(f"帖子解析错误: {e}")
                continue

        # 保存数据并去重
        if new_posts > 0:
            df = pd.DataFrame(posts)
            df.drop_duplicates(subset=['url'], keep='first', inplace=True)
            posts = df.to_dict('records')  # 更新 posts
            df.to_csv(data_file, index=False, encoding='utf-8-sig')
            print(f"已保存 {len(posts)} 条帖子至 {data_file}（本次新增 {new_posts} 条）")

        # 滚动加载更多
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause)
        print(f"当前收集 {len(posts)} 条帖子...")

        # 检查反爬
        if '请稍后再试' in driver.page_source:
            print("可能被反爬限制，尝试延长延时或使用 VPN")
            break

        # 模拟刷新搜索（突破 200 条限制）
        if new_posts == 0 and len(post_elements) < 5:
            print("搜索结果可能受限，重新加载搜索页...")
            driver.get(search_url)
            time.sleep(10)
            driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(2)

        if len(posts) >= max_posts:
            break

    # 最终保存
    df = pd.DataFrame(posts)
    if not df.empty:
        df.drop_duplicates(subset=['url'], keep='first', inplace=True)
        df.to_csv(data_file, index=False, encoding='utf-8-sig')
        print(f"最终保存 {len(df)} 条帖子至 {data_file}")

finally:
    driver.quit()