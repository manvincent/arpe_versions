from psychopy import visual, event, core
import numpy as np # whole numpy lib is available, prepend 'np.'
import os
from config import *
from runBandit_joy import springDynamics


def runInstruct_short(expInfo, dispInfo, taskInfo, taskObj):
    imagePath = f'{expInfo.instructDir}/pages_short'
    # Get number of instruction pages
    numPages = len(os.listdir(imagePath))
    pages = np.arange(numPages)
    # Initialize instruct page object
    instruct_maxRT = 0
    instructObj = InstructPages(expInfo, dispInfo, taskInfo, taskObj, imagePath)
    currPage = 1
    while True:
        # Reset all joystick buttons
        taskObj.joy._device.buttons = [False for i in range(taskObj.nButtons)]
        # Show instruction screen
        instructObj.showInstruct(currPage)
        # For the last screen
        if currPage == numPages:
            if taskObj.joy.getButton(0):
                break
            elif taskObj.joy.getButton(4):
                # Move back a screen
                currPage = max(1,currPage-1)
                print('Page: '  + str(currPage))
            elif 'escape' in response:
                core.wait(1)
                taskObj.joy._device.close()
                taskObj.screen.close()
                core.quit()
        # For simple screen (prev/next responses)
        else:
            # Show instruction screen
            instructObj.showInstruct(currPage)
            response = event.getKeys(keyList=['escape'])
            if taskObj.joy.getButton(4):
                # Move back a screen
                currPage = max(1,currPage-1)
                print('Page: '  + str(currPage))
            elif taskObj.joy.getButton(10):
                # Move forward a screen
                currPage = min(len(pages), currPage+1)
                print('Page: ' + str(currPage))
            elif 'escape' in response:
                core.wait(1)
                taskObj.joy._device.close()
                taskObj.screen.close()
                core.quit()
                
def runInstruct_long(expInfo, dispInfo, taskInfo, taskObj):
    imagePath = f'{expInfo.instructDir}/pages_long'
    # Set allowable time (in seconds) for interactive pages
    instruct_maxRT = 10
    instruct_numTrials = 5
    # Get number of instruction pages
    numPages = len(os.listdir(imagePath))
    pages = np.arange(numPages)
    # Initialize instruct page object
    instructObj = InstructPages(expInfo, dispInfo, taskInfo, taskObj, imagePath, instruct_maxRT)
    currPage = 1
    while True:
        # Reset all joystick buttons
        taskObj.joy._device.buttons = [False for i in range(taskObj.nButtons)]
        # Show instruction screen
        instructObj.showInstruct(currPage)
        if currPage == 9:
            if taskObj.joy.getButton(0):
                # Run interactive demo
                instructObj.moveRod('left')
                # Then move forward a screen
                currPage = min(len(pages), currPage+1)
                print('Page: ' + str(currPage))
        elif currPage == 10:
            if taskObj.joy.getButton(0):
                # Run interactive demo
                instructObj.moveRod('right')
                # Then move forward a screen
                currPage = min(len(pages), currPage+1)
                print('Page: ' + str(currPage))


        elif currPage == 12:
            if taskObj.joy.getButton(0):
                # Run interactive demo
                isHit = instructObj.choosePatch('left')
                if isHit:
                    # Then move forward a screen
                    currPage = min(len(pages), currPage+1)
                    print('Page: ' + str(currPage))
        elif currPage == 13:
            if taskObj.joy.getButton(0):
                # Run interactive demo
                isHit = instructObj.choosePatch('right')
                if isHit:
                    # Then move forward a screen
                    currPage = min(len(pages), currPage+1)
                    print('Page: ' + str(currPage))
        elif currPage == 19:
            if taskObj.joy.getButton(0):
                # Run interactive demo
                for tI in np.arange(instruct_numTrials):
                    instructObj.choosePatch_hit()
                # Then move forward a screen
                currPage = min(len(pages), currPage+1)
                print('Page: ' + str(currPage))
        # For the last screen
        elif currPage == numPages:
            if taskObj.joy.getButton(0):
                break
            elif taskObj.joy.getButton(4):
                # Move back a screen
                currPage = max(1,currPage-1)
                print('Page: '  + str(currPage))
            elif 'escape' in response:
                core.wait(1)
                taskObj.joy._device.close()
                taskObj.screen.close()
                core.quit()
        # For simple screen (prev/next responses)
        else:
            # Show instruction screen
            instructObj.showInstruct(currPage)
            response = event.getKeys(keyList=['escape'])
            if taskObj.joy.getButton(4):
                # Move back a screen
                currPage = max(1,currPage-1)
                print('Page: '  + str(currPage))
            elif taskObj.joy.getButton(10):
                # Move forward a screen
                currPage = min(len(pages), currPage+1)
                print('Page: ' + str(currPage))
            elif 'escape' in response:
                core.wait(1)
                taskObj.joy._device.close()
                taskObj.screen.close()
                core.quit()





