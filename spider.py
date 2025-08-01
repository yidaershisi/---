#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔趣阁小说爬虫模块
支持多线程爬取、断点续爬、错误处理等功能
"""

import requests
import os
import json
import re
import time
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import chardet

class NovelSpider:
    def __init__(self, base_url="https://www.577ff.cfd", max_workers=5):
        self.base_url = base_url
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.progress_file = "download_progress.json"
        self.lock = threading.Lock()
        
    def get_page_content(self, url, retries=3):
        """获取页面内容，包含重试机制"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                # 自动检测编码
                detected = chardet.detect(response.content)
                encoding = detected.get('encoding', 'utf-8')
                if encoding.lower() in ['gb2312', 'gbk']:
                    encoding = 'gbk'
                
                response.encoding = encoding
                return response.text
            except Exception as e:
                print(f"获取页面失败 (尝试 {attempt + 1}/{retries}): {url}")
                print(f"错误: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    return None
        return None
    
    def parse_novel_info(self, novel_id):
        """解析小说基本信息和章节列表"""
        novel_url = f"{self.base_url}/book/{novel_id}/"
        print(f"正在解析小说信息: {novel_url}")
        
        content = self.get_page_content(novel_url)
        if not content:
            raise Exception(f"无法获取小说页面: {novel_url}")
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 提取小说标题
        title_elem = soup.find('h1') or soup.find('title')
        novel_title = title_elem.get_text().strip() if title_elem else f"小说_{novel_id}"
        
        # 清理标题中的非法字符
        novel_title = re.sub(r'[<>:"/\\|?*]', '_', novel_title)
        
        # 提取章节列表
        chapters = []
        
        # 尝试多种章节列表选择器
        chapter_selectors = [
            'div.listmain dd a',
            '.chapter-list a',
            '#list dd a',
            'div.book-list a',
            'ul.chapter a',
            'div.volume a'
        ]
        
        for selector in chapter_selectors:
            chapter_links = soup.select(selector)
            if chapter_links:
                break
        
        if not chapter_links:
            # 如果没有找到章节链接，尝试查找所有包含数字的链接
            all_links = soup.find_all('a', href=True)
            chapter_links = [link for link in all_links if re.search(r'\d+\.html?$', link.get('href', ''))]
        
        for i, link in enumerate(chapter_links):
            href = link.get('href')
            if href:
                chapter_url = urljoin(novel_url, href)
                chapter_title = link.get_text().strip()
                if chapter_title:
                    chapters.append({
                        'index': i + 1,
                        'title': chapter_title,
                        'url': chapter_url
                    })
        
        if not chapters:
            raise Exception("未找到任何章节链接")
        
        print(f"找到小说: {novel_title}，共 {len(chapters)} 章")
        return {
            'title': novel_title,
            'chapters': chapters,
            'novel_id': novel_id
        }
    
    def extract_chapter_content(self, chapter_url):
        """提取章节内容"""
        content = self.get_page_content(chapter_url)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # 尝试多种内容选择器
        content_selectors = [
            '#chaptercontent',
            '#content',
            '.content',
            '#chapter_content',
            '.chapter-content',
            '.read-content',
            '#booktext',
            '.text-content'
        ]
        
        chapter_content = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                chapter_content = content_elem
                break
        
        if not chapter_content:
            # 如果没有找到内容区域，尝试查找最大的文本块
            text_elements = soup.find_all(['div', 'p'], string=True)
            if text_elements:
                chapter_content = max(text_elements, key=lambda x: len(x.get_text()))
        
        if chapter_content:
            # 清理内容
            for script in chapter_content(["script", "style"]):
                script.decompose()
            
            text = chapter_content.get_text()
            # 清理多余的空白字符
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = re.sub(r'[ \t]+', ' ', text)
            text = text.strip()
            
            return text
        
        return None
    
    def download_chapter(self, chapter_info, novel_dir, progress_data):
        """下载单个章节"""
        chapter_index = chapter_info['index']
        chapter_title = chapter_info['title']
        chapter_url = chapter_info['url']
        
        # 检查是否已下载
        if str(chapter_index) in progress_data.get('completed_chapters', []):
            print(f"章节 {chapter_index} 已存在，跳过")
            return True
        
        print(f"正在下载第 {chapter_index} 章: {chapter_title}")
        
        content = self.extract_chapter_content(chapter_url)
        if content:
            # 清理文件名
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', chapter_title)
            filename = f"{chapter_index:04d}_{safe_title}.txt"
            filepath = os.path.join(novel_dir, filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"第{chapter_index}章 {chapter_title}\n\n")
                    f.write(content)
                
                # 更新进度
                with self.lock:
                    if 'completed_chapters' not in progress_data:
                        progress_data['completed_chapters'] = []
                    progress_data['completed_chapters'].append(str(chapter_index))
                    self.save_progress(progress_data)
                
                print(f"✓ 第 {chapter_index} 章下载完成")
                return True
            except Exception as e:
                print(f"✗ 第 {chapter_index} 章保存失败: {e}")
                return False
        else:
            print(f"✗ 第 {chapter_index} 章内容提取失败")
            return False
    
    def save_progress(self, progress_data):
        """保存下载进度"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存进度失败: {e}")
    
    def load_progress(self):
        """加载下载进度"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载进度失败: {e}")
        return {}
    
    def download_novel(self, novel_id, output_dir="novels"):
        """下载整本小说"""
        try:
            # 解析小说信息
            novel_info = self.parse_novel_info(novel_id)
            novel_title = novel_info['title']
            chapters = novel_info['chapters']
            
            # 创建小说目录
            novel_dir = os.path.join(output_dir, f"{novel_id}_{novel_title}")
            os.makedirs(novel_dir, exist_ok=True)
            
            # 加载进度
            progress_data = self.load_progress()
            if novel_id not in progress_data:
                progress_data[novel_id] = {
                    'title': novel_title,
                    'total_chapters': len(chapters),
                    'completed_chapters': []
                }
            
            print(f"开始下载小说: {novel_title}")
            print(f"总章节数: {len(chapters)}")
            print(f"已完成: {len(progress_data[novel_id].get('completed_chapters', []))} 章")
            
            # 多线程下载
            success_count = 0
            failed_chapters = []
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_chapter = {
                    executor.submit(self.download_chapter, chapter, novel_dir, progress_data[novel_id]): chapter
                    for chapter in chapters
                }
                
                for future in as_completed(future_to_chapter):
                    chapter = future_to_chapter[future]
                    try:
                        success = future.result()
                        if success:
                            success_count += 1
                        else:
                            failed_chapters.append(chapter)
                    except Exception as e:
                        print(f"章节 {chapter['index']} 下载异常: {e}")
                        failed_chapters.append(chapter)
            
            # 生成合并文件
            self.merge_chapters(novel_dir, novel_title)
            
            print(f"\n下载完成!")
            print(f"成功: {success_count} 章")
            print(f"失败: {len(failed_chapters)} 章")
            
            if failed_chapters:
                print("失败章节:")
                for chapter in failed_chapters:
                    print(f"  第 {chapter['index']} 章: {chapter['title']}")
            
            return novel_dir
            
        except Exception as e:
            print(f"下载失败: {e}")
            return None
    
    def merge_chapters(self, novel_dir, novel_title):
        """合并所有章节为一个完整文件"""
        try:
            merged_file = os.path.join(novel_dir, f"{novel_title}_完整版.txt")
            
            # 获取所有章节文件并排序
            chapter_files = [f for f in os.listdir(novel_dir) if f.endswith('.txt') and not f.endswith('_完整版.txt')]
            chapter_files.sort(key=lambda x: int(x.split('_')[0]))
            
            with open(merged_file, 'w', encoding='utf-8') as merged:
                merged.write(f"{novel_title}\n\n")
                
                for chapter_file in chapter_files:
                    chapter_path = os.path.join(novel_dir, chapter_file)
                    try:
                        with open(chapter_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            merged.write(content)
                            merged.write("\n\n" + "="*50 + "\n\n")
                    except Exception as e:
                        print(f"合并章节 {chapter_file} 失败: {e}")
            
            print(f"已生成完整版文件: {merged_file}")
            
        except Exception as e:
            print(f"合并章节失败: {e}")

def main():
    """主函数"""
    spider = NovelSpider(max_workers=3)  # 设置3个线程
    
    print("笔趣阁小说下载器")
    print("="*30)
    
    while True:
        novel_id = input("请输入小说ID (输入 'quit' 退出): ").strip()
        if novel_id.lower() == 'quit':
            break
        
        if not novel_id:
            print("请输入有效的小说ID")
            continue
        
        try:
            result = spider.download_novel(novel_id)
            if result:
                print(f"小说已保存到: {result}")
            else:
                print("下载失败")
        except KeyboardInterrupt:
            print("\n用户中断下载")
            break
        except Exception as e:
            print(f"发生错误: {e}")
        
        print("\n" + "-"*30 + "\n")

if __name__ == "__main__":
    main()