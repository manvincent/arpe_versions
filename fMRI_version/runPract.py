from psychopy import visual, gui, data, core, event, logging, info
from psychopy.constants import *
import numpy as np
from copy import deepcopy as dcopy
from matplotlib import pyplot as plt
from initTask import *
from runBandit_mouse import springDynamics


def initPract(taskInfo):
    # task properties
    maxTrials = 40
    pWin = 0.5
    # Randomise stimulus order for practice
    stim1_left = np.random.binomial(1, 0.5, maxTrials).astype(bool)
    # Initialize which stim is p(high)
    stim1_high = bool(np.random.binomial(1, 0.5))
    # Store which stim is the selected stim
    selectedStim = np.zeros(maxTrials,dtype=int)
    # Encode practice pWins
    pWinVec = np.zeros(10, dtype = bool)
    pWinVec[:int(pWin * 10)] = True
    np.random.shuffle(pWinVec)
    # Create containers for the trajectories
    hand_position_trials = np.empty(maxTrials, dtype=object)
    hand_velocity_trials = np.empty(maxTrials, dtype=object)
    object_position_trials = np.empty(maxTrials, dtype=object)
    object_velocity_trials = np.empty(maxTrials, dtype=object)
    # Create container for responses
    practResponses = Responses(maxTrials)
    # Create container for history of hit/miss
    isHit_history = np.ones(maxTrials, dtype=float) * np.nan
    # Initialize stim attribute containers
    def stimParam(numTrials):
        # For the first axis, indices of 0 = stim1 and 1 = stim2
        pWin = np.ones((2,numTrials), dtype=float) * np.nan
        isHit = np.ones((2,numTrials), dtype=float) * np.nan
        isSelected = np.ones((2,numTrials), dtype=float) * np.nan
        isWin = np.ones((2,numTrials), dtype=float) * np.nan
        return dict(pWin=pWin,
                    isHit=isHit,
                    isSelected=isSelected,
                    isWin=isWin)
    stimAttrib = dict2class(stimParam(maxTrials))
    # Container for final spring tension
    final_K_o = float()
    # Container to store trial-by-trial tensions
    trial_K_o = np.ones(maxTrials, dtype=float) * np.nan
    # Wrap into dictionary
    practInfo = dict2class(dict(maxTrials=maxTrials,
                                pWin=pWin,
                                stim1_left=stim1_left,
                                stim1_high=stim1_high,
                                selectedStim=selectedStim,
                                pWinVec=pWinVec,
                                hand_position_trials=hand_position_trials,
                                hand_velocity_trials=hand_velocity_trials,
                                object_position_trials=object_position_trials,
                                object_velocity_trials=object_velocity_trials,
                                practResponses=practResponses,
                                isHit_history=isHit_history,
                                stimAttrib=stimAttrib,
                                final_K_o=final_K_o,
                                trial_K_o=trial_K_o))
    taskInfo.__dict__.update({'practInfo': practInfo})
    return


