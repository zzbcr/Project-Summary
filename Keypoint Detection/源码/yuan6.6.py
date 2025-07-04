import sys
import cv2
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer
from ultralytics import YOLO
import torch

# 设备选择
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
model = YOLO('D:\Train_Custom_Dataset-main\Train_Custom_Dataset-main\关键点检测\汽车关键点检测\car\\n_pretrain(1)\weights\\best.pt').to(device)

# 框（rectangle）可视化配置
bbox_color = (150, 0, 0)  # 框的 BGR 颜色
bbox_thickness = 2  # 框的线宽

# 框类别文字
bbox_labelstr = {
    'font_size': 1,
    'font_thickness': 2,
    'offset_x': 0,
    'offset_y': -10,
}

# 关键点 BGR 配色
kpt_color_map = {
    0: {'name': '1', 'color': [255, 0, 0], 'radius': 10},
    1: {'name': '2', 'color': [255, 0, 0], 'radius': 10},
    2: {'name': '3', 'color': [255, 0, 0], 'radius': 10},
    3: {'name': '4', 'color': [255, 0, 0], 'radius': 10},
    4: {'name': '5', 'color': [0, 255, 0], 'radius': 10},
    5: {'name': '6', 'color': [0, 255, 0], 'radius': 10},
    6: {'name': '7', 'color': [0, 255, 0], 'radius': 10},
    7: {'name': '8', 'color': [0, 255, 0], 'radius': 10},
    8: {'name': '9', 'color': [0, 0, 255], 'radius': 10},
    9: {'name': '10', 'color': [0, 0, 255], 'radius': 10},
    10: {'name': '11', 'color': [0, 0, 255], 'radius': 10},
    11: {'name': '12', 'color': [0, 0, 255], 'radius': 10},
}

# 点类别文字
kpt_labelstr = {
    'font_size': 1.5,  # 字体大小
    'font_thickness': 3,  # 字体粗细
    'offset_x': 10,  # X 方向，文字偏移距离，向右为正
    'offset_y': 0,  # Y 方向，文字偏移距离，向下为正
}

# 骨架连接 BGR 配色
skeleton_map = [
    {'srt_kpt_id': 0, 'dst_kpt_id': 1, 'color': [196, 75, 255], 'thickness': 2},
    {'srt_kpt_id': 1, 'dst_kpt_id': 2, 'color': [196, 75, 255], 'thickness': 2},
    {'srt_kpt_id': 2, 'dst_kpt_id': 3, 'color': [196, 75, 255], 'thickness': 2},
    {'srt_kpt_id': 3, 'dst_kpt_id': 0, 'color': [196, 75, 255], 'thickness': 2},
    {'srt_kpt_id': 4, 'dst_kpt_id': 5, 'color': [180, 187, 28], 'thickness': 2},
    {'srt_kpt_id': 5, 'dst_kpt_id': 6, 'color': [180, 187, 28], 'thickness': 2},
    {'srt_kpt_id': 6, 'dst_kpt_id': 7, 'color': [180, 187, 28], 'thickness': 2},
    {'srt_kpt_id': 7, 'dst_kpt_id': 4, 'color': [180, 187, 28], 'thickness': 2},
    {'srt_kpt_id': 8, 'dst_kpt_id': 9, 'color': [47, 255, 173], 'thickness': 2},
    {'srt_kpt_id': 9, 'dst_kpt_id': 10, 'color': [47, 255, 173], 'thickness': 2},
    {'srt_kpt_id': 10, 'dst_kpt_id': 11, 'color': [47, 255, 173], 'thickness': 2},
    {'srt_kpt_id': 11, 'dst_kpt_id': 8, 'color': [47, 255, 173], 'thickness': 2},
    {'srt_kpt_id': 0, 'dst_kpt_id': 4, 'color': [128, 0, 128], 'thickness': 2},
    {'srt_kpt_id': 1, 'dst_kpt_id': 5, 'color': [128, 0, 128], 'thickness': 2},
    {'srt_kpt_id': 2, 'dst_kpt_id': 6, 'color': [128, 0, 128], 'thickness': 2},
    {'srt_kpt_id': 3, 'dst_kpt_id': 7, 'color': [128, 0, 128], 'thickness': 2 },
    {'srt_kpt_id': 4, 'dst_kpt_id': 8, 'color': [0, 255, 255], 'thickness': 2},
    {'srt_kpt_id': 5, 'dst_kpt_id': 9, 'color': [0, 255, 255], 'thickness': 2},
    {'srt_kpt_id': 6, 'dst_kpt_id': 10, 'color': [0, 255, 255], 'thickness': 2},
    {'srt_kpt_id': 7, 'dst_kpt_id': 11, 'color': [0, 255, 255], 'thickness': 2},
]

