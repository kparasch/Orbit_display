import numpy as np
from plot_worker import BPM_LIST

class References(object):
    def __init__(self):
        self.bpm_list = [line.strip('\n,\'') for line in open(BPM_LIST,'r').readlines()]#[:-2]
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

    def set_ref_to_save(self, flag, ref_to_save: str):
        if flag:
            self.ref_to_save = ref_to_save
    
    def save_reference(self, worker):
        if self.ref_to_save == '1':
            print('Saving to reference 1.')
            self.reference_1_x = worker.orbit_x.copy()
            self.reference_1_y = worker.orbit_y.copy()
            if worker.active_reference == 1:
                self.switch_to_ref1(True, worker)
        elif self.ref_to_save == '2':
            print('Saving to reference 2.')
            self.reference_2_x = worker.orbit_x.copy()
            self.reference_2_y = worker.orbit_y.copy()
            if worker.active_reference == 2:
                self.switch_to_ref2(True, worker)
        else:
            raise Exception(f'Unknown reference: {self.ref_to_save}')

