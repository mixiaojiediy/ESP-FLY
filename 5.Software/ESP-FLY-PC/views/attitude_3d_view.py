"""
Attitude3DView - 3D姿态显示组件
使用PyVista/VTK渲染3D无人机模型，实时显示姿态
"""

import os
import time
import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, pyqtSlot
from common.resource_path import resource_path

# 尝试导入PyVista，如果失败则使用简化版本
try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
    import vtk

    PYVISTA_AVAILABLE = True
    print("[信息] PyVista加载成功")
except ImportError as e:
    PYVISTA_AVAILABLE = False
    print(f"[警告] PyVista导入失败 (ImportError): {e}")
    print("[警告] 3D姿态显示将使用简化版本")
except Exception as e:
    PYVISTA_AVAILABLE = False
    print(f"[错误] PyVista加载失败 (其他错误): {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    print("[警告] 3D姿态显示将使用简化版本")


class Attitude3DView(QWidget):
    """
    3D姿态显示组件View

    使用PyVista/VTK进行3D渲染，支持：
    - 自定义OBJ模型加载（带MTL材质）
    - 默认几何体模型（备用）
    - 实时姿态旋转更新
    - 简化文本视图（无PyVista时）
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 当前姿态角
        self._roll = 0.0
        self._pitch = 0.0
        self._yaw = 0.0

        # 存储材质颜色映射
        self._material_colors = {}

        # PyVista相关对象
        self._plotter = None
        self._drone_mesh = None
        self._drone_actor = None
        self._transform = None

        # ========== 性能优化：渲染节流 ==========
        # 限制3D渲染频率，避免打包后卡顿
        self._last_render_time = 0
        self._render_interval = 0.033  # 30Hz (1/30 = 0.033秒)，从50Hz降低到30Hz

        if PYVISTA_AVAILABLE:
            self._init_pyvista_scene()
        else:
            self._init_simple_view()

    def _parse_mtl_file(self, mtl_path: str) -> dict:
        """
        解析MTL文件，提取材质颜色

        Args:
            mtl_path: MTL文件路径

        Returns:
            dict: 材质名称到颜色的映射
        """
        if not os.path.exists(mtl_path):
            return {}

        materials = {}
        current_material = None

        try:
            with open(mtl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("newmtl "):
                        # 新材质定义
                        current_material = line[7:].strip()
                        materials[current_material] = {}
                    elif line.startswith("Kd ") and current_material:
                        # 漫反射颜色 (Diffuse color)
                        parts = line.split()
                        if len(parts) == 4:
                            r, g, b = float(parts[1]), float(parts[2]), float(parts[3])
                            # 转换为0-255范围
                            materials[current_material]["color"] = [
                                int(r * 255),
                                int(g * 255),
                                int(b * 255),
                            ]

            print(f"[3D视图] 从MTL文件读取了 {len(materials)} 个材质")
            return materials
        except Exception as e:
            print(f"[3D视图] 解析MTL文件失败: {e}")
            return {}

    def _apply_material_colors(self):
        """根据材质ID应用颜色"""
        try:
            # 获取材质ID数组
            mat_ids = self._drone_mesh.cell_data["MaterialIds"]

            # 创建RGB颜色数组
            n_cells = self._drone_mesh.n_cells
            colors = np.zeros((n_cells, 3), dtype=np.uint8)

            # 为每个单元分配颜色
            mat_names = list(self._material_colors.keys())
            for i, mat_id in enumerate(mat_ids):
                if 0 <= mat_id < len(mat_names):
                    mat_name = mat_names[mat_id]
                    if "color" in self._material_colors[mat_name]:
                        colors[i] = self._material_colors[mat_name]["color"]
                    else:
                        colors[i] = [200, 200, 200]  # 默认灰色
                else:
                    colors[i] = [200, 200, 200]  # 默认灰色

            # 将颜色添加到mesh
            self._drone_mesh.cell_data["RGB"] = colors
            self._drone_mesh.set_active_scalars("RGB", preference="cell")
            print(f"[3D视图] 已应用材质颜色")

        except Exception as e:
            print(f"[3D视图] 应用材质颜色失败: {e}")

    def _init_pyvista_scene(self):
        """初始化PyVista 3D场景"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # 创建PyVista绘图器
        self._plotter = QtInteractor(self)
        layout.addWidget(self._plotter.interactor)

        # VTK变换
        self._transform = vtk.vtkTransform()

        # 加载无人机模型
        self._create_drone_model()

        # 设置相机视角
        self._plotter.camera_position = [(5, 5, 5), (0, 0, 0), (0, 0, 1)]

        # 设置背景
        self._plotter.set_background("white")

    def _create_drone_model(self):
        """加载或创建无人机模型"""
        # 尝试加载自定义OBJ模型（使用资源路径工具支持打包后的exe）
        model_path = resource_path(os.path.join("resources", "models", "ESP-FLY-V5_1 v3.obj"))

        if os.path.exists(model_path):
            try:
                print(f"[3D视图] 正在加载自定义模型: {model_path}")

                # 从OBJ文件中读取MTL文件名
                mtl_filename = None
                try:
                    with open(model_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("mtllib "):
                                mtl_filename = line[7:].strip()
                                break
                except:
                    pass

                # 确定MTL文件路径
                if mtl_filename:
                    mtl_path = os.path.join(os.path.dirname(model_path), mtl_filename)
                    print(f"[3D视图] OBJ引用的MTL文件: {mtl_filename}")
                else:
                    mtl_path = model_path.replace(".obj", ".mtl")
                    print(f"[3D视图] 使用默认MTL文件名: {os.path.basename(mtl_path)}")

                # 读取MTL材质文件
                self._material_colors = self._parse_mtl_file(mtl_path)

                # 使用VTK的OBJ reader
                reader = vtk.vtkOBJReader()
                reader.SetFileName(model_path)
                reader.Update()

                # 转换为PyVista mesh
                self._drone_mesh = pv.wrap(reader.GetOutput())

                # 尝试应用颜色数据
                has_color = False

                # 方法1: 检查是否有RGB颜色数组
                if (
                    "RGB" in self._drone_mesh.point_data
                    or "RGB" in self._drone_mesh.cell_data
                ):
                    preference = (
                        "point" if "RGB" in self._drone_mesh.point_data else "cell"
                    )
                    self._drone_mesh.set_active_scalars("RGB", preference=preference)
                    print(f"[3D视图] 使用{preference} RGB颜色")
                    has_color = True

                # 方法2: 检查是否有材质ID，并应用MTL颜色
                elif (
                    "MaterialIds" in self._drone_mesh.cell_data
                    and self._material_colors
                ):
                    print(f"[3D视图] 检测到材质ID，尝试应用MTL颜色...")
                    self._apply_material_colors()
                    has_color = True

                if not has_color:
                    print(f"[3D视图] 未找到颜色数据，将使用默认颜色")

                # 计算模型边界，用于自动缩放
                bounds = self._drone_mesh.bounds
                x_range = bounds[1] - bounds[0]
                y_range = bounds[3] - bounds[2]
                z_range = bounds[5] - bounds[4]
                max_range = max(x_range, y_range, z_range)

                # 自动缩放到合适大小
                if max_range > 0:
                    scale_factor = 4 / max_range
                    self._drone_mesh.points *= scale_factor
                    print(f"[3D视图] 模型已缩放，缩放因子: {scale_factor:.6f}")

                # 将模型中心移到原点
                center = self._drone_mesh.center
                self._drone_mesh.points -= center

                print(f"[3D视图] 自定义模型加载成功！")

                # 添加到场景
                if self._drone_mesh.active_scalars is not None:
                    self._drone_actor = self._plotter.add_mesh(
                        self._drone_mesh,
                        show_edges=False,
                        smooth_shading=True,
                        lighting=True,
                        rgb=True,
                        interpolate_before_map=True,
                    )
                else:
                    self._drone_actor = self._plotter.add_mesh(
                        self._drone_mesh,
                        color="red",
                        show_edges=False,
                        smooth_shading=True,
                        lighting=True,
                    )

                # 设置变换
                self._drone_actor.SetUserTransform(self._transform)

            except Exception as e:
                print(f"[3D视图] 加载自定义模型失败: {e}")
                print(f"[3D视图] 使用默认几何体模型")
                self._create_default_drone_model()
        else:
            print(f"[3D视图] 未找到自定义模型，使用默认几何体")
            self._create_default_drone_model()

    def _create_default_drone_model(self):
        """创建默认的简单几何体模型（备用）"""
        # 中心球
        center = pv.Sphere(radius=0.25, center=(0, 0, 0))

        # 四个机臂（十字形）
        arm_length = 1.25
        arm_radius = 0.075

        # 前臂 (X+)
        arm1 = pv.Cylinder(
            center=(arm_length / 2, 0, 0),
            direction=(1, 0, 0),
            radius=arm_radius,
            height=arm_length,
        )

        # 后臂 (X-)
        arm2 = pv.Cylinder(
            center=(-arm_length / 2, 0, 0),
            direction=(1, 0, 0),
            radius=arm_radius,
            height=arm_length,
        )

        # 右臂 (Y+)
        arm3 = pv.Cylinder(
            center=(0, arm_length / 2, 0),
            direction=(0, 1, 0),
            radius=arm_radius,
            height=arm_length,
        )

        # 左臂 (Y-)
        arm4 = pv.Cylinder(
            center=(0, -arm_length / 2, 0),
            direction=(0, 1, 0),
            radius=arm_radius,
            height=arm_length,
        )

        # 四个电机（球体）
        motor_radius = 0.2
        motor1 = pv.Sphere(radius=motor_radius, center=(arm_length, 0, 0))
        motor2 = pv.Sphere(radius=motor_radius, center=(-arm_length, 0, 0))
        motor3 = pv.Sphere(radius=motor_radius, center=(0, arm_length, 0))
        motor4 = pv.Sphere(radius=motor_radius, center=(0, -arm_length, 0))

        # 合并所有部件
        self._drone_mesh = (
            center + arm1 + arm2 + arm3 + arm4 + motor1 + motor2 + motor3 + motor4
        )

        # 添加到场景
        self._drone_actor = self._plotter.add_mesh(
            self._drone_mesh, color="lightblue", show_edges=False, smooth_shading=True
        )

        # 设置变换
        self._drone_actor.SetUserTransform(self._transform)

    def _init_simple_view(self):
        """初始化简化视图（当PyVista不可用时）"""
        layout = QVBoxLayout(self)

        self._label = QLabel("3D姿态显示\n(需要安装PyVista)")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #666;
                background-color: #f0f0f0;
                border: 2px dashed #ccc;
                border-radius: 10px;
                padding: 40px;
            }
        """
        )

        layout.addWidget(self._label)

        # 简单的文本显示
        self._angle_label = QLabel()
        self._angle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._angle_label)

        self._update_simple_view()

    def _update_pyvista_model(self):
        """更新PyVista模型姿态（带节流优化）"""
        try:
            # ========== 性能优化：渲染节流 ==========
            # 限制渲染频率为30Hz，避免打包后卡顿
            current_time = time.time()
            if current_time - self._last_render_time < self._render_interval:
                return  # 跳过本次渲染
            
            self._last_render_time = current_time
            
            # 重置变换
            self._transform.Identity()

            # 按照ZYX顺序应用旋转（Yaw-Pitch-Roll）
            # VTK使用度数，不需要转换为弧度
            self._transform.RotateZ(self._yaw)  # 偏航角（绕Z轴）
            self._transform.RotateY(-self._roll)  # 横滚角（绕Y轴）
            self._transform.RotateX(-self._pitch)  # 俯仰角（绕X轴）

            # 强制更新变换
            self._transform.Modified()

            # 刷新渲染
            self._plotter.render()

        except Exception as e:
            print(f"[3D视图] 更新失败: {e}")

    def _update_simple_view(self):
        """更新简化视图"""
        if hasattr(self, "_angle_label"):
            self._angle_label.setText(
                f"Roll: {self._roll:+.1f}°  "
                f"Pitch: {self._pitch:+.1f}°  "
                f"Yaw: {self._yaw:+.1f}°"
            )

    # ========== Data Binding Slots ==========

    @pyqtSlot(float, float, float)
    def update_attitude(self, roll: float, pitch: float, yaw: float):
        """
        更新3D姿态显示（50Hz）

        Args:
            roll: 横滚角(度)
            pitch: 俯仰角(度)
            yaw: 偏航角(度)
        """
        self._roll = roll
        self._pitch = pitch
        self._yaw = yaw

        if PYVISTA_AVAILABLE and self._plotter is not None:
            self._update_pyvista_model()
        else:
            self._update_simple_view()