def process_frame(img_bgr):
    start_time = time.time()
    results = model(img_bgr, verbose=False)
    num_bbox = len(results[0].boxes.cls)
    bboxes_xyxy = results[0].boxes.xyxy.cpu().numpy().astype('uint32')
    bboxes_keypoints = results[0].keypoints.data.cpu().numpy().astype('uint32')
    for idx in range(num_bbox):
        bbox_xyxy = bboxes_xyxy[idx]
        bbox_label = results[0].names[0]
        img_bgr = cv2.rectangle(img_bgr, (bbox_xyxy[0], bbox_xyxy[1]), (bbox_xyxy[2], bbox_xyxy[3]), bbox_color,
                                bbox_thickness)
        img_bgr = cv2.putText(img_bgr, bbox_label,
                              (bbox_xyxy[0] + bbox_labelstr['offset_x'], bbox_xyxy[1] + bbox_labelstr['offset_y']),
                              cv2.FONT_HERSHEY_SIMPLEX, bbox_labelstr['font_size'], bbox_color,
                              bbox_labelstr['font_thickness'])
        bbox_keypoints = bboxes_keypoints[idx]
        for skeleton in skeleton_map:
            srt_kpt_id = skeleton['srt_kpt_id']
            srt_kpt_x = bbox_keypoints[srt_kpt_id][0]
            srt_kpt_y = bbox_keypoints[srt_kpt_id][1]
            dst_kpt_id = skeleton['dst_kpt_id']
            dst_kpt_x = bbox_keypoints[dst_kpt_id][0]
            dst_kpt_y = bbox_keypoints[dst_kpt_id][1]
            skeleton_color = skeleton['color']
            skeleton_thickness = skeleton['thickness']
            img_bgr = cv2.line(img_bgr, (srt_kpt_x, srt_kpt_y), (dst_kpt_x, dst_kpt_y), color=skeleton_color,
                               thickness=skeleton_thickness)
        for kpt_id in kpt_color_map:
            kpt_color = kpt_color_map[kpt_id]['color']
            kpt_radius = kpt_color_map[kpt_id]['radius']
            kpt_x = bbox_keypoints[kpt_id][0]
            kpt_y = bbox_keypoints[kpt_id][1]
            img_bgr = cv2.circle(img_bgr, (kpt_x, kpt_y), kpt_radius, kpt_color, -1)
            kpt_label = str(kpt_id)
            img_bgr = cv2.putText(img_bgr, kpt_label,
                                  (kpt_x + kpt_labelstr['offset_x'], kpt_y + kpt_labelstr['offset_y']),
                                  cv2.FONT_HERSHEY_SIMPLEX, kpt_labelstr['font_size'], kpt_color,
                                  kpt_labelstr['font_thickness'])
    end_time = time.time()
    FPS = 1 / (end_time - start_time)
    FPS_string = 'FPS  ' + str(int(FPS))
    img_bgr = cv2.putText(img_bgr, FPS_string, (25, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.25, (255, 0, 255), 2)
    return img_bgr

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.out = None  # 新增: 用于保存视频的VideoWriter对象
        self.camera_open = False  # 摄像头状态标志
        self.paused = False

    def initUI(self):
        self.setWindowTitle('Key Detection App')
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        self.label = QLabel(self)
        layout.addWidget(self.label)
        self.open_image_button = QPushButton("上传图片", self)
        self.open_image_button.clicked.connect(self.open_image)
        layout.addWidget(self.open_image_button)
        self.open_video_button = QPushButton("上传视频", self)
        self.open_video_button.clicked.connect(self.open_video)
        layout.addWidget(self.open_video_button)
        # self.take_photo_button = QPushButton("Take Photo", self)
        # self.take_photo_button.clicked.connect(self.take_photo)
        # layout.addWidget(self.take_photo_button)
        self.toggle_camera_button = QPushButton("开关摄像头", self)
        self.toggle_camera_button.clicked.connect(self.toggle_camera)
        layout.addWidget(self.toggle_camera_button)
        self.pause_resume_button = QPushButton("暂停")
        self.pause_resume_button.clicked.connect(self.pause_resume)  # 连接到新的槽函数
        layout.addWidget(self.pause_resume_button)
        self.save_button = QPushButton("保存结果", self)
        self.save_button.clicked.connect(self.save_result)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

    def pause_resume(self):  # 新增：暂停/继续功能
        if self.paused:
            self.timer.start(30)
        else:
            self.timer.stop()
        self.paused = not self.paused  # 切换暂停状态

    def toggle_camera(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.timer.stop()
            self.cap = None
        else:
            self.cap = cv2.VideoCapture(0)
            self.timer.start(30)

    def open_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.xpm *.jpg)")
        if filename:
            img_bgr = cv2.imread(filename)
            processed_img = process_frame(img_bgr)
            self.display_image(processed_img)

    def open_video(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Videos (*.mp4 *.avi)")
        if filename:
            self.cap = cv2.VideoCapture(filename)
            fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 可根据需要调整编解码器
            output_filename, _ = QFileDialog.getSaveFileName(self, "Save Video As", "", "Videos (*.avi)")
            if output_filename:
                self.out = cv2.VideoWriter(output_filename, fourcc, fps, (width, height))
            self.timer.start(30)
    #
    # def take_photo(self):
    #     if not self.cap or not self.cap.isOpened():
    #         self.cap = cv2.VideoCapture(0)
    #     ret, frame = self.cap.read()
    #     if ret:
    #         processed_frame = process_frame(frame)
    #         self.display_image(processed_frame)
    #         self.cap.release()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            processed_frame = process_frame(frame)
            self.display_image(processed_frame)
            if self.out is not None:  # 如果存在视频写入器，则写入帧
                self.out.write(processed_frame)
        else:
            self.timer.stop()
            if self.cap:
                self.cap.release()
            if self.out:
                self.out.release()  # 释放视频写入器
                self.out = None  # 清空引用

    def display_image(self, img_bgr):
        rgb_image = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        self.label.setPixmap(pixmap.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio))
        self.current_image = img_bgr  # 保存当前图像以便后续保存

    def save_result(self):
        if hasattr(self, 'current_image'):
            filename, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "JPEG(*.jpg);;PNG(*.png)")
            if filename:
                cv2.imwrite(filename, self.current_image)

    def closeEvent(self, event):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        if self.out:
            self.out.release()  # 确保退出程序时也释放视频写入器
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CameraApp()
    ex.show()
    sys.exit(app.exec_())