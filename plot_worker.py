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




# def bar_plot(graph, x, y):
#     #graph.curve.setData(y)
#     graph.clear()
#     for xpos, xlabel in xticks:
#         graph.addItem(pg.InfiniteLine(pos=xpos, angle=90))
#     graph.getPlotItem().getAxis('bottom').setTicks([xticks])
#     graph.addItem(pg.BarGraphItem(x=x, height=y, width=0.5, pen=MYCOL, brush=MYCOL))

class References(object):
    def __init__(self):
        self.bpm_list = [line.strip('\n,\'') for line in open('bpm_list.txt','r').readlines()][:-2]
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
            #thread, restart_thread = self.get_and_stop_thread(worker)

            orbit_h = worker.bars_h.opts['height'] + worker.reference_h
            orbit_v = worker.bars_v.opts['height'] + worker.reference_v

            worker.reference_h = self.zero
            worker.reference_v = self.zero

            worker.bars_h.setOpts(height=orbit_h - worker.reference_h)
            worker.bars_v.setOpts(height=orbit_v - worker.reference_v)

            #if restart_thread:
            #    thread.start()

    def switch_to_ref1(self, flag, worker):
        if flag:
            #thread, restart_thread = self.get_and_stop_thread(worker)

            orbit_h = worker.bars_h.opts['height'] + worker.reference_h
            orbit_v = worker.bars_v.opts['height'] + worker.reference_v

            worker.reference_h = self.reference_1_h
            worker.reference_v = self.reference_1_v

            worker.bars_h.setOpts(height=orbit_h - worker.reference_h)
            worker.bars_v.setOpts(height=orbit_v - worker.reference_v)
            #if restart_thread:
            #    thread.start()

    def switch_to_ref2(self, flag, worker):
        if flag:
            #thread, restart_thread = self.get_and_stop_thread(worker)

            orbit_h = worker.bars_h.opts['height'] + worker.reference_h
            orbit_v = worker.bars_v.opts['height'] + worker.reference_v
            
            worker.reference_h = self.reference_2_h
            worker.reference_v = self.reference_2_v

            worker.bars_h.setOpts(height=orbit_h - worker.reference_h)
            worker.bars_v.setOpts(height=orbit_v - worker.reference_v)

            #if restart_thread:
            #    thread.start()

    def set_ref_to_save(self, flag, ref_to_save: str):
        if flag:
            self.ref_to_save = ref_to_save
    
    def save_reference(self, worker):
        # thread, restart_thread = self.get_and_stop_thread(worker)

        print('trying to save', self.ref_to_save)
        if self.ref_to_save == '1':
            print('saving 1')
            self.reference_1_h = worker.bars_h.opts['height'] + worker.reference_h
            self.reference_1_v = worker.bars_v.opts['height'] + worker.reference_v
        elif self.ref_to_save == '2':
            self.reference_2_h = worker.bars_h.opts['height'] + worker.reference_h
            self.reference_2_v = worker.bars_v.opts['height'] + worker.reference_v
        else:
            raise Exception(f'Unknown reference: {self.ref_to_save}')
        
        # if restart_thread:
        #     thread.start()

    

class Plot_worker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, plot_h, plot_v):
        super().__init__()

        self.plot_h = plot_h
        self.plot_v = plot_v

        self.bpm_address = '/PETRA/REFORBIT/BPM_SWR_13'
        self.bpm_property = {'x' : 'SA_X_BBAGO', 'y' : 'SA_Y_BBAGO'}

        self.bpm_list = [line.strip('\n,\'') for line in open('bpm_list.txt','r').readlines()][:-2]
        self.N = len(self.bpm_list) 
        self.ymin=-500
        self.ymax=500

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
	
        xticks =  [[21.5, 'W'], [45.5 ,'NW'], [67.5, 'N'], [98.5, 'NO'], 
                   [172.5, 'O'], [205.5, 'SO'], [224.5, 'S'], [245.5, 'SWL']]

        for graph in [self.plot_h, self.plot_v]: 
            for xpos, xlabel in xticks:
                graph.addItem(pg.InfiniteLine(pos=xpos, angle=90))
            graph.getPlotItem().getAxis('bottom').setTicks([xticks])
        self.reference_h = np.zeros(self.N)
        self.reference_v = np.zeros(self.N)

        print('Plot worker initialized')

    def get_bpm_data(self):
        orbit_x = pt.get(address=self.bpm_address, property=self.bpm_property['x'])['data'][:-2]
        orbit_y = pt.get(address=self.bpm_address, property=self.bpm_property['y'])['data'][:-2]
        self.bars_h.setOpts(height=orbit_x - self.reference_h)
        self.bars_v.setOpts(height=orbit_y - self.reference_v)


    def attach_callback_x(self, id, cc, d):
        orbit_x = d['data'][:-2]
        self.bars_h.setOpts(height=orbit_x - self.reference_h)

    def attach_callback_y(self, id, cc, d):
        orbit_y = d['data'][:-2]
        self.bars_v.setOpts(height=orbit_y - self.reference_v)
        

    @pyqtSlot()
    def plot(self):
        bar_plot(self.plot_h, np.arange(self.N), 100*np.sin(np.arange(self.N)) + np.random.random(self.N)*10-5)
        bar_plot(self.plot_v, np.arange(self.N), 100*np.sin(np.arange(self.N)) + np.random.random(self.N)*10-5)

    @pyqtSlot()
    def check_interruption(self):
        if self.thread().isInterruptionRequested():
            #self.thread().timer.stop()
            print('Plot thread has been requested to interrupt.')
            self.finished.emit()
            pt.detach(self.lidx)
            pt.detach(self.lidy)
            return

    @pyqtSlot()
    def start_plotting(self):
        #self.selectedBPMs.setEnabled(False)
        print('Starting to_plot!')
        self.thread().timer.start()
        lidx = pt.attach(address=self.bpm_address, property=self.bpm_property['x'], callback=self.attach_callback_x, interval=100)
        self.lidx = lidx
        lidy = pt.attach(address=self.bpm_address, property=self.bpm_property['y'], callback=self.attach_callback_y, interval=100)
        self.lidy = lidy
        print(f'Tine IDs: {lidx}, {lidy}')

def get_plot_thread(plot_h, plot_v):
    plot_thread = QThread()
    print('Plot thread initialized')
    worker = Plot_worker(plot_h, plot_v)
    worker.moveToThread(plot_thread)
    timer = QTimer()
    timer.moveToThread(plot_thread)
    plot_thread.started.connect(worker.start_plotting)
    worker.finished.connect(plot_thread.quit)
    plot_thread.destroyed.connect(lambda : print('Plot thread destroyed'))
    worker.destroyed.connect(lambda : print('Plot worker destroyed'))
    timer.destroyed.connect(lambda : print('Plot timer destroyed'))
    plot_thread.worker = worker ### attach worker to thread so that it is not garbage collected
    plot_thread.timer = timer ### attach timer to thread so that it is not garbage collected
    QThreadPool.globalInstance().setExpiryTimeout(-1)

    timer.timeout.connect(lambda : worker.get_bpm_data())
    # timer.timeout.connect(lambda : worker.bars_h.setOpts(height=100*np.sin(np.arange(worker.N)) + np.random.random(worker.N)*10-5 - worker.reference_h))
    # timer.timeout.connect(lambda : worker.bars_v.setOpts(height=100*np.sin(np.arange(worker.N)) + np.random.random(worker.N)*10-5 - worker.reference_v))

    timer.timeout.connect(worker.check_interruption)
    timer.setInterval(100)
    plot_thread.finished.connect(timer.stop)
    return plot_thread
