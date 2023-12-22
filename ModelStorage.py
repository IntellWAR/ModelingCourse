import csv
import simpy
import random

file = open("logfile.csv", "w")

env = simpy.Environment()

mapfile = 'Map.csv'
num_mails = 5 # Кол-во посылок


Time:int = 0
store = simpy.Store(env, capacity=num_mails)

def swapDict(key1, key2, dict):
    temp = dict[key1]
    dict[key1] = dict[key2]
    dict[key2] = temp


class Map():
    def __init__(self):
        self.data = 0
        self.input()


    def input(self):
        with open(mapfile, newline='') as csvfile:
            self.data = list(csv.reader(csvfile))
        #print(self.data)

        #print(data[0].index('Border of the Map -'))
        #print(' '.join(format(ord(data[0][6]), 'b') for x in data[0][6]))
        for i in range(self.data[0].index('Border of the Map -')+1):
            for row in self.data:
                del row[0]

        #Deleting empty cells
        for i in range (len(self.data)):
            self.data[i] = [x for x in self.data[i] if x]
        self.data = [x for x in self.data if x]
        #print(self.data)

        self.parsing()

    def parsing(self):

        # Walls (Unavailable cells)
        for i in range (len(self.data)):
            for j in range (len(self.data[i])):
                if self.data[i][j] == "X":
                    Walls['{}{}'.format(i,j)] = Wall(pos = [i,j])

        # Robots
        for i in range (len(self.data)):
            for j in range (len(self.data[i])):
                if self.data[i][j] == "R":
                    Robots['{:}{:}'.format(i, j)] = Robot(pos = [i, j])
                    MoveMap['{:}{:}'.format(i, j)] = Robot(pos = [i, j])
                    # print(Robots['{}{}'.format(i,j)])
                    # exec(f"Wall_ID{i}{j} = Wall({i,j})")
                    # print(f"Wall_ID{i}{j} = {eval(f'Wall_ID{i}{j}')}")

        # Sources
        for i in range (len(self.data)):
            for j in range (len(self.data[i])):
                if self.data[i][j] == "G":
                    Sources['{}{}'.format(i,j)] = Source(pos = [i,j])
                    MoveMap['{}{}'.format(i, j)] = EmptyCell(pos=[i, j])
                    #print(Sources['{}{}'.format(i, j)].retPos)
        # Destinationes
        num = 0
        for i in range (len(self.data)):
            for j in range (len(self.data[i])):
                if self.data[i][j] == "Y":
                    num += 1
                    Dests['{}{}'.format(i,j)] = Dest(pos = [i,j], num=num)
                    MoveMap['{}{}'.format(i, j)] = EmptyCell(pos=[i,j])

        # Empty Cells
        for i in range (len(self.data)):
            for j in range (len(self.data[i])):
                if self.data[i][j] == "-":
                    MoveMap['{}{}'.format(i, j)] = EmptyCell(pos=[i,j])



class EmptyCell():
    def __init__(self, pos):
        self.pos = pos
    def genRes(self):
        cell = simpy.Resource(env, capacity=1)
        return cell
    def type(self):
        return "EmptyCell"

class Wall():
    def __init__(self, pos):
        self.pos = pos
    def retPos(self):
        return self.pos

class Robot():
    def __init__(self, pos):
        self.Mail0 = Mail(0,0)
        self.pos = pos
        self.RID = f"{pos[0]}{pos[1]}"
        self.mail:Mail = Mail(0,0)
        self.dest = 0
    def retPos(self):
        return self.pos
    # def rotate(self):
    #     yield env.timeout(1)
    def getMail(self):
        global store
        self.mail = yield store.get()
        print('dest:',self.mail.retDest)
        print('Посылка №{} получена'.format(self.mail.retNum()))
        self.updDest()
        yield env.timeout(1)
    def updDest(self):
        # if self.mail == Mail(0,0):
        #     self.dest = 1
        # elif self.mail.retDest() != 0:
        #     self.dest = self.mail.retDest()
        # elif self.mail.retNum() != 0:
        #     self.dest = -1
        self.dest = self.mail.retDest()
        print("dest = ", self.dest)
    def retDest(self):
        return self.dest
    def putMail(self):
        print('Put',self.pos)
        i = self.pos[0]
        j = self.pos[1]
        if '{}{}'.format(i,j) in Dests:
            if Dests['{}{}'.format(i,j)].retNum() == self.dest:
                #yield env.timeout(1)
                self.mail = Mail(destination=-1, number=0)
                print('Посылка №{:0} доставлена в пункт №{:0}'.format(self.mail.retNum(), self.dest))
                if self.mail.retNum() == num_mails - 1:
                    return -1
                self.updDest()
        yield env.timeout(1)

    def move(self, direction):
        i = self.pos[0]
        j = self.pos[1]
        if direction == "up":
            print('вверх', self.pos)
            cell = MoveMap['{}{}'.format(i-1, j)]
            #with cell.request() as req:
                #yield req
            swapDict('{}{}'.format(i,j), '{}{}'.format(i-1,j), MoveMap)
            self.pos[0] -= 1
            #yield env.timeout(1)


        if direction == "down":
            print('вниз', self.pos)
            #cell = MoveMap['{}{}'.format(i+1,j)]
            #with cell.request() as req:
               # yield req
            swapDict('{}{}'.format(i, j), '{}{}'.format(i+1, j), MoveMap)
            self.pos[0] += 1
            #yield env.timeout(1)


        if direction == "right":
            print('вправо', self.pos)
            cell = MoveMap['{}{}'.format(i,j+1)]
            #with cell.request() as req:
                #yield req
            swapDict('{}{}'.format(i, j), '{}{}'.format(i, j+1), MoveMap)
            self.pos[1] += 1
            #yield env.timeout(1)

        if direction == "left":
            print('влево', self.pos)
            cell = MoveMap['{}{}'.format(i,j-1)]
            #with cell.request() as req:
                #yield req
            swapDict('{}{}'.format(i, j), '{}{}'.format(i, j-1), MoveMap)
            self.pos[1] -= 1
            #yield env.timeout(1)
    def type(self):
        return "Robot"