def runPract(expInfo, dispInfo, taskInfo, taskObj, keyInfo):
    # Show practice start screen
    while True:
        # Reset all joystick buttons
        taskObj.joy._device.buttons = [False for i in range(taskObj.nButtons)]
        # Draw practice start screen
        taskObj.practStart.draw()
        taskObj.screen.flip()
        response = event.getKeys(keyList=['escape'])
        if taskObj.joy.getButton(0):
            practClock = core.Clock()
            print('received trigger')
            break
        elif 'escape' in response:
            core.wait(1)
            taskObj.joy._device.close()
            taskObj.screen.close()
            core.quit()
    # Get practice trial info
    practClock = core.Clock()
    practInfo = taskInfo.practInfo
    # Proceed to trials
    outCounter = 0
    targetAcc = 0
    for tI in range(practInfo.maxTrials):
        if targetAcc < 6:
            # Print practice trial number
            print('Pract Trial No: ' + str(tI))
            practTrialStart = practClock.getTime()
            # Set up trial structure
            taskObj.ITI.start(taskInfo.trialInfo.maxJitter)
            # Show start fixation
            taskObj.trialFix.setAutoDraw(True)
            taskObj.screen.flip()
            # Store current trial's spring tension
            practInfo.trial_K_o[tI] = taskInfo.springInfo.K_o
            # Initialize practice trial
            outCounter = initPractTrial(tI, outCounter, practInfo, dispInfo, taskInfo, taskObj)
            # Run the trial
            outCounter = runPractTrial(tI, outCounter, practInfo, expInfo, taskObj, taskInfo, dispInfo, practClock)
            # Evaluate whether the accuracy is stable
            targetAcc = computeSpringTension(tI, targetAcc, practInfo, taskInfo)
            taskObj.ITI.complete()
            # Print trial timestamp
            # print('Pract Trial time ' + str(tI) + ': ' + str(practClock.getTime() - practTrialStart ))
        else:
            break
    # Show end ITI and save data
    taskObj.ITI.start(taskInfo.trialInfo.minJitter)# Close screen
    taskObj.expFix.setAutoDraw(True)
    taskObj.screen.flip()
    print('Finished practice / staircase)')
    print(f'Final spring param: {taskInfo.springInfo.K_o}')
    # Record final staircased spring parameter
    practInfo.final_K_o = taskInfo.springInfo.K_o
    # Saving the data
    savePractData(tI, expInfo, practInfo)
    # Store final physics parameters
    taskObj.expFix.setAutoDraw(False)
    taskObj.ITI.complete()
    # Show practice end screen
    while True:
        taskObj.practEnd.draw()
        taskObj.screen.flip()
        response = event.waitKeys(keyList=[keyInfo.instructDone,'escape'])
        if keyInfo.instructDone in response:
            break
        elif 'escape' in response:
            core.wait(1)
            taskObj.joy._device.close()
            taskObj.screen.close()
            core.quit()
    return

def computeSpringTension(tI, targetAcc, practInfo, taskInfo):
    print(f'Spring tension: {taskInfo.springInfo.K_o}')
    # No evaluation in the first 10 practice trials
    if tI >= 5:
        # History of accuracy
        hitHistory = practInfo.isHit_history[tI-5:tI]
        # Average accuracy
        mean_acc = np.nansum(hitHistory ) / len(hitHistory)
        print(f'Mean accuracy: {mean_acc}')
        # Increase tension if acc below threshold
        if mean_acc < taskInfo.springInfo.acc_thresh - taskInfo.springInfo.acc_tol:
            if not taskInfo.springInfo.K_o >= taskInfo.springInfo.K_o_max:
                taskInfo.springInfo.K_o += taskInfo.springInfo.K_o_delta
            # targetAcc = 0
        # Decrease tension if acc above threshold
        elif mean_acc > taskInfo.springInfo.acc_thresh + taskInfo.springInfo.acc_tol:
            if not taskInfo.springInfo.K_o <= taskInfo.springInfo.K_o_min:
                taskInfo.springInfo.K_o -= taskInfo.springInfo.K_o_delta
            # targetAcc = 0
        else:
            targetAcc += 1
    return targetAcc


def savePractData(tI, expInfo, practInfo):
    # Save ancilliary data
    ancOutDir = f'{expInfo.outDir}/ancillary'
    if not os.path.exists(ancOutDir):
        os.mkdir(ancOutDir)
    # Record last trial of session
    practInfo.__dict__.update({'numPractTrials': tI+1})
    # Save data
    save_obj(practInfo, f'{ancOutDir}/sub{expInfo.SubNo}_pract_data')
    return


def initPractTrial(tI, outCounter, practInfo, dispInfo, taskInfo, taskObj):
    # Update outcome bin idx counter
    if outCounter == len(practInfo.pWinVec):
        outCounter = 0
    # End start-trial fixation
    taskObj.trialFix.setAutoDraw(False)

    # Define stimulus and responses images for this trial
    if (practInfo.stim1_left[tI]):
        taskObj.leftStim.image = taskObj.pract_stim1.path
        taskObj.rightStim.image = taskObj.pract_stim2.path
    else:
        taskObj.leftStim.image = taskObj.pract_stim2.path
        taskObj.rightStim.image = taskObj.pract_stim1.path

    # Rescale images
    leftStim_rescaledSize = rescaleStim(taskObj.leftStim, dispInfo.imageSize, dispInfo)
    rightStim_rescaledSize = rescaleStim(taskObj.rightStim, dispInfo.imageSize, dispInfo)
    taskObj.leftStim.setSize(leftStim_rescaledSize)
    taskObj.rightStim.setSize(rightStim_rescaledSize)

    # Reset starting positions
    taskObj.handMass.setPos(dispInfo.imagePosC)
    taskObj.objectMass.setPos(dispInfo.objectPosC)
    return outCounter



