from PyQt6.QtCore import pyqtSignal, QObject, QThread, QCoreApplication, QTimer, pyqtSlot
import pyqtgraph as pg
import numpy as np
import time
DESYCyan = (0, 159, 223)
DESYOrange = (241, 143, 31)
cool = (8, 247, 254)
bluish = (33, 41, 70)
pink = (254, 83, 187)
DESYdarkblue = (0,75,110)
MYCOL = DESYOrange

xticks =  [[21.5, 'W'], [45.5 ,'NW'], [67.5, 'N'], [98.5, 'NO'], 
           [172.5, 'O'], [205.5, 'SO'], [224.5, 'S'], [245.5, 'SWL']]


def bar_plot(graph, x, y):
    #graph.curve.setData(y)
    graph.clear()
    for xpos, xlabel in xticks:
        graph.addItem(pg.InfiniteLine(pos=xpos, angle=90))
    graph.getPlotItem().getAxis('bottom').setTicks([xticks])
    graph.addItem(pg.BarGraphItem(x=x, height=y, width=0.5, pen=MYCOL, brush=MYCOL))

class References(object):
    def __init__(self):
        self.bpm_list = [line.strip('\n,\'') for line in open('bpm_list.txt','r').readlines()]
        self.N = len(self.bpm_list) 

        self.zero = np.zeros(self.N)

        self.reference_1_h = np.zeros(self.N)
        self.reference_1_v = np.zeros(self.N)

        self.reference_2_h = np.zeros(self.N)
        self.reference_2_v = np.zeros(self.N)
        
        self.ref_to_save = '1'

    def get_and_stop_thread(self, worker):
        thread = worker.thread()
        if thread.isRunning():
            worker.finished.emit()
            thread.wait()
            restart_thread = True
        else:
            restart_thread = False
        return thread, restart_thread

    def switch_to_no_ref(self, flag, worker):
        if flag:
            thread, restart_thread = self.get_and_stop_thread(worker)

            orbit_h = worker.bars_h.opts['height'] + worker.reference_h
            orbit_v = worker.bars_v.opts['height'] + worker.reference_v

            worker.reference_h = self.zero
            worker.reference_v = self.zero

            worker.bars_h.setOpts(height=orbit_h - worker.reference_h)
            worker.bars_v.setOpts(height=orbit_v - worker.reference_v)

            if restart_thread:
                thread.start()

    def switch_to_ref1(self, flag, worker):
        if flag:
            thread, restart_thread = self.get_and_stop_thread(worker)

            orbit_h = worker.bars_h.opts['height'] + worker.reference_h
            orbit_v = worker.bars_v.opts['height'] + worker.reference_v

            worker.reference_h = self.reference_1_h
            worker.reference_v = self.reference_1_v

            worker.bars_h.setOpts(height=orbit_h - worker.reference_h)
            worker.bars_v.setOpts(height=orbit_v - worker.reference_v)
            
            if restart_thread:
                thread.start()

    def switch_to_ref2(self, flag, worker):
        if flag:
            thread, restart_thread = self.get_and_stop_thread(worker)

            orbit_h = worker.bars_h.opts['height'] + worker.reference_h
            orbit_v = worker.bars_v.opts['height'] + worker.reference_v
            
            worker.reference_h = self.reference_2_h
            worker.reference_v = self.reference_2_v

            worker.bars_h.setOpts(height=orbit_h - worker.reference_h)
            worker.bars_v.setOpts(height=orbit_v - worker.reference_v)

            if restart_thread:
                thread.start()

    def set_ref_to_save(self, flag, ref_to_save: str):
        if flag:
            self.ref_to_save = ref_to_save
    
    def save_reference(self, worker):
        thread, restart_thread = self.get_and_stop_thread(worker)

        if self.ref_to_save == '1':
            print('Saving to reference 1')
            self.reference_1_h = worker.bars_h.opts['height'] + worker.reference_h
            self.reference_1_v = worker.bars_v.opts['height'] + worker.reference_v
        elif self.ref_to_save == '2':
            print('Saving to reference 2')
            self.reference_2_h = worker.bars_h.opts['height'] + worker.reference_h
            self.reference_2_v = worker.bars_v.opts['height'] + worker.reference_v
        else:
            raise Exception(f'Unknown reference: {self.ref_to_save}')
        
        if restart_thread:
            thread.start()

    

class Plot_worker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.plot_h = pg.plot()
        self.plot_v = pg.plot()

        self.bpm_list = [line.strip('\n,\'') for line in open('bpm_list.txt','r').readlines()]
        self.N = len(self.bpm_list) 
        self.ymin=-100
        self.ymax=100

        self.plot_h.setYRange(self.ymin, self.ymax)
        self.plot_v.setYRange(self.ymin, self.ymax)

        self.bars_h = pg.BarGraphItem(x=np.arange(self.N), height=np.zeros(self.N), width=0.5, pen=MYCOL, brush=MYCOL)
        self.bars_v = pg.BarGraphItem(x=np.arange(self.N), height=np.zeros(self.N), width=0.5, pen=MYCOL, brush=MYCOL)

        self.plot_h.addItem(self.bars_h)
        self.plot_v.addItem(self.bars_v)

        self.plot_h.setLabel('left', 'Horizontal', units='mm')
        self.plot_v.setLabel('left', 'Vertical', units='mm')

        self.plot_h.setBackground(DESYdarkblue)
        self.plot_v.setBackground(DESYdarkblue)

        self.reference_h = np.zeros(self.N)
        self.reference_v = np.zeros(self.N)

        print('Plot worker initialized')



    def plot(self):
        N = self.N
        self.bars_h.setOpts(height=100*np.sin(np.arange(N)) + np.random.random(N)*10-5 - self.reference_h)
        self.bars_v.setOpts(height=100*np.sin(np.arange(N)) + np.random.random(N)*10-5 - self.reference_h)

    @pyqtSlot()
    def check_interruption(self):
        if self.thread().isInterruptionRequested():
            #self.thread().timer.stop()
            print('Plot thread has been requested to interrupt.')
            self.finished.emit()
            return

    @pyqtSlot()
    def start_plotting(self):
        #self.selectedBPMs.setEnabled(False)
        print('Starting to_plot!')
        self.thread().timer.start()


def get_plot_thread():
    plot_thread = QThread()
    print('Plot thread initialized')
    worker = Plot_worker()
    worker.moveToThread(plot_thread)
    timer = QTimer()
    timer.moveToThread(plot_thread)
    #plot_thread.started.connect(worker.start_plotting)
    plot_thread.started.connect(timer.start)
    worker.finished.connect(plot_thread.quit)
    plot_thread.destroyed.connect(lambda : print('Plot thread destroyed'))
    worker.destroyed.connect(lambda : print('Plot worker destroyed'))
    timer.destroyed.connect(lambda : print('Plot timer destroyed'))
    plot_thread.worker = worker ### attach worker to thread so that it is not garbage collected
    plot_thread.timer = timer ### attach timer to thread so that it is not garbage collected
    timer.timeout.connect(lambda : worker.plot())
    timer.timeout.connect(worker.check_interruption)
    timer.setInterval(50)
    plot_thread.finished.connect(timer.stop)
    return plot_thread