class Mail():
    def __init__(self, destination, number):
        self.destination = destination
        self.number = number
    def retNum(self):
        return self.number

    def retDest(self):
        return self.destination

class Dest():
    def __init__(self, pos, num):
        self.pos = pos
        self.num = num

    def retNum(self):
        return self.num

    def retPos(self):
        return self.pos

class Source():
    def __init__(self, pos):
        self.pos = pos
        global store

    def produce(self):
        for i in range(num_mails):  # Производим num_mails посылок
            mail = Mail(number=i+1, destination=1)  # Создание товара
            yield store.put(mail)  # Помещяем посылки в очередь на получение

    def retStore(self):
        return self.store

    def retPos(self):
        return self.pos

class Controller():
    def __init__(self, RID, pathC, pathF, pathB):
        self.RID = RID
        self.pathB = pathB
        self.pathF = pathF
        self.pathC = pathC
        self.dest = 0
        self.pos = (0,0)
        self.action = env.process(self.move())
    def updRobots(self):
        self.dest = Robots[self.RID].retDest()

    def move(self):
        global Time
        while True:
            yield env.process(Sources['74'].produce())
            a = Robots[self.RID].retPos()
            # print('T',Time)
            # print('RID',self.RID)
            # print('pos',self.pos)
            self.updRobots()
            print(self.dest)
            if self.dest == -1:
                print('назад', self.dest)
                yield env.process(self.backward())
                yield env.process(Robots[self.RID].getMail())
                file.write(f'get Mail:{2};time:{env.now};RID:{self.RID};pos:{Robots[self.RID].retPos()}\n')
            elif self.dest == 0:
                print('Начало движения')
                yield env.process(self.beg())
                yield env.process(Robots[self.RID].getMail())
            elif self.dest == 1:
                print('вперёд',self.dest)
                yield env.process(self.forward())
                file.write(f'put Mail:{3};time:{env.now};RID:{self.RID};pos:{Robots[self.RID].retPos()}\n')
                if Robots[self.RID].putMail() == -1:
                    print('Доставка завершена!')
                return 0

    def beg(self):
        for nextPos in pathC:
            Robots[self.RID].move(nextPos)
            yield env.timeout(1)
            file.write(f'move:{1};time:{env.now};RID:{self.RID};pos:{Robots[self.RID].retPos()}\n')
    def forward(self):
        for nextPos in pathF:
            Robots[self.RID].move(nextPos)
            yield env.timeout(1)
            file.write(f'move:{1};time:{env.now};RID:{self.RID};pos:{Robots[self.RID].retPos()}\n')
    def backward(self):
        for nextPos in pathB:
            Robots[self.RID].move(nextPos)
            yield env.timeout(1)
            file.write(f'move:{1};time:{env.now};RID:{self.RID};pos:{Robots[self.RID].retPos()}\n')


Walls = {}
Robots = {}
Sources = {}
Dests = {}
MoveMap = {}    # Всё, кроме стен и вместо источника посылок и места назначения - пустые клетки

Map = Map()     # Загрузка карты и парсинг по классам

# print("Walls:")
# print(Walls)
# print("Robots:")
# print(Robots)
# print("Sources:")
# print(Sources)
# print("Dests:")
# print(Dests)

pathF = ['left','left','left','left', 'up', 'up', 'up', 'up', 'up', 'up', 'up','right']
pathC = ['down', 'right', 'right']
pathB = ['left','left','left','left', 'down', 'down', 'down', 'down', 'down', 'down', 'down','right']
RID = '{}{}'.format(6, 2)
#print(Robots[RID].retPos())
Con = Controller(RID, pathC = pathC, pathB = pathB, pathF = pathF)
env.run()
#print(Robots[RID].retPos())