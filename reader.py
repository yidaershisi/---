#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔趣阁小说阅读器
功能丰富的桌面阅读器，支持多种阅读设置和管理功能
"""

import sys
import os
import json
import re
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class BookmarkManager:
    """书签管理器"""
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.bookmark_file = os.path.join(config_dir, "bookmarks.json")
        self.bookmarks = self.load_bookmarks()
    
    def load_bookmarks(self):
        try:
            if os.path.exists(self.bookmark_file):
                with open(self.bookmark_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载书签失败: {e}")
        return {}
    
    def save_bookmarks(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.bookmark_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存书签失败: {e}")
    
    def add_bookmark(self, book_path, chapter_index, position, note=""):
        if book_path not in self.bookmarks:
            self.bookmarks[book_path] = []
        
        bookmark = {
            'chapter_index': chapter_index,
            'position': position,
            'note': note,
            'created_time': datetime.now().isoformat()
        }
        
        self.bookmarks[book_path].append(bookmark)
        self.save_bookmarks()
    
    def get_bookmarks(self, book_path):
        return self.bookmarks.get(book_path, [])
    
    def remove_bookmark(self, book_path, index):
        if book_path in self.bookmarks and 0 <= index < len(self.bookmarks[book_path]):
            del self.bookmarks[book_path][index]
            self.save_bookmarks()

class ReadingStats:
    """阅读统计"""
    def __init__(self, config_dir):
        self.config_dir = config_dir
        self.stats_file = os.path.join(config_dir, "reading_stats.json")
        self.stats = self.load_stats()
        self.session_start = datetime.now()
    
    def load_stats(self):
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载统计失败: {e}")
        return {}
    
    def save_stats(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存统计失败: {e}")
    
    def update_reading_time(self, book_path, minutes):
        if book_path not in self.stats:
            self.stats[book_path] = {'total_time': 0, 'sessions': 0}
        
        self.stats[book_path]['total_time'] += minutes
        self.stats[book_path]['sessions'] += 1
        self.save_stats()
    
    def get_stats(self, book_path):
        return self.stats.get(book_path, {'total_time': 0, 'sessions': 0})

class NovelReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config_dir = os.path.join(os.path.expanduser("~"), ".novel_reader")
        self.config_file = os.path.join(self.config_dir, "config.json")
        
        # 初始化组件
        self.bookmark_manager = BookmarkManager(self.config_dir)
        self.reading_stats = ReadingStats(self.config_dir)
        
        # 阅读状态
        self.current_book = None
        self.chapters = []
        self.current_chapter_index = 0
        self.current_position = 0
        
        # 加载配置
        self.config = self.load_config()
        
        # 初始化界面
        self.init_ui()
        self.apply_theme()
        
        # 定时器用于统计阅读时间
        self.reading_timer = QTimer()
        self.reading_timer.timeout.connect(self.update_reading_time)
        self.reading_timer.start(60000)  # 每分钟更新一次
    
    def load_config(self):
        default_config = {
            'font_family': 'Microsoft YaHei',
            'font_size': 14,
            'line_spacing': 1.5,
            'theme': 'light',
            'window_geometry': None,
            'last_book': None,
            'last_chapter': 0,
            'last_position': 0
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
        except Exception as e:
            print(f"加载配置失败: {e}")
        
        return default_config
    
    def save_config(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def init_ui(self):
        self.setWindowTitle("笔趣阁小说阅读器")
        self.setWindowIcon(QIcon())
        
        # 恢复窗口几何
        if self.config['window_geometry']:
            self.restoreGeometry(QByteArray.fromBase64(self.config['window_geometry'].encode()))
        else:
            self.resize(1000, 700)
            self.center()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板（章节列表）
        self.create_sidebar()
        main_layout.addWidget(self.sidebar, 1)
        
        # 右侧阅读区域
        self.create_reading_area()
        main_layout.addWidget(self.reading_area, 4)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 设置快捷键
        self.setup_shortcuts()
    
    def create_sidebar(self):
        self.sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        # 章节列表
        sidebar_layout.addWidget(QLabel("章节列表"))
        self.chapter_list = QListWidget()
        self.chapter_list.itemClicked.connect(self.on_chapter_selected)
        sidebar_layout.addWidget(self.chapter_list)
        
        # 书签列表
        sidebar_layout.addWidget(QLabel("书签"))
        self.bookmark_list = QListWidget()
        self.bookmark_list.itemDoubleClicked.connect(self.on_bookmark_selected)
        sidebar_layout.addWidget(self.bookmark_list)
        
        # 书签操作按钮
        bookmark_buttons = QHBoxLayout()
        add_bookmark_btn = QPushButton("添加书签")
        add_bookmark_btn.clicked.connect(self.add_bookmark)
        remove_bookmark_btn = QPushButton("删除书签")
        remove_bookmark_btn.clicked.connect(self.remove_bookmark)
        bookmark_buttons.addWidget(add_bookmark_btn)
        bookmark_buttons.addWidget(remove_bookmark_btn)
        sidebar_layout.addLayout(bookmark_buttons)
    
    def create_reading_area(self):
        self.reading_area = QWidget()
        reading_layout = QVBoxLayout(self.reading_area)
        
        # 章节标题
        self.chapter_title = QLabel()
        self.chapter_title.setAlignment(Qt.AlignCenter)
        self.chapter_title.setStyleSheet("font-weight: bold; font-size: 18px; margin: 10px;")
        reading_layout.addWidget(self.chapter_title)
        
        # 文本显示区域
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.verticalScrollBar().valueChanged.connect(self.on_scroll_changed)
        reading_layout.addWidget(self.text_display)
        
        # 导航按钮
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一章")
        self.prev_btn.clicked.connect(self.prev_chapter)
        self.next_btn = QPushButton("下一章")
        self.next_btn.clicked.connect(self.next_chapter)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.next_btn)
        reading_layout.addLayout(nav_layout)
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        open_action = QAction('打开小说', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_book)
        file_menu.addAction(open_action)
        
        open_file_action = QAction('打开小说文件', self)
        open_file_action.setShortcut('Ctrl+Shift+O')
        open_file_action.triggered.connect(self.open_file_directly)
        file_menu.addAction(open_file_action)
        
        open_folder_action = QAction('打开章节文件夹', self)
        open_folder_action.setShortcut('Ctrl+Shift+D')
        open_folder_action.triggered.connect(self.open_folder_directly)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 视图菜单
        view_menu = menubar.addMenu('视图')
        
        fullscreen_action = QAction('全屏模式', self)
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        # 设置菜单
        settings_menu = menubar.addMenu('设置')
        
        font_action = QAction('字体设置', self)
        font_action.triggered.connect(self.font_settings)
        settings_menu.addAction(font_action)
        
        theme_action = QAction('主题设置', self)
        theme_action.triggered.connect(self.theme_settings)
        settings_menu.addAction(theme_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具')
        
        search_action = QAction('搜索', self)
        search_action.setShortcut('Ctrl+F')
        search_action.triggered.connect(self.show_search)
        tools_menu.addAction(search_action)
        
        stats_action = QAction('阅读统计', self)
        stats_action.triggered.connect(self.show_stats)
        tools_menu.addAction(stats_action)
    
    def create_toolbar(self):
        toolbar = self.addToolBar('主工具栏')
        
        # 打开文件
        open_action = QAction('打开', self)
        open_action.triggered.connect(self.open_book)
        toolbar.addAction(open_action)
        
        toolbar.addSeparator()
        
        # 字体大小调整
        toolbar.addWidget(QLabel('字体大小:'))
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(self.config['font_size'])
        self.font_size_spin.valueChanged.connect(self.change_font_size)
        toolbar.addWidget(self.font_size_spin)
        
        toolbar.addSeparator()
        
        # 主题切换
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['浅色', '深色', '护眼', '羊皮纸'])
        theme_map = {'light': 0, 'dark': 1, 'green': 2, 'sepia': 3}
        self.theme_combo.setCurrentIndex(theme_map.get(self.config['theme'], 0))
        self.theme_combo.currentTextChanged.connect(self.change_theme)
        toolbar.addWidget(self.theme_combo)
    
    def create_status_bar(self):
        self.status_bar = self.statusBar()
        
        # 阅读进度
        self.progress_label = QLabel("进度: 0%")
        self.status_bar.addWidget(self.progress_label)
        
        # 章节信息
        self.chapter_info_label = QLabel("")
        self.status_bar.addPermanentWidget(self.chapter_info_label)
        
        # 阅读时间
        self.reading_time_label = QLabel("")
        self.status_bar.addPermanentWidget(self.reading_time_label)
    
    def setup_shortcuts(self):
        # 翻页快捷键
        QShortcut(QKeySequence(Qt.Key_Left), self, self.prev_chapter)
        QShortcut(QKeySequence(Qt.Key_Right), self, self.next_chapter)
        QShortcut(QKeySequence(Qt.Key_PageUp), self, self.scroll_up)
        QShortcut(QKeySequence(Qt.Key_PageDown), self, self.scroll_down)
        
        # 书签快捷键
        QShortcut(QKeySequence('Ctrl+B'), self, self.add_bookmark)
        
        # 搜索快捷键
        QShortcut(QKeySequence('Ctrl+F'), self, self.show_search)
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def open_book(self):
        # 创建选择对话框，让用户选择打开文件还是文件夹
        choice = QMessageBox.question(
            self, "选择打开方式", 
            "请选择要打开的内容类型：\n\n• 是(Yes) - 打开单个小说文件\n• 否(No) - 打开小说章节文件夹",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if choice == QMessageBox.Yes:
            # 打开单个文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择小说文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
            )
            if file_path:
                self.load_book(file_path)
        elif choice == QMessageBox.No:
            # 打开文件夹
            dir_path = QFileDialog.getExistingDirectory(
                self, "选择小说章节文件夹"
            )
            if dir_path:
                 self.load_book(dir_path)
    
    def open_file_directly(self):
        """直接打开小说文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择小说文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        if file_path:
            self.load_book(file_path)
    
    def open_folder_directly(self):
        """直接打开章节文件夹"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择小说章节文件夹"
        )
        if dir_path:
            self.load_book(dir_path)
    
    def load_book(self, file_path):
        try:
            # 检查是否是合并文件还是章节文件夹
            if os.path.isfile(file_path):
                self.load_merged_book(file_path)
            else:
                self.load_chapter_book(file_path)
            
            self.current_book = file_path
            self.config['last_book'] = file_path
            self.save_config()
            
            # 恢复上次阅读位置
            if self.config['last_chapter'] < len(self.chapters):
                self.current_chapter_index = self.config['last_chapter']
                self.display_chapter()
                self.text_display.verticalScrollBar().setValue(self.config['last_position'])
            
            self.update_bookmark_list()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载小说失败: {e}")
    
    def load_merged_book(self, file_path):
        """加载合并的小说文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 按分隔符分割章节
        chapter_parts = re.split(r'={50,}', content)
        
        self.chapters = []
        for i, part in enumerate(chapter_parts):
            part = part.strip()
            if part:
                lines = part.split('\n')
                title = lines[0].strip() if lines else f"第{i+1}章"
                content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else part
                
                self.chapters.append({
                    'title': title,
                    'content': content
                })
        
        self.update_chapter_list()
    
    def load_chapter_book(self, dir_path):
        """加载章节文件夹"""
        chapter_files = [f for f in os.listdir(dir_path) if f.endswith('.txt') and not f.endswith('_完整版.txt')]
        chapter_files.sort(key=lambda x: int(x.split('_')[0]))
        
        self.chapters = []
        for chapter_file in chapter_files:
            chapter_path = os.path.join(dir_path, chapter_file)
            with open(chapter_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            title = lines[0].strip() if lines else chapter_file
            chapter_content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else content
            
            self.chapters.append({
                'title': title,
                'content': chapter_content
            })
        
        self.update_chapter_list()
    
    def update_chapter_list(self):
        self.chapter_list.clear()
        for i, chapter in enumerate(self.chapters):
            item = QListWidgetItem(f"{i+1}. {chapter['title']}")
            item.setData(Qt.UserRole, i)
            self.chapter_list.addItem(item)
    
    def display_chapter(self):
        if 0 <= self.current_chapter_index < len(self.chapters):
            chapter = self.chapters[self.current_chapter_index]
            self.chapter_title.setText(chapter['title'])
            self.text_display.setPlainText(chapter['content'])
            
            # 更新章节列表选中状态
            self.chapter_list.setCurrentRow(self.current_chapter_index)
            
            # 更新状态栏
            self.update_status_bar()
            
            # 保存当前位置
            self.config['last_chapter'] = self.current_chapter_index
            self.save_config()
    
    def update_status_bar(self):
        if self.chapters:
            progress = (self.current_chapter_index + 1) / len(self.chapters) * 100
            self.progress_label.setText(f"进度: {progress:.1f}%")
            
            self.chapter_info_label.setText(
                f"第 {self.current_chapter_index + 1} 章 / 共 {len(self.chapters)} 章"
            )
            
            # 显示阅读时间
            if self.current_book:
                stats = self.reading_stats.get_stats(self.current_book)
                hours = stats['total_time'] // 60
                minutes = stats['total_time'] % 60
                self.reading_time_label.setText(f"阅读时间: {hours}h {minutes}m")
    
    def on_chapter_selected(self, item):
        chapter_index = item.data(Qt.UserRole)
        if chapter_index is not None:
            self.current_chapter_index = chapter_index
            self.display_chapter()
    
    def prev_chapter(self):
        if self.current_chapter_index > 0:
            self.current_chapter_index -= 1
            self.display_chapter()
    
    def next_chapter(self):
        if self.current_chapter_index < len(self.chapters) - 1:
            self.current_chapter_index += 1
            self.display_chapter()
    
    def scroll_up(self):
        scrollbar = self.text_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() - scrollbar.pageStep())
    
    def scroll_down(self):
        scrollbar = self.text_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() + scrollbar.pageStep())
    
    def on_scroll_changed(self, value):
        self.current_position = value
        self.config['last_position'] = value
    
    def change_font_size(self, size):
        self.config['font_size'] = size
        self.apply_font_settings()
        self.save_config()
    
    def change_theme(self, theme_name):
        theme_map = {'浅色': 'light', '深色': 'dark', '护眼': 'green', '羊皮纸': 'sepia'}
        self.config['theme'] = theme_map.get(theme_name, 'light')
        self.apply_theme()
        self.save_config()
    
    def apply_font_settings(self):
        font = QFont(self.config['font_family'], self.config['font_size'])
        self.text_display.setFont(font)
        
        # 设置行间距
        cursor = self.text_display.textCursor()
        block_format = QTextBlockFormat()
        block_format.setLineHeight(self.config['line_spacing'] * 100, QTextBlockFormat.ProportionalHeight)
        cursor.select(QTextCursor.Document)
        cursor.mergeBlockFormat(block_format)
    
    def apply_theme(self):
        themes = {
            'light': {
                'bg': '#ffffff',
                'text': '#000000',
                'sidebar_bg': '#f5f5f5'
            },
            'dark': {
                'bg': '#2b2b2b',
                'text': '#ffffff',
                'sidebar_bg': '#3c3c3c'
            },
            'green': {
                'bg': '#c7edcc',
                'text': '#2d5016',
                'sidebar_bg': '#b8e6c1'
            },
            'sepia': {
                'bg': '#f4ecd8',
                'text': '#5c4b37',
                'sidebar_bg': '#ede0c8'
            }
        }
        
        theme = themes.get(self.config['theme'], themes['light'])
        
        # 应用主题样式
        self.text_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme['bg']};
                color: {theme['text']};
                border: none;
                padding: 20px;
            }}
        """)
        
        self.sidebar.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['sidebar_bg']};
            }}
        """)
        
        self.apply_font_settings()
    
    def font_settings(self):
        font, ok = QFontDialog.getFont(QFont(self.config['font_family'], self.config['font_size']), self)
        if ok:
            self.config['font_family'] = font.family()
            self.config['font_size'] = font.pointSize()
            self.font_size_spin.setValue(self.config['font_size'])
            self.apply_font_settings()
            self.save_config()
    
    def theme_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("主题设置")
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        # 主题选择
        theme_group = QGroupBox("选择主题")
        theme_layout = QVBoxLayout(theme_group)
        
        theme_buttons = QButtonGroup()
        themes = [('浅色', 'light'), ('深色', 'dark'), ('护眼', 'green'), ('羊皮纸', 'sepia')]
        
        for name, value in themes:
            radio = QRadioButton(name)
            if value == self.config['theme']:
                radio.setChecked(True)
            theme_buttons.addButton(radio)
            radio.theme_value = value
            theme_layout.addWidget(radio)
        
        layout.addWidget(theme_group)
        
        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted:
            for button in theme_buttons.buttons():
                if button.isChecked():
                    self.config['theme'] = button.theme_value
                    theme_map = {'light': 0, 'dark': 1, 'green': 2, 'sepia': 3}
                    self.theme_combo.setCurrentIndex(theme_map.get(button.theme_value, 0))
                    self.apply_theme()
                    self.save_config()
                    break
    
    def show_search(self):
        text, ok = QInputDialog.getText(self, "搜索", "请输入搜索内容:")
        if ok and text:
            self.search_text(text)
    
    def search_text(self, text):
        cursor = self.text_display.textCursor()
        cursor.movePosition(QTextCursor.Start)
        
        found = self.text_display.find(text)
        if not found:
            QMessageBox.information(self, "搜索结果", "未找到匹配的内容")
    
    def add_bookmark(self):
        if not self.current_book:
            QMessageBox.warning(self, "警告", "请先打开一本小说")
            return
        
        note, ok = QInputDialog.getText(self, "添加书签", "书签备注 (可选):")
        if ok:
            self.bookmark_manager.add_bookmark(
                self.current_book,
                self.current_chapter_index,
                self.current_position,
                note
            )
            self.update_bookmark_list()
            QMessageBox.information(self, "成功", "书签已添加")
    
    def remove_bookmark(self):
        current_row = self.bookmark_list.currentRow()
        if current_row >= 0:
            self.bookmark_manager.remove_bookmark(self.current_book, current_row)
            self.update_bookmark_list()
            QMessageBox.information(self, "成功", "书签已删除")
    
    def update_bookmark_list(self):
        self.bookmark_list.clear()
        if self.current_book:
            bookmarks = self.bookmark_manager.get_bookmarks(self.current_book)
            for i, bookmark in enumerate(bookmarks):
                chapter_title = self.chapters[bookmark['chapter_index']]['title'] if bookmark['chapter_index'] < len(self.chapters) else "未知章节"
                item_text = f"{chapter_title}"
                if bookmark['note']:
                    item_text += f" - {bookmark['note']}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, bookmark)
                self.bookmark_list.addItem(item)
    
    def on_bookmark_selected(self, item):
        bookmark = item.data(Qt.UserRole)
        if bookmark:
            self.current_chapter_index = bookmark['chapter_index']
            self.display_chapter()
            self.text_display.verticalScrollBar().setValue(bookmark['position'])
    
    def show_stats(self):
        if not self.current_book:
            QMessageBox.warning(self, "警告", "请先打开一本小说")
            return
        
        stats = self.reading_stats.get_stats(self.current_book)
        hours = stats['total_time'] // 60
        minutes = stats['total_time'] % 60
        
        progress = (self.current_chapter_index + 1) / len(self.chapters) * 100 if self.chapters else 0
        
        message = f"""
阅读统计信息:

总阅读时间: {hours} 小时 {minutes} 分钟
阅读会话: {stats['sessions']} 次
当前进度: {progress:.1f}%
当前章节: 第 {self.current_chapter_index + 1} 章
总章节数: {len(self.chapters)}
        """
        
        QMessageBox.information(self, "阅读统计", message)
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def update_reading_time(self):
        if self.current_book:
            self.reading_stats.update_reading_time(self.current_book, 1)
            self.update_status_bar()
    
    def closeEvent(self, event):
        # 保存窗口几何
        self.config['window_geometry'] = self.saveGeometry().toBase64().data().decode()
        self.save_config()
        
        # 更新最后阅读时间
        if self.current_book:
            session_time = (datetime.now() - self.reading_stats.session_start).total_seconds() / 60
            self.reading_stats.update_reading_time(self.current_book, int(session_time))
        
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("笔趣阁小说阅读器")
    app.setApplicationVersion("1.0")
    
    # 设置应用图标和样式
    app.setStyle('Fusion')
    
    reader = NovelReader()
    
    # 如果有上次打开的书籍，自动加载
    if reader.config['last_book'] and os.path.exists(reader.config['last_book']):
        reader.load_book(reader.config['last_book'])
    
    reader.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()