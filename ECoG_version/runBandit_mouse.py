from psychopy import visual, gui, data, core, event, logging, info
from psychopy.constants import *
import numpy as np  # whole numpy lib is available, prepend 'np.'
import os
from config import *

def runBandit_mouse(expInfo, dispInfo, taskInfo, taskObj, keyInfo):
    # Assign the instruction condition (between subject)
    taskInfo.subID = expInfo.SubNo
    # Send task start trigger
    if expInfo.Modality == 'ephys':
        sendTrigger(taskInfo, 'taskStart_ID')
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
                    taskObj.screen.close()
                    core.quit()
        # Intitialize session
        taskObj.ITI.start(taskInfo.trialInfo.disDaqTime)
        taskObj.screen.flip()
        if expInfo.Modality == 'ephys':
            sendTrigger(taskInfo, 'sessStart_ID')
        taskObj.expFix.setAutoDraw(False)
        sessionInfo = taskInfo.sessionInfo[sI]
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
            # Set up trial structure
            taskObj.ITI.start(sessionInfo.itiDur[tI])
            # Show start fixation
            taskObj.trialFix.setAutoDraw(True)
            taskObj.screen.flip()
            # Record onset for start fixation
            sessionInfo.sessionOnsets.tPreFix[tI] = sessionClock.getTime()
            if expInfo.Modality == 'ephys':
                sendTrigger(taskInfo, 'preFix_ID')
            # Initialize the trial and show magnitudes
            outCounter = initTrial(tI, outCounter, expInfo, dispInfo, taskInfo, taskObj, sessionInfo, sessionClock)
            # Run the trial
            outCounter = runTrial(tI, sI, outCounter, expInfo, taskObj, taskInfo, dispInfo, sessionInfo, sessionClock)
            # Compute reversal (for next trial)
            # reverseStatus, revCounter = computeReversal(tI, revCounter, taskInfo, sessionInfo, reverseStatus)
            taskObj.ITI.complete()
            # Print trial timestamp
            print('Trial time ' + str(tI) + ': ' + str(sessionClock.getTime() - trialStart))
            if expInfo.Modality == 'ephys':
                sendTrigger(taskInfo, 'trialEnd_ID')

        # Show end ITI and save data
        taskObj.ITI.start(5)# Close screen
        taskObj.expFix.setAutoDraw(True)
        taskObj.screen.flip()
        # Print session time
        print('Session Time: ' + str(sessionClock.getTime() / 60))
        if expInfo.Modality == 'ephys':
            sendTrigger(taskInfo, 'sessEnd_ID')
        # Saving the data
        saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj)
        taskObj.expFix.setAutoDraw(False)
        taskObj.ITI.complete()
    # Send task end trigger
    if expInfo.Modality == 'ephys':
        sendTrigger(taskInfo, 'taskEnd_ID')
    # Save final data set
    saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj)
    return


def saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj):
    # Save ancilliary data
    ancOutDir = f'{expInfo.outDir}/ancillary'
    if not os.path.exists(ancOutDir):
        os.mkdir(ancOutDir)
    save_obj(expInfo, f'{ancOutDir}/sub{expInfo.SubNo}_sess{sI+1}_expInfo')
    save_obj(dispInfo, f'{ancOutDir}/sub{expInfo.SubNo}_sess{sI+1}_dispInfo')
    # Save data
    # Record last trial of session
    taskInfo.__dict__.update({'lastTrial_idx': tI,
                              'lastSess_idx': sI})
    # Record last trial of current session
    taskInfo.sessionInfo[sI].__dict__.update({'lastTrialSess_idx': tI})
    # Write out                          
    save_obj(taskInfo, f'{expInfo.outDir}/sub{expInfo.SubNo}_sess{sI+1}_data')
    # If last session already saved, save again as full dataset
    if os.path.exists(f'{expInfo.outDir}/sub{expInfo.SubNo}_sess{taskInfo.numSessions}_data'):
        save_obj(taskInfo, f'{expInfo.outDir}/sub{expInfo.SubNo}_allSess_data')
    return




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

def runTrial(tI, sI, outCounter, expInfo, taskObj, taskInfo, dispInfo, sessionInfo, sessionClock):
    # Initialize containers to record mass dynamics
    object_position = []
    object_velocity = []
    hand_position = []
    hand_velocity = []
    movement_init = False

    # Initialize iteration over frames
    response = event.clearEvents() # Allow keyboard responses
    # Reset mouse cursor position
    taskObj.mouse.setPos(dispInfo.imagePosC)
    # Initialize response recordings
    sessionInfo.sessionOnsets.tResp_start[tI] = respOnset = np.nan
    sessionInfo.sessionOnsets.tResp_end[tI] = respOffset = np.nan
    sessionInfo.sessionResponses.respKey[tI] = np.nan
    waitTime = taskInfo.trialInfo.maxRT
    sessionInfo.sessionResponses.rt_start[tI] = np.nan
    sessionInfo.sessionResponses.rt_end[tI] = np.nan
    sessionInfo.isHit_history[tI] = np.nan

    # Init
    q1 = 0 # Initialize position of object
    q2 = 0 # Initialize velocity of object
    # Initialize criteria for hits vs misses
    durFrames = []
    isHit = False

    # Flip screen and wait for response
    taskObj.ITI.complete()
    taskObj.screen.flip()
    sessionInfo.sessionOnsets.tTarget[tI] = sessionClock.getTime()
    if expInfo.Modality == 'ephys':
        sendTrigger(taskInfo, 'target_ID')
    # Check that starting position is centered!
    startPos, _ = np.round(taskObj.mouse.getPos(),2)
    if np.abs(startPos) > taskObj.centerThresh:
        taskObj.ITI.start(taskInfo.trialInfo.maxRT + sessionInfo.isiDur[tI] + sessionInfo.fbDur[tI])
        taskObj.nonCentered.setAutoDraw(True)
        taskObj.screen.flip()
        taskObj.nonCentered.setAutoDraw(False)
        taskObj.ITI.complete()
    else:
        # Iterate over frames
        while (sessionClock.getTime() - sessionInfo.sessionOnsets.tTarget[tI]) <= taskInfo.trialInfo.maxRT:
            mX, _ = np.round(taskObj.mouse.getPos(),2)
            if mX != startPos and not movement_init:
                movement_init = True
                sessionInfo.sessionOnsets.tResp_start[tI] = respOnset = sessionClock.getTime()
                # Send trigger
                if expInfo.Modality == 'ephys':
                    sendTrigger(taskInfo, 'resp_start_ID')
            if hand_position:
                dX, _ = np.round(taskObj.mouse.getRel(),2)
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
                break
            # Allow exiting (and saving) with Keyboard
            response = event.getKeys(keyList=['escape'])
            if 'escape' in response:
                # Save trial
                print('Trying to save!')
                saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj)
                core.wait(1)
                taskObj.screen.close()
                core.quit()
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
    # Store the trajectories for this trial
    sessionInfo.hand_position_trials[tI] = np.array(hand_position)
    sessionInfo.hand_velocity_trials[tI] = np.array(hand_velocity)
    sessionInfo.object_position_trials[tI] = np.array(object_position)
    sessionInfo.object_velocity_trials[tI] = np.array(object_velocity)
    # Trune off end-of-trial fixation
    taskObj.trialFix.setAutoDraw(False)
    # Save data
    saveData(sI, tI, expInfo, dispInfo, taskInfo, taskObj)


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
