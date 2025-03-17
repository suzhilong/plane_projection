# OpenGL 平面投影演示工具

这是一个使用Python和OpenGL实现的平面投影演示工具。该工具通过同时显示两个窗口（透视投影和正交投影），直观地展示了两种投影方式的区别。

## 功能特点

- **双窗口显示**：左侧窗口使用透视投影，右侧窗口使用正交投影
- **实时对比**：两个窗口同步显示相同的场景，便于直接对比
- **自定义纹理**：支持使用用户提供的图片作为平面纹理，默认使用棋盘格
- **棋盘格平面**：当未指定图片时，使用黑白相间的棋盘格作为参考平面
- **坐标轴显示**：显示X、Y、Z坐标轴，帮助理解空间位置
- **可调整视点**：支持调整视点与平面的距离
- **视角旋转**：通过鼠标拖动旋转视角
- **实时信息显示**：显示当前投影模式、视点距离和视场角等信息

## 安装依赖

```bash
pip install -r requirements.txt
```

对于GLUT版本，还需要安装系统依赖：

```bash
# Ubuntu/Debian
sudo apt-get install freeglut3 freeglut3-dev

# CentOS/RHEL
sudo yum install freeglut freeglut-devel

# macOS
brew install freeglut
```

## 使用方法

### 基本用法

运行以下命令启动平面投影演示（使用默认棋盘格）：

```bash
python plane_projection.py
```

### 使用自定义图片

指定图片作为平面纹理：

```bash
python plane_projection.py -i path/to/your/image.jpg
```

支持的图片格式包括：JPG、PNG、BMP等（由Pillow库支持的格式）。

## 控制说明

- **+/-键**：放大/缩小视图
- **W/S键**：调整视点与平面的距离
- **T键**：切换纹理/棋盘格显示（仅当加载了图片时有效）
- **鼠标左键拖动**：旋转视角
- **ESC键**：退出程序

## 纹理说明

- 程序会自动将图片调整为OpenGL所需的2的幂次方尺寸（如512x512、1024x1024等）
- 图片会被拉伸以适应平面大小
- 如果图片加载失败，程序会自动回退到使用棋盘格

## 投影原理说明

### 透视投影 (Perspective Projection)

透视投影模拟了人眼的视觉效果，具有以下特点：
- 远处的物体看起来更小
- 平行线会在远处汇聚
- 提供真实的深度感知
- 使用`gluPerspective(fov, aspect, near, far)`函数设置

### 正交投影 (Orthographic Projection)

正交投影不会产生透视效果，具有以下特点：
- 物体大小不随距离变化
- 平行线始终保持平行
- 适合工程制图和CAD应用
- 使用`glOrtho(left, right, bottom, top, near, far)`函数设置

## 技术实现

该程序使用了以下技术：
- **PyOpenGL**：Python的OpenGL绑定
- **GLUT**：用于创建窗口和处理输入
- **NumPy**：用于数学计算
- **Pillow**：用于图片处理和纹理加载

## 系统要求

- Python 3.6+
- OpenGL支持
- 支持的操作系统：Windows, macOS, Linux 