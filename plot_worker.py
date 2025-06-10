from PyQt6.QtCore import pyqtSignal, QObject, QThread, QCoreApplication, QTimer, pyqtSlot, QThreadPool
import pyqtgraph as pg
import numpy as np
import time
import PyTine as pt

DESYCyan = (0, 159, 223)
DESYOrange = (241, 143, 31)
cool = (8, 247, 254)
bluish = (33, 41, 70)
pink = (254, 83, 187)
DESYdarkblue = (0,75,110)
MYCOL = DESYOrange


class References(object):
    def __init__(self):
        self.bpm_list = [line.strip('\n,\'') for line in open('bpm_list.txt','r').readlines()][:-2]
        self.N = len(self.bpm_list) 

        self.zero = np.zeros(self.N)

        self.reference_1_x = np.zeros(self.N)
        self.reference_1_y = np.zeros(self.N)

        self.reference_2_x = np.zeros(self.N)
        self.reference_2_y = np.zeros(self.N)
        
        self.ref_to_save = '1'

    def switch_to_no_ref(self, flag, worker):
        if flag:
            worker.reference_x = self.zero
            worker.reference_y = self.zero
            worker.plot()
            worker.active_reference = 0

    def switch_to_ref1(self, flag, worker):
        if flag:
            worker.reference_x = self.reference_1_x
            worker.reference_y = self.reference_1_y
            worker.plot()
            worker.active_reference = 1

    def switch_to_ref2(self, flag, worker):
        if flag:
            worker.reference_x = self.reference_2_x
            worker.reference_y = self.reference_2_y
            worker.plot()
            worker.active_reference = 2

    def plot_orbit_minus_ref(worker):
        worker.bars_h.setOpts(height=worker.orbit_x - worker.reference_x)
        worker.bars_v.setOpts(height=worker.orbit_y - worker.reference_y)

    def set_ref_to_save(self, flag, ref_to_save: str):
        if flag:
            self.ref_to_save = ref_to_save
    
    def save_reference(self, worker):
        print('trying to save', self.ref_to_save)

        if self.ref_to_save == '1':
            print('saving 1')
            self.reference_1_x = worker.bars_h.opts['height'] + worker.reference_x
            self.reference_1_y = worker.bars_v.opts['height'] + worker.reference_y
            if worker.active_reference == 1:
                self.switch_to_ref1(True, worker)
        elif self.ref_to_save == '2':
            self.reference_2_x = worker.bars_h.opts['height'] + worker.reference_x
            self.reference_2_y = worker.bars_v.opts['height'] + worker.reference_y
            if worker.active_reference == 2:
                self.switch_to_ref2(True, worker)
        else:
            raise Exception(f'Unknown reference: {self.ref_to_save}')

    
class Plot_worker(QObject):
    def __init__(self):
        super().__init__()

        self.plot_h = pg.plot()
        self.plot_v = pg.plot()

        self.bpm_list = [line.strip('\n,\'') for line in open('bpm_list.txt','r').readlines()][:-2]
        self.N = len(self.bpm_list) 
        self.ymin = -0.002
        self.ymax = +0.002

        self.plot_h.setYRange(self.ymin, self.ymax)
        self.plot_v.setYRange(self.ymin, self.ymax)

        self.bars_h = pg.BarGraphItem(x=np.arange(self.N), height=np.zeros(self.N), width=0.5, pen=MYCOL, brush=MYCOL)
        self.bars_v = pg.BarGraphItem(x=np.arange(self.N), height=np.zeros(self.N), width=0.5, pen=MYCOL, brush=MYCOL)

        self.plot_h.addItem(self.bars_h)
        self.plot_v.addItem(self.bars_v)

        self.plot_h.setLabel('left', 'Horizontal', units='m')
        self.plot_v.setLabel('left', 'Vertical', units='m')

        self.plot_h.setBackground(DESYdarkblue)
        self.plot_v.setBackground(DESYdarkblue)
	
        xticks =  [[-0.5, 'SWR'], [21.5, 'W'], [45.5 ,'NW'], [67.5, 'N'], [98.5, 'NO'], 
                   [172.5, 'O'], [205.5, 'SO'], [224.5, 'S'], [245.5, 'SWL']]

        for graph in [self.plot_h, self.plot_v]: 
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
        self.bars_h.setOpts(height=self.orbit_x - self.reference_x)
        self.bars_v.setOpts(height=self.orbit_y - self.reference_y)

    @pyqtSlot(np.ndarray)
    def plot_x(self, orbit_x):
        self.orbit_x = orbit_x
        self.bars_h.setOpts(height=self.orbit_x - self.reference_x)

    @pyqtSlot(np.ndarray)
    def plot_y(self, orbit_y):
        self.orbit_y = orbit_y
        self.bars_v.setOpts(height=self.orbit_y - self.reference_y)


