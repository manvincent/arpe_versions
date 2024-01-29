import os
import numpy as np
from copy import deepcopy as dcopy
import pickle
import dill
import json
from DAQ_config import *

def class2dict(instance, built_dict={}):
  if not hasattr(instance, "__dict__"):
    return instance
  new_subdic = vars(instance)
  for key, value in new_subdic.items():
    new_subdic[key] = class2dict(value)
  return new_subdic

def convert(x):
    if hasattr(x, "tolist"):  # numpy arrays have this
      return x.tolist()
    raise TypeError(x)

def save_json(obj, name):
    with open(f'{name}.json',"w") as f:
        json.dump(obj,f, default=convert)

def load_json(name):
    with open(name) as f:
        data = json.load(f)

def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        dill.dump(obj, f)

def load_obj(name):
    with open(name, 'rb') as f:
        return pickle.load(f)

def saveData(sI, tI, expInfo, dispInfo, taskInfo):
    # Save ancilliary data
    ancOutDir = f'{expInfo.outDir}/ancillary'
    if not os.path.exists(ancOutDir):
        os.mkdir(ancOutDir)
    save_obj(expInfo, f'{ancOutDir}/sub{expInfo.SubNo}_sess{sI+1}_expInfo')
    save_obj(dispInfo, f'{ancOutDir}/sub{expInfo.SubNo}_sess{sI+1}_dispInfo')
    # Save data
    # Record last trial and last session
    taskInfo.__dict__.update({'lastTrial_idx': tI,
                              'lastSess_idx': sI})
    # Record last trial of current session
    taskInfo.sessionInfo[sI].__dict__.update({'lastTrialSess_idx': tI})
    # Write out
    if expInfo.Modality == 'ephys':
        del taskInfo.port
    save_obj(taskInfo, f'{expInfo.outDir}/sub{expInfo.SubNo}_sess{sI+1}_data')
    # If last session already saved, save again as full dataset
    if os.path.exists(f'{expInfo.outDir}/sub{expInfo.SubNo}_sess{taskInfo.numSessions}_data'):
        save_obj(taskInfo, f'{expInfo.outDir}/sub{expInfo.SubNo}_allSess_data')

    # Create a copy and convert to dict
    taskInfo_copy = dcopy(taskInfo)
    taskDict = class2dict(taskInfo_copy)
    for i in np.arange(len(taskDict['sessionInfo'])):
        taskDict['sessionInfo'][i] = class2dict(taskDict['sessionInfo'][i])
    save_json(taskDict, f'{expInfo.outDir}/sub{expInfo.SubNo}_sess{sI+1}_data')
    # If last session already saved, save again as full dataset
    if os.path.exists(f'{expInfo.outDir}/sub{expInfo.SubNo}_sess{taskInfo.numSessions}_data'):
        save_json(taskDict, f'{expInfo.outDir}/sub{expInfo.SubNo}_allSess_data')

    # Reload the port devices
    if expInfo.Modality == 'ephys':
        port = initDAQ()
        taskInfo.__dict__.update({'port': port})
    return

def saveDataTrial(sI, tI, expInfo, taskInfo):
    # Record last trial and last session
    taskInfo.__dict__.update({'lastTrial_idx': tI,
                              'lastSess_idx': sI})
    # Record last trial of current session
    taskInfo.sessionInfo[sI].__dict__.update({'lastTrialSess_idx': tI})

    # Write out
    if expInfo.Modality == 'ephys':
        del taskInfo.port
    
    # Create a copy and convert to dict
    taskInfo_copy = dcopy(taskInfo)
    taskDict = class2dict(taskInfo_copy)
    for i in np.arange(len(taskDict['sessionInfo'])):
        taskDict['sessionInfo'][i] = class2dict(taskDict['sessionInfo'][i])
    save_json(taskDict, f'{expInfo.outDir}/sub{expInfo.SubNo}_sess{sI+1}_data')
    # If last session already saved, save again as full dataset
    if os.path.exists(f'{expInfo.outDir}/sub{expInfo.SubNo}_sess{taskInfo.numSessions}_data'):
        save_json(taskDict, f'{expInfo.outDir}/sub{expInfo.SubNo}_allSess_data')

    # Reload the port devices
    if expInfo.Modality == 'ephys':
        port = initDAQ()      
        taskInfo.__dict__.update({'port': port})
    return

def saveTTLsToTxt(expInfo, taskInfo, tTTL, trigger_label):
    # Save ancilliary data
    ttlDir = f'{expInfo.outDir}/TTL'
    if not os.path.exists(ttlDir):
        os.makedirs(ttlDir)    
    triggerID = getattr(taskInfo.triggerCodes, trigger_label)
    fname_ttl = f'{ttlDir}/sub{expInfo.SubNo}_TTL'    
    with open(fname_ttl, 'a') as f:
        TTL_str = f'{str(tTTL)}:{str(triggerID)}\n'
        f.write(TTL_str)
        
def savePractData(tI, expInfo, practInfo):
    # Save ancilliary data
    ancOutDir = f'{expInfo.outDir}/ancillary'
    if not os.path.exists(ancOutDir):
        os.mkdir(ancOutDir)
    # Record last trial of session
    practInfo.__dict__.update({'numPractTrials': tI+1})
    # Save data
    save_obj(practInfo, f'{ancOutDir}/sub{expInfo.SubNo}_pract_data')

    # Create a copy and convert to dict
    practInfo_copy = dcopy(practInfo)
    practDict = class2dict(practInfo_copy)
    save_json(practDict, f'{ancOutDir}/sub{expInfo.SubNo}_pract_data')
    
    # Save staircase parameter
    with open(f'{ancOutDir}/sub{expInfo.SubNo}_SC_param.txt', 'w') as file:
        file.write(str(practInfo.final_K_o))
    return
                