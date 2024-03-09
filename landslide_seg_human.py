import cv2
import os
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore

class ImageSelector(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.image = None
        self.original_image = None
        self.total_area = 2.7
        self.rois = []
        self.roi_pixels = []
        self.folder = None
        self.image_files = []
        self.current_image_index = -1  # Initialize the current image index
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Image Selector')
        self.setGeometry(100, 100, 800, 600)

        self.label = QtWidgets.QLabel()
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        self.btn_select = QtWidgets.QPushButton('Select Image')
        self.btn_select.clicked.connect(self.select_image)

        self.btn_next = QtWidgets.QPushButton('Next Image')  # The "Next" button
        self.btn_next.clicked.connect(self.next_image)

        self.btn_roi = QtWidgets.QPushButton('Add ROI')
        self.btn_roi.clicked.connect(self.add_roi)

        self.btn_calculate = QtWidgets.QPushButton('Calculate Area')
        self.btn_calculate.clicked.connect(self.calculate_area)

        self.btn_clear = QtWidgets.QPushButton('Clear')
        self.btn_clear.clicked.connect(self.clear_all)

        self.text_area = QtWidgets.QLineEdit()
        self.text_area.setPlaceholderText('Enter total area')

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.btn_select)
        layout.addWidget(self.btn_next)  # Add the "Next" button to the layout
        layout.addWidget(self.btn_roi)
        layout.addWidget(self.btn_calculate)
        layout.addWidget(self.btn_clear)
        layout.addWidget(self.text_area)
        self.setLayout(layout)

    def select_image(self):
        self.folder = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Image Folder')
        if self.folder:
            self.image_files = sorted(os.listdir(self.folder))
            self.current_image_index = 0
            self.load_image()

    def load_image(self):  # New method to load the image
        if self.current_image_index < 0 or self.current_image_index >= len(self.image_files):
            return  # Do nothing if there's no image or the index is out of bounds

        image_path = os.path.join(self.folder, self.image_files[self.current_image_index])
        self.image = cv2.imread(image_path)
        self.original_image = self.image.copy()
        self.display_image()

    def display_image(self):
        if self.image is None:
            return

        image_name = self.image_files[self.current_image_index]  # Get the current image name
        self.image_with_text = self.add_text_to_image(self.image, image_name)  # Overlay text on the image
        
        height, width, channel = self.image_with_text.shape
        bytesPerLine = 3 * width
        qimg = QtGui.QImage(self.image_with_text.data, width, height, bytesPerLine, QtGui.QImage.Format_RGB888).rgbSwapped()
        pixmap = QtGui.QPixmap.fromImage(qimg)
        self.label.setPixmap(pixmap)

    def add_text_to_image(self, image, text):  # New method to add text to the image
        font = cv2.FONT_HERSHEY_SIMPLEX
        position = (10, 30)  # Position of the text
        font_scale = 1
        font_color = (0, 0, 255)  # White color
        line_type = 2

        img_with_text = cv2.putText(
            np.copy(image), text, position, font, 
            font_scale, font_color, line_type
        )
        return img_with_text

    def next_image(self):  # New method for the "Next" button
        self.current_image_index += 1
        if self.current_image_index < len(self.image_files):
            self.clear_all()
            self.load_image()
        else:
            self.current_image_index = -1  # If it's the last image, loop back to the first image

    # ... (rest of your code remains the same)
    def add_roi(self):
        if self.image is None:
            return

        roi = cv2.selectROI('Select ROI', self.image)
        self.rois.append(roi)

        # 在这里画上文本标注
        roi_number = len(self.rois)  # 当前ROI的序号
        text = f'ROI {roi_number}'

        x, y, w, h = roi
        # 画出选框
        cv2.rectangle(self.image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # 计算文本位置
        text_position = (x, y - 10) if y - 10 > 0 else (x, y + 20)
        # 设置文本样式
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_color = (0, 0, 255)  # 红色
        line_type = 2
        # 将文本画到图像上
        cv2.putText(self.image, text, text_position, font, font_scale, font_color, line_type)

        self.display_image()

        mask = np.zeros(self.original_image.shape[:2], np.uint8)
        cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        roi_pixels = cv2.countNonZero(mask)
        self.roi_pixels.append(roi_pixels)

    def calculate_area(self):
        if not self.roi_pixels:
            return

        total_area_text = self.text_area.text().strip()
        if not total_area_text:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Please enter the total area.')
            return

        try:
            total_area = float(total_area_text)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, 'Warning', 'Invalid input for total area.')
            return

        if total_area == 0:
            return

        height, width = self.original_image.shape[:2]
        total_pixels = height * width

        areas = []
        total_roi_pixels = sum(self.roi_pixels)
        ratio = total_roi_pixels / total_pixels
        total_roi_area = ratio * total_area
        areas.append(total_roi_area)

        for i, pixels in enumerate(self.roi_pixels):
            ratio = pixels / total_pixels
            area = ratio * total_area
            areas.append(area)

        result = f'Total ROI Area: {total_roi_area:.2f}\n' + '\n'.join([f'ROI {i + 1}: {area:.2f}' for i, area in enumerate(areas[1:])])
        QtWidgets.QMessageBox.information(self, 'Calculated Areas', result)

    def clear_all(self):
        self.image = None
        self.original_image = None
        self.rois.clear()
        self.roi_pixels.clear()
        self.text_area.clear()
        self.label.clear()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    selector = ImageSelector()
    selector.show()
    app.exec_()
