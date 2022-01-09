import sys
from collections import deque, defaultdict
import heapq
import copy

"""
テスト用の適当なプログラム(過去のAHCのやつ)
"""
######################################################################

DAY_MAX = 2000
SKILL_INITIAL_VAL = 0.01
INF = 10**18
SKILL_MAX = 20

######################################################################

DEBUG = 0
if __name__ != "__main__":
    DEBUG = 1
    import DebugLib as dl

def MyInput():
    global DEBUG
    if DEBUG: return dl.DebugInput()
    else: return input()


def MyPrint(*arg, **keys):
    global DEBUG
    if DEBUG: return dl.DebugPrint(*arg, **keys)
    else: return print(*arg, **keys)

######################################################################

def L2Norm(ar):
    r = 0
    for x in ar:
        r += x**2
    return pow(r, 0.5)

######################################################################
class Game:
    global DAY_MAX, SKILL_INITIAL_VAL, SKILL_MAX
    def __init__(self,n,m,k,r,d,uv):
        Game.day = 0
        Game.taskNow = [-1]*(m+1)
        Game.taskDay = [-1]*(m+1)
        Game.limit = [0]*(n+1)
        Game.graph = [[] for i in range(n+1)]
        Game.graphRev = [[] for i in range(n+1)]
        Game.q = []
        heapq.heapify(Game.q)
        Game.finishedTask = 0
        Game.dist = [0]*(n+1)
        Game.atLeast = [[SKILL_INITIAL_VAL for i in range(k)] for j in range(m+1)]
        Game.atMost = [[SKILL_MAX*2 for i in range(k)] for j in range(m+1)]
        v = SKILL_INITIAL_VAL + pow(SKILL_MAX*2 - SKILL_INITIAL_VAL, 0.5)
        Game.expectedVector = [[v for i in range(k)] for j in range(m+1)]
        Game.bonus = [0 for j in range(m+1)]
        
        Game.notUpdateFlg = [False]*(m+1)

        #(task番号, かかった日数)の形で2次元配列で管理する
        Game.taskToPerson = [[] for i in range(m+1)] 
        
        for u,v in uv[1:]:
            Game.graph[u].append(v)
            Game.graphRev[v].append(u)
        for i in range(1,n+1):
            if Game.limit[i] == len(Game.graphRev[i]):
                heapq.heappush(Game.q, [-Game.dist[i], i])
        
        rv = (4/2000)*(r-1000)
        for i in range(n,0,-1):
            for y in Game.graphRev[i]:
                dis = L2Norm(d[y]) + len(Game.graph[i])*rv
                Game.dist[y] = max(Game.dist[y], Game.dist[i] + dis)

    #1日経過(シミュレーション用)
    def PassDay(self): Game.day += 1
    
    #現在の日数を返す
    def GetDay(self): return Game.day
    
    #personにtaskNum番目のTaskを任せる
    def AllocTask(self, person, taskNum):
        assert Game.taskNow[person] == -1, "Task allocate error"
        Game.taskNow[person] = taskNum #人物aにタスクbを割り振る
        Game.taskDay[person] = Game.day

    #personの担当していたTaskが終わる
    def ReturnPerson(self, person):
        assert Game.taskNow[person] != -1, "Task return error"
        d = Game.day - Game.taskDay[person]
        Game.taskToPerson[person].append([Game.taskNow[person], d + 1])
        for y in Game.graph[Game.taskNow[person]]:
            Game.limit[y] += 1
            if Game.limit[y] == len(Game.graphRev[y]):
                heapq.heappush(Game.q, [-Game.dist[y], y])
        Game.taskNow[person] = -1
        Game.finishedTask += 1
        

    #人物xがタスクを受け持てる状態かどうかを返す
    def CanAllocTask(self, x):
        if Game.taskNow[x] == -1: return True
        else: return False
    
    #タスクを1つ獲得する(1つも獲得できない時は-1)
    def GetTask(self):
        if Game.q: return heapq.heappop(Game.q)[1]
        else: return -1

    #personの現在のスキル予想値(vector)を返す
    def GetExpectedSkill(self, person):
        if Game.notUpdateFlg[person]: return [SKILL_INITIAL_VAL]*k
        else: return Game.expectedVector[person]

    def GetTaskData(self, person):
        return copy.deepcopy( Game.taskToPerson[person] )

    #personの能力予想値をセットする
    def SetSkills(self, person, vector):
        Game.expectedVector[person] = vector

######################################################################

