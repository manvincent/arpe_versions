from psychopy import visual, gui, data, core, event, logging, info, parallel
from psychopy.constants import *
import numpy as np  # whole numpy lib is available, prepend 'np.'
import os
import pyxid2
import csv
from config import *

def runBandit_joy(expInfo, dispInfo, taskInfo, taskObj, keyInfo):
    # Assign the instruction condition (between subject)
    taskInfo.subID = expInfo.SubNo
    taskClock = core.Clock()
    # Send task start trigger
    if expInfo.Modality == 'ephys':
        sendTrigger(taskInfo, 'taskStart_ID')
        tTTL = taskClock.getTime()
        saveTTLsToTxt(expInfo, taskInfo, tTTL, 'trialStart_ID')
    # Loop through sessions
    for sI in np.arange(taskInfo.numSessions):
        # Wait for start confirmation
        while True:
            # Draw experimenter wait screen
            taskObj.waitExp.draw()
            taskObj.screen.flip()
            # Wait for starting confirmation response
            response = event.waitKeys(keyList=[keyInfo.instructDone, 'escape'])
            if keyInfo.instructDone in response:
                # Initialize session clock
                sessionClock = core.Clock()
                break
            elif 'escape' in response:
                print("Aborting program...")
                core.wait(2)
                taskObj.joy._device.close()
                taskObj.screen.close()
                core.quit()
        if (expInfo.Modality == 'fmri'):
            # Wait for scanner pulse if fMRI
            while True:
                # Draw pulse-wait screen
                taskObj.scanPulse.draw()
                taskObj.screen.flip()
                # Wait for starting confirmation response
                response = event.waitKeys(keyList=[keyInfo.pulseCode, 'escape'])
                if keyInfo.pulseCode in response:
                    print('Received scanner trigger..')
                    # Initialize session clock
                    sessionClock = core.Clock()
                    taskObj.expFix.setAutoDraw(True)
                    break
                elif 'escape' in response:
                    print("Aborting program...")
                    core.wait(2)
                    taskObj.joy._device.close()
                    taskObj.screen.close()
                    core.quit()

        # Evalutate the hit accuracy on the last session
        if sI > 0: 
            # Get last session info
            lastSessionInfo = taskInfo.sessionInfo[sI - 1]
            # Get average hit accuracy on last session
            meanAcc = lastSessionInfo.isHit_history.mean() 
            # Evaluate if it exceedes defined threshold
            if meanAcc > taskInfo.hitCriterion:
                taskObj.ITI.start(5)
                taskObj.fasterResp.setAutoDraw(True)
                taskObj.screen.flip()
                taskObj.fasterResp.setAutoDraw(False)
                # Record this in the session info
                taskInfo.sessionInfo[sI].promptedFaster = True        
                taskObj.ITI.complete()             
            
        # Intitialize session
        taskObj.ITI.start(taskInfo.trialInfo.disDaqTime)
        taskObj.screen.flip()
        if expInfo.Modality == 'ephys':
            sendTrigger(taskInfo, 'sessStart_ID')
            tTTL = taskClock.getTime()
            saveTTLsToTxt(expInfo, taskInfo, tTTL, 'sessStart_ID')
        sessionInfo = taskInfo.sessionInfo[sI]
        taskObj.expFix.setAutoDraw(False)
        taskObj.ITI.complete()  # Close static period
        # Record disdaq time
        sessionInfo.__dict__.update({'tDisDaq':sessionClock.getTime()})
        print('Disdaq time: ' + str(sessionClock.getTime()))
        # Initialize the reverseStatus to False
        # reverseStatus = False
        # revCounter = 0
        outCounter = 0

        # Proceed to trials
        for tI in range(taskInfo.trialInfo.trialsPerSess):
            # Print trial number
            print('Trial No: ' + str(tI))
            # show fixation while loading
            trialStart = sessionClock.getTime()
            if expInfo.Modality == 'ephys':
                sendTrigger(taskInfo, 'trialStart_ID')
                tTTL = taskClock.getTime()
                saveTTLsToTxt(expInfo,taskInfo,tTTL,'trialStart_ID')
                
            # Set up trial structure
            taskObj.ITI.start(sessionInfo.itiDur[tI])
            # Show start fixation
            taskObj.trialFix.setAutoDraw(True)
            taskObj.screen.flip()
            # Record onset for start fixation
            sessionInfo.sessionOnsets.tPreFix[tI] = sessionClock.getTime()
            if expInfo.Modality == 'ephys':
                sendTrigger(taskInfo, 'preFix_ID')
                #tTTL = sessionInfo.sessionOnsets.tPreFix[tI]
                tTTL = taskClock.getTime()
                saveTTLsToTxt(expInfo,taskInfo,tTTL,'preFix_ID')
            # Initialize the trial and show magnitudes
            outCounter = initTrial(tI, outCounter, expInfo, dispInfo, taskInfo, taskObj, sessionInfo, sessionClock)
            # Run the trial
            outCounter = runTrial(tI, sI, outCounter, expInfo, taskObj, taskInfo, dispInfo, sessionInfo, sessionClock, taskClock)
            # Compute reversal (for next trial)
            # reverseStatus, revCounter = computeReversal(tI, revCounter, taskInfo, sessionInfo, reverseStatus)
            taskObj.ITI.complete()
            # Print trial timestamp
            print('Trial time ' + str(tI) + ': ' + str(sessionClock.getTime() - trialStart))
            if expInfo.Modality == 'ephys':
                sendTrigger(taskInfo, 'trialEnd_ID')
                #tTTL = sessionClock.getTime()
                tTTL = taskClock.getTime()
                saveTTLsToTxt(expInfo,taskInfo,tTTL,'trialEnd_ID')

        # Show end ITI and save data
        taskObj.ITI.start(5)# Close screen
        taskObj.expFix.setAutoDraw(True)
        taskObj.screen.flip()
        # Print session time
        print('Session Time: ' + str(sessionClock.getTime() / 60))
        if expInfo.Modality == 'ephys':
            sendTrigger(taskInfo, 'sessEnd_ID')
            #tTTL = sessionClock.getTime()
            tTTL = taskClock.getTime()
            saveTTLsToTxt(expInfo,taskInfo,tTTL,'sessEnd_ID')
        # Saving the data
        saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj) # here save data for the session.
        taskObj.expFix.setAutoDraw(False)
        taskObj.ITI.complete()
    # Send task end trigger
    if expInfo.Modality == 'ephys':
        sendTrigger(taskInfo, 'taskEnd_ID')
        tTTL = taskClock.getTime()
        saveTTLsToTxt(expInfo,taskInfo,tTTL,'taskEnd_ID')
    # Save final data set
    saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj)
    return


def saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj):
    dillOutDir = f'{expInfo.outDir}/sub{expInfo.SubNo}/sess{sI+1}/main'
    if not os.path.exists(dillOutDir):
        os.makedirs(dillOutDir)
    # Save ancilliary data
    ancOutDir = f'{expInfo.outDir}/sub{expInfo.SubNo}/sess{sI+1}/ancillary'
    if not os.path.exists(ancOutDir):
        os.makedirs(ancOutDir)
    save_obj(expInfo, f'{ancOutDir}/sub{expInfo.SubNo}_sess{sI+1}_expInfo')
    save_obj(dispInfo, f'{ancOutDir}/sub{expInfo.SubNo}_sess{sI+1}_dispInfo')
    # Save data
    # Record last trial and last session
    taskInfo.__dict__.update({'lastTrial_idx': tI,
                              'lastSess_idx': sI})
    # Record last trial of current session
    taskInfo.sessionInfo[sI].__dict__.update({'lastTrialSess_idx': tI})
    # Write out
    del taskInfo.port
    save_obj(taskInfo, f'{dillOutDir}/sub{expInfo.SubNo}_sess{sI+1}_data')
    if expInfo.interface == 'TTL':
        port = parallel.ParallelPort(address=taskInfo.portID)
    elif expInfo.interface == 'cpod':
        devices = pyxid2.get_xid_devices()
        port = devices[0]
        port.set_pulse_duration(50)
    taskInfo.__dict__.update({'port': port})
    # If last session already saved, save again as full dataset
    if os.path.exists(f'{dillOutDir}/sub{expInfo.SubNo}_sess{taskInfo.numSessions}_data'):
        save_obj(taskInfo, f'{dillOutDir}/sub{expInfo.SubNo}_allSess_data')
    return


