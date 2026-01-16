import sys
import time
import cv2
import numpy as np

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QFileDialog, QHBoxLayout, QVBoxLayout,
    QSpinBox, QComboBox
)
from PySide6.QtGui import QPainter, QPen, QImage
from PySide6.QtCore import Qt, QTimer


MAX_LINES = 19999


# =========================
# 预处理参数预设
# =========================
PRESETS = {
    "人像": {
        "blur": 5,
        "th_block": 11,
        "th_c": 2
    },
    "建筑": {
        "blur": 3,
        "th_block": 15,
        "th_c": 3
    },
    "风景": {
        "blur": 7,
        "th_block": 21,
        "th_c": 4
    }
}


# =========================
# 左侧：原图显示
# =========================
class ImageView(QWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.image = None
        self.size_wh = None

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        self.load(e.mimeData().urls()[0].toLocalFile())

    def load(self, path):
        """
        使用 np.fromfile + cv2.imdecode
        以支持 Windows 下的中文 / 日文路径
        """
        try:
            data = np.fromfile(path, dtype=np.uint8)
            img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        except Exception:
            img = None

        if img is None:
            return False

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.image = img
        h, w, _ = img.shape
        self.size_wh = (w, h)
        self.update()
        return True

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.lightGray)

        if self.image is None:
            p.drawText(self.rect(), Qt.AlignCenter, "拖拽图片或打开文件")
            p.end()
            return

        h, w, _ = self.image.shape
        qimg = QImage(self.image.data, w, h, w * 3, QImage.Format_RGB888)
        scale = min(self.width() / w, self.height() / h)
        tw, th = int(w * scale), int(h * scale)
        p.drawImage(
            (self.width() - tw) // 2,
            (self.height() - th) // 2,
            qimg.scaled(tw, th, Qt.KeepAspectRatio)
        )
        p.end()


# =========================
# 右侧：线稿画布
# =========================
class LineCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.lines = []
        self.size_wh = None
        self.pen_width = 2

    def reset(self, size_wh):
        self.lines.clear()
        self.size_wh = size_wh
        self.update()

    def add(self, line):
        self.lines.append(line)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), Qt.white)

        if not self.size_wh:
            p.drawText(self.rect(), Qt.AlignCenter, "等待绘制")
            p.end()
            return

        w, h = self.size_wh
        scale = min(self.width() / w, self.height() / h)

        pen = QPen(Qt.black)
        pen.setWidth(self.pen_width)
        p.setPen(pen)

        for x1, y1, x2, y2 in self.lines:
            p.drawLine(
                int(x1 * scale), int(y1 * scale),
                int(x2 * scale), int(y2 * scale)
            )
        p.end()


