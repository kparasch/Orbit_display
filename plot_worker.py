from PyQt6.QtCore import pyqtSignal, QObject, QThread, QCoreApplication, QTimer, pyqtSlot, QThreadPool
import pyqtgraph as pg
import numpy as np
import pydoocs

DESYCyan = (0, 159, 223)
DESYOrange = (241, 143, 31)
DESYdarkblue = (0,75,110)
MYCOL = DESYOrange

NM_TO_M = 1e-9
BPM_ADDRESS_X = 'PETRA/REFORBIT/*/SA_X_BBAGO'
BPM_ADDRESS_Y = 'PETRA/REFORBIT/*/SA_Y_BBAGO'
REFRESH_RATE = 100

def get_pydoocs_orbit():
    data_x = pydoocs.read(BPM_ADDRESS_X)
    orbit_x = np.array([dd[1] for dd in data_x['data'][:-2]])
    data_y = pydoocs.read(BPM_ADDRESS_Y)
    orbit_y = np.array([dd[1] for dd in data_y['data'][:-2]])
    orbit_x *= NM_TO_M
    orbit_y *= NM_TO_M
    return orbit_x, orbit_y
    
class Plot_worker(QObject):
    def __init__(self):
        super().__init__()

        self.plot_x = pg.plot()
        self.plot_y = pg.plot()

        self.bpm_list = [line.strip('\n,\'') for line in open('bpm_list.txt','r').readlines()][:-2]
        self.N = len(self.bpm_list) 
        self.ymin = -0.002
        self.ymax = +0.002

        self.plot_x.setYRange(self.ymin, self.ymax)
        self.plot_y.setYRange(self.ymin, self.ymax)

        self.bars_x = pg.BarGraphItem(x=np.arange(self.N), height=np.zeros(self.N), width=0.5, pen=MYCOL, brush=MYCOL)
        self.bars_y = pg.BarGraphItem(x=np.arange(self.N), height=np.zeros(self.N), width=0.5, pen=MYCOL, brush=MYCOL)

        self.plot_x.addItem(self.bars_x)
        self.plot_y.addItem(self.bars_y)

        self.plot_x.setLabel('left', 'Horizontal', units='m')
        self.plot_y.setLabel('left', 'Vertical', units='m')

        self.plot_x.setBackground(DESYdarkblue)
        self.plot_y.setBackground(DESYdarkblue)
	
        xticks =  [[-0.5, 'SWR'], [21.5, 'W'], [45.5 ,'NW'], [67.5, 'N'], [98.5, 'NO'], 
                   [172.5, 'O'], [205.5, 'SO'], [224.5, 'S'], [245.5, 'SWL']]

        for graph in [self.plot_x, self.plot_y]: 
            for xpos, xlabel in xticks:
                graph.addItem(pg.InfiniteLine(pos=xpos, angle=90))
            graph.getPlotItem().getAxis('bottom').setTicks([xticks])

        self.active_reference = 0
        self.reference_x = np.zeros(self.N)
        self.reference_y = np.zeros(self.N)
        self.orbit_x = np.zeros(self.N)
        self.orbit_y = np.zeros(self.N)

        print('Plot worker initialized')

    @pyqtSlot()
    def plot(self):
        self.bars_x.setOpts(height=self.orbit_x - self.reference_x)
        self.bars_y.setOpts(height=self.orbit_y - self.reference_y)

    @pyqtSlot(np.ndarray)
    def store_x(self, orbit_x):
        self.orbit_x = orbit_x
        self.bars_x.setOpts(height=self.orbit_x - self.reference_x)

    @pyqtSlot(np.ndarray)
    def store_y(self, orbit_y):
        self.orbit_y = orbit_y
        self.bars_y.setOpts(height=self.orbit_y - self.reference_y)

    def get_bpm_data(self):
        orbit_x, orbit_y = get_pydoocs_orbit()
        self.store_x(orbit_x)
        self.store_y(orbit_y)


class Thread_worker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    got_x = pyqtSignal(np.ndarray)
    got_y = pyqtSignal(np.ndarray)
    
    def __init__(self):
        super().__init__()

        self.bpm_list = [line.strip('\n,\'') for line in open('bpm_list.txt','r').readlines()][:-2]
        self.N = len(self.bpm_list) 

        self.orbit_x = np.zeros(self.N)
        self.orbit_y = np.zeros(self.N)

        print('Plot worker initialized')

    @pyqtSlot()
    def emit_orbit(self):
        self.orbit_x, self.orbit_y = get_pydoocs_orbit()
        self.got_x.emit(self.orbit_x)
        self.got_y.emit(self.orbit_y)

    @pyqtSlot()
    def check_interruption(self):
        if self.thread().isInterruptionRequested():
            self.thread().timer.stop()
            print('Plot thread has been requested to interrupt.')
            self.finished.emit()
            return

    @pyqtSlot()
    def subscribe(self):
        print('Starting to_plot!')
        self.thread().timer.start()

def get_plot_thread(plot_worker):
    plot_thread = QThread()
    print('Plot thread initialized')
    worker = Thread_worker()
    worker.moveToThread(plot_thread)
    worker.got_x.connect(plot_worker.store_x)
    worker.got_y.connect(plot_worker.store_y)

    timer = QTimer()
    timer.setInterval(REFRESH_RATE)
    timer.moveToThread(plot_thread)
    timer.timeout.connect(worker.check_interruption)
    timer.timeout.connect(worker.emit_orbit)
    plot_thread.started.connect(worker.subscribe)
    worker.finished.connect(plot_thread.quit)
    
    # destructors
    plot_thread.destroyed.connect(lambda : print('Plot thread destroyed'))
    worker.destroyed.connect(lambda : print('Plot worker destroyed'))
    timer.destroyed.connect(lambda : print('Plot timer destroyed'))

    # attach to thread to prevent garbage collection
    plot_thread.worker = worker
    plot_thread.timer = timer 

    return plot_thread