def saveData_csvtxt(sI, tI, expInfo, sessionInfo):

    txtOutDir = f'{expInfo.outDir}/sub{expInfo.SubNo}/csvtxt'
    if not os.path.exists(txtOutDir):
        os.makedirs(txtOutDir)

    stim1_High = sessionInfo.stimAttrib.isHigh[0,tI]
    stim2_High = sessionInfo.stimAttrib.isHigh[1,tI]
    stim1_left = sessionInfo.stim1_left[tI]
    stim1_pWin = sessionInfo.stimAttrib.pWin[0,tI]
    stim2_pWin = sessionInfo.stimAttrib.pWin[1,tI]
    isEasy = sessionInfo.isEasy[tI]
    # Response attributes
    responseKey = sessionInfo.sessionResponses.respKey[tI]
    selected_stim1 = sessionInfo.stimAttrib.isSelected[0,tI]
    selected_stim2 = sessionInfo.stimAttrib.isSelected[1,tI]
    RT_start = sessionInfo.sessionResponses.rt_start[tI]
    RT_end = sessionInfo.sessionResponses.rt_end[tI]
    isHit = sessionInfo.isHit_history[tI]
    # Outcome attributes
    highChosen = sessionInfo.highChosen
    stim1_isWin = sessionInfo.stimAttrib.isWin[0,tI]
    stim2_isWin = sessionInfo.stimAttrib.isWin[1,tI]
    isWin = [1 if (sessionInfo.stimAttrib.isWin[0,tI] == 1) or (sessionInfo.stimAttrib.isWin[1,tI] == 1) else 
                 (0 if (sessionInfo.stimAttrib.isWin[0,tI] == 0) or (sessionInfo.stimAttrib.isWin[1,tI] == 0) else 
                 np.nan)]

    isHit = sessionInfo.isHit_history[tI]
    selectedStim = sessionInfo.selectedStim[tI]
    highChosen = sessionInfo.highChosen[tI]
    payOut = sessionInfo.payOut[tI]

    fname1 = f'{txtOutDir}/sub{expInfo.SubNo}_trialdata.csv'
    trialdata_header = ['sessionID','trialID','isHit','isWin','payOut','highChosen','isEasy','selectedStim','responseKey','RT_start','RT_end','stim1_High',
                     'stim2_High','stim1_left','stim1_pWin','stim2_pWin','stim1_isWin','stim2_isWin','selected_stim1','selected_stim2']
    f1 = open(fname1,'a',newline='')

    with f1:
        writer = csv.DictWriter(f1,fieldnames = trialdata_header)
        if ((sI==0) & (tI==0)):
            writer.writeheader()
        writer.writerow({'sessionID':sI+1,'trialID':tI+1,'isHit':isHit,'isWin':isWin[0],'payOut':payOut,'highChosen':highChosen,'isEasy':isEasy,'selectedStim':selectedStim,
                         'responseKey':responseKey,'RT_start':RT_start,'RT_end':RT_end,'stim1_High':stim1_High,'stim2_High':stim2_High,'stim1_left':stim1_left,
                         'stim1_pWin':stim1_pWin,'stim2_pWin':stim2_pWin,'stim1_isWin':stim1_isWin,'stim2_isWin':stim2_isWin,'selected_stim1':selected_stim1,
                         'selected_stim2':selected_stim2})
    f1.close()

    fname_handpos = f'{txtOutDir}/sub{expInfo.SubNo}_hand_position'
    f_handpos = open(fname_handpos,'a')
    np.savetxt(f_handpos,sessionInfo.hand_position_trials[tI], newline=',', delimiter=',', encoding=None,fmt='%1.4f')
    f_handpos.write('\n')
    f_handpos.close()

    fname_handvel = f'{txtOutDir}/sub{expInfo.SubNo}_hand_velocity'
    f_handvel = open(fname_handvel,'a')
    np.savetxt(f_handvel,sessionInfo.hand_velocity_trials[tI], newline=',',delimiter=',',encoding=None,fmt='%1.4f')
    f_handvel.write('\n')
    f_handvel.close()

    fname_objpos = f'{txtOutDir}/sub{expInfo.SubNo}_object_position'
    f_objpos = open(fname_objpos,'a')
    np.savetxt(f_objpos,sessionInfo.object_position_trials[tI],newline=',',delimiter=',',encoding=None,fmt='%1.4f')
    f_objpos.write('\n')
    f_objpos.close()

    fname_objvel = f'{txtOutDir}/sub{expInfo.SubNo}_object_velocity'
    f_objvel = open(fname_objvel,'a')
    np.savetxt(f_objvel,sessionInfo.object_velocity_trials[tI],newline=',',delimiter=',',encoding=None,fmt='%1.4f')
    f_objvel.write('\n')
    f_objvel.close()


