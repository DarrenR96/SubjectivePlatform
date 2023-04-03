import numpy as np 
import cv2 
import subprocess 
import os 

def readYUV420(name: str, resolution: tuple, upsampleUV: bool = False):
    height = resolution[0]
    width = resolution[1]
    bytesY = int(height * width)
    bytesUV = int(bytesY/4)
    Y = []
    U = []
    V = []
    with open(name,"rb") as yuvFile:
        while (chunkBytes := yuvFile.read(bytesY + 2*bytesUV)):
            Y.append(np.reshape(np.frombuffer(chunkBytes, dtype=np.uint8, count=bytesY, offset = 0), (width, height)))
            U.append(np.reshape(np.frombuffer(chunkBytes, dtype=np.uint8, count=bytesUV, offset = bytesY),  (width//2, height//2)))
            V.append(np.reshape(np.frombuffer(chunkBytes, dtype=np.uint8, count=bytesUV, offset = bytesY + bytesUV), (width//2, height//2)))
    Y = np.stack(Y)
    U = np.stack(U)
    V = np.stack(V)
    if upsampleUV:
        U = U.repeat(2, axis=1).repeat(2, axis=2)
        V = V.repeat(2, axis=1).repeat(2, axis=2)
    return Y, U, V

def writeYUV420(name: str, Y, U, V, downsample=True):
    towrite = bytearray()
    if downsample:
        U = U[:, ::2, ::2]
        V = V[:, ::2, ::2]
    for i in range(Y.shape[0]):
        towrite.extend(Y[i].tobytes())
        towrite.extend(U[i].tobytes())
        towrite.extend(V[i].tobytes())
    with open(name, "wb") as destination:
        destination.write(towrite)

def YUV2RGB(yuv):
    m = np.array([[ 1.0, 1.0, 1.0],
                 [-0.000007154783816076815, -0.3441331386566162, 1.7720025777816772],
                 [ 1.4019975662231445, -0.7141380310058594 , 0.00001542569043522235] ])
    
    rgb = np.dot(yuv,m)
    rgb[:,:,:,0]-=179.45477266423404
    rgb[:,:,:,1]+=135.45870971679688
    rgb[:,:,:,2]-=226.8183044444304
    rgb = np.clip(rgb,0,255)
    return rgb

def RGB2YUV(rgb):
    m = np.array([[ 0.29900, -0.16874,  0.50000],
                 [0.58700, -0.33126, -0.41869],
                 [ 0.11400, 0.50000, -0.08131]])
    yuv = np.dot(rgb,m)
    yuv[:,:,:,1:]+=128.0
    yuv = np.clip(yuv,0,255)
    return yuv

def returnYUV(x, xres, returnRGB=False):
    Y,U,V = readYUV420(x, xres, True)
    YUV = np.stack([Y,U,V], -1)
    if returnRGB:
        return(YUV2RGB(YUV))
    else:
        return(YUV)

def runTerminalCmd(command):
    process = subprocess.run(command, shell=True)

def createVideo(A, B, Ares, Bres, frameLimit=64, maxWidth=1080, maxHeight=600, titleA='A', titleB='B', outputName='output', processing='processing/'):
    aRGB = returnYUV(A, Ares, returnRGB=True)
    bRGB = returnYUV(B, Bres, returnRGB=True)
    height, width = Ares[1], Bres[0]
    currentDims = 2*width

    spacing = maxWidth - currentDims
    aRGB, bRGB = aRGB[:frameLimit], bRGB[:frameLimit]
    canvasSize = (frameLimit, maxHeight, maxWidth, 3)
    canvas = np.zeros(canvasSize)
    y_offset = maxHeight - height

    # Rectangle coords
    _rectStart = (width + spacing//2, 0)
    _rectEnd = (width + spacing//2, maxHeight)

    # Title coords
    aOrig = (width//2 - 5,y_offset//2)
    bOrig = (width//2  + width + spacing - 5, y_offset//2)
    for _frame in range(frameLimit):
        # Write A
        canvas[_frame, y_offset:, :width] = aRGB[_frame]

        # Write B 
        canvas[_frame, y_offset:, -width:] = bRGB[_frame]

        # Separator
        canvas[_frame] = cv2.rectangle(canvas[_frame], _rectStart, _rectEnd, (255, 255, 255), 2)

        # Labels
        canvas[_frame] = cv2.putText(canvas[_frame], titleA, aOrig, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        canvas[_frame] = cv2.putText(canvas[_frame], titleB, bOrig, cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
    canvas = RGB2YUV(canvas)
    canvas = np.clip(np.rint(canvas),0,255).astype(np.uint8)
    writeYUV420(os.path.join(processing, 'output.yuv'), canvas[:,:,:,0],canvas[:,:,:,1],canvas[:,:,:,2])
    runTerminalCmd(f"ffmpeg -f rawvideo -pix_fmt yuv420p -s:v {maxWidth}x{maxHeight} -i {os.path.join(processing, 'output.yuv')} -c:v libx264 -crf 1 {os.path.join(processing, outputName+'.mp4')} -y")
    runTerminalCmd(f"rm {os.path.join(processing, 'output.yuv')}")