# =========================
# 主窗口
# =========================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("draw_the_picture")

        # Views
        self.view_src = ImageView()
        self.view_dst = LineCanvas()
        self.view_src.setFixedSize(480, 360)
        self.view_dst.setFixedSize(480, 360)

        # Controls
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 10)
        self.spin_width.setValue(2)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(1, 2000)
        self.spin_interval.setValue(10)

        self.spin_limit = QSpinBox()
        self.spin_limit.setRange(1, MAX_LINES)
        self.spin_limit.setValue(2000)

        self.combo_preset = QComboBox()
        self.combo_preset.addItems(PRESETS.keys())

        # Buttons
        self.btn_open = QPushButton("打开图片")
        self.btn_start = QPushButton("开始 / 重来")
        self.btn_pause = QPushButton("暂停")
        self.btn_export = QPushButton("导出 PNG")

        # Status
        self.lbl_state = QLabel("状态：等待图片")
        self.lbl_count = QLabel("线条数：0")
        self.lbl_speed = QLabel("速度：- s/条")

        # Layout
        views = QHBoxLayout()
        views.addWidget(self.view_src)
        views.addWidget(self.view_dst)

        params = QHBoxLayout()
        params.addWidget(QLabel("线宽"))
        params.addWidget(self.spin_width)
        params.addWidget(QLabel("间隔(ms)"))
        params.addWidget(self.spin_interval)
        params.addWidget(QLabel("上限"))
        params.addWidget(self.spin_limit)
        params.addWidget(QLabel("预设"))
        params.addWidget(self.combo_preset)

        info = QHBoxLayout()
        info.addWidget(self.lbl_state)
        info.addStretch()
        info.addWidget(self.lbl_count)
        info.addWidget(self.lbl_speed)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_open)
        buttons.addWidget(self.btn_start)
        buttons.addWidget(self.btn_pause)
        buttons.addWidget(self.btn_export)

        layout = QVBoxLayout(self)
        layout.addLayout(views)
        layout.addLayout(params)
        layout.addLayout(info)
        layout.addLayout(buttons)

        # Connections
        self.btn_open.clicked.connect(self.open_image)
        self.btn_start.clicked.connect(self.start)
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_export.clicked.connect(self.export_png)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.draw_step)

        # State
        self.target = None
        self.residual = None
        self.paused = False
        self.total = 0

    # =========================
    # 打开图片
    # =========================
    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开图片", "", "Images (*.png *.jpg *.jpeg)"
        )
        if path:
            if self.view_src.load(path):
                self.lbl_state.setText("状态：图片已加载")
            else:
                self.lbl_state.setText("状态：图片读取失败（路径或文件名问题）")

    # =========================
    # 黑白预处理
    # =========================
    def preprocess(self):
        p = PRESETS[self.combo_preset.currentText()]
        gray = cv2.cvtColor(self.view_src.image, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (p["blur"], p["blur"]), 0)
        bw = cv2.adaptiveThreshold(
            blur, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            p["th_block"], p["th_c"]
        )
        return bw

    # =========================
    # 开始
    # =========================
    def start(self):
        if self.view_src.image is None:
            return

        self.lbl_state.setText("状态：预处理中")
        QApplication.processEvents()

        self.target = self.preprocess()
        self.residual = self.target.copy()

        self.view_dst.pen_width = self.spin_width.value()
        self.view_dst.reset(self.view_src.size_wh)

        self.total = 0
        self.paused = False
        self.lbl_count.setText("线条数：0")
        self.lbl_speed.setText("速度：- s/条")

        self.timer.start(self.spin_interval.value())
        self.lbl_state.setText("状态：绘制中")

    # =========================
    # 单步绘制（±100 稳定版）
    # =========================
    def draw_step(self):
        if self.paused or self.total >= self.spin_limit.value():
            return

        t0 = time.perf_counter()

        ys, xs = np.where(self.residual > 0)
        if len(xs) < 20:
            return

        idx = np.random.randint(len(xs))
        cx, cy = xs[idx], ys[idx]

        angles = np.linspace(0, np.pi, 16)

        best_line = None
        best_score = 0

        h, w = self.residual.shape

        for a in angles:
            dx, dy = np.cos(a), np.sin(a)
            score = 0
            pts = []

            for t in range(-100, 101):
                x = int(cx + dx * t)
                y = int(cy + dy * t)
                if 0 <= x < w and 0 <= y < h:
                    if self.residual[y, x] > 0:
                        score += 1
                        pts.append((x, y))

            if score > best_score and len(pts) > 10:
                best_score = score
                best_line = (pts[0][0], pts[0][1], pts[-1][0], pts[-1][1])

        if best_line:
            x1, y1, x2, y2 = best_line
            self.view_dst.add(best_line)
            cv2.line(
                self.residual,
                (x1, y1), (x2, y2),
                0, self.spin_width.value()
            )

        dt = time.perf_counter() - t0
        self.total += 1

        self.lbl_count.setText(f"线条数：{self.total}")
        self.lbl_speed.setText(f"速度：{dt:.4f} s/条")

    # =========================
    # 暂停
    # =========================
    def toggle_pause(self):
        self.paused = not self.paused
        self.btn_pause.setText("继续" if self.paused else "暂停")
        self.lbl_state.setText("状态：暂停" if self.paused else "状态：绘制中")

    # =========================
    # 导出 PNG
    # =========================
    def export_png(self):
        if not self.view_dst.lines:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "导出 PNG", "", "PNG Files (*.png)"
        )
        if not path:
            return

        w, h = self.view_src.size_wh
        img = QImage(w, h, QImage.Format_RGBA8888)
        img.fill(Qt.transparent)

        p = QPainter(img)
        pen = QPen(Qt.black)
        pen.setWidth(self.view_dst.pen_width)
        p.setPen(pen)

        for x1, y1, x2, y2 in self.view_dst.lines:
            p.drawLine(x1, y1, x2, y2)

        p.end()
        img.save(path, "PNG")
        self.lbl_state.setText("状态：已导出")


# =========================
# 入口
# =========================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 720)
    w.show()
    sys.exit(app.exec())
