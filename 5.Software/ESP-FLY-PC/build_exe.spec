# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件
用于将 ESP-FLY-PC 打包成 Windows exe 可执行文件

打包模式：目录模式（onedir）
- 优势：启动速度快，运行性能好，无需每次解压文件
- 输出：dist/ESP-FLY-PC/ 文件夹，包含 ESP-FLY-PC.exe 和所有依赖文件
"""

import os
import glob
import site
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_all

# 项目根目录（spec 文件所在目录）
# 使用 __file__ 获取当前 spec 文件所在目录
try:
    project_root = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # 如果 __file__ 不存在，使用当前工作目录
    project_root = os.getcwd()

# 收集所有需要的数据文件
datas = [
    # 配置文件（打包进exe内部，作为资源文件）
    ('data/config.ini', '.'),  # 打包到临时目录的根目录，可通过 resource_path("config.ini") 访问
    # 3D模型资源文件
    ('resources', 'resources'),
]

# 收集 PyQt6 的隐藏导入
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pyqtgraph',
    'pyvista',
    'pyvistaqt',
    'vtk',
    'vtkmodules',
    'vtkmodules.all',
    'vtkmodules.qt.QVTKRenderWindowInteractor',
    'vtkmodules.util',
    'vtkmodules.util.numpy_support',
    'vtkmodules.numpy_interface.dataset_adapter',
    # VTK核心模块
    'vtkmodules.vtkCommonCore',
    'vtkmodules.vtkCommonDataModel',
    'vtkmodules.vtkCommonMath',
    'vtkmodules.vtkCommonTransforms',
    'vtkmodules.vtkRenderingCore',
    'vtkmodules.vtkRenderingOpenGL2',
    'vtkmodules.vtkInteractionStyle',
    'vtkmodules.vtkInteractionWidgets',
    'vtkmodules.vtkFiltersCore',
    'vtkmodules.vtkFiltersGeneral',
    'vtkmodules.vtkIOGeometry',
    'vtkmodules.vtkIOLegacy',
    'vtkmodules.vtkIOPLY',
    'numpy',
    'netifaces',
    'matplotlib',  # PyVista需要matplotlib
    'matplotlib.backends.backend_qtagg',  # PyQt6后端
]

# 收集 PyVista/VTK 的所有子模块（包括动态导入的模块）
try:
    pyvista_submodules = collect_submodules('pyvista')
    hiddenimports.extend(pyvista_submodules)
except:
    pass

try:
    vtk_submodules = collect_submodules('vtkmodules')
    hiddenimports.extend(vtk_submodules)
except:
    pass

# 收集 PyVista/VTK 的数据文件和二进制文件
# collect_all 返回 (binaries, datas, hiddenimports)
binaries = []

try:
    # 使用 collect_all 收集所有相关文件（包括 DLL）
    pyvista_all = collect_all('pyvista')
    if pyvista_all and len(pyvista_all) >= 3:
        binaries.extend(pyvista_all[0])  # 二进制文件（DLL等）
        datas.extend(pyvista_all[1])  # 数据文件
        hiddenimports.extend(pyvista_all[2])  # 隐藏导入
        print(f"[信息] 收集到 {len(pyvista_all[0])} 个PyVista二进制文件")
except Exception as e:
    print(f"[警告] 收集PyVista文件时出错: {e}")
    import traceback
    traceback.print_exc()
    # 回退到基本收集方法
    try:
        pyvista_datas = collect_data_files('pyvista')
        datas.extend(pyvista_datas)
    except:
        pass

try:
    # 使用 collect_all 收集VTK的所有文件
    vtk_all = collect_all('vtkmodules')
    if vtk_all and len(vtk_all) >= 3:
        binaries.extend(vtk_all[0])  # 二进制文件（DLL等）
        datas.extend(vtk_all[1])  # 数据文件
        hiddenimports.extend(vtk_all[2])  # 隐藏导入
        print(f"[信息] 收集到 {len(vtk_all[0])} 个VTK二进制文件")
except Exception as e:
    print(f"[警告] 收集VTK文件时出错: {e}")
    import traceback
    traceback.print_exc()
    # 回退到基本收集方法
    try:
        vtk_datas = collect_data_files('vtk')
        datas.extend(vtk_datas)
    except:
        pass

# 手动添加VTK的DLL文件（如果collect_all失败或收集不完整）
# 即使collect_all成功，也尝试手动添加以确保完整性
print("[信息] 尝试手动查找VTK DLL文件...")
try:
    # 查找site-packages中的VTK DLL
    for site_pkg in site.getsitepackages():
        vtk_dll_pattern = os.path.join(site_pkg, 'vtkmodules', '**', '*.dll')
        vtk_dlls = glob.glob(vtk_dll_pattern, recursive=True)
        if vtk_dlls:
            print(f"[信息] 在 {site_pkg} 中找到 {len(vtk_dlls)} 个VTK DLL文件")
            for dll in vtk_dlls:
                # 计算相对路径，DLL应该放在与vtkmodules同级目录
                rel_path = os.path.relpath(dll, site_pkg)
                target_dir = os.path.dirname(rel_path)
                # 避免重复添加
                dll_tuple = (dll, target_dir)
                if dll_tuple not in binaries:
                    binaries.append(dll_tuple)
            break
except Exception as e:
    print(f"[警告] 手动查找VTK DLL时出错: {e}")

print(f"[信息] 总共收集到 {len(binaries)} 个二进制文件")

# 收集matplotlib的数据文件（PyVista需要）
try:
    matplotlib_datas = collect_data_files('matplotlib')
    datas.extend(matplotlib_datas)
    print(f"[信息] 收集到 {len(matplotlib_datas)} 个matplotlib数据文件")
except Exception as e:
    print(f"[警告] 收集matplotlib数据文件时出错: {e}")

# 字节码加密（可选，设置为 None 表示不加密）
block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=binaries,  # 包含VTK/PyVista的DLL文件
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 注意：不能排除matplotlib，因为PyVista依赖它
        # 'matplotlib',  # PyVista需要matplotlib
        'pandas',
        'scipy',
        # 'PIL',  # matplotlib可能需要PIL
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 启动画面（Splash Screen）
# 注意：在目录模式（onedir）下，Splash Screen 存在兼容性问题
# 会导致程序启动时卡住（KeyError: '_PYI_SPLASH_IPC'）
# 由于目录模式启动速度已经很快，因此禁用 Splash
# 如需启用，请确保在单文件模式（onefile）下使用
# splash = Splash(
#     'splash.png',
#     binaries=a.binaries,
#     datas=a.datas,
#     text_pos=None,
#     text_size=9,
#     text_font='Arial',
#     text_color='darkgray',
#     text_default='',
#     minify_script=True,
#     always_on_top=True,
# )

exe = EXE(
    pyz,
    a.scripts,
    # splash,  # 添加启动画面（临时禁用）
    # splash.binaries,  # 添加启动画面的二进制文件（临时禁用）
    [],
    name='ESP-FLY-PC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用UPX压缩，VTK的DLL可能无法被UPX正确处理
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口（发布版本）
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径，如 'icon.ico'
)

# 目录模式打包：将所有依赖文件放在exe同目录下
# 这样可以避免每次启动时解压文件，大幅提升启动速度和运行性能
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='ESP-FLY-PC',
)