def saveTTLsToTxt(expInfo,taskInfo,tTTL,trigger_label):
    txtOutDir = f'{expInfo.outDir}/sub{expInfo.SubNo}/csvtxt'
    if not os.path.exists(txtOutDir):
        os.makedirs(txtOutDir)
    triggerID = getattr(taskInfo.triggerInfo_dec, trigger_label)
    fname_ttl = f'{txtOutDir}/sub{expInfo.SubNo}_TTLs'
    f_ttl = open(fname_ttl,'a')
    TTLstr = str(tTTL) + ',' + str(triggerID) + '\n'
    f_ttl.write(TTLstr)
    f_ttl.close()


def initTrial(tI, outCounter, expInfo, dispInfo, taskInfo, taskObj, sessionInfo, sessionClock):
    # Update outcome bin idx counter
    if outCounter == len(sessionInfo.pWinHighVec):
        outCounter = 0
        np.random.shuffle(sessionInfo.pWinHighVec)
        np.random.shuffle(sessionInfo.pWinLowVec)


    # Initialize trial display drawings
    # End start-trial fixation
    taskObj.trialFix.setAutoDraw(False)

    # Define stimulus and responses images for this trial
    if (sessionInfo.stim1_left[tI]):
        taskObj.leftStim.image = taskObj.stim1.path
        taskObj.rightStim.image = taskObj.stim2.path
    else:
        taskObj.leftStim.image = taskObj.stim2.path
        taskObj.rightStim.image = taskObj.stim1.path

    # Alternate between easy and hard trials (rescale size)
    if sessionInfo.isEasy[tI]:
        taskObj.leftStim.rescaledSize = rescaleStim(taskObj.leftStim, dispInfo.imageSize_easy, dispInfo)
        taskObj.rightStim.rescaledSize = rescaleStim(taskObj.rightStim, dispInfo.imageSize_easy, dispInfo)
    else:
        taskObj.leftStim.rescaledSize = rescaleStim(taskObj.leftStim, dispInfo.imageSize_hard, dispInfo)
        taskObj.rightStim.rescaledSize = rescaleStim(taskObj.rightStim, dispInfo.imageSize_hard, dispInfo)
    taskObj.leftStim.setSize(taskObj.leftStim.rescaledSize)
    taskObj.rightStim.setSize(taskObj.rightStim.rescaledSize)

    # Compute win probabilities for each stim
    if (sessionInfo.stim1_high):
        # Toggle which stim is high/low
        taskObj.stim1.pWin = sessionInfo.stimAttrib.pWin[0, tI] = taskInfo.pWinHigh
        sessionInfo.stimAttrib.isHigh[0, tI] = True
        taskObj.stim2.pWin = sessionInfo.stimAttrib.pWin[1, tI] = taskInfo.pWinLow
        sessionInfo.stimAttrib.isHigh[1, tI] = False
    else:
        # Toggle which stim is high/low
        taskObj.stim1.pWin = sessionInfo.stimAttrib.pWin[0, tI] = taskInfo.pWinLow
        sessionInfo.stimAttrib.isHigh[0, tI] = False
        taskObj.stim2.pWin = sessionInfo.stimAttrib.pWin[1, tI] = taskInfo.pWinHigh
        sessionInfo.stimAttrib.isHigh[1, tI] = True

    # Reset starting positions
    taskObj.handMass.setPos(dispInfo.imagePosC)
    taskObj.objectMass.setPos(dispInfo.objectPosC)

    return outCounter

def springDynamics(taskInfo, dispInfo, q1, q2, mX):
    M = taskInfo.springInfo.M_o
    K = taskInfo.springInfo.K_o
    Ts = 1/dispInfo.fps # timestep (temporal scaling)
    # Define dynamics matrices
    a11 = 1
    a12 = Ts
    a21 = -(Ts*K)/M
    a22 = 1
    b1 = 0
    b2 = Ts/M
    # Update position and velocity of object
    q1 = a11 * q1 + a12 * q2 + b1 * mX # update position of the object
    q2 = a21 * q1 + a22 * q2 + b2 * mX # update velocity of the object
    return q1, q2

