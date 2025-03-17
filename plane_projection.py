#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import numpy as np
import argparse
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from PIL import Image

# 全局变量
zoom = 5.0
grid_size = 8.0  # 棋盘格大小
grid_cells = 8  # 棋盘格单元格数量
eye_z = 5.0  # 视点Z坐标（与棋盘格的距离）
fov = 60.0  # 透视投影的视场角 - 【重要】决定透视投影的视场角大小

# 视角旋转 (两个窗口共享)
rotate_x, rotate_y = 0, 0
last_x, last_y = 0, 0
mouse_pressed = False
active_window = 0  # 当前活动窗口

# 窗口ID
perspective_window = 0  # 透视投影窗口ID
orthographic_window = 0  # 正交投影窗口ID

# 纹理相关
use_texture = False  # 是否使用纹理
texture_id = 0  # 纹理ID
texture_path = ""  # 纹理图片路径

def load_texture(image_path):
    """加载纹理图片"""
    global use_texture, texture_id
    
    try:
        # 打开图片
        img = Image.open(image_path)
        
        # 确保图片尺寸是2的幂次方（OpenGL纹理要求）
        width, height = img.size
        if not (width & (width - 1) == 0) or not (height & (height - 1) == 0):
            # 调整图片尺寸为最接近的2的幂次方
            new_width = 2 ** (width - 1).bit_length()
            new_height = 2 ** (height - 1).bit_length()
            img = img.resize((new_width, new_height), Image.LANCZOS)
            print(f"图片尺寸已调整为 {new_width}x{new_height} (2的幂次方)")
        
        # 转换为RGBA模式
        if img.mode != "RGBA":
            img = img.convert("RGBA")
            
        # 上下翻转图片，修复OpenGL纹理坐标系与图片坐标系不一致的问题
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        
        # 获取图片数据
        img_data = np.array(list(img.getdata()), np.uint8)
        
        # 创建纹理
        texture_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        
        # 设置纹理参数
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        
        # 加载纹理数据
        width, height = img.size
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        
        use_texture = True
        print(f"成功加载纹理: {image_path}")
        return True
    except Exception as e:
        print(f"加载纹理失败: {e}")
        use_texture = False
        return False

def init():
    """初始化OpenGL设置"""
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    
    # 启用混合
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # 如果指定了纹理路径，尝试加载纹理
    global texture_path, use_texture
    if texture_path and os.path.exists(texture_path):
        load_texture(texture_path)
    else:
        use_texture = False

def calculate_ortho_size():
    """计算正交投影的尺寸，使其与透视投影下的平面大小一致"""
    # 【重要】计算透视投影下在平面距离处的可视区域高度
    # 使用公式: height = 2 * tan(fov/2) * distance
    # 这个公式是从透视投影的几何关系推导出来的
    # fov是视场角，eye_z是视点到平面的距离
    height = 2.0 * np.tan(np.radians(fov/2.0)) * eye_z
    return height / 2.0  # 返回半高（对应于glOrtho的参数）

