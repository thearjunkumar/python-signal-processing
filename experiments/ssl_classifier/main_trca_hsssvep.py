import os
cwd = os.getcwd()
import sys
path = os.path.join(cwd, "..\\..\\")
sys.path.append(path)

import numpy as np

from splearn.data import MultipleSubjects, HSSSVEP
from splearn.filter.butterworth import butter_bandpass_filter
from splearn.filter.notch import notch_filter
from splearn.filter.channels import pick_channels
from splearn.utils import Logger, Config
from splearn.cross_decomposition.trca import TRCA
from splearn.cross_validate.leave_one_out import block_evaluation
####

config = {
    "run_name": "trca_hsssvep_run2",
    "data": {
        "load_subject_ids": np.arange(1,36),
        # "selected_channels": ["PO8", "PZ", "PO7", "PO4", "POz", "PO3", "O2", "Oz", "O1"], # AA paper
        "selected_channels": ["PZ", "PO5", "PO3", "POz", "PO4", "PO6", "O1", "Oz", "O2"], # hsssvep paper        
    },
    "seed": 1234
}

main_logger = Logger(filename_postfix=config["run_name"])
main_logger.write_to_log("Config")
main_logger.write_to_log(config)

config = Config(config)

####

"""
def func_preprocessing(data):
    data_x = data.data
    # selected_channels = ['P7','P3','PZ','P4','P8','O1','Oz','O2','P1','P2','POz','PO3','PO4']
    selected_channels = config.data.selected_channels
    data_x = pick_channels(data_x, channel_names=data.channel_names, selected_channels=selected_channels)
    # data_x = notch_filter(data_x, sampling_rate=data.sampling_rate, notch_freq=50.0)
    data_x = butter_bandpass_filter(data_x, lowcut=4, highcut=75, sampling_rate=data.sampling_rate, order=6)
    start_t = 125
    end_t = 125 + 250
    data_x = data_x[:,:,:,start_t:end_t]
    data.set_data(data_x)
"""

def func_preprocessing(data):
    data_x = data.data
    data_x = pick_channels(data_x, channel_names=data.channel_names, selected_channels=config.data.selected_channels)
    # data_x = notch_filter(data_x, sampling_rate=data.sampling_rate, notch_freq=50.0)
    data_x = butter_bandpass_filter(data_x, lowcut=7, highcut=90, sampling_rate=data.sampling_rate, order=6)
    start_t = 160
    end_t = start_t + 250
    data_x = data_x[:,:,:,start_t:end_t]
    data.set_data(data_x)

data = MultipleSubjects(
    dataset=HSSSVEP, 
    root=os.path.join(path, "../data/hsssvep"), 
    subject_ids=config.data.load_subject_ids, 
    func_preprocessing=func_preprocessing,
    verbose=True, 
)

print("Final data shape:", data.data.shape)

num_channel = data.data.shape[2]
num_classes = 40
signal_length = data.data.shape[3]

####

from sklearn.metrics import accuracy_score

def leave_one_block_evaluation(classifier, X, Y, block_seq_labels=None):
    test_results_acc = []
    blocks, targets, channels, samples = X.shape
    
    main_logger.write_to_log("Begin", break_line=True)
    
    for block_i in range(blocks):
        test_acc = block_evaluation(classifier, X, Y, block_i, block_seq_labels[block_i] if block_seq_labels is not None else None)
        test_results_acc.append(test_acc)
        
        this_result = {
            "test_subject_id": block_i+1,
            "acc": test_acc,
        }
        
        main_logger.write_to_log(this_result)
        
    mean_acc = np.array(test_results_acc).mean().round(3)*100

    print(f'Mean test accuracy: {mean_acc}%')
    
    main_logger.write_to_log("Mean acc: "+str(mean_acc), break_line=True)


trca_classifier = TRCA(sampling_rate=data.sampling_rate)
leave_one_block_evaluation(classifier=trca_classifier, X=data.data, Y=data.targets)