def runTrial(tI, sI, outCounter, expInfo, taskObj, taskInfo, dispInfo, sessionInfo, sessionClock, taskClock):
    # Initialize containers to record mass dynamics
    object_position = []
    object_velocity = []
    hand_position = []
    hand_velocity = []
    movement_init = False

    # Initialize iteration over frames
    response = event.clearEvents() # Allow keyboard responses
    # Reset cursor position
    mX = 0
    # Initialize response recordings
    sessionInfo.sessionOnsets.tResp_start[tI] = respOnset = np.nan
    sessionInfo.sessionOnsets.tResp_end[tI] = respOffset = np.nan
    sessionInfo.sessionResponses.respKey[tI] = np.nan
    waitTime = taskInfo.trialInfo.maxRT
    sessionInfo.sessionResponses.rt_start[tI] = np.nan
    sessionInfo.sessionResponses.rt_end[tI] = np.nan
    sessionInfo.isHit_history[tI] = np.nan
    sessionInfo.offSet[tI] = np.nan

    # Init
    q1 = 0 # Initialize position of object
    q2 = 0 # Initialize velocity of object
    # Measure offset of joystick
    sessionInfo.offSet[tI] = offSet = np.round(taskObj.joy.getX(),2)

    # Initialize criteria for hits vs misses
    durFrames = []
    isHit = False

    # Flip screen and wait for response
    taskObj.ITI.complete()
    taskObj.screen.flip()
    sessionInfo.sessionOnsets.tTarget[tI] = sessionClock.getTime()
    if expInfo.Modality == 'ephys':
        sendTrigger(taskInfo, 'target_ID')
        tTTL = sessionInfo.sessionOnsets.tTarget[tI]
        saveTTLsToTxt(expInfo,taskInfo,tTTL,'target_ID')
    # Check that starting position is centered!
    startPos = np.round(taskObj.joy.getX(),2) - offSet
    q1 = startPos
    if np.abs(offSet) > taskObj.centerThresh:
        taskObj.ITI.start(taskInfo.trialInfo.maxRT + sessionInfo.isiDur[tI] + sessionInfo.fbDur[tI])
        taskObj.nonCentered.setAutoDraw(True)
        taskObj.screen.flip()
        taskObj.nonCentered.setAutoDraw(False)
        taskObj.ITI.complete()
    else:
        # Iterate over frames
        while (sessionClock.getTime() - sessionInfo.sessionOnsets.tTarget[tI]) <= taskInfo.trialInfo.maxRT:
            if expInfo.invertJoy:
                mX = np.round(taskObj.joy.getX() * -1,2)
            else:
                mX = np.round(taskObj.joy.getX(),2)
            if mX != startPos and not movement_init:
                movement_init = True
                sessionInfo.sessionOnsets.tResp_start[tI] = respOnset = sessionClock.getTime()
                # Send trigger
                if expInfo.Modality == 'ephys':
                    sendTrigger(taskInfo, 'resp_start_ID')
                    #tTTL = sessionInfo.sessionOnsets.tResp_start[tI]
                    tTTL = taskClock.getTime()
                    saveTTLsToTxt(expInfo,taskInfo,tTTL,'resp_start_ID')
            if hand_position:
                dX = mX - hand_position[-1]
            else:
                dX = np.nan
            taskObj.handMass.setPos([mX, dispInfo.imagePosC[1]])
            # Compute position/velocity of object
            q1, q2 = springDynamics(taskInfo, dispInfo, q1, q2, mX)
            objectPos = [q1, dispInfo.objectPosC[1]]
            taskObj.objectMass.setPos(objectPos)
            # Draw stims
            taskObj.leftStim.draw()
            taskObj.rightStim.draw()
            # Draw masses
            taskObj.handMass.draw()
            taskObj.objectMass.draw()
            taskObj.screen.flip()
            # Evaluate if object is inside target at criterion
            if taskObj.leftStim.contains(objectPos):
                durFrames.append(0)
            elif taskObj.rightStim.contains(objectPos):
                durFrames.append(1)
            else:
                durFrames = []
            # Contain mass dynamics on this frame
            object_position.append(q1)
            object_velocity.append(q2)
            hand_position.append(mX)
            hand_velocity.append(dX)
            # Evaluate success -- reaches min frames inside a target
            if len(durFrames) > taskInfo.trialInfo.targetDur and durFrames.count(durFrames[0]) == len(durFrames):
                isHit = True
                sessionInfo.sessionOnsets.tResp_end[tI] = respOffset = sessionClock.getTime()
                if expInfo.Modality == 'ephys':
                    sendTrigger(taskInfo, 'resp_end_ID')
                    #tTTL = sessionInfo.sessionOnsets.tResp_end[tI]
                    tTTL = taskClock.getTime()
                    saveTTLsToTxt(expInfo,taskInfo,tTTL,'resp_end_ID')
                break
            # Allow exiting (and saving) with Keyboard
            response = event.getKeys(keyList=['escape'])
            if 'escape' in response:
                # Save trial
                print('Trying to save!')
                saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj)
                core.wait(1)
                taskObj.joy._device.close()
                taskObj.screen.close()
                core.quit()

        if (expInfo.Modality == 'ephys') and (expInfo.isOutcomeDelay):
            # Start of outcome delay
            taskObj.ITI.start(sessionInfo.outDelayDur[tI])
            #taskObj.trialFix.setAutoDraw(True)
            taskObj.leftStim.setAutoDraw(True)
            taskObj.rightStim.setAutoDraw(True)
            taskObj.screen.flip()
            sendTrigger(taskInfo, 'outDelayStart_ID')
            sessionInfo.sessionOnsets.tOutDelay[tI] = sessionClock.getTime()
            #tTTL = sessionInfo.sessionOnsets.tOutDelay[tI]
            tTTL = taskClock.getTime()
            saveTTLsToTxt(expInfo,taskInfo,tTTL,'outDelayStart_ID')
            taskObj.leftStim.setAutoDraw(False)
            taskObj.rightStim.setAutoDraw(False)
            #taskObj.trialFix.setAutoDraw(False)
            taskObj.ITI.complete() # End of outcome delay

        # Encode movement initiation RT
        sessionInfo.sessionResponses.rt_start[tI] = respOnset - sessionInfo.sessionOnsets.tTarget[tI]
        # Encode whether and which choice was made
        eval_position = object_position[-1] #hand_position[int(-1*len(hand_position)//4):] # Look at last quarter of frames
        if (not eval_position < startPos + taskObj.centerThresh/2) or (not eval_position > startPos - taskObj.centerThresh/2):
            # Show action outcome feedback
            taskObj.ITI.start(sessionInfo.isiDur[tI]) #Start of ISI
            if isHit:
                sessionInfo.sessionResponses.rt_end[tI] = waitTime = respOffset - sessionInfo.sessionOnsets.tTarget[tI]
            # Record choice (independent of action success)
            respKey = 0 if np.mean(eval_position) < 0 else 1
            sessionInfo.sessionResponses.respKey[tI] = respKey

            # Display action feedback (hit vs miss)
            if respKey == 0: # If they chose left option
                # Define what the left target image should be based on hit or miss
                if (sessionInfo.stim1_left[tI]):
                    taskObj.leftTarget.image = taskObj.stim1.hit_path if isHit else taskObj.stim1.miss_path
                else:
                    taskObj.leftTarget.image = taskObj.stim2.hit_path if isHit else taskObj.stim2.miss_path
                # Rescale the left target image
                if sessionInfo.isEasy[tI]:
                    taskObj.leftTarget.rescaledSize = rescaleStim(taskObj.leftTarget, dispInfo.imageSize_easy, dispInfo)
                else:
                    taskObj.leftTarget.rescaledSize = rescaleStim(taskObj.leftTarget, dispInfo.imageSize_hard, dispInfo)
                taskObj.leftTarget.setSize(taskObj.leftTarget.rescaledSize)
                # Dim out the unchosen stim
                taskObj.rightStim.opacity = 0.5
                # Show the left target and right stim images
                taskObj.leftTarget.setAutoDraw(True)
                taskObj.rightStim.setAutoDraw(True)
            elif respKey == 1:
                # Define what the right target image should be based on hit or miss
                if (sessionInfo.stim1_left[tI]):
                    taskObj.rightTarget.image = taskObj.stim2.hit_path if isHit else taskObj.stim2.miss_path
                else:
                    taskObj.rightTarget.image = taskObj.stim1.hit_path if isHit else taskObj.stim1.miss_path
                # Rescale the right target image
                if sessionInfo.isEasy[tI]:
                    taskObj.rightTarget.rescaledSize = rescaleStim(taskObj.rightTarget, dispInfo.imageSize_easy, dispInfo)
                else:
                    taskObj.rightTarget.rescaledSize = rescaleStim(taskObj.rightTarget, dispInfo.imageSize_hard, dispInfo)
                taskObj.rightTarget.setSize(taskObj.rightTarget.rescaledSize)
                # Dim out the unchosen stim
                taskObj.leftStim.opacity = 0.5
                # Show the right target and left stim images
                taskObj.rightTarget.setAutoDraw(True)
                taskObj.leftStim.setAutoDraw(True)

            taskObj.screen.flip()
            sessionInfo.sessionOnsets.tAOut[tI] = sessionClock.getTime()
            if expInfo.Modality == 'ephys':
                sendTrigger(taskInfo, 'Aout_ID')
                #tTTL=sessionInfo.sessionOnsets.tAOut[tI] 
                tTTL = taskClock.getTime()
                saveTTLsToTxt(expInfo,taskInfo,tTTL,'Aout_ID')
            # Reset the targets for the next trial
            taskObj.leftTarget.setAutoDraw(False)
            taskObj.rightTarget.setAutoDraw(False)
            # Reset the stims for the next trial
            taskObj.leftStim.opacity = taskObj.rightStim.opacity = 1
            taskObj.leftStim.setAutoDraw(False)
            taskObj.rightStim.setAutoDraw(False)
            taskObj.ITI.complete() # End of ISI

            # Start of feedback
            taskObj.ITI.start(sessionInfo.fbDur[tI])
            # Compute outcome
            outCounter = computeOutcome(tI, outCounter, taskInfo, taskObj, sessionInfo, respKey, isHit)

            # Show reward outcome feedback
            taskObj.screen.flip()
            sessionInfo.sessionOnsets.tROut[tI] = sessionClock.getTime() if isHit else np.nan
            if expInfo.Modality == 'ephys':
                sendTrigger(taskInfo, 'Rout_ID')
                #tTTL = sessionInfo.sessionOnsets.tROut[tI]
                tTTL = taskClock.getTime()
                saveTTLsToTxt(expInfo,taskInfo,tTTL,'Rout_ID')
            taskObj.ITI.complete() # End of feedback

        else: # If no response was made on this trial
            taskObj.ITI.start(sessionInfo.isiDur[tI] + sessionInfo.fbDur[tI])
            respKey = np.nan
            taskObj.noRespErr.setAutoDraw(True)
            taskObj.screen.flip()
            taskObj.noRespErr.setAutoDraw(False)
            # Set onsets to nan
            sessionInfo.sessionOnsets.tAOut[tI] = np.nan
            sessionInfo.sessionOnsets.tROut[tI] = np.nan
            # Set stim attributes to nan
            sessionInfo.stimAttrib.isSelected[:, tI] = np.nan
            sessionInfo.stimAttrib.isHit[:, tI] = np.nan
            sessionInfo.stimAttrib.isWin[:, tI] = np.nan
            taskObj.ITI.complete()

    #  Present trial-end fixation
    taskObj.ITI.start(
                    (taskInfo.trialInfo.maxJitter - sessionInfo.itiDur[tI]) +
                    (taskInfo.trialInfo.maxRT - waitTime) +
                    (taskInfo.trialInfo.isiMaxTime - sessionInfo.isiDur[tI]) +
                    (taskInfo.trialInfo.fbMaxTime - sessionInfo.fbDur[tI])
                    )
    taskObj.rewardOut.setAutoDraw(False)
    taskObj.winOut.setAutoDraw(False)
    taskObj.noWinOut.setAutoDraw(False)
    taskObj.trialFix.setAutoDraw(True)
    taskObj.screen.flip()
    sessionInfo.sessionOnsets.tPostFix[tI] = sessionClock.getTime()
    if expInfo.Modality == 'ephys':
        sendTrigger(taskInfo, 'postFix_ID')
        #tTTL = sessionInfo.sessionOnsets.tPostFix[tI] 
        tTTL = taskClock.getTime()
        saveTTLsToTxt(expInfo,taskInfo,tTTL,'postFix_ID')
    # Store the trajectories for this trial
    sessionInfo.hand_position_trials[tI] = np.array(hand_position)
    sessionInfo.hand_velocity_trials[tI] = np.array(hand_velocity)
    sessionInfo.object_position_trials[tI] = np.array(object_position)
    sessionInfo.object_velocity_trials[tI] = np.array(object_velocity)
    # turn off end-of-trial fixation
    taskObj.trialFix.setAutoDraw(False)
    # Save data
    saveData_csvtxt(sI, tI, expInfo,sessionInfo)
    #saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj)
    return outCounter


