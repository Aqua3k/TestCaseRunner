import DebugLib as dl

fileName = ""
def SetFileName(s):
    global fileName
    fileName = s
def GetFileName():
    global fileName
    return fileName

fileContents = ""
def SetFileContents():
    global fileContents
    path = GetFileName()
    with open(path) as f:
        fileContents = [s.strip() for s in f.readlines()][::-1]

scores = []
def SetScoreSub(score):
    scores.append([GetFileName(), score])
def GetScore():
    return scores

