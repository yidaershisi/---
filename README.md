# 笔趣阁小说爬取与阅读工具

一个功能完整的小说下载和阅读工具，支持从笔趣阁网站爬取小说并提供优质的阅读体验。

## 功能特点

### 🕷️ 爬虫功能
- **智能解析**：自动解析小说目录页面和章节内容
- **多线程下载**：支持多线程并发下载，提高效率
- **断点续传**：支持断点续爬，避免重复下载
- **错误处理**：完善的错误处理机制，应对网络问题
- **自动编码检测**：智能检测网页编码，确保内容正确
- **进度保存**：实时保存下载进度，支持随时恢复

### 📖 阅读器功能
- **多主题支持**：浅色、深色、护眼绿、羊皮纸四种主题
- **字体调节**：支持字体大小、字体样式、行间距调整
- **章节导航**：左侧章节列表，支持快速跳转
- **书签管理**：添加、删除和管理书签，支持备注
- **阅读记忆**：自动记住上次阅读位置
- **全文搜索**：支持文本搜索功能
- **阅读统计**：记录阅读时间、进度等统计信息
- **全屏模式**：支持全屏阅读，沉浸式体验
- **快捷键支持**：丰富的快捷键操作

## 安装要求

### 系统要求
- Windows 10/11
- Python 3.7+

### 依赖库
```
requests==2.31.0
beautifulsoup4==4.12.2
PyQt5==5.15.9
lxml==4.9.3
chardet==5.2.0
```

## 安装步骤

1. **克隆或下载项目**
   ```bash
   # 如果使用git
   git clone <项目地址>
   cd 笔趣阁
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **运行程序**
   ```bash
   python main.py
   ```

## 使用说明

### 下载小说

1. **获取小说ID**
   - 在浏览器中打开笔趣阁网站
   - 找到想要下载的小说
   - 从网址中复制小说ID（数字部分）
   - 例如：`https://www.577ff.cfd/book/12345/` 中的 `12345`

2. **开始下载**
   - 打开程序，切换到"小说下载"选项卡
   - 输入小说ID
   - 选择保存目录（默认为novels文件夹）
   - 点击"开始下载"按钮

3. **下载完成**
   - 程序会自动创建小说文件夹
   - 按章节分别保存为txt文件
   - 同时生成完整版合并文件

### 阅读小说

1. **打开阅读器**
   - 切换到"小说阅读"选项卡
   - 点击"打开阅读器"按钮
   - 或者双击"最近下载的小说"列表中的项目

2. **阅读操作**
   - 使用左侧章节列表导航
   - 通过工具栏调整字体和主题
   - 使用快捷键快速操作

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+O | 打开文件 |
| Ctrl+F | 搜索文本 |
| Ctrl+B | 添加书签 |
| F11 | 全屏模式 |
| ← → | 上一章/下一章 |
| Page Up/Down | 向上/向下翻页 |
| Ctrl+Q | 退出程序 |

## 文件结构

```
笔趣阁/
├── main.py              # 主程序入口
├── spider.py            # 爬虫模块
├── reader.py            # 阅读器模块
├── requirements.txt     # 依赖列表
├── README.md           # 说明文档
└── novels/             # 下载的小说目录
    └── 小说ID_小说名/
        ├── 0001_第一章.txt
        ├── 0002_第二章.txt
        └── 小说名_完整版.txt
```

## 配置文件

程序会在用户目录下创建配置文件夹：
- Windows: `C:\Users\用户名\.novel_reader\`

配置文件包括：
- `config.json` - 阅读器设置
- `bookmarks.json` - 书签数据
- `reading_stats.json` - 阅读统计
- `download_progress.json` - 下载进度

## 注意事项

1. **网络连接**：确保网络连接稳定，下载过程中避免断网
2. **磁盘空间**：确保有足够的磁盘空间保存小说文件
3. **防火墙**：如果遇到网络问题，检查防火墙设置
4. **合法使用**：请遵守相关法律法规，仅用于个人学习研究

## 故障排除

### 常见问题

1. **下载失败**
   - 检查网络连接
   - 确认小说ID正确
   - 尝试更换网络环境

2. **编码问题**
   - 程序已自动处理编码检测
   - 如仍有问题，请检查系统编码设置

3. **界面显示异常**
   - 确保已正确安装PyQt5
   - 尝试重启程序

4. **文件打开失败**
   - 检查文件路径是否正确
   - 确认文件未被其他程序占用

## 技术特点

- **模块化设计**：爬虫和阅读器分离，便于维护
- **异步下载**：多线程下载，提高效率
- **智能解析**：多种选择器适配不同页面结构
- **用户友好**：直观的图形界面，操作简单
- **数据持久化**：配置和进度自动保存
- **跨平台兼容**：基于Python和Qt，支持多平台

## 版本历史

### v1.0 (当前版本)
- 初始版本发布
- 完整的下载和阅读功能
- 图形用户界面
- 多主题支持
- 书签和统计功能

## 许可证

本项目仅供学习和研究使用，请遵守相关法律法规。

## 贡献

欢迎提交问题报告和功能建议！

---

**享受愉快的阅读时光！** 📚✨