def computeOutcome(tI, outCounter, taskInfo, taskObj, sessionInfo, respKey, isHit):
    # Determine which stim was chosen
    if (respKey == 0):
        if (sessionInfo.stim1_left[tI]):
            resp_stimIdx = 0
            sessionInfo.selectedStim[tI] = 1
            pWin = taskObj.stim1.pWin
        else:
            resp_stimIdx = 1
            sessionInfo.selectedStim[tI] = 2
            pWin = taskObj.stim2.pWin
    elif (respKey == 1):
        if (sessionInfo.stim1_left[tI]):
            resp_stimIdx = 1
            sessionInfo.selectedStim[tI] = 2
            pWin = taskObj.stim2.pWin
        else:
            resp_stimIdx = 0
            sessionInfo.selectedStim[tI] = 1
            pWin = taskObj.stim1.pWin

    # Determine whether the outcome is a win or loss
    isWin = sessionInfo.pWinHighVec[outCounter] if pWin == taskInfo.pWinHigh else sessionInfo.pWinLowVec[outCounter]

    # Present the outcome screen
    if isHit:
        if isWin:
            taskObj.rewardOut.setText(f'Caught a fish!')
            taskObj.winOut.setAutoDraw(True)
        else:
            taskObj.rewardOut.setText(f'Did NOT catch a fish.')
            taskObj.noWinOut.setAutoDraw(True)
    else:
        taskObj.rewardOut.setText(f'Failed to land in the patch.')
    taskObj.rewardOut.setAutoDraw(True)
    # Update outcome bin counter
    outCounter += 1
    # Record stim attributes
    sessionInfo.stimAttrib.isSelected[resp_stimIdx, tI] = 1
    sessionInfo.stimAttrib.isHit[resp_stimIdx, tI] = isHit
    sessionInfo.stimAttrib.isWin[resp_stimIdx, tI] = isWin
    sessionInfo.stimAttrib.isSelected[1-resp_stimIdx, tI] = 0
    sessionInfo.stimAttrib.isHit[1-resp_stimIdx, tI] = np.nan
    sessionInfo.stimAttrib.isWin[1-resp_stimIdx, tI] = np.nan
    # Store history of hit/miss
    sessionInfo.isHit_history[tI] = isHit
    # Record whether they chose the high value option
    sessionInfo.highChosen[tI] = True if (pWin == taskInfo.pWinHigh) else False
    # Record the observed payOut
    sessionInfo.payOut[tI] = 1 if isWin and isHit else 0
    return outCounter