def runPractTrial(tI, outCounter, practInfo, expInfo, taskObj, taskInfo, dispInfo, practClock):
    # Initialize containers to record mass dynamics
    object_position = []
    object_velocity = []
    hand_position = []
    hand_velocity = []
    movement_init = False

    # Initialize iteration over frames
    response = event.clearEvents() # Allow keyboard responses
    # Initialize response recordings
    practInfo.practResponses.respKey[tI] = np.nan
    practInfo.practResponses.rt_start[tI] = np.nan
    practInfo.practResponses.rt_end[tI] = np.nan
    practInfo.isHit_history[tI] = np.nan
    # Init
    q1 = 0 # Initialize position of object
    q2 = 0 # Initialize velocity of object
    # Initialize criteria for hits vs misses
    durFrames = []
    isHit = False

    # Flip screen and wait for response
    taskObj.ITI.complete()
    taskObj.screen.flip()
    startTime = practClock.getTime()

    # Check that starting position is centered!
    startPos = np.round(taskObj.joy.getX(),2)
    if np.abs(startPos) > taskObj.centerThresh:
        taskObj.ITI.start(taskInfo.trialInfo.isiMaxTime + taskInfo.trialInfo.fbMaxTime)
        taskObj.nonCentered.setAutoDraw(True)
        taskObj.screen.flip()
        taskObj.nonCentered.setAutoDraw(False)
        taskObj.ITI.complete()
    else:
        # Iterate over frames
        while (practClock.getTime() - startTime) <= taskInfo.trialInfo.maxRT:
            mX = np.round(taskObj.joy.getX(),2)
            # Record RT of first movement (away from center)
            if np.abs(startPos) > taskObj.centerThresh and not movement_init:
                movement_init = True
                practInfo.practResponses.rt_start[tI] = practClock.getTime() - startTime
            # Get starting RT once joystick position is out of
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
                respOnset = practClock.getTime()
                break
            # Allow exiting (and saving) with Keyboard
            response = event.getKeys(keyList=['escape'])
            if 'escape' in response:
                # Save trial
                print('Trying to save practice section!')
                savePractData(tI, expInfo, practInfo)
                core.wait(1)
                taskObj.joy._device.close()
                taskObj.screen.close()
                core.quit()
        # Encode whether and which choice was made
        eval_position = object_position[-1] # hand_position[int(-1*len(hand_position)//4):] # Look at last quarter of frames
        if not np.abs(np.sum(eval_position)) < taskObj.centerThresh:
            # Show action outcome feedback
            taskObj.ITI.start(taskInfo.trialInfo.isiMaxTime) #Start of ISI
            if isHit:
                practInfo.practResponses.rt_end[tI] = respOnset - startTime
            # Record choice (independent of action success)
            respKey = 0 if np.mean(eval_position) < 0 else 1
            practInfo.practResponses.respKey[tI] = respKey

            # Display action feedback (hit vs miss)
            if respKey == 0: # If they chose left option
                # Define what the left target image should be based on hit or miss
                if (practInfo.stim1_left[tI]):
                    taskObj.leftTarget.image = taskObj.pract_stim1.hit_path if isHit else taskObj.pract_stim1.miss_path
                else:
                    taskObj.leftTarget.image = taskObj.pract_stim2.hit_path if isHit else taskObj.pract_stim2.miss_path
                # Rescale the left target image
                leftTarget_rescaledSize = rescaleStim(taskObj.leftTarget, dispInfo.imageSize, dispInfo)
                taskObj.leftTarget.setSize(leftTarget_rescaledSize)
                # Dim out the unchosen stim
                taskObj.rightStim.opacity = 0.5
                # Show the left target and right stim images
                taskObj.leftTarget.setAutoDraw(True)
                taskObj.rightStim.setAutoDraw(True)
            elif respKey == 1:
                # Define what the right target image should be based on hit or miss
                if (practInfo.stim1_left[tI]):
                    taskObj.rightTarget.image = taskObj.pract_stim2.hit_path if isHit else taskObj.pract_stim2.miss_path
                else:
                    taskObj.rightTarget.image = taskObj.pract_stim1.hit_path if isHit else taskObj.pract_stim1.miss_path
                # Rescale the left target image
                rightTarget_rescaledSize = rescaleStim(taskObj.rightTarget, dispInfo.imageSize, dispInfo)
                taskObj.rightTarget.setSize(rightTarget_rescaledSize)
                # Dim out the unchosen stim
                taskObj.leftStim.opacity = 0.5
                # Show the right target and left stim images
                taskObj.rightTarget.setAutoDraw(True)
                taskObj.leftStim.setAutoDraw(True)

            taskObj.screen.flip()
            # Reset the targets for the next trial
            taskObj.leftTarget.setAutoDraw(False)
            taskObj.rightTarget.setAutoDraw(False)
            # Reset the stims for the next trial
            taskObj.leftStim.opacity = taskObj.rightStim.opacity = 1
            taskObj.leftStim.setAutoDraw(False)
            taskObj.rightStim.setAutoDraw(False)
            taskObj.ITI.complete() # End of ISI

            # Start of feedback
            taskObj.ITI.start(taskInfo.trialInfo.fbMaxTime)
            # Compute outcome
            outCounter = computeOutcome(tI, outCounter, taskInfo, taskObj, practInfo, respKey, isHit)

            # Show reward outcome feedback
            taskObj.screen.flip()
            taskObj.ITI.complete() # End of feedback

        else: # If no response was made on this trial
            taskObj.ITI.start(taskInfo.trialInfo.isiMaxTime + taskInfo.trialInfo.fbMaxTime)
            respKey = np.nan
            taskObj.noRespErr.setAutoDraw(True)
            taskObj.screen.flip()
            taskObj.noRespErr.setAutoDraw(False)
            # Set stim attributes to nan
            practInfo.stimAttrib.isSelected[:, tI] = np.nan
            practInfo.stimAttrib.isHit[:, tI] = np.nan
            practInfo.stimAttrib.isWin[:, tI] = np.nan
            taskObj.ITI.complete()

    #  Present trial-end fixation
    taskObj.ITI.start(taskInfo.trialInfo.maxJitter)
    taskObj.rewardOut.setAutoDraw(False)
    taskObj.winOut.setAutoDraw(False)
    taskObj.noWinOut.setAutoDraw(False)
    taskObj.trialFix.setAutoDraw(True)
    taskObj.screen.flip()

    # Store the trajectories for this trial
    practInfo.hand_position_trials[tI] = np.array(hand_position)
    practInfo.hand_velocity_trials[tI] = np.array(hand_velocity)
    practInfo.object_position_trials[tI] = np.array(object_position)
    practInfo.object_velocity_trials[tI] = np.array(object_velocity)
    taskObj.trialFix.setAutoDraw(False)
    return outCounter