class Thread_worker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    got_x = pyqtSignal(np.ndarray)
    got_y = pyqtSignal(np.ndarray)
    
    def __init__(self):
        super().__init__()

        self.nm_to_m = 1e-9

        self.bpm_list = [line.strip('\n,\'') for line in open('bpm_list.txt','r').readlines()][:-2]
        self.N = len(self.bpm_list) 

        self.bpm_address = '/PETRA/REFORBIT/BPM_SWR_13'
        self.bpm_property = {'x' : 'SA_X_BBAGO', 'y' : 'SA_Y_BBAGO'}

        self.orbit_x = np.zeros(self.N)
        self.orbit_y = np.zeros(self.N)

        print('Plot worker initialized')

    def get_bpm_data(self):
        self.orbit_x[:] = pt.get(address=self.bpm_address, property=self.bpm_property['x'])['data'][:-2]
        self.orbit_y[:] = pt.get(address=self.bpm_address, property=self.bpm_property['y'])['data'][:-2]
        self.orbit_x *= self.nm_to_m
        self.orbit_y *= self.nm_to_m
        self.got_x.emit(orbit_x)
        self.got_y.emit(orbit_y)
        self.bars_h.setOpts(height=orbit_x - self.reference_h)
        self.bars_v.setOpts(height=orbit_y - self.reference_v)

    def attach_callback_x(self, id, cc, d):
        self.orbit_x[:] = d['data'][:-2] 
        self.orbit_x *= self.nm_to_m
        self.got_x.emit(self.orbit_x)

    def attach_callback_y(self, id, cc, d):
        self.orbit_y[:] = d['data'][:-2] #
        self.orbit_y *= self.nm_to_m
        self.got_y.emit(self.orbit_y)

    @pyqtSlot()
    def check_interruption(self):
        if self.thread().isInterruptionRequested():
            self.thread().timer.stop()
            print('Plot thread has been requested to interrupt.')
            self.finished.emit()
            pt.detach(self.lidx)
            pt.detach(self.lidy)
            print(f'Tine IDs detached: {self.lidx}, {self.lidy}')
            return

    @pyqtSlot()
    def subscribe(self):
        #self.selectedBPMs.setEnabled(False)
        print('Starting to_plot!')
        self.thread().timer.start()
        lidx = pt.attach(address=self.bpm_address, property=self.bpm_property['x'], callback=self.attach_callback_x, interval=100)
        self.lidx = lidx
        lidy = pt.attach(address=self.bpm_address, property=self.bpm_property['y'], callback=self.attach_callback_y, interval=100)
        self.lidy = lidy
        print(f'Tine IDs: {lidx}, {lidy}')

def get_plot_thread(plot_worker):
    plot_thread = QThread()
    print('Plot thread initialized')
    worker = Thread_worker()
    worker.moveToThread(plot_thread)
    worker.got_x.connect(plot_worker.plot_x)
    worker.got_y.connect(plot_worker.plot_y)

    timer = QTimer()
    timer.moveToThread(plot_thread)
    timer.timeout.connect(worker.check_interruption)
    plot_thread.started.connect(worker.subscribe)
    worker.finished.connect(plot_thread.quit)
    
    # destructors
    plot_thread.destroyed.connect(lambda : print('Plot thread destroyed'))
    worker.destroyed.connect(lambda : print('Plot worker destroyed'))
    timer.destroyed.connect(lambda : print('Plot timer destroyed'))

    # attach to thread to prevent garbage collection
    plot_thread.worker = worker
    plot_thread.timer = timer 

    #prevent thread from expiring?
    QThreadPool.globalInstance().setExpiryTimeout(-1)

    # timer.timeout.connect(lambda : worker.get_bpm_data())

    # timer.setInterval(100)
    # plot_thread.finished.connect(timer.stop)
    return plot_thread