def computeReversal(tI, revCounter, taskInfo, sessionInfo, reverseStatus):
    # No reversals in the first 4 trials of the task
    if (tI < 3):
        sessionInfo.reverseTrial[tI] = False
    # After the first 4 trials, reversals are possible
    if (tI >= 3):
        # Reversals are possible if 4 continuous correct responses
        if (np.all(sessionInfo.highChosen[tI-3:tI+1] == True)) and (np.all(np.diff(sessionInfo.selectedStim[tI-3:tI+1]) == 0)):
            reverseStatus = True
        # If 4 continuous incorrect responses, not sufficient learning. Reset reversalStatus
        if (np.all(sessionInfo.highChosen[tI-3:tI+1] == False)):
            reverseStatus = False
            revCounter = 0
        # If reversals are possible
        sessionInfo.reverseStatus[tI] = reverseStatus
        # Store the reversal status of the trial
        if (reverseStatus):
            # Determine whether reversals occurs on this trials
            reverse = sessionInfo.reverseVec[revCounter]
            # Add to counter of how many trials into reversal possible (index reverseVec)
            if revCounter < 3:
                revCounter += 1
            if (reverse):
                # Execute high stim reversal
                sessionInfo.stim1_high = not sessionInfo.stim1_high
                sessionInfo.reverseTrial[tI] = True
                print('Reversal occured!')
                # Reset the reverseStatus
                reverseStatus = False
                revCounter = 0
                np.random.shuffle(sessionInfo.reverseVec)
    return reverseStatus, revCounter
