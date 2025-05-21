import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QGridLayout, QPushButton, QProgressBar, QTableWidget, QSizePolicy
from PyQt6.QtWidgets import QTableWidgetItem, QCheckBox, QButtonGroup, QGroupBox
from PyQt6.QtCore import Qt, QThread
#from colors import DESYCyan, DESYOrange, Dunkelblau, Gelb, Dunkelrot, Petrol, Grun, Olive
import pyqtgraph as pg
import numpy as np

from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPen, QBrush, QColor, QPalette
from plot_worker import get_plot_thread, References

DESYCyan = (0, 159, 223)
DESYOrange = (241, 143, 31)
bluish = (33, 41, 70)
DESYdarkblue = (0,75,110)
MYCOL = DESYOrange

app = QApplication([])
window = QWidget()
#window.setStyleSheet("background-color: rgb(0,75,110);")

total_width = 1000
total_height = 690
# window.setStyleSheet(f'background-color: {Dunkelblau};'
#                      f'color: {Olive};')
window.setWindowTitle("Orbit display")
window.setGeometry(100, 100, total_width, total_height)


layout = QGridLayout(parent=window)
window.setLayout(layout)


plot_h = pg.plot()
plot_v = pg.plot()
plot_thread = get_plot_thread(plot_h, plot_v)
worker = plot_thread.worker

button_plot = QPushButton('Plot', parent=window) 
button_plot.clicked.connect(lambda : worker.get_bpm_data())
# button_plot.clicked.connect(lambda : worker.bars_h.setOpts(height=np.random.random(worker.N)*10-5))
# button_plot.clicked.connect(lambda : worker.bars_v.setOpts(height=np.random.random(worker.N)*10-5))


button_start = QPushButton('Start', parent=window) 
button_start.clicked.connect(plot_thread.start)

button_stop = QPushButton('Stop', parent=window) 
button_stop.clicked.connect(plot_thread.requestInterruption)


references = References()

button_save = QPushButton('Save reference', parent=window) 
button_save.clicked.connect(lambda : references.save_reference(worker))

group_display_box = QGroupBox(parent=window)
group_display = QButtonGroup(parent=window)
checkbox_orbit = QCheckBox('Orbit', parent=window)
checkbox_ref1 = QCheckBox('Orbit - Reference 1', parent=window)
checkbox_ref2 = QCheckBox('Orbit - Reference 2', parent=window)
group_display.addButton(checkbox_orbit)
group_display.addButton(checkbox_ref1)
group_display.addButton(checkbox_ref2)
checkbox_orbit.setChecked(True)

checkbox_orbit.checkStateChanged.connect(lambda : references.switch_to_no_ref(checkbox_orbit.isChecked(), worker))
checkbox_ref1.checkStateChanged.connect(lambda : references.switch_to_ref1(checkbox_ref1.isChecked(), worker))
checkbox_ref2.checkStateChanged.connect(lambda : references.switch_to_ref2(checkbox_ref2.isChecked(), worker))

class GroupSave(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.group = QButtonGroup(parent=self)
        self.box1 = QCheckBox('to Reference 1', parent=self)
        self.box2 = QCheckBox('to Reference 2', parent=self)

        self.group.addButton(self.box1)
        self.group.addButton(self.box2)

        self.layout = QGridLayout(parent=self)
        self.layout.addWidget(self.box1, 0, 1)
        self.layout.addWidget(self.box2, 0, 2)
        self.box1.setChecked(True)

group_save = GroupSave(parent=window)
group_save.box1.checkStateChanged.connect(lambda : references.set_ref_to_save(group_save.box1.isChecked(), '1'))
group_save.box2.checkStateChanged.connect(lambda : references.set_ref_to_save(group_save.box2.isChecked(), '2'))

# checkbox_orbit.clicked.connect(checkbox_orbit.setDisabled)
# checkbox_orbit.clicked.connect(checkbox_ref1.setEnabled)
# checkbox_orbit.clicked.connect(checkbox_ref2.setEnabled)
# checkbox_orbit.clicked.connect(checkbox_ref1.)
# 
# checkbox_ref1.clicked.connect(checkbox_orbit.setEnabled)
# checkbox_ref1.clicked.connect(checkbox_ref1.setDisabled)
# checkbox_ref1.clicked.connect(checkbox_ref2.setEnabled)
# 
# checkbox_ref2.clicked.connect(checkbox_orbit.setEnabled)
# checkbox_ref2.clicked.connect(checkbox_ref1.setEnabled)
# checkbox_ref2.clicked.connect(checkbox_ref2.setDisabled)

layout.addWidget(plot_thread.worker.plot_h, 0, 0, 1, 3)
layout.addWidget(plot_thread.worker.plot_v, 1, 0, 1, 3)

layout.addWidget(button_plot, 2, 0, 1, 1)
layout.addWidget(button_start, 2, 1, 1, 1)
layout.addWidget(button_stop, 2, 2, 1, 1)
layout.addWidget(button_save, 3, 0, 1, 1)
layout.addWidget(checkbox_orbit, 4, 0, 1, 1)
layout.addWidget(checkbox_ref1, 5, 0, 1, 1)
layout.addWidget(checkbox_ref2, 6, 0, 1, 1)
layout.addWidget(group_save, 3, 1, 1, 1)
window.show()
sys.exit(app.exec())
