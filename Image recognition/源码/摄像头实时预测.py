import sys
import cv2
import numpy as np
from PIL import Image, ImageFont, ImageDraw
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QImage, QPixmap, QPainter
from PyQt5.QtCore import Qt, QTimer
from PyQt5.Qt import pyqtSlot
import torch
from torchcam.methods import CAM
from torchvision import transforms
import os

# 设置字体路径
font_path = 'D:\\Train_Custom_Dataset-main\\Train_Custom_Dataset-main\\图像分类\\昆虫分类\\SimHei.ttf'
font = ImageFont.truetype(font_path, 30)

# 有 GPU 就用 GPU，没有就用 CPU
device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
print('device:', device)

# 加载模型和标签
model = torch.load('D:\\Train_Custom_Dataset-main\\Train_Custom_Dataset-main\\图像分类\\昆虫分类\\checkpoint\\efficientnet-0.901-1.pth', map_location=device)
model = model.eval().to(device)
idx_to_labels_cn = np.load('D:\\Train_Custom_Dataset-main\\Train_Custom_Dataset-main\\图像分类\\昆虫分类\\idx_to_labels.npy', allow_pickle=True).item()

# CAM 方法
cam_extractor = CAM(model, target_layer='features', fc_layer='classifier.1')

# 测试集图像预处理
test_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225])
])

# 确保photo文件夹存在
photo_folder = 'photo'
if not os.path.exists(photo_folder):
    os.makedirs(photo_folder)

# 定义overlay_mask函数
def overlay_mask(image, mask, alpha=0.5):
    mask = mask.astype(np.float32) / 255.0
    mask = cv2.applyColorMap(np.uint8(255 * mask), cv2.COLORMAP_JET)
    mask = cv2.cvtColor(mask, cv2.COLOR_BGR2RGB)
    mask = cv2.resize(mask, (image.shape[1], image.shape[0]))
    mask = np.clip(mask, 0, 255).astype(np.uint8)
    return cv2.addWeighted(image, alpha, mask, 1 - alpha, 0)

class CameraApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        self.cap = cv2.VideoCapture(0)
        self.camera_open = True
        self.background_image = QPixmap('D:\\Train_Custom_Dataset-main\\Train_Custom_Dataset-main\\图像分类\\昆虫分类\\1.jpg')

        if self.background_image.isNull():
            print("Failed to load background image. Check the path and file.")
        else:
            print("Background image loaded successfully.")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        self.video_path = None
        self.video_timer = QTimer(self)
        self.video_timer.timeout.connect(self.play_video)
        self.current_frame = None
        self.video_cap = None

    def initUI(self):
        self.setWindowTitle('Camera App')
        self.setFixedSize(1450, 1200)

        main_layout = QVBoxLayout(self)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.button = QPushButton('关闭摄像头', self)
        self.button.clicked.connect(self.toggle_camera)
        self.button.setFixedSize(200, 60)
        button_layout.addWidget(self.button)

        self.upload_button = QPushButton('上传图像', self)
        self.upload_button.clicked.connect(self.upload_image)
        self.upload_button.setFixedSize(200, 60)
        button_layout.addWidget(self.upload_button)

        self.upload_video_button = QPushButton('上传视频', self)
        self.upload_video_button.clicked.connect(self.upload_video)
        self.upload_video_button.setFixedSize(200, 60)
        button_layout.addWidget(self.upload_video_button)

        self.capture_button = QPushButton('图像保存', self)
        self.capture_button.clicked.connect(self.capture_image)
        self.capture_button.setFixedSize(200, 60)
        button_layout.addWidget(self.capture_button)

        main_layout.addLayout(button_layout, 0)

        self.label = QLabel(self)
        self.label.setFixedSize(1400, 1080)
        main_layout.addWidget(self.label, 0, Qt.AlignTop)

    def toggle_camera(self):
        if self.video_cap is not None:
            self.video_cap.release()
            self.video_cap = None
            self.video_timer.stop()

        self.camera_open = not self.camera_open
        if not self.camera_open:
            self.timer.stop()
            self.label.clear()
            self.button.setText('打开摄像头')
        else:
            self.timer.start(30)
            self.button.setText('关闭摄像头')
            self.update_frame()

    @pyqtSlot()
    def upload_image(self):
        options = QFileDialog.Options()
        image_path, _ = QFileDialog.getOpenFileName(self, "选择图像", "", "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*)", options=options)
        
        if image_path:
            print(f"Selected file: {image_path}")
            self.toggle_camera()

            image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                print("无法读取上传的图像，返回值是 None。请检查文件格式和路径。")
                return

            self.display_image(image)

    @pyqtSlot()
    def upload_video(self):
        options = QFileDialog.Options()
        video_path, _ = QFileDialog.getOpenFileName(self, "选择视频", "", "Videos (*.mp4 *.avi *.mov);;All Files (*)", options=options)
        
        if video_path:
            print(f"Selected video: {video_path}")
            self.toggle_camera()  # 关闭摄像头
            self.video_cap = cv2.VideoCapture(video_path)
            self.video_timer.start(30)

    def play_video(self):
        ret, self.current_frame = self.video_cap.read()
        if not ret:
            self.video_cap.release()
            self.video_timer.stop()
            return
        
        self.display_image(self.current_frame)

    def process_frame(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        input_tensor = test_transform(img_pil).unsqueeze(0).to(device)
        pred_logits = model(input_tensor)
        pred_probs = torch.nn.functional.softmax(pred_logits, dim=1)

        pred_top3 = torch.topk(pred_probs, 3)
        pred_ids = pred_top3[1].detach().cpu().numpy().squeeze().tolist()
        pred_probs = pred_top3[0].detach().cpu().numpy().squeeze().tolist()

        activation_map = cam_extractor(pred_ids[0], pred_logits)
        activation_map = activation_map[0][0].detach().cpu().numpy()
        result = overlay_mask(img_rgb, activation_map, alpha=0.7)

        result_pil = Image.fromarray(result)
        draw = ImageDraw.Draw(result_pil)

        text_y = 50
        for i in range(3):
            label = idx_to_labels_cn.get(pred_ids[i], "Unknown")
            prob = pred_probs[i]
            text = f' {label} - {prob:.2f}'
            draw.text((50, text_y), text, font=font, fill=(255, 0, 0))
            text_y += 40

        img_rgb = np.array(result_pil)
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        return img_bgr

    def display_image(self, img):
        processed_image = self.process_frame(img)
        self.label.setPixmap(self.convert_cv_qt(processed_image))

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret and self.camera_open:
            frame = self.process_frame(frame)
            self.label.setPixmap(self.convert_cv_qt(frame))

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.background_image.isNull():
            painter.drawPixmap(self.rect(), self.background_image)
        painter.end()

    def capture_image(self):
        rect = self.label.geometry()
        screen = QApplication.primaryScreen()
        if screen is not None:
            screenshot = screen.grabWindow(self.winId(), rect.x(), rect.y(), rect.width(), rect.height())
            filename = os.path.join(photo_folder, '{:d}.jpg'.format(cv2.getTickCount()))
            screenshot.save(filename)
            print(f'图片保存为{filename}')

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.label.width(), self.label.height(), Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def closeEvent(self, event):
        self.cap.release()
        if self.video_cap is not None:
            self.video_cap.release()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CameraApp()
    ex.show()
    sys.exit(app.exec_())