'''
    # Plot curves for demo
    fig, ax = plt.subplots()
    ax.set_title(f'Trial {tI}')
    ax.plot(hand_position,  label='hand position', linewidth=3, color='blue', alpha=1)
    ax.plot(hand_velocity, label='hand velocity', linewidth=3, color='blue', alpha=0.5)
    ax.plot(object_position,  label='mass position', linewidth=3, color='green', alpha=1)
    ax.plot(object_velocity, label='mass velocity', linewidth=3, color='green', alpha=0.5)

    ax.legend()
    fig.show()
'''




def computeOutcome(tI, outCounter, taskInfo, taskObj, practInfo, respKey, isHit):
    # Determine which stim was chosen
    if (respKey == 0):
        if (practInfo.stim1_left[tI]):
            resp_stimIdx = 0
            practInfo.selectedStim[tI] = 1
        else:
            resp_stimIdx = 1
            practInfo.selectedStim[tI] = 2
    elif (respKey == 1):
        if (practInfo.stim1_left[tI]):
            resp_stimIdx = 1
            practInfo.selectedStim[tI] = 2
        else:
            resp_stimIdx = 0
            practInfo.selectedStim[tI] = 1
    # Determine whether the outcome is a win or loss
    isWin = practInfo.pWinVec[outCounter]

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
    practInfo.stimAttrib.isSelected[resp_stimIdx, tI] = 1
    practInfo.stimAttrib.isHit[resp_stimIdx, tI] = isHit
    practInfo.stimAttrib.isWin[resp_stimIdx, tI] = isWin
    practInfo.stimAttrib.isSelected[1-resp_stimIdx, tI] = 0
    practInfo.stimAttrib.isHit[1-resp_stimIdx, tI] = np.nan
    practInfo.stimAttrib.isWin[1-resp_stimIdx, tI] = np.nan
    # Store history of hit/miss
    practInfo.isHit_history[tI] = isHit
    return outCounter
