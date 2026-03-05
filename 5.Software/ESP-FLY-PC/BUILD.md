# ESP-FLY-PC 打包说明

本文档说明如何将 ESP-FLY-PC 打包成 Windows exe 可执行文件。

## 前置要求

1. **Python 环境**
   - Python 3.8 或更高版本
   - 已安装项目依赖包（运行 `pip install -r requirements.txt`）

2. **操作系统**
   - Windows 10/11（推荐）

## 快速打包

### 方法一：使用打包脚本（推荐）

1. 双击运行 `build_exe.bat` 脚本
2. 等待打包完成
3. 在 `dist` 目录下找到 `ESP-FLY-PC.exe`

### 方法二：手动打包

```bash
# 1. 安装 PyInstaller（如果未安装）
pip install pyinstaller

# 2. 执行打包命令
pyinstaller build_exe.spec

# 3. 打包完成后，exe 文件在 dist 目录下
```

## 打包输出

打包完成后，会生成以下目录：

```
dist/
└── ESP-FLY-PC/             # 应用程序文件夹（目录模式）
    ├── ESP-FLY-PC.exe      # 主可执行文件
    ├── config.ini          # 配置文件（首次运行自动创建）
    ├── resources/          # 资源文件（3D模型等）
    ├── *.dll               # 依赖库文件（VTK、PyQt6等）
    └── ...                 # 其他依赖文件

build/                      # 临时构建文件（可删除）
```

## 文件说明

- **build_exe.spec**: PyInstaller 打包配置文件
- **build_exe.bat**: Windows 打包脚本
- **create_splash_image.py**: 生成启动画面图片的脚本
- **splash.png**: 启动画面图片（自动生成）
- **common/resource_path.py**: 资源路径工具（支持打包后的路径）

## 打包后的文件结构

打包后使用**目录模式**（onedir），优势：
- **启动速度快**：无需每次解压文件到临时目录
- **运行性能好**：直接从磁盘加载 DLL，避免临时目录 IO 开销
- **占用空间小**：共享依赖库文件

包含内容：
- 所有 Python 代码和依赖库
- PyQt6 GUI 框架
- PyVista/VTK 3D 渲染库（DLL 文件在同目录）
- pyqtgraph 图表库
- 所有资源文件（3D 模型等）

## 配置文件处理

打包后的程序首次运行时：
1. **配置文件已包含在应用目录**：`config.ini` 已打包到应用文件夹中
2. **自动创建用户配置**：首次运行会在应用目录下创建 `config.ini`（从打包资源复制）
3. **优先使用用户配置**：如果应用目录下有 `config.ini`，优先使用该文件（允许用户自定义）
4. **配置持久化**：用户修改的配置会保存，不会被覆盖

## 资源文件

- **3D 模型文件**：已打包到应用目录的 `resources` 文件夹中
- **配置文件**：已打包到应用目录，首次运行会自动创建用户可编辑的副本
- **依赖库文件**：所有 DLL 文件与 exe 在同一目录，无需解压

## 常见问题

### 1. 打包失败：找不到模块

**解决方法**：
- 确保所有依赖都已安装：`pip install -r requirements.txt`
- 检查 `build_exe.spec` 中的 `hiddenimports` 列表

### 2. 打包后 exe 无法运行

**解决方法**：
- 检查是否有杀毒软件拦截
- 尝试在命令行运行 exe，查看错误信息
- 确保所有资源文件都已正确打包

### 3. 打包后的文件夹很大（>100MB）

**原因**：
- PyQt6 和 PyVista/VTK 库体积较大
- 这是正常现象，包含所有依赖库和资源文件

**说明**：
- 当前使用目录模式（onedir）打包，以获得最佳性能
- 如需单文件打包，可修改 spec 文件，但会牺牲启动速度和运行性能

### 4. 3D 模型无法加载

**解决方法**：
- 检查 `resources/models/` 目录下的文件是否存在
- 确保 `build_exe.spec` 中的 `datas` 包含了资源文件

### 5. 配置文件路径错误

**解决方法**：
- 配置文件已打包到应用目录，程序会自动处理
- 首次运行会在应用目录创建 `config.ini`（从打包资源复制）
- 如果应用目录下有 `config.ini`，优先使用该文件

## 启动画面

**注意**：当前版本**已禁用启动画面**，原因如下：

1. **目录模式兼容性问题**：PyInstaller 的 Splash Screen 在目录模式（onedir）下存在 IPC 通信问题，会导致程序启动时卡住
2. **启动速度已足够快**：目录模式无需解压文件，启动速度本身就很快，不需要启动画面遮挡
3. **更好的用户体验**：直接显示主窗口，比显示启动画面再切换更流畅

**如需启用启动画面**（仅在单文件模式下）：

在 `build_exe.spec` 中取消注释以下代码：
```python
splash = Splash(
    'splash.png',  # 启动画面图片
    binaries=a.binaries,
    datas=a.datas,
    text_pos=None,
    text_size=9,
    text_font='Arial',
    text_color='darkgray',
    text_default='',
    minify_script=True,
    always_on_top=True,
)
```

并在 EXE 配置中添加：
```python
exe = EXE(
    pyz,
    a.scripts,
    splash,  # 添加启动画面
    splash.binaries,  # 添加启动画面的二进制文件
    ...
)
```

**⚠️ 警告**：在目录模式下启用启动画面可能导致程序无法启动！

## 高级配置

### 添加图标

在 `build_exe.spec` 中修改：
```python
icon='icon.ico',  # 图标文件路径
```

### 修改输出文件名

在 `build_exe.spec` 中修改：
```python
name='ESP-FLY-PC',  # 改为你想要的名称
```

### 显示控制台窗口（调试用）

在 `build_exe.spec` 中修改：
```python
console=True,  # 改为 True
```

## 测试打包结果

1. 在 `dist/ESP-FLY-PC/` 目录下运行 `ESP-FLY-PC.exe`
2. 检查功能是否正常：
   - 连接无人机
   - 3D 姿态显示
   - 波形图表
   - PID 调参
   - 飞行控制
3. 检查启动速度是否显著提升（相比之前的单文件模式）

## 分发说明

打包完成后，可以：
1. **分发整个 `ESP-FLY-PC` 文件夹**（包含 exe 和所有依赖文件）
2. **推荐打包成压缩包**：将 `dist/ESP-FLY-PC/` 文件夹打包成 zip，方便分发
3. **用户无需安装 Python**：解压后可直接运行 exe 文件
4. **可自定义配置**：用户可以编辑应用目录下的 `config.ini` 来自定义配置
5. **性能优势**：目录模式启动速度快，运行流畅，避免了单文件模式的卡顿问题

## 注意事项

1. **目录完整性**：分发时请确保整个 `ESP-FLY-PC` 文件夹完整，不要只复制 exe 文件
2. **杀毒软件**：某些杀毒软件可能误报，需要添加信任
3. **Windows Defender**：可能需要添加排除项
4. **依赖库更新**：如果更新了依赖库，需要重新打包
5. **启动速度**：目录模式启动速度比单文件模式快很多，运行更流畅

## 技术支持

如遇到打包问题，请检查：
1. Python 版本是否符合要求
2. 所有依赖是否已正确安装
3. 资源文件是否存在
4. 查看打包过程中的错误信息