class MyJudge:
    global DAY_MAX
    def __init__(self,n,m,k,r):
        MyJudge.s = [[None]] + [[None] + list(map(int, MyInput().split())) for i in range(m)]
        MyJudge.t = [[None]] +[[None] + list(map(int, MyInput().split())) for i in range(n)]
        MyJudge.dayRet = [[] for i in range(DAY_MAX+1)]
        MyJudge.nVal = n

    def RecieveQuery(self, ar):
        ar = ar[1:]
        ar = ar[::-1]
        while ar:
            a = ar.pop()
            b = ar.pop()
            d = MyJudge.t[b][a]
            if Game.day + d <= DAY_MAX: MyJudge.dayRet[Game.day + d - 1].append(a)

    def ReturnList(self):
        if Game.day >= DAY_MAX: return [-1]
        if Game.finishedTask == MyJudge.nVal: return [-1]
        return [len(MyJudge.dayRet[Game.day])] + MyJudge.dayRet[Game.day]

######################################################################

def Input():
    n,m,k,r = map(int, MyInput().split())
    d = [[None]] + [list(map(int, MyInput().split())) for i in range(n)]
    uv = [[None]] +[list(map(int, MyInput().split())) for i in range(r)]
    return n,m,k,r,d,uv

n,m,k,r,d,uv = Input()
game = Game(n,m,k,r,d,uv)
if DEBUG:
    judge = MyJudge(n,m,k,r)

# 答えを出力
def Query(ar):
    if not DEBUG:
        print(len(ar)//2, *ar)
        sys.stdout.flush()
        ret = sys.stdin.readline().strip().split()
        ret = list(map(int, ret))
    else:
        ar = [len(ar)//2] + ar
        MyPrint(*ar)
        judge.RecieveQuery(ar)
        ret = judge.ReturnList()
    return ret

def CalcSkill(person):
    skill = [0]*k
    for i in range(k):
        l,h = game.atLeast[person][i], game.atMost[person][i]
        if h < l: h = l
        v = l + pow(h-l, 0.5)
        v = round(v, 3) + game.bonus[person]
        v = max(game.atLeast[person][i], v)
        v = min(game.atMost[person][i], v)
        skill[i] = v
    return skill

def CalcDay(taskNum, person):
    global k, INF
    ret = -INF
    expectedSkill = game.GetExpectedSkill(person)
    taskVec = d[taskNum]
    for i in range(k):
        v = max(0, taskVec[i] - expectedSkill[i])
        ret = max(ret, v)
    return ret

#Taskを割り振る
def Task():
    global m, k, INF
    c = 0
    for i in range(1,m+1):
        if game.CanAllocTask(i): c += 1
    tasks = []
    for i in range(c):
        taskNum = game.GetTask()
        if taskNum == -1: break
        tasks.append(taskNum)

    ar = []
    for taskNum in tasks:
        shortest = INF
        person = -1
        for i in range(1,m+1):
            if not game.CanAllocTask(i): continue
            ret = CalcDay(taskNum, i)
            if ret < shortest:
                shortest = ret
                person = i
        ar.append(person)
        ar.append(taskNum)
        game.AllocTask(person, taskNum)
    return ar

#人物xの能力を見積もる
def EstimateSkills(person):
    global k, SKILL_MAX

    if game.notUpdateFlg[person]: return

    taskNum, days = game.GetTaskData(person)[-1]
    taskVec = d[taskNum]

    expected = CalcDay(taskNum, person)
    game.bonus[person] = (expected- days)/3

    for i in range(k):
        dd = max(0, taskVec[i] - days)
        game.atLeast[person][i] = max(game.atLeast[person][i], dd)
        if taskVec[i] - days < 0:
            game.atMost[person][i] = min(game.atMost[person][i], SKILL_MAX + taskVec[i])
    
    skill = CalcSkill(person)
    game.SetSkills(person, skill)
    if DEBUG:
        ar = [person] + skill
        MyPrint("#s", *ar)

def ReturnTaskAll(ar):
    ar = ar[1:]
    for x in ar:
        game.ReturnPerson(x)
        EstimateSkills(x)
        
def SkillUpdate():
    global m, SKILL_INITIAL_VAL, k, DEBUG
    for i in range(1, m+1):
        skill = copy.deepcopy(game.atLeast[i])
        if skill.count(SKILL_INITIAL_VAL) >= 7:
            Game.notUpdateFlg[i] = True
            game.SetSkills(i, [SKILL_INITIAL_VAL]*k)

######################################################################

def Simulate():
    while 1:
        #タスクを割り振る
        ar = Task()
        #タスクが帰ってくる
        ar = Query(ar)
        if ar[0] == -1:
            break
        ReturnTaskAll(ar)
        game.PassDay()

Simulate()
score = max(n + 2000 - game.GetDay(), Game.finishedTask)