def reshape(width, height):
    """窗口大小改变回调"""
    # 获取当前窗口ID
    current_window = glutGetWindow()
    
    # 设置视口
    glViewport(0, 0, width, height)
    
    # 【重要】设置投影矩阵 - 这是设置投影方式的开始
    glMatrixMode(GL_PROJECTION)  # 切换到投影矩阵模式
    glLoadIdentity()  # 重置投影矩阵
    
    aspect = width / height  # 计算窗口宽高比
    
    # 【重要】根据窗口ID设置不同的投影方式
    if current_window == perspective_window:
        # 【重要】透视投影 - 使用gluPerspective函数
        # 参数说明:
        # 1. fov: 视场角，决定了透视效果的强度
        # 2. aspect: 窗口宽高比
        # 3. 0.1: 近裁剪面距离
        # 4. 100.0: 远裁剪面距离
        gluPerspective(fov, aspect, 0.1, 100.0)
    else:
        # 【重要】正交投影 - 使用glOrtho函数
        # 首先计算正交投影的尺寸，使其与透视投影下的平面大小一致
        ortho_size = calculate_ortho_size()
        # 参数说明:
        # 1,2: 左右边界 (-ortho_size * aspect, ortho_size * aspect)
        # 3,4: 下上边界 (-ortho_size, ortho_size)
        # 5,6: 近远裁剪面 (0.1, 100.0)
        glOrtho(-ortho_size * aspect, ortho_size * aspect, 
                -ortho_size, ortho_size, 0.1, 100.0)
    
    # 【重要】切换回模型视图矩阵模式
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def draw_textured_plane():
    """绘制带纹理的平面"""
    # 启用纹理
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    
    # 绘制带纹理的四边形
    glColor4f(1.0, 1.0, 1.0, 1.0)  # 白色，不影响纹理颜色
    glBegin(GL_QUADS)
    # 左下角
    glTexCoord2f(0.0, 0.0)
    glVertex3f(-grid_size/2, -grid_size/2, -eye_z)
    # 右下角
    glTexCoord2f(1.0, 0.0)
    glVertex3f(grid_size/2, -grid_size/2, -eye_z)
    # 右上角
    glTexCoord2f(1.0, 1.0)
    glVertex3f(grid_size/2, grid_size/2, -eye_z)
    # 左上角
    glTexCoord2f(0.0, 1.0)
    glVertex3f(-grid_size/2, grid_size/2, -eye_z)
    glEnd()
    
    # 绘制边框
    glDisable(GL_TEXTURE_2D)
    glColor4f(1.0, 0.0, 0.0, 1.0)  # 红色边框
    glLineWidth(3.0)
    glBegin(GL_LINE_LOOP)
    glVertex3f(-grid_size/2, -grid_size/2, -eye_z)
    glVertex3f(grid_size/2, -grid_size/2, -eye_z)
    glVertex3f(grid_size/2, grid_size/2, -eye_z)
    glVertex3f(-grid_size/2, grid_size/2, -eye_z)
    glEnd()
    glLineWidth(1.0)

def draw_checkerboard():
    """绘制棋盘格平面"""
    cell_size = grid_size / grid_cells
    
    # 棋盘格位于z = -eye_z平面上
    glBegin(GL_QUADS)
    for i in range(grid_cells):
        for j in range(grid_cells):
            # 计算单元格位置
            x1 = -grid_size/2 + i * cell_size
            x2 = x1 + cell_size
            y1 = -grid_size/2 + j * cell_size
            y2 = y1 + cell_size
            
            # 设置颜色 (黑白相间)
            if (i + j) % 2 == 0:
                glColor4f(1.0, 1.0, 1.0, 1.0)  # 白色
            else:
                glColor4f(0.2, 0.2, 0.2, 1.0)  # 黑色
            
            # 绘制单元格 (在z = -eye_z平面上)
            glVertex3f(x1, y1, -eye_z)
            glVertex3f(x2, y1, -eye_z)
            glVertex3f(x2, y2, -eye_z)
            glVertex3f(x1, y2, -eye_z)
    glEnd()
    
    # 绘制边框
    glColor4f(1.0, 0.0, 0.0, 1.0)  # 红色边框
    glLineWidth(3.0)
    glBegin(GL_LINE_LOOP)
    glVertex3f(-grid_size/2, -grid_size/2, -eye_z)
    glVertex3f(grid_size/2, -grid_size/2, -eye_z)
    glVertex3f(grid_size/2, grid_size/2, -eye_z)
    glVertex3f(-grid_size/2, grid_size/2, -eye_z)
    glEnd()
    glLineWidth(1.0)

