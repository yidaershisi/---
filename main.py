#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
笔趣阁小说工具主程序
整合爬虫和阅读器功能的统一界面
"""

import sys
import os
import threading
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 导入自定义模块
from spider import NovelSpider
from reader import NovelReader

class DownloadWorker(QThread):
    """下载工作线程"""
    progress_updated = pyqtSignal(str)
    download_finished = pyqtSignal(str, bool)
    
    def __init__(self, novel_id, output_dir):
        super().__init__()
        self.novel_id = novel_id
        self.output_dir = output_dir
        self.spider = NovelSpider(max_workers=3)
    
    def run(self):
        try:
            self.progress_updated.emit(f"开始下载小说 ID: {self.novel_id}")
            result = self.spider.download_novel(self.novel_id, self.output_dir)
            
            if result:
                self.progress_updated.emit("下载完成！")
                self.download_finished.emit(result, True)
            else:
                self.progress_updated.emit("下载失败！")
                self.download_finished.emit("", False)
                
        except Exception as e:
            self.progress_updated.emit(f"下载出错: {str(e)}")
            self.download_finished.emit("", False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.reader_window = None
        self.download_worker = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("笔趣阁小说工具 v1.0")
        self.setWindowIcon(QIcon())
        self.resize(800, 600)
        self.center()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title_label = QLabel("笔趣阁小说下载与阅读工具")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                margin: 20px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 下载选项卡
        self.create_download_tab()
        
        # 阅读选项卡
        self.create_reader_tab()
        
        # 帮助选项卡
        self.create_help_tab()
        
        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
    
    def create_download_tab(self):
        download_widget = QWidget()
        layout = QVBoxLayout(download_widget)
        
        # 说明文字
        info_label = QLabel("""
        <h3>小说下载功能</h3>
        <p>请输入笔趣阁小说的ID来下载小说。小说ID可以从网址中获取，例如：</p>
        <p><b>https://www.577ff.cfd/book/12345/</b> 中的 <b>12345</b> 就是小说ID</p>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 输入区域
        input_group = QGroupBox("下载设置")
        input_layout = QFormLayout(input_group)
        
        self.novel_id_input = QLineEdit()
        self.novel_id_input.setPlaceholderText("请输入小说ID，例如：12345")
        input_layout.addRow("小说ID:", self.novel_id_input)
        
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText("novels")
        self.output_dir_input.setPlaceholderText("下载保存目录")
        
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.output_dir_input)
        
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(browse_btn)
        
        dir_widget = QWidget()
        dir_widget.setLayout(dir_layout)
        input_layout.addRow("保存目录:", dir_widget)
        
        layout.addWidget(input_group)
        
        # 下载按钮
        button_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("开始下载")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.download_btn.clicked.connect(self.start_download)
        
        self.stop_btn = QPushButton("停止下载")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_download)
        self.stop_btn.setEnabled(False)
        
        button_layout.addWidget(self.download_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 进度显示
        progress_group = QGroupBox("下载进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        self.progress_text.setMaximumHeight(200)
        progress_layout.addWidget(self.progress_text)
        
        layout.addWidget(progress_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(download_widget, "小说下载")
    
    def create_reader_tab(self):
        reader_widget = QWidget()
        layout = QVBoxLayout(reader_widget)
        
        # 说明文字
        info_label = QLabel("""
        <h3>小说阅读功能</h3>
        <p>支持打开下载的小说文件进行阅读，提供丰富的阅读体验：</p>
        <ul>
        <li>多种主题模式（浅色、深色、护眼、羊皮纸）</li>
        <li>字体大小和样式调整</li>
        <li>章节导航和跳转</li>
        <li>书签管理功能</li>
        <li>阅读进度记忆</li>
        <li>全文搜索功能</li>
        <li>阅读统计信息</li>
        </ul>
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 阅读器控制
        reader_group = QGroupBox("阅读器")
        reader_layout = QVBoxLayout(reader_group)
        
        # 打开阅读器按钮
        open_reader_btn = QPushButton("打开阅读器")
        open_reader_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 15px 30px;
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        open_reader_btn.clicked.connect(self.open_reader)
        reader_layout.addWidget(open_reader_btn)
        
        # 快速打开文件
        quick_open_btn = QPushButton("快速打开小说文件")
        quick_open_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        quick_open_btn.clicked.connect(self.quick_open_file)
        reader_layout.addWidget(quick_open_btn)
        
        # 快速打开文件夹
        quick_open_folder_btn = QPushButton("快速打开章节文件夹")
        quick_open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
        """)
        quick_open_folder_btn.clicked.connect(self.quick_open_folder)
        reader_layout.addWidget(quick_open_folder_btn)
        
        layout.addWidget(reader_group)
        
        # 最近下载的小说
        recent_group = QGroupBox("最近下载的小说")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_novels_list = QListWidget()
        self.recent_novels_list.itemDoubleClicked.connect(self.open_recent_novel)
        recent_layout.addWidget(self.recent_novels_list)
        
        refresh_btn = QPushButton("刷新列表")
        refresh_btn.clicked.connect(self.refresh_recent_novels)
        recent_layout.addWidget(refresh_btn)
        
        layout.addWidget(recent_group)
        
        self.tab_widget.addTab(reader_widget, "小说阅读")
        
        # 初始化时刷新最近小说列表
        self.refresh_recent_novels()
    
    def create_help_tab(self):
        help_widget = QWidget()
        layout = QVBoxLayout(help_widget)
        
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>使用帮助</h2>
        
        <h3>1. 小说下载</h3>
        <p><b>步骤：</b></p>
        <ol>
        <li>在浏览器中打开笔趣阁网站，找到想要下载的小说</li>
        <li>从网址中复制小说ID（数字部分）</li>
        <li>在"小说下载"选项卡中输入小说ID</li>
        <li>选择保存目录（默认为novels文件夹）</li>
        <li>点击"开始下载"按钮</li>
        </ol>
        
        <p><b>注意事项：</b></p>
        <ul>
        <li>下载过程中请保持网络连接稳定</li>
        <li>支持断点续传，可以随时停止和继续下载</li>
        <li>下载的小说会按章节分别保存，同时生成完整版文件</li>
        </ul>
        
        <h3>2. 小说阅读</h3>
        <p><b>功能特点：</b></p>
        <ul>
        <li><b>多主题支持：</b>浅色、深色、护眼绿、羊皮纸四种主题</li>
        <li><b>字体调节：</b>支持字体大小、字体样式、行间距调整</li>
        <li><b>章节导航：</b>左侧章节列表，支持快速跳转</li>
        <li><b>书签功能：</b>可添加书签并添加备注</li>
        <li><b>阅读记忆：</b>自动记住上次阅读位置</li>
        <li><b>搜索功能：</b>支持全文搜索（Ctrl+F）</li>
        <li><b>阅读统计：</b>记录阅读时间和进度</li>
        </ul>
        
        <p><b>快捷键：</b></p>
        <ul>
        <li>Ctrl+O：打开文件</li>
        <li>Ctrl+F：搜索文本</li>
        <li>Ctrl+B：添加书签</li>
        <li>F11：全屏模式</li>
        <li>左右箭头：上一章/下一章</li>
        <li>Page Up/Down：向上/向下翻页</li>
        </ul>
        
        <h3>3. 技术支持</h3>
        <p>如果遇到问题，请检查：</p>
        <ul>
        <li>网络连接是否正常</li>
        <li>小说ID是否正确</li>
        <li>是否有足够的磁盘空间</li>
        <li>防火墙是否阻止了程序访问网络</li>
        </ul>
        
        <h3>4. 版本信息</h3>
        <p>笔趣阁小说工具 v1.0</p>
        <p>支持多线程下载、断点续传、丰富的阅读体验</p>
        """)
        
        layout.addWidget(help_text)
        
        self.tab_widget.addTab(help_widget, "使用帮助")
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def browse_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if dir_path:
            self.output_dir_input.setText(dir_path)
    
    def start_download(self):
        novel_id = self.novel_id_input.text().strip()
        if not novel_id:
            QMessageBox.warning(self, "警告", "请输入小说ID")
            return
        
        if not novel_id.isdigit():
            QMessageBox.warning(self, "警告", "小说ID应该是数字")
            return
        
        output_dir = self.output_dir_input.text().strip() or "novels"
        
        # 清空进度显示
        self.progress_text.clear()
        
        # 创建下载线程
        self.download_worker = DownloadWorker(novel_id, output_dir)
        self.download_worker.progress_updated.connect(self.update_progress)
        self.download_worker.download_finished.connect(self.download_completed)
        
        # 更新按钮状态
        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # 开始下载
        self.download_worker.start()
        self.status_bar.showMessage("正在下载...")
    
    def stop_download(self):
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.terminate()
            self.download_worker.wait()
            
            self.progress_text.append("下载已停止")
            self.download_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_bar.showMessage("下载已停止")
    
    def update_progress(self, message):
        self.progress_text.append(message)
        # 自动滚动到底部
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def download_completed(self, result_path, success):
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            self.status_bar.showMessage("下载完成")
            
            # 询问是否立即打开阅读器
            reply = QMessageBox.question(
                self, "下载完成", 
                f"小说下载完成！\n保存位置：{result_path}\n\n是否立即打开阅读器？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.open_reader_with_book(result_path)
            
            # 刷新最近小说列表
            self.refresh_recent_novels()
        else:
            self.status_bar.showMessage("下载失败")
            QMessageBox.critical(self, "错误", "下载失败，请检查网络连接和小说ID")
    
    def open_reader(self):
        if self.reader_window is None:
            self.reader_window = NovelReader()
        
        self.reader_window.show()
        self.reader_window.raise_()
        self.reader_window.activateWindow()
    
    def open_reader_with_book(self, book_path):
        self.open_reader()
        
        # 查找完整版文件
        if os.path.isdir(book_path):
            complete_files = [f for f in os.listdir(book_path) if f.endswith('_完整版.txt')]
            if complete_files:
                complete_file = os.path.join(book_path, complete_files[0])
                self.reader_window.load_book(complete_file)
            else:
                self.reader_window.load_book(book_path)
        else:
            self.reader_window.load_book(book_path)
    
    def quick_open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择小说文件", "", "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            self.open_reader_with_book(file_path)
    
    def quick_open_folder(self):
        """快速打开章节文件夹"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择小说章节文件夹"
        )
        
        if dir_path:
            self.open_reader_with_book(dir_path)
    
    def refresh_recent_novels(self):
        self.recent_novels_list.clear()
        
        novels_dir = "novels"
        if os.path.exists(novels_dir):
            for item in os.listdir(novels_dir):
                item_path = os.path.join(novels_dir, item)
                if os.path.isdir(item_path):
                    # 查找完整版文件
                    complete_files = [f for f in os.listdir(item_path) if f.endswith('_完整版.txt')]
                    if complete_files:
                        novel_name = complete_files[0].replace('_完整版.txt', '')
                        list_item = QListWidgetItem(novel_name)
                        list_item.setData(Qt.UserRole, item_path)
                        self.recent_novels_list.addItem(list_item)
    
    def open_recent_novel(self, item):
        book_path = item.data(Qt.UserRole)
        if book_path:
            self.open_reader_with_book(book_path)
    
    def closeEvent(self, event):
        # 关闭阅读器窗口
        if self.reader_window:
            self.reader_window.close()
        
        # 停止下载线程
        if self.download_worker and self.download_worker.isRunning():
            self.download_worker.terminate()
            self.download_worker.wait()
        
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("笔趣阁小说工具")
    app.setApplicationVersion("1.0")
    
    # 设置应用样式
    app.setStyle('Fusion')
    
    # 设置全局样式表
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f8f9fa;
        }
        QTabWidget::pane {
            border: 1px solid #c0c0c0;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #e9ecef;
            padding: 8px 16px;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: white;
            border-bottom: 2px solid #007bff;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()