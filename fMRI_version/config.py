import pickle
import dill
from PIL import Image

class dict2class(object):
    """
    Converts dictionary into class object
    Dict key,value pairs become attributes
    """
    def __init__(self, dict):
        for key, val in dict.items():
            setattr(self, key, val)


class SaveObject:
    pass


def copyAttrib(objfrom, objto, names):
    for n in names:
        if hasattr(objfrom, n):
            v = getattr(objfrom, n)
            setattr(objto, n, v);


def save_obj(obj, name):
    with open(name + '.pkl', 'wb') as f:
        dill.dump(obj, f)


def load_obj(name):
    with open(name, 'rb') as f:
        return pickle.load(f)


def keyConfig():
    # input information - define keycodes (according to pyglet backend)
    pulseCode = '5'
    respLeft = '1'
    respRight = '4'
    instructPrev = '2'
    instructNext = '3'
    instructDone = 'space'
    instructAllow = [instructPrev, instructNext, 'escape']
    escapeKey = 'p'
    return dict(pulseCode=pulseCode,
                  respLeft=respLeft,
                  respRight=respRight,
                  instructPrev=instructPrev,
                  instructNext=instructNext,
                  instructDone=instructDone,
                  instructAllow=instructAllow,
                  escapeKey=escapeKey)

# Set up functions used here
def counterbalance(expInfo):
    if is_odd(expInfo['SubNo']):
        expInfo['sub_cb'] = 1
    elif not is_odd(expInfo['SubNo']):
        expInfo['sub_cb'] = 2
    else:
        print("Error! Did not specify subject number correctly!")
        core.wait(3)
        core.quit()
    return expInfo


def is_odd(num):
    return num % 2 != 0

def minmax(num):
    return 2*(num+1)/2 - 1


def pix2norm(sizePix, dispInfo):
    normX = (3.9*sizePix[0]/dispInfo.monitorX)*dispInfo.screenScaling
    normY = (3.9*sizePix[1]/dispInfo.monitorY)*dispInfo.screenScaling
    return normX,normY


def rescaleStim(imageObj, normScale, dispInfo):
    # get raw image dimensions
    with Image.open(imageObj.image) as im:
        imSize = im.size
    # convert to 'norm' scale
    normSize = pix2norm(imSize,dispInfo)
    # resize according to input
    rescaledSize = [normSize[0]*normScale,normSize[1]*normScale]
    return rescaledSize

def rescale(image, normScale):
    scale = normScale
    imageRatio = image.size[1] / image.size[0]
    rescaledSize = (scale, scale*imageRatio)
    return rescaledSize

def sendTrigger(taskInfo, trigger_label):    
    triggerID = getattr(taskInfo.triggerInfo, trigger_label)
    taskInfo.port.setData(triggerID)
    core.wait(0.05)
    taskInfo.port.setData(0)