def draw_axes():
    """绘制坐标轴"""
    glLineWidth(2.0)
    glBegin(GL_LINES)
    # X轴 (红色)
    glColor3f(1.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(2.0, 0.0, 0.0)
    
    # Y轴 (绿色)
    glColor3f(0.0, 1.0, 0.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 2.0, 0.0)
    
    # Z轴 (蓝色)
    glColor3f(0.0, 0.0, 1.0)
    glVertex3f(0.0, 0.0, 0.0)
    glVertex3f(0.0, 0.0, -2.0)
    glEnd()
    glLineWidth(1.0)
    
    # 绘制轴标签
    glRasterPos3f(2.2, 0, 0)
    glutBitmapString(GLUT_BITMAP_HELVETICA_12, b"X")
    
    glRasterPos3f(0, 2.2, 0)
    glutBitmapString(GLUT_BITMAP_HELVETICA_12, b"Y")
    
    glRasterPos3f(0, 0, -2.2)
    glutBitmapString(GLUT_BITMAP_HELVETICA_12, b"Z")

def draw_ui():
    """绘制用户界面"""
    # 获取当前窗口ID
    current_window = glutGetWindow()
    
    # 保存当前矩阵
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    viewport = glGetIntegerv(GL_VIEWPORT)
    width, height = viewport[2], viewport[3]
    
    glOrtho(0, width, 0, height, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # 绘制当前模式信息
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(10, height - 20)
    if current_window == perspective_window:
        mode_text = "Mode: Perspective"
    else:
        mode_text = "Mode: Orthographic"
    glutBitmapString(GLUT_BITMAP_HELVETICA_12, mode_text.encode('ascii', 'ignore'))
    
    # 绘制视点位置信息
    glRasterPos2f(10, height - 40)
    eye_text = f"Distance to plane: {eye_z:.1f}"
    glutBitmapString(GLUT_BITMAP_HELVETICA_12, eye_text.encode('ascii', 'ignore'))
    
    # 绘制纹理信息
    glRasterPos2f(10, height - 60)
    if use_texture:
        texture_text = f"Texture: {os.path.basename(texture_path)}"
    else:
        texture_text = "Texture: None (using checkerboard)"
    glutBitmapString(GLUT_BITMAP_HELVETICA_12, texture_text.encode('ascii', 'ignore'))
    
    # 绘制视场角信息（仅在透视投影窗口显示）
    if current_window == perspective_window:
        glRasterPos2f(10, height - 80)
        fov_text = f"Field of View: {fov:.1f}°"
        glutBitmapString(GLUT_BITMAP_HELVETICA_12, fov_text.encode('ascii', 'ignore'))
    
    # 绘制缩放信息（仅在正交投影窗口显示）
    if current_window == orthographic_window:
        glRasterPos2f(10, height - 80)
        ortho_size = calculate_ortho_size()
        ortho_text = f"Ortho Size: {ortho_size:.1f}"
        glutBitmapString(GLUT_BITMAP_HELVETICA_12, ortho_text.encode('ascii', 'ignore'))
    
    # 绘制帮助信息
    glRasterPos2f(10, 10)
    help_text = "+/-: Zoom | W/S: Plane Distance | Left mouse: Rotate | T: Toggle Texture | ESC: Exit"
    glutBitmapString(GLUT_BITMAP_HELVETICA_12, help_text.encode('ascii', 'ignore'))
    
    # 恢复矩阵
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display():
    """渲染场景"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    glLoadIdentity()
    
    # 应用旋转
    glRotatef(rotate_x, 1, 0, 0)
    glRotatef(rotate_y, 0, 1, 0)
    
    # 绘制坐标轴
    draw_axes()
    
    # 根据是否使用纹理选择绘制方式
    if use_texture:
        draw_textured_plane()
    else:
        draw_checkerboard()
    
    # 绘制UI
    draw_ui()
    
    glutSwapBuffers()

def toggle_texture():
    """切换纹理显示"""
    global use_texture
    
    if texture_id > 0:  # 如果已加载纹理
        use_texture = not use_texture
        print(f"纹理显示: {'开启' if use_texture else '关闭'}")
    else:
        print("未加载纹理，无法切换")

def keyboard(key, x, y):
    """键盘回调"""
    global eye_z, zoom, fov
    
    if key == b'\x1b':  # ESC键
        sys.exit(0)
    elif key == b'+' or key == b'=':  # +键 - 放大
        zoom = max(1.0, zoom - 0.5)
        fov = max(20.0, fov - 2.0)  # 【重要】同时减小视场角，增强透视效果
        # 更新两个窗口的投影矩阵
        glutSetWindow(perspective_window)
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        glutPostRedisplay()
        glutSetWindow(orthographic_window)
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        glutPostRedisplay()
    elif key == b'-' or key == b'_':  # -键 - 缩小
        zoom = min(20.0, zoom + 0.5)
        fov = min(120.0, fov + 2.0)  # 【重要】同时增加视场角，减弱透视效果
        # 更新两个窗口的投影矩阵
        glutSetWindow(perspective_window)
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        glutPostRedisplay()
        glutSetWindow(orthographic_window)
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        glutPostRedisplay()
    elif key == b'w' or key == b'W':  # W键 - 减小与棋盘格的距离
        eye_z = max(0.5, eye_z - 0.5)
        # 【重要】更新两个窗口的投影矩阵（因为正交投影的大小依赖于eye_z）
        glutSetWindow(perspective_window)
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        glutPostRedisplay()
        glutSetWindow(orthographic_window)
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        glutPostRedisplay()
    elif key == b's' or key == b'S':  # S键 - 增加与棋盘格的距离
        eye_z = min(20.0, eye_z + 0.5)
        # 【重要】更新两个窗口的投影矩阵（因为正交投影的大小依赖于eye_z）
        glutSetWindow(perspective_window)
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        glutPostRedisplay()
        glutSetWindow(orthographic_window)
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        glutPostRedisplay()
    elif key == b't' or key == b'T':  # T键 - 切换纹理显示
        toggle_texture()
        # 更新两个窗口
        glutSetWindow(perspective_window)
        glutPostRedisplay()
        glutSetWindow(orthographic_window)
        glutPostRedisplay()

def mouse(button, state, x, y):
    """鼠标按钮回调"""
    global mouse_pressed, last_x, last_y, active_window
    
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            mouse_pressed = True
            last_x, last_y = x, y
            active_window = glutGetWindow()  # 记录当前活动窗口
        elif state == GLUT_UP:
            mouse_pressed = False

def motion(x, y):
    """鼠标移动回调"""
    global rotate_x, rotate_y, last_x, last_y
    
    if mouse_pressed:
        dx = x - last_x
        dy = y - last_y
        
        rotate_y += dx * 0.5
        rotate_x += dy * 0.5
        
        # 限制X轴旋转角度，防止平面翻转
        rotate_x = max(-80, min(80, rotate_x))
        
        last_x, last_y = x, y
        
        # 更新两个窗口
        glutSetWindow(perspective_window)
        glutPostRedisplay()
        glutSetWindow(orthographic_window)
        glutPostRedisplay()
        
        # 恢复活动窗口
        glutSetWindow(active_window)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='OpenGL平面投影演示工具')
    parser.add_argument('-i', '--image', type=str, help='指定要加载的图片路径')
    return parser.parse_args()

def main():
    """主函数"""
    global perspective_window, orthographic_window, texture_path
    
    # 解析命令行参数
    args = parse_arguments()
    if args.image:
        texture_path = args.image
    
    # 初始化GLUT
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    
    # 获取屏幕尺寸
    screen_width = glutGet(GLUT_SCREEN_WIDTH)
    screen_height = glutGet(GLUT_SCREEN_HEIGHT)
    
    # 计算窗口尺寸和位置
    window_width = screen_width // 3
    window_height = screen_height // 2
    
    # 【重要】创建透视投影窗口（左侧）
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(50, 100)
    perspective_window = glutCreateWindow("Perspective Projection")
    
    # 初始化OpenGL设置
    init()
    
    # 设置回调
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)  # 【重要】这里设置了reshape回调，它会设置投影方式
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    
    # 【重要】创建正交投影窗口（右侧）
    glutInitWindowSize(window_width, window_height)
    glutInitWindowPosition(50 + window_width + 20, 100)
    orthographic_window = glutCreateWindow("Orthographic Projection")
    
    # 初始化OpenGL设置
    init()
    
    # 设置回调
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)  # 【重要】这里设置了reshape回调，它会设置投影方式
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    
    # 打印使用说明
    print("=== Plane Projection Demo (Dual Window) ===")
    print("Controls:")
    print("  +/-: Zoom in/out")
    print("  W/S: Adjust distance to plane")
    print("  T: Toggle texture/checkerboard")
    print("  Left mouse drag: Rotate view")
    print("  ESC: Exit program")
    
    if texture_path:
        print(f"尝试加载图片: {texture_path}")
    else:
        print("未指定图片，使用默认棋盘格")
    
    # 主循环
    glutMainLoop()

if __name__ == "__main__":
    main() 