class InstructPages(object):
    def __init__(self, expInfo, dispInfo, taskInfo, taskObj, imagePath, instruct_maxRT):
        self.screen = taskObj.screen
        self.posMid = [0, 0]
        # Display information
        self.monitorX = dispInfo.monitorX
        self.monitorY = dispInfo.monitorY
        self.screenScaling = dispInfo.screenScaling
        self.imageSize = 0.9
        self.imagePath = imagePath
        # Import task objects
        self.expInfo = expInfo
        self.dispInfo = dispInfo
        self.taskInfo = taskInfo
        self.taskObj = taskObj
        # Start a clock for instructions
        self.instructClock = core.Clock()
        self.maxRT = instruct_maxRT

    def showInstruct(self, page):
        self.instructScreen = visual.ImageStim(win=self.screen,
                                               image = f'{self.imagePath}/instruct_{page}.png',
                                               pos=self.posMid)
        # Rescale images
        self.instructScreen.rescaledSize = rescaleStim(self.instructScreen, self.imageSize, self)
        self.instructScreen.setSize(self.instructScreen.rescaledSize)
        # Draw objects
        self.instructScreen.draw()
        # Flip screen
        self.screen.flip()
        return


    def choosePatch_hit(self):
        stim1_left = bool(np.random.binomial(1, 0.5))
        # Randomize which image shown on the left/right
        if stim1_left:
            self.taskObj.leftStim.image = self.taskObj.pract_stim1.path
            self.taskObj.rightStim.image = self.taskObj.pract_stim2.path
        else:
            self.taskObj.leftStim.image = self.taskObj.pract_stim2.path
            self.taskObj.rightStim.image = self.taskObj.pract_stim1.path
        # Rescale images
        leftStim_rescaledSize = rescaleStim(self.taskObj.leftStim, self.dispInfo.imageSize, self.dispInfo)
        rightStim_rescaledSize = rescaleStim(self.taskObj.rightStim, self.dispInfo.imageSize, self.dispInfo)
        self.taskObj.leftStim.setSize(leftStim_rescaledSize)
        self.taskObj.rightStim.setSize(rightStim_rescaledSize)


        # Initialize iteration over frames
        response = event.clearEvents() # Allow keyboard responses
        # Initialize dyanmics and positions
        mX = 0 # Initialize hand position
        q1 = 0 # Initialize position of object
        q2 = 0 # Initialize velocity of object

        # Initialize criteria for hits vs misses
        durFrames = []
        isHit = False
        hand_position = []
        object_position = []

        # Flip screen and wait for response
        self.screen.flip()
        startTime = self.instructClock.getTime()

        # Check that starting position is centered!
        startPos = np.round(self.taskObj.joy.getX(),2)
        if np.abs(startPos) > self.taskObj.centerThresh:
            self.taskObj.nonCentered.setAutoDraw(True)
            self.screen.flip()
            self.taskObj.nonCentered.setAutoDraw(False)
            core.wait(3)
        else:
            # Iterate over frames
            while (self.instructClock.getTime() - startTime) <= self.maxRT:
                if self.expInfo.invertJoy:
                    mX = np.round(self.taskObj.joy.getX() * -1,2)
                else: 
                    mX = np.round(self.taskObj.joy.getX(),2)
                self.taskObj.handMass.setPos([mX, self.dispInfo.imagePosC[1]])
                # Compute position/velocity of object
                q1, q2 = springDynamics(self.taskInfo, self.dispInfo, q1, q2, mX)
                objectPos = [q1, self.dispInfo.objectPosC[1]]
                self.taskObj.objectMass.setPos(objectPos)
                # Draw stims
                self.taskObj.leftStim.draw()
                self.taskObj.rightStim.draw()
                # Draw masses
                self.taskObj.handMass.draw()
                self.taskObj.objectMass.draw()
                self.screen.flip()
                # Evaluate if object is inside target at criterion
                if self.taskObj.leftStim.contains(objectPos):
                    durFrames.append(0)
                elif self.taskObj.rightStim.contains(objectPos):
                    durFrames.append(1)
                else:
                    durFrames = []
                hand_position.append(mX)
                object_position.append(q1)

                # Evaluate success -- reaches min frames inside a target
                if len(durFrames) > self.taskInfo.trialInfo.targetDur and durFrames.count(durFrames[0]) == len(durFrames):
                    isHit = True
                    break
                # Allow exiting (and saving) with Keyboard
                response = event.getKeys(keyList=['escape'])
                if 'escape' in response:
                    # Save trial
                    print('Exiting during instructions!')
                    core.wait(1)
                    self.taskObj.joy._device.close()
                    self.taskObj.screen.close()
                    core.quit()

            # Record choice (independent of action success)
            if not np.sum(hand_position) == 0:
                # Record choice (independent of action success)
                eval_position = object_position[-1] #hand_position[int(-1*len(hand_position)//4):] # Look at last quarter of frames
                respKey = 0 if np.mean(eval_position) < 0 else 1


                # Display action feedback (hit vs miss)
                if respKey == 0: # If they chose left option
                    if stim1_left:
                        self.taskObj.leftTarget.image = self.taskObj.pract_stim1.hit_path if isHit else self.taskObj.pract_stim1.miss_path
                    else:
                        self.taskObj.leftTarget.image = self.taskObj.pract_stim2.hit_path if isHit else self.taskObj.pract_stim2.miss_path
                    leftTarget_rescaledSize = rescaleStim(self.taskObj.leftTarget, self.dispInfo.imageSize, self.dispInfo)
                    self.taskObj.leftTarget.setSize(leftTarget_rescaledSize)
                    # Dim out the unchosen stim
                    self.taskObj.rightStim.opacity = 0.5
                    # Show the left target and right stim images
                    self.taskObj.leftTarget.setAutoDraw(True)
                    self.taskObj.rightStim.setAutoDraw(True)
                elif respKey == 1:
                    if stim1_left:
                        self.taskObj.rightTarget.image = self.taskObj.pract_stim2.hit_path if isHit else self.taskObj.pract_stim2.miss_path
                    else:
                        self.taskObj.rightTarget.image = self.taskObj.pract_stim1.hit_path if isHit else self.taskObj.pract_stim1.miss_path
                    rightTarget_rescaledSize = rescaleStim(self.taskObj.rightTarget, self.dispInfo.imageSize, self.dispInfo)
                    self.taskObj.rightTarget.setSize(rightTarget_rescaledSize)
                    # Dim out the unchosen stim
                    self.taskObj.leftStim.opacity = 0.5
                    # Show the right target and left stim images
                    self.taskObj.rightTarget.setAutoDraw(True)
                    self.taskObj.leftStim.setAutoDraw(True)
                self.screen.flip()
                core.wait(3)
                # Reset the targets for the next trial
                self.taskObj.leftTarget.setAutoDraw(False)
                self.taskObj.rightTarget.setAutoDraw(False)
                # Reset the stims for the next trial
                self.taskObj.leftStim.opacity = self.taskObj.rightStim.opacity = 1
                self.taskObj.leftStim.setAutoDraw(False)
                self.taskObj.rightStim.setAutoDraw(False)
                # Show "not hit" outcome
                if not isHit:
                    self.taskObj.rewardOut.setText(f'Failed to land in the patch.')
                    self.taskObj.rewardOut.setAutoDraw(True)
                    self.screen.flip()
                    self.taskObj.rewardOut.setAutoDraw(False)
                    core.wait(3)
            else:
                # If no response was made on this trial
                self.taskObj.noRespErr.setAutoDraw(True)
                self.taskObj.screen.flip()
                self.taskObj.noRespErr.setAutoDraw(False)
                core.wait(3)

        # Show fixation between trials
        self.taskObj.trialFix.setAutoDraw(True)
        self.screen.flip()
        core.wait(1)
        self.taskObj.trialFix.setAutoDraw(False)
        self.screen.flip()

        return

    def moveRod(self, direction):
        response = event.clearEvents() # Allow keyboard responses
        # Initialize dyanmics and positions
        mX = 0 # Initialize hand position
        q1 = 0 # Initialize position of object
        q2 = 0 # Initialize velocity of object
        # Iterate over frames
        startTime = self.instructClock.getTime()
        while (self.instructClock.getTime() - startTime) <= self.maxRT:
            # Allow rod movement
            if self.expInfo.invertJoy:
                mX = np.round(self.taskObj.joy.getX() * -1,2)
            else: 
                mX = np.round(self.taskObj.joy.getX(),2)            
            if direction == 'left':
                mX = 0 if mX >= 0 else mX
            elif direction == 'right':
                mX = 0 if mX <= 0 else mX
            self.taskObj.handMass.setPos([mX, self.dispInfo.imagePosC[1]])
            # Compute position/velocity of object
            q1, q2 = springDynamics(self.taskInfo, self.dispInfo, q1, q2, mX)
            objectPos = [q1, self.dispInfo.objectPosC[1]]
            self.taskObj.objectMass.setPos(objectPos)
            # Draw masses
            self.taskObj.handMass.draw()
            self.taskObj.objectMass.draw()
            self.screen.flip()
            # Allow exiting (and saving) with Keyboard
            response = event.getKeys(keyList=['escape'])
            if 'escape' in response:
                # Save trial
                print('Exiting during instructions!')
                core.wait(1)
                self.taskObj.joy._device.close()
                self.taskObj.screen.close()
                core.quit()
        return

    def choosePatch(self, direction):
        # Randomize which image shown on the left/right
        if bool(np.random.binomial(1, 0.5)):
            self.taskObj.leftStim.image = self.taskObj.pract_stim1.path
            self.taskObj.rightStim.image = self.taskObj.pract_stim2.path
        else:
            self.taskObj.leftStim.image = self.taskObj.pract_stim2.path
            self.taskObj.rightStim.image = self.taskObj.pract_stim1.path
        # Rescale images
        leftStim_rescaledSize = rescaleStim(self.taskObj.leftStim, self.dispInfo.imageSize, self.dispInfo)
        rightStim_rescaledSize = rescaleStim(self.taskObj.rightStim, self.dispInfo.imageSize, self.dispInfo)
        self.taskObj.leftStim.setSize(leftStim_rescaledSize)
        self.taskObj.rightStim.setSize(rightStim_rescaledSize)

        # Initialize iteration over frames
        response = event.clearEvents() # Allow keyboard responses
        # Initialize dyanmics and positions
        mX = 0 # Initialize hand position
        q1 = 0 # Initialize position of object
        q2 = 0 # Initialize velocity of object
        # Initialize criteria for hits vs misses
        durFrames = []
        isHit = False

        # Flip screen and wait for response
        self.screen.flip()
        startTime = self.instructClock.getTime()


        # Iterate over frames
        while (self.instructClock.getTime() - startTime) <= self.maxRT:
            if self.expInfo.invertJoy:
                mX = np.round(self.taskObj.joy.getX() * -1,2)
            else: 
                mX = np.round(self.taskObj.joy.getX(),2)
            if direction == 'left':
                mX = 0 if mX >= 0 else mX
            elif direction == 'right':
                mX = 0 if mX <= 0 else mX
            self.taskObj.handMass.setPos([mX, self.dispInfo.imagePosC[1]])
            # Compute position/velocity of object
            q1, q2 = springDynamics(self.taskInfo, self.dispInfo, q1, q2, mX)
            objectPos = [q1, self.dispInfo.objectPosC[1]]
            self.taskObj.objectMass.setPos(objectPos)
            # Draw stims
            self.taskObj.leftStim.draw()
            self.taskObj.rightStim.draw()
            # Draw masses
            self.taskObj.handMass.draw()
            self.taskObj.objectMass.draw()
            self.screen.flip()
            # Evaluate if object is inside target at criterion
            if direction == 'left':
                if self.taskObj.leftStim.contains(objectPos):
                    durFrames.append(0)
                else:
                    durFrames = []
            elif direction == 'right':
                if self.taskObj.rightStim.contains(objectPos):
                    durFrames.append(1)
                else:
                    durFrames = []
            # Evaluate success -- reaches min frames inside a target
            if len(durFrames) > self.taskInfo.trialInfo.targetDur and durFrames.count(durFrames[0]) == len(durFrames):
                isHit = True
                break
            # Allow exiting (and saving) with Keyboard
            response = event.getKeys(keyList=['escape'])
            if 'escape' in response:
                # Save trial
                print('Exiting during instructions!')
                core.wait(1)
                self.taskObj.joy._device.close()
                self.taskObj.screen.close()
                core.quit()
        # Present error screen
        if not isHit:
            self.taskObj.rewardOut.setText(f'Failed to land in patch.\nPlease try again!')
            self.taskObj.rewardOut.setAutoDraw(True)
            self.screen.flip()
            core.wait(3)
            self.taskObj.rewardOut.setAutoDraw(False)

        return isHit
