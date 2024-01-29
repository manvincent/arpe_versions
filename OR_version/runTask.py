
import os
import fnmatch
from psychopy import visual, gui, data, core, event, logging, info
from psychopy.constants import *
homeDir = '/home/olab/Desktop/Experiments/ape_v9_intraop'
# Ensure that relative paths start from the same directory as this script
os.chdir(homeDir)
outDir = f'{homeDir}/Output'
stimDir = f'{homeDir}/Images'
payDir = f'{homeDir}/Payout'
instructDir = f'{stimDir}/instruct'
# Create directories if they don't exist
if not os.path.exists(outDir):
    os.mkdir(outDir)
if not os.path.exists(stimDir):
    os.mkdir(stimDir)
if not os.path.exists(payDir):
    os.mkdir(payDir)


# Add dependencies
from config import *
from initTask import *
from runInstruct import *
from runPract import *
from runBandit_joy import *
from runBandit_mouse import *

## Experiment start ##
# Store info about the experiment session
# Reference:
    # SubNo. - int
    # numSessions: int (max 6 for unique stimuli)
    # Version - test or debug
    # Modality - behav, ephys
    # Interface - TTL
    # Instruction - long or short

check = 0
while check == 0:
    expName = 'Fishing game'  # from the Builder filename that created this script
    expInfo = {'SubNo': 999,
               'startSession': 1, # Starting session ID
               'numSessions': 2, # The max session ID
               'Version': 'debug',
               'Modality': 'ephys',
               'doInstruct': True,
               'doPract': True,
               'doTask': True,
               'invertJoy': False}
    dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)
    if dlg.OK == False:
        print('User Cancelled')  # user pressed cancel
        core.wait(3)
        core.quit()
    # Check to see there's no existing subject ID - if there is, repeat this dialogue box
    exist = False
    for file in os.listdir(outDir):
        if fnmatch.fnmatch(file, f"*sub{expInfo['SubNo']}*"):
            exist = True
    if (exist):
        check = 0
        print('That file already exists, try another subject number!')
    else:
        check = 1

expInfo.update({'date': data.getDateStr(),  # add a simple timestamp
                'expName': expName,
                'homeDir': homeDir,
                'outDir': outDir,
                'stimDir': stimDir,
                'payDir': payDir,
                'instructDir': instructDir})

# Set whether instruction is long or short format 
if expInfo['doInstruct']:
    instructInfo = {'Instruction': 'short'} # can be long or short
    dlg = gui.DlgFromDict(dictionary=instructInfo, title='instruct')
    expInfo.update({'instructType': instructInfo['Instruction']})
    
# Set mass parameter
if not expInfo['doPract']:
    pract_filePath = f"{outDir}/ancillary/sub{expInfo['SubNo']}_SC_param.txt"
    # Check to see if practice file exists, and pull mass parameter from that
    if os.path.exists(pract_filePath): 
        with open(pract_filePath, 'r') as f:
            final_K_o = float(f.read())
    else: # Otherwise set mass parameter manually
        print('No practice file found. Set parameter manually.')
        springInfo = {'K_o': 1.0}
        dlg = gui.DlgFromDict(dictionary=springInfo, title='param')
        final_K_o = springInfo['K_o']
else:
    final_K_o = []
expInfo.update({'final_K_o': final_K_o})

# Set type of trigger system
if expInfo['Modality'] == 'ephys':
    interfaceInfo = {'interface': 'DAQ'}
    dlg = gui.DlgFromDict(dictionary=interfaceInfo, title='interface')
    expInfo.update({'interface': interfaceInfo['interface']})


# Set up between-subject counterbalance
expInfo = dict2class(counterbalance(expInfo))  # output is given by expInfo.sub_cb
#####  Task Section  #####
taskClock = core.Clock()
# Initialize general parameters
[screen, dispInfo, taskInfo, taskObj, keyInfo] = initTask(expInfo)


if __name__ == "__main__":
    # Run instructions
    if (expInfo.doInstruct):
        if expInfo.instructType == 'long':            
            runInstruct_long(expInfo, dispInfo, taskInfo, taskObj)
        elif expInfo.instructType == 'short':
            runInstruct_short(expInfo, dispInfo, taskInfo, taskObj)
    if (expInfo.doPract):
        initPract(taskInfo)
        runPract(expInfo, dispInfo, taskInfo, taskObj, keyInfo)
    # Run the task
    if (expInfo.doTask):
        # runBandit_joy(expInfo, dispInfo, taskInfo, taskObj, keyInfo)
        runBandit_mouse(expInfo, dispInfo, taskInfo, taskObj, keyInfo)
    # Close screen after experiment ends
    screen.close()
    # Print out the final payment amount across the session(s)
    sessionPay = 0
    for sI in np.arange(taskInfo.numSessions):
        sessionPay = sessionPay + np.sum(taskInfo.sessionInfo[sI].payOut)
    print('Points Earned: ' + str(sessionPay))
    np.savetxt(f'{expInfo.payDir}/sub_{expInfo.SubNo}_payment.txt', ["Points Earned: $%s" % sessionPay], fmt='%s')
