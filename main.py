import subprocess
import sys
import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QFrame, QGridLayout
from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont, QColor, QPalette
import psutil

import platform

class SystemMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cpu_usage_history = np.zeros(60)
        self.memory_usage_history = np.zeros(60)
        self.initUI()

        self.update_interval = 4000
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_system_info)
        self.timer.start(self.update_interval)
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            self.gpu_name = gpus[0].name if gpus else "GPU: Not found"
        except ImportError:
            self.gpu_name = "GPU: not supported"

        self.cpu_name = self.get_cpu_name()

    def get_cpu_name(self):
        if platform.system() == "Windows":
            try:
                output = subprocess.check_output("wmic cpu get name", universal_newlines=True)
                lines = [line.strip() for line in output.split("\n") if line.strip()]
                if len(lines) > 1:
                    return lines[1]
                else:
                    return "Unknown CPU"
            except subprocess.CalledProcessError:
                return "Unknown CPU"
        elif platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo", "r") as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(":")[1].strip()
            except FileNotFoundError:
                return "Unknown CPU"
        return "Unknown CPU"

    def initUI(self):
        self.setWindowTitle("System Monitor")
        self.setGeometry(100, 100, 530, 400)
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)

        self.cpu_plot = pg.PlotWidget(title="CPU Usage (%)")
        self.memory_plot = pg.PlotWidget(title="Memory Usage (%)")
        self.layout.addWidget(self.cpu_plot)
        self.layout.addWidget(self.memory_plot)

        self.system_info_label = QLabel()
        self.system_info_label.setFont(QFont('Arial', 10))
        self.system_info_label.setStyleSheet("color: #E0E0E0;")
        self.layout.addWidget(self.system_info_label)

        self.process_grid_layout = QGridLayout()
        self.layout.addLayout(self.process_grid_layout)

        self.process_labels_cpu = [QLabel("-------------") for _ in range(5)]
        self.process_labels_memory = [QLabel("-------------") for _ in range(5)]

        for i in range(5):
            self.process_grid_layout.addWidget(self.process_labels_cpu[i], i, 0)
            self.process_grid_layout.addWidget(self.process_labels_memory[i], i, 1)

        self.setCentralWidget(self.central_widget)
        self.apply_dark_theme()

    def update_system_info(self):
        cpu_usage = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        self.cpu_usage_history = np.roll(self.cpu_usage_history, -1)
        self.cpu_usage_history[-1] = cpu_usage

        self.memory_usage_history = np.roll(self.memory_usage_history, -1)
        self.memory_usage_history[-1] = memory.percent

        self.cpu_plot.plot(self.cpu_usage_history, pen=pg.mkPen('#0066CC', width=2), clear=True)
        self.memory_plot.plot(self.memory_usage_history, pen=pg.mkPen('#0066CC', width=2), clear=True)
        self.update_system_info_label()
        self.update_process_info()

    def update_process_info(self):
        num_cores = psutil.cpu_count()

        processes = [(p.info['name'], p.info['cpu_percent'], p.memory_info().rss / (1024 ** 2))
                     for p in psutil.process_iter(attrs=['name', 'cpu_percent', 'memory_percent'])
                     if p.info['name'] != "System Idle Process"]

        top_cpu_processes = sorted(processes, key=lambda x: x[1], reverse=True)[:5]
        top_cpu_processes = [(name, cpu / num_cores, memory) for name, cpu, memory in top_cpu_processes]

        top_memory_processes = sorted(processes, key=lambda x: x[2], reverse=True)[:5]

        for i, (name, cpu, memory) in enumerate(top_cpu_processes):
            if i < len(self.process_labels_cpu):
                self.process_labels_cpu[i].setText(f"{name}: CPU {cpu:.2f}%")

        for i, (name, cpu, memory) in enumerate(top_memory_processes):
            if i < len(self.process_labels_memory):
                self.process_labels_memory[i].setText(f"{name}: Memory {memory:.2f} MB")

    def update_system_info_label(self):
        cpu_name = "Unknown CPU"
        if hasattr(psutil, 'cpu_freq'):
            cpu_info = psutil.cpu_freq()
            cpu_name = f"CPU: {psutil.cpu_count(logical=True)} cores, {cpu_info.current:.2f} MHz"

        memory_info = f"Memory: {psutil.virtual_memory().total / (1024 ** 3):.2f} GB"
        cpu_info = f"CPU: {self.cpu_name}"
        self.system_info_label.setText(f"{cpu_info}\n{self.gpu_name}\n{memory_info}")


    def apply_dark_theme(self):
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 45))
        app.setPalette(palette)
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; }
            QLabel { color: #E0E0E0; }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SystemMonitorApp()
    window.show()
    sys.exit(app.exec())