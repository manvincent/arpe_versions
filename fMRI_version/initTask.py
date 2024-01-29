from psychopy import visual, gui, data, core, event, logging, info, hardware
from psychopy.hardware import joystick
from psychopy.constants import *
from psychopy import parallel
import numpy as np
from copy import deepcopy as dcopy
import os
from config import *

def initTask(expInfo):
    ###### Task parameters properties ######
    # task properties
    numSessions = 8
    numTrials = 320
    # trial timing
    def trialParam(numSessions, numTrials):
        maxRT = 3.5
        targetDur = 60 # in frames
        if (expInfo.Modality == 'fmri'):
            TR = 1.12 # Delete first 4 volumes
            disDaqTime = 4 * TR
            isiMinTime = 1.50
            isiMaxTime = 2.00
            fbMinTime = 1.50
            fbMaxTime = 2.00
        elif (expInfo.Modality == 'ephys') or (expInfo.Modality == 'behav'):
            disDaqTime = 0
            isiMinTime = isiMaxTime = 1.75
            fbMinTime = fbMaxTime = 1.75
        minJitter = 0.5
        maxJitter = 1.5
        trialsPerSess = numTrials // numSessions
        return dict(
                    maxRT=maxRT,
                    targetDur=targetDur,
                    isiMinTime=isiMinTime,
                    isiMaxTime=isiMaxTime,
                    fbMinTime=fbMinTime,
                    fbMaxTime=fbMaxTime,
                    disDaqTime=disDaqTime,
                    minJitter=minJitter,
                    maxJitter=maxJitter,
                    trialsPerSess=trialsPerSess)
    trialInfo = dict2class(trialParam(numSessions, numTrials))

    def springParam(expInfo):
        M_o = 0.5
        K_o = expInfo.final_K_o if expInfo.final_K_o else 1
        acc_thresh = 0.7
        acc_tol = 0.1
        K_o_delta = 0.05
        K_o_min = 0.5
        K_o_max = 1.5
        return dict(M_o=M_o,
                    K_o=K_o,
                    acc_thresh=acc_thresh,
                    acc_tol=acc_tol,
                    K_o_delta=K_o_delta,
                    K_o_min=K_o_min,
                    K_o_max=K_o_max)
    springInfo = dict2class(springParam(expInfo))

    def taskParam(numTrials):
        subID = int()
        pWinHigh = 0.7
        pWinLow = 0.3
        pReversal = 0.25
        return dict(subID=subID,
                    pWinHigh=pWinHigh,
                    pWinLow=pWinLow,
                    pReversal=pReversal)
    taskInfo = dict2class(taskParam(numTrials))
    taskInfo.__dict__.update({'trialInfo': trialInfo,
                              'springInfo': springInfo,
                              'numSessions': numSessions,
                              'numTrials': numTrials})
    # Set up triggers
    if expInfo.Modality == 'ephys':
        port = parallel.ParallelPort(address=0xDFF8)
        def triggerLegend():
            taskStart_ID = 4 #8
            taskEnd_ID = [7,5,4] #88
            sessStart_ID = [3,2,1] #7
            sessEnd_ID = [7,4,3,1] #77
            trialStart_ID = [2,2,1] #5
            trialEnd_ID = [6,5,3,2,1] #55
            preFix_ID = [4,2] #10
            target_ID = [4,2,1] #11
            resp_start_ID = [4,3] #12
            resp_end_ID = [4,3,1] #13
            Aout_ID = [4,3,2] #14
            Rout_ID= [4,3,2,1] #15
            postFix_ID = 5 #16
            return dict(taskStart_ID=taskStart_ID,
                        taskEnd_ID=taskEnd_ID,
                        trialStart_ID=trialStart_ID,
                        trialEnd_ID=trialEnd_ID,
                        preFix_ID=preFix_ID,
                        target_ID=target_ID,
                        resp_start_ID=resp_start_ID,
                        resp_end_ID=resp_end_ID,
                        Aout_ID=Aout_ID,
                        Rout_ID=Rout_ID,
                        postFix_ID=postFix_ID)
        triggerInfo = dict2class(triggerLegend())
        taskInfo.__dict__.update({'port': port,
                                  'triggerInfo': triggerInfo})
    ###### Setting up the display structure #######

    def dispParam(expInfo):
        xRes = 1600
        yRes = 1200
        screenColor=[0.1, 0.2, 0.75]
        screenColSpace='rgb'
        screenPos=(0, 0)
        screenUnit='norm'
        backend = 'pyglet'
        screenWinType=backend
        if (expInfo.Version == 'debug'):
            screenScaling = 0.9
            screen = visual.Window(color=screenColor,
                                   colorSpace=screenColSpace,
                                   size=(xRes * screenScaling, yRes * screenScaling),
                                   pos=screenPos,
                                   units=screenUnit,
                                   winType=screenWinType,
                                   fullscr=False,
                                   screen=0,
                                   allowGUI=True,
                                   gammaErrorPolicy='ignore')
        elif (expInfo.Version == 'test'):
            screenScaling = 1
            screen = visual.Window(color=screenColor,
                                   colorSpace=screenColSpace,
                                   size=(xRes * screenScaling, yRes * screenScaling),
                                   pos=screenPos,
                                   units=screenUnit,
                                   winType=screenWinType,
                                   fullscr=True,
                                   screen=1,
                                   allowGUI=False,
                                   gammaErrorPolicy='ignore')
        monitorX = screen.size[0]
        monitorY = screen.size[1]
        fps = screen.getActualFrameRate(nIdentical=10,
                                        nMaxFrames=100,
                                        nWarmUpFrames=10,
                                        threshold=1)
        textFont = 'Helvetica'
        if (expInfo.Modality == 'fmri'):
            textHeight = 0.1
            imageSize_hard = 0.3
        elif (expInfo.Modality == 'ephys') or (expInfo.Modality == 'behav'):
            textHeight = 1
            imageSize_hard = 0.4
        imageSize = 0.5
        imageSize_easy = 0.6
        colour1 = [0, 108, 237] # rgb 255 values
        colour2 = [228, 140, 0]
        imagePosL = [-0.7,0]
        imagePosR = [0.7,0]
        imagePosC = [0,-0.6]
        imagePosH = [0,0.5]
        objectPosC = [0,0]
        targetPosL = [-0.7,0.05]
        targetPosR = [0.7,0.05]


        dispInfo = dict2class(dict(screenScaling=screenScaling,
                                backend=backend,
                                monitorX=monitorX,
                                monitorY=monitorY,
                                fps=fps,
                                textFont=textFont,
                                textHeight=textHeight,
                                imageSize=imageSize,
                                imageSize_easy=imageSize_easy,
                                imageSize_hard=imageSize_hard,
                                colour1=colour1,
                                colour2=colour2,
                                imagePosL=imagePosL,
                                imagePosR=imagePosR,
                                imagePosC=imagePosC,
                                imagePosH=imagePosH,
                                objectPosC=objectPosC,
                                targetPosL=targetPosL,
                                targetPosR=targetPosR))
        return dispInfo, screen
    [dispInfo, screen] = dispParam(expInfo)

    # Set up python objects for all generic task objects

    # Start loading images
    loadScreen = visual.TextStim(screen,
                                 text="Loading...",
                                 font=dispInfo.textFont,
                                 pos=screen.pos,
                                 height=0.1,
                                 color='black')
    loadScreen.setAutoDraw(True)
    screen.flip()
    # display 'save' screen
    saveScreen = visual.TextStim(screen,
                                 text="Saving...",
                                 font=dispInfo.textFont,
                                 pos=screen.pos,
                                 height=0.1,
                                 color='black')
    # Keyboard info
    keyInfo = dict2class(keyConfig())

    # Stimuli

    pract_stim1 = TrialObj(taskInfo, pathToFile=f'{expInfo.instructDir}/instruct_stimA')
    pract_stim2 = TrialObj(taskInfo, pathToFile=f'{expInfo.instructDir}/instruct_stimB')
    stim1 = TrialObj(taskInfo, pathToFile=f'{expInfo.stimDir}/stimA')
    stim2 = TrialObj(taskInfo,  pathToFile=f'{expInfo.stimDir}/stimB')

    # Fixations
    expFix = visual.TextStim(screen,
                             text="+",
                             font=dispInfo.textFont,
                             pos=screen.pos,
                             height=0.15,
                             color='red',
                             wrapWidth=1.8)
    trialFix = visual.TextStim(screen,
                               text="+",
                               font=dispInfo.textFont,
                               pos=[0, 0],
                               height=0.15,
                               color='black',
                               wrapWidth=1.8)
    cueFix = visual.TextStim(screen,
                               text="+",
                               font=dispInfo.textFont,
                               pos=[0, 0],
                               height=0.15,
                               color='blue',
                               wrapWidth=1.8)

    # Stims are the patch images presented at the start of the trial
    leftStim = visual.ImageStim(win=screen,
                                size=dispInfo.imageSize,
                                pos=dispInfo.imagePosL)
    rightStim = visual.ImageStim(win=screen,
                                size=dispInfo.imageSize,
                                pos=dispInfo.imagePosR)
    leftMag = visual.TextStim(win=screen,
                              font=dispInfo.textFont,
                              pos=np.add(dispInfo.imagePosL,[0,0.5]),
                              height=dispInfo.textHeight,
                              color='black',
                              bold=True,
                              wrapWidth=.5)
    rightMag = visual.TextStim(win=screen,
                              font=dispInfo.textFont,
                              pos=np.add(dispInfo.imagePosR,[0,0.5]),
                              height=dispInfo.textHeight,
                              color='black',
                              bold=True,
                              wrapWidth=.5)
    # Targets are the hit/miss action outcome images
    leftTarget = visual.ImageStim(win=screen,
                                size=dispInfo.imageSize,
                                pos=dispInfo.targetPosL)
    rightTarget = visual.ImageStim(win=screen,
                                 size=dispInfo.imageSize,
                                 pos=dispInfo.targetPosR)
    # Masses
    handMass = visual.ImageStim(win=screen,
                                image=f'{expInfo.stimDir}/hand.png',
                                size=dispInfo.imageSize,
                                pos=dispInfo.imagePosC)
    objectMass = visual.ImageStim(win=screen,
                                  image=f'{expInfo.stimDir}/object.png',
                                  size=dispInfo.imageSize)
    # Rescale the masses
    handMass_rescaledSize = rescaleStim(handMass, dispInfo.imageSize, dispInfo)
    objectMass_rescaledSize = rescaleStim(objectMass, dispInfo.imageSize, dispInfo)
    handMass.setSize(handMass_rescaledSize)
    objectMass.setSize(objectMass_rescaledSize)
    # Initiate mouse
    mouse = event.Mouse(win=screen,
                        visible=False,
                        newPos=dispInfo.imagePosC)
    # if (not expInfo.doTask) or expInfo.Modality == 'behav':
    # Initiate joystick
    # joystick.backend = dispInfo.backend
    # nJoys = joystick.getNumJoysticks()
    # if nJoys < 1:
    #     raise Exception('No joysticks detected')
    # else:        
    #     joyID = nJoys - 2
    #     joy = joystick.Joystick(joyID)
    #     nButtons = joy.getNumButtons()
        
    # Define center threshold regardless of manipulandum
    centerThresh = 0.3
    # Error messages
    nonCentered = visual.TextStim(screen,
                              text="Round forfeited.\n\nRod not centered!",
                              font=dispInfo.textFont,
                              pos=screen.pos,
                              height=dispInfo.textHeight,
                              color='black',
                              bold=True,
                              wrapWidth=1.8)
    # Reward outcome text and images
    rewardOut = visual.TextStim(screen,
                                font=dispInfo.textFont,
                                pos=screen.pos,
                                height=dispInfo.textHeight,
                                color='black',
                                bold=True,
                                wrapWidth=1.8)
    winOut = visual.ImageStim(win=screen,
                                image=f'{expInfo.stimDir}/win.png',
                                size=dispInfo.imageSize,
                                pos=dispInfo.imagePosH)
    noWinOut = visual.ImageStim(win=screen,
                                image=f'{expInfo.stimDir}/noWin.png',
                                size=dispInfo.imageSize,
                                pos=dispInfo.imagePosH)
    # Rescale the outcome images
    winOut_rescaledSize = rescaleStim(winOut, dispInfo.imageSize, dispInfo)
    noWinOut_rescaledSize = rescaleStim(noWinOut, dispInfo.imageSize, dispInfo)
    winOut.setSize(winOut_rescaledSize)
    noWinOut.setSize(noWinOut_rescaledSize)
    # Initialize special messages
    waitExp = visual.ImageStim(win=screen,
                                  image=f'{expInfo.stimDir}/new_session.png',
                                  pos=dispInfo.objectPosC,
                                  size=dispInfo.imageSize)
    waitExp_rescaledSize = rescaleStim(waitExp, 1, dispInfo)
    waitExp.setSize(waitExp_rescaledSize)
    readyExp = visual.TextStim(screen,
                               text="Please get ready. Press " + keyInfo.instructDone + " to start",
                               font=dispInfo.textFont,
                               pos=screen.pos,
                               height=0.15,
                               color='black',
                               wrapWidth=1.8)
    scanPulse = visual.TextStim(screen,
                                text="Waiting for the scanner...",
                                font=dispInfo.textFont,
                                pos=screen.pos,
                                height=0.15,
                                color='black',
                                wrapWidth=1.8)
    noRespErr = visual.TextStim(screen,
                                text="Failed to land in the patch.",
                                font=dispInfo.textFont,
                                pos=screen.pos,
                                height=0.07,
                                color='black',
                                wrapWidth=1.8)

    # Initialize pract start/end screens
    practStart = visual.TextStim(screen,
                              text="Get ready for some practice.\n\nThe practice has no impact on your overall score.\n\nClick the trigger to start.",
                              font=dispInfo.textFont,
                              pos=screen.pos,
                              height=0.15,
                              color='black',
                              wrapWidth=1.8)
    practEnd = visual.TextStim(screen,
                               text="End of practice. Get ready for the task.\n\nYou will start playing for points!",
                               font=dispInfo.textFont,
                               pos=screen.pos,
                               height=0.15,
                               color='black',
                               wrapWidth=1.8)
    # ITI object
    ITI = core.StaticPeriod(screenHz=dispInfo.fps, win=screen, name='ITI')
    # Wrap objects into dictionary
    # if (not expInfo.doTask) or expInfo.Modality == 'behav':
    taskObj = dict2class(dict(screen=screen,
                           loadScreen=loadScreen,
                           saveScreen=saveScreen,
                           pract_stim1=pract_stim1,
                           pract_stim2=pract_stim2,
                           stim1=stim1,
                           stim2=stim2,
                           expFix=expFix,
                           trialFix=trialFix,
                           cueFix=cueFix,
                           leftStim=leftStim,
                           rightStim=rightStim,
                           leftMag=leftMag,
                           rightMag=rightMag,
                           leftTarget=leftTarget,
                           rightTarget=rightTarget,
                           handMass=handMass,
                           objectMass=objectMass,
                           mouse=mouse,
                        #    joy=joy,
                        #    nButtons=nButtons,
                           centerThresh=centerThresh,
                           nonCentered=nonCentered,
                           rewardOut=rewardOut,
                           winOut=winOut,
                           noWinOut=noWinOut,
                           waitExp=waitExp,
                           readyExp=readyExp,
                           scanPulse=scanPulse,
                           noRespErr=noRespErr,
                           practStart=practStart,
                           practEnd=practEnd,
                           ITI=ITI))
    # elif expInfo.doTask and expInfo.Modality == 'fmri':
    #     taskObj = dict2class(dict(screen=screen,
    #                           loadScreen=loadScreen,
    #                           saveScreen=saveScreen,
    #                           pract_stim1=pract_stim1,
    #                           pract_stim2=pract_stim2,
    #                           stim1=stim1,
    #                           stim2=stim2,
    #                           expFix=expFix,
    #                           trialFix=trialFix,
    #                           cueFix=cueFix,
    #                           leftStim=leftStim,
    #                           rightStim=rightStim,
    #                           leftMag=leftMag,
    #                           rightMag=rightMag,
    #                           leftTarget=leftTarget,
    #                           rightTarget=rightTarget,
    #                           handMass=handMass,
    #                           objectMass=objectMass,
    #                           mouse=mouse,
    #                           centerThresh=centerThresh,
    #                           nonCentered=nonCentered,
    #                           rewardOut=rewardOut,
    #                           winOut=winOut,
    #                           noWinOut=noWinOut,
    #                           waitExp=waitExp,
    #                           readyExp=readyExp,
    #                           scanPulse=scanPulse,
    #                           noRespErr=noRespErr,
    #                           practStart=practStart,
    #                           practEnd=practEnd,
    #                           ITI=ITI))

    # Initialize task variables
    taskInfo = initSessions(taskInfo, numSessions)
    # Close loading screen
    loadScreen.setAutoDraw(False)
    return screen, dispInfo, taskInfo, taskObj, keyInfo



class TrialObj(object):
    def __init__(self, taskInfo, pathToFile):
        # Initialize design containers
        self.pWin = float()
        self.path = f'{pathToFile}.png'
        self.hit_path = f'{pathToFile}_hit.png'
        self.miss_path = f'{pathToFile}_miss.png'

class Onsets(object):
    def __init__(self,numTrials):
        self.tPreFix = np.ones(numTrials, dtype=float) * np.nan
        self.tTarget = np.ones(numTrials, dtype=float) * np.nan
        self.tResp_start = np.ones(numTrials, dtype=float) * np.nan
        self.tResp_end = np.ones(numTrials, dtype=float) * np.nan
        self.tAOut = np.ones(numTrials, dtype=float) * np.nan
        self.tROut = np.ones(numTrials, dtype=float) * np.nan
        self.tPostFix = np.ones(numTrials, dtype=float) * np.nan

class Responses(object):
    def __init__(self,numTrials):
        self.respKey = np.ones(numTrials, dtype=float) * np.nan
        self.rt_start = np.ones(numTrials, dtype=float) * np.nan
        self.rt_end = np.ones(numTrials, dtype=float) * np.nan

def initSessions(taskInfo, numSessions):
    # Set up the session-wise design
    sessionInfo = np.empty(taskInfo.numSessions, dtype=object)

    for sI in range(taskInfo.numSessions):
        # Specify which stim is on the left/right
        stim1_left = np.random.binomial(1, 0.5, taskInfo.trialInfo.trialsPerSess).astype(bool)
        # Initialize (before first reversal) which stim is p(high)
        stim1_high = bool(np.random.binomial(1, 0.5))
        # Trial design randomisations
        itiDur = np.random.permutation(np.linspace(taskInfo.trialInfo.minJitter,
                                     taskInfo.trialInfo.maxJitter,
                                      taskInfo.trialInfo.trialsPerSess))
        isiDur = np.random.permutation(np.linspace(taskInfo.trialInfo.isiMinTime,
                                     taskInfo.trialInfo.isiMaxTime,
                                      taskInfo.trialInfo.trialsPerSess))
        fbDur = np.random.permutation(np.linspace(taskInfo.trialInfo.fbMinTime,
                                     taskInfo.trialInfo.fbMaxTime,
                                      taskInfo.trialInfo.trialsPerSess))
        # Store whether the good (pWinHigh) option was chosen
        highChosen = np.zeros(taskInfo.trialInfo.trialsPerSess,dtype=bool)
        # Store which stim is the selected stim
        selectedStim = np.zeros(taskInfo.trialInfo.trialsPerSess,dtype=int)
        # Create vector to control reversals
        reverseVec = np.zeros(int(1//taskInfo.pReversal), dtype=bool)
        # reverseVec[0] = 1
        np.random.shuffle(reverseVec)
        # Store whether reversals are possible on trial tI
        reverseStatus = np.zeros(taskInfo.trialInfo.trialsPerSess,dtype=bool)
        # Store whether a reversal occurred on trial tI
        reverseTrial = np.zeros(taskInfo.trialInfo.trialsPerSess,dtype=bool)
        # Set which trials in this session are easy vs hard
        isEasy = np.zeros(taskInfo.trialInfo.trialsPerSess,dtype=bool)
        # isEasy[:int(taskInfo.trialInfo.trialsPerSess//2)] = True
        # np.random.shuffle(isEasy)
        # Intitialize pWinHigh bin
        pWinHighVec = np.zeros(10, dtype = bool)
        pWinHighVec[:int(taskInfo.pWinHigh * 10)] = True
        np.random.shuffle(pWinHighVec)
        # Intitialize pWinLow bin
        pWinLowVec = np.zeros(10, dtype = bool)
        pWinLowVec[:int(taskInfo.pWinLow * 10)] = True
        np.random.shuffle(pWinLowVec)
        # Create containers for the trajectories
        hand_position_trials = np.empty(taskInfo.trialInfo.trialsPerSess, dtype=object)
        hand_velocity_trials = np.empty(taskInfo.trialInfo.trialsPerSess, dtype=object)
        object_position_trials = np.empty(taskInfo.trialInfo.trialsPerSess, dtype=object)
        object_velocity_trials = np.empty(taskInfo.trialInfo.trialsPerSess, dtype=object)
        # Create container for history of hit/miss
        isHit_history = np.ones(taskInfo.trialInfo.trialsPerSess, dtype=float) * np.nan
        # Initialize joystick offset containers
        offSet = np.ones(taskInfo.trialInfo.trialsPerSess, dtype=float) * np.nan
        # Initialize timing containers
        sessionOnsets = Onsets(taskInfo.trialInfo.trialsPerSess)
        sessionResponses = Responses(taskInfo.trialInfo.trialsPerSess)
        # Initialize stim attribute containers
        def stimParam(taskInfo):
            # For the first axis, indices of 0 = stim1 and 1 = stim2
            pWin = np.ones((2,taskInfo.trialInfo.trialsPerSess), dtype=float) * np.nan
            isHigh = np.zeros((2,taskInfo.trialInfo.trialsPerSess), dtype=bool)
            isHit = np.ones((2,taskInfo.trialInfo.trialsPerSess), dtype=float) * np.nan
            isSelected = np.ones((2,taskInfo.trialInfo.trialsPerSess), dtype=float) * np.nan
            isWin = np.ones((2,taskInfo.trialInfo.trialsPerSess), dtype=float) * np.nan
            return dict(pWin=pWin,
                        isHigh=isHigh,
                        isHit=isHit,
                        isSelected=isSelected,
                        isWin=isWin)
        stimAttrib = dict2class(stimParam(taskInfo))
        # Initialize payout container
        payOut = np.zeros(taskInfo.trialInfo.trialsPerSess,dtype=float)
        # Flatten into class object
        sessionInfo[sI] = dict2class(dict(stim1_left=stim1_left,
                                       stim1_high=stim1_high,
                                       itiDur=itiDur,
                                       isiDur=isiDur,
                                       fbDur=fbDur,
                                       highChosen=highChosen,
                                       selectedStim=selectedStim,
                                       reverseVec=reverseVec,
                                       reverseStatus=reverseStatus,
                                       reverseTrial=reverseTrial,
                                       isEasy=isEasy,
                                       pWinHighVec=pWinHighVec,
                                       pWinLowVec=pWinLowVec,
                                       hand_position_trials=hand_position_trials,
                                       hand_velocity_trials=hand_velocity_trials,
                                       object_position_trials=object_position_trials,
                                       object_velocity_trials=object_velocity_trials,
                                       isHit_history=isHit_history,
                                       offSet=offSet,
                                       sessionOnsets=sessionOnsets,
                                       sessionResponses=sessionResponses,
                                       stimAttrib=stimAttrib,
                                       payOut=payOut))
    taskInfo.__dict__.update({'sessionInfo': sessionInfo})
    return(taskInfo)
