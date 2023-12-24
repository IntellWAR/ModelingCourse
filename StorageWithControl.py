mapfile = 'Map.csv'
num_mails = 100000  # Кол-во посылок
expec = [0.8, 0.15, 0.05]  # Распределение весов

import csv
import simpy
import random
import time

start_time = time.time()

file = open("logfile.csv", "w")
file.write(f'actions:1-move,2-getMail,3-putMail\n')
file.write(f'action;time;RID;pos_i;pos_j\n')
env = simpy.Environment()

Time: int = 0
store = simpy.Store(env, capacity=num_mails)

Walls = {}
Robots = {}
Sources = {}  # Конвейер
Dests = {}  # Корзины
MoveMap = {}  # Доступная территория для передвижения
PherMaps = {}
is_move = 1
is_block = 0
k = 0  # Global syka counter


# def swapDict(key1, key2, dict):
#     temp = dict[key1]
#     dict[key1] = dict[key2]
#     dict[key2] = temp


class Map():
    def __init__(self):
        self.data = 0
        self.input()

    def input(self):
        with open(mapfile, newline='') as csvfile:
            self.data = list(csv.reader(csvfile))
        # print(self.data)

        # print(data[0].index('Border of the Map -'))
        # print(' '.join(format(ord(data[0][6]), 'b') for x in data[0][6]))
        for i in range(self.data[0].index('Border of the Map -') + 1):
            for row in self.data:
                del row[0]

        # Deleting empty cells
        for i in range(len(self.data)):
            self.data[i] = [x for x in self.data[i] if x]
        self.data = [x for x in self.data if x]
        # print(self.data)

        self.parsing()

    def parsing(self):

        # Walls (Unavailable cells)
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                if self.data[i][j] == "X":
                    Walls['{}{}'.format(i, j)] = Wall(pos=[i, j])

        # Robots
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                if self.data[i][j] == "R":
                    Robots['{}{}'.format(i, j)] = Robot(pos=[i, j])
                    MoveMap['{}{}'.format(i, j)] = EmptyCell(pos=[i, j], robot=True)
                    # print(Robots['{}{}'.format(i,j)])
                    # exec(f"Wall_ID{i}{j} = Wall({i,j})")
                    # print(f"Wall_ID{i}{j} = {eval(f'Wall_ID{i}{j}')}")

        # Sources
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                if self.data[i][j] == "G":
                    Sources['{}{}'.format(i, j)] = Source(pos=[i, j])
                    MoveMap['{}{}'.format(i, j)] = EmptyCell(pos=[i, j])

        # Destinationes
        num = 0
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                if self.data[i][j] == "Y":
                    num += 1
                    Dests['{}{}'.format(i, j)] = Dest(pos=[i, j], num=num)
                    MoveMap['{}{}'.format(i, j)] = EmptyCell(pos=[i, j])

        # Empty Cells
        for i in range(len(self.data)):
            for j in range(len(self.data[i])):
                if self.data[i][j] == "-":
                    MoveMap['{}{}'.format(i, j)] = EmptyCell(pos=[i, j])


class EmptyCell():
    def __init__(self, pos, robot=False):
        self.pos = pos
        self.cell = simpy.Resource(env, capacity=1)
        self.robot = robot

    def getRes(self):
        return self.cell

    def isEmpty(self):
        return not self.robot

    def occupy(self):
        self.robot = True

    def liberate(self):
        self.robot = False

    # def genRes(self):
    #     self.cell = simpy.Resource(env, capacity=1)

    def retType(self):
        return "EmptyCell"

    def retPos(self):
        return self.pos


class Wall():
    def __init__(self, pos):
        self.pos = pos

    def retPos(self):
        return self.pos


class PheromoneCell():
    def __init__(self, pos, up_pher=0.0, down_pher=0.0, left_pher=0.0, right_pher=0.0, holding_pher=0.0):
        self.pos = pos
        self.up_pher = up_pher
        self.down_pher = down_pher
        self.left_pher = left_pher
        self.right_pher = right_pher
        self.holding_pher = holding_pher

    def __str__(self):
        return f'up_pher:{self.up_pher};down_pher: {self.down_pher};left_pher: {self.left_pher};right_pher: {self.right_pher}'

    def addPher(self, direction, correction_pher):
        if direction == 'up':
            self.up_pher += correction_pher
        if direction == 'down':
            self.down_pher += correction_pher
        if direction == 'left':
            self.left_pher += correction_pher
        if direction == 'right':
            self.right_pher += correction_pher
        if direction == 'hold':
            self.holding_pher += correction_pher

    def del_pheromon(self, coef: float = 0.7):
        if self.up_pher:
            self.up_pher *= coef
        if self.down_pher:
            self.down_pher *= coef
        if self.left_pher:
            self.left_pher *= coef
        if self.right_pher:
            self.right_pher *= coef
        if self.holding_pher:
            self.holding_pher *= coef

    def chooseDirection(self, ignore_direction=[]):
        dir = []
        weights = []
        if 'up' not in ignore_direction:
            dir.append('up')
            weights.append(self.up_pher)
        if 'down' not in ignore_direction:
            dir.append('down')
            weights.append(self.down_pher)
        if 'left' not in ignore_direction:
            dir.append('left')
            weights.append(self.left_pher)
        if 'right' not in ignore_direction:
            dir.append('right')
            weights.append(self.right_pher)
        dir.append('hold')
        weights.append(self.holding_pher)
        a = random.choices(dir, weights=weights)[0]
        return random.choices(dir, weights=weights)[0]


class PherMap():
    def __init__(self):
        self.PheromoneMap = {}
        global MoveMap

    def create(self, map=MoveMap):
        for value in map.values():
            pos = value.retPos()
            i = pos[0]
            j = pos[1]
            self.PheromoneMap['{}{}'.format(i, j)] = PheromoneCell(pos=[i, j])
            if '{}{}'.format(i - 1, j) in map:
                self.PheromoneMap['{}{}'.format(i, j)].up_pher = 1
            if '{}{}'.format(i + 1, j) in map:
                self.PheromoneMap['{}{}'.format(i, j)].down_pher = 1
            if '{}{}'.format(i, j - 1) in map:
                self.PheromoneMap['{}{}'.format(i, j)].left_pher = 1
            if '{}{}'.format(i, j + 1) in map:
                self.PheromoneMap['{}{}'.format(i, j)].right_pher = 1
            self.PheromoneMap['{}{}'.format(i, j)].holding_pher = 0.9

    def decreaseAll(self):
        for value in self.PheromoneMap.values():
            value.del_pheromon()

    def retPheromoneCell(self, pos):
        i = pos[0]
        j = pos[1]
        return self.PheromoneMap['{}{}'.format(i, j)]


class Robot():
    def __init__(self, pos):
        self.pos = pos
        self.RID = '{}{}'.format(pos[0], pos[1])
        self.mail: Mail = Mail(destination=-1, number=0)
        self.dest = None
        self.saved_path = []

    def retPos(self):
        return self.pos

    # def rotate(self):
    #     yield env.timeout(1)
    def getMail(self):
        global store
        global is_move
        # yield env.timeout(1)
        i = self.pos[0]
        j = self.pos[1]
        if '{}{}'.format(i, j) in Sources:
            is_move = 0
            self.mail = yield store.get()
            if self.mail.retNum() % 100 == 0:
                print('Посылка №{} получена'.format(self.mail.retNum()))
            file.write(f'{2};{env.now};{self.RID};{self.pos[0]};{self.pos[1]}\n')
            self.updWeights(PherMap=PherMaps[f'{self.dest}'], pos=self.pos, saved_path=self.saved_path)
            self.saved_path = []
            self.updDest()
            yield env.timeout(1)
        else:
            is_move = 1

    def updWeights(self, saved_path, pos, PherMap):
        i = pos[0]
        j = pos[1]
        PherMap.decreaseAll()
        for direction in saved_path[::-1]:
            if direction == 'hold':
                continue
            elif direction == 'up':
                i += 1
                PherMap.retPheromoneCell([i, j]).addPher(direction, 1 / len(saved_path))
            elif direction == 'down':
                i -= 1
                PherMap.retPheromoneCell([i, j]).addPher(direction, 1 / len(saved_path))
            elif direction == 'left':
                j += 1
                PherMap.retPheromoneCell([i, j]).addPher(direction, 1 / len(saved_path))
            elif direction == 'right':
                j -= 1
                PherMap.retPheromoneCell([i, j]).addPher(direction, 1 / len(saved_path))

    def updDest(self):
        self.dest = self.mail.retDest()

    def retDest(self):
        self.updDest()
        return self.dest

    def putMail(self):
        # yield env.timeout(1)
        global is_move
        global k
        i = self.pos[0]
        j = self.pos[1]
        if '{}{}'.format(i, j) in Dests:
            if Dests['{}{}'.format(i, j)].retNum() == self.dest:
                is_move = 0
                k += 1
                if self.mail.retNum() % 100 == 0:
                    print('Посылка №{} доставлена в пункт №{}'.format(self.mail.retNum(), self.dest))
                    if self.mail.retNum() == num_mails:
                        end_time = time.time()
                        print('Доставка завершена,\n модельное время = {},\n реальное время = {:.2f}c'.format(env.now,
                                                                                                              end_time - start_time))
                self.mail = Mail(destination=-1, number=0)
                file.write(f'{3};{env.now};{self.RID};{self.pos[0]};{self.pos[1]}\n')
                self.updWeights(PherMap=PherMaps[f'{self.dest}'], pos=self.pos, saved_path=self.saved_path)
                self.saved_path = []
                self.updDest()

                yield env.timeout(1)
            else:
                is_move = 1
        else:
            is_move = 1

    def move(self, direction):
        global is_block
        i = self.pos[0]
        j = self.pos[1]
        if direction == "up":
            if MoveMap['{}{}'.format(i - 1, j)].retType() == "Robot":
                is_block = 1
                return 0
            is_block = 0
            self.saved_path.append("up")
            cell = MoveMap['{}{}'.format(i - 1, j)].getRes()
            with cell.request() as req:
                yield req
            MoveMap['{}{}'.format(i - 1, j)].occupy()
            MoveMap['{}{}'.format(i, j)].liberate()
            self.pos[0] -= 1
            # print('вверх', self.pos)

        if direction == "down":
            if MoveMap['{}{}'.format(i + 1, j)].retType() == "Robot":
                is_block = 1
                return 0
            is_block = 0
            self.saved_path.append("down")
            cell = MoveMap['{}{}'.format(i + 1, j)].getRes()
            with cell.request() as req:
                yield req
            MoveMap['{}{}'.format(i + 1, j)].occupy()
            MoveMap['{}{}'.format(i, j)].liberate()
            self.pos[0] += 1
            # print('вниз', self.pos)

        if direction == "right":
            if MoveMap['{}{}'.format(i, j + 1)].retType() == "Robot":
                is_block = 1
                return 0
            is_block = 0
            self.saved_path.append("right")
            cell = MoveMap['{}{}'.format(i, j + 1)].getRes()
            with cell.request() as req:
                yield req
            MoveMap['{}{}'.format(i, j + 1)].occupy()
            MoveMap['{}{}'.format(i, j)].liberate()
            self.pos[1] += 1
            # print('вправо', self.pos)

        if direction == "left":
            if MoveMap['{}{}'.format(i, j - 1)].retType() == "Robot":
                is_block = 1
                print(is_block)
                return 0
            is_block = 0
            self.saved_path.append("left")
            cell = MoveMap['{}{}'.format(i, j - 1)].getRes()
            with cell.request() as req:
                yield req
            MoveMap['{}{}'.format(i, j - 1)].occupy()
            MoveMap['{}{}'.format(i, j)].liberate()
            self.pos[1] -= 1
            # print('влево', self.pos)

        if direction == "hold":
            self.saved_path.append("hold")
            # print('стоять', self.pos)

    def retType(self):
        return "Robot"

    def retPos(self):
        return self.pos


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

    def produce(self, k, values):
        mail = Mail(number=k + 1, destination=random.choices(values, expec)[0])  # Создание товара
        yield store.put(mail)  # Помещяем посылки в очередь на получение

    def retPos(self):
        return self.pos


def act():
    global PherMaps
    for dest in range(len(Dests)):
        PherMaps[f'{dest + 1}'] = PherMap()
        PherMaps[f'{dest + 1}'].create()
        # for key, value in PherMaps[f'{dest}'].PheromoneMap.items():
        #     print(key, value)

    PherMaps[f'{-1}'] = PherMap()
    PherMaps[f'{-1}'].create()  # Обратный путь

    dest_nums = []
    for value in Dests.values():
        dest_nums.append(value.retNum())
    k = 0
    for k in range(num_mails):
        yield env.process(Sources['74'].produce(k, dest_nums))

    Con = {}
    for key in Robots.keys():
        Con[key] = Controller(RID=key)


class Controller():
    def __init__(self, RID):
        self.RID = RID
        self.dest = None
        self.pos = None
        self.action = env.process(self.move())

    def updRobots(self):
        self.dest = Robots[self.RID].retDest()

    def move(self):
        global Time
        global k
        while k < num_mails:
            self.updRobots()
            self.pos = Robots[self.RID].retPos()
            if self.dest == -1:
                # print('назад')
                yield env.process(Robots[self.RID].getMail())
                if is_move == 1:
                    ignore_dir = []
                    while True:
                        dir = PherMaps[f'{-1}'].PheromoneMap['{}{}'.format(self.pos[0], self.pos[1])].chooseDirection(
                            ignore_dir)
                        yield env.process(Robots[self.RID].move(dir))
                        if is_block == 1:
                            ignore_dir.append(dir)
                        else:
                            file.write(f'{1};{env.now};{self.RID};{self.pos[0]};{self.pos[1]}\n')
                            yield env.timeout(1)
                            break

            else:
                # print('вперёд')
                yield env.process(Robots[self.RID].putMail())
                if is_move == 1:
                    ignore_dir = []
                    while True:
                        dir = PherMaps[f"{self.dest}"].PheromoneMap[
                            '{}{}'.format(self.pos[0], self.pos[1])].chooseDirection(ignore_dir)
                        yield env.process(Robots[self.RID].move(dir))
                        if is_block == 1:
                            ignore_dir.append(dir)
                        else:
                            file.write(f'{1};{env.now};{self.RID};{self.pos[0]};{self.pos[1]}\n')
                            yield env.timeout(1)
                            break


Map = Map()  # Загрузка карты и парсинг по классам

# print("Walls:")
# print(Walls)
# print("Robots:")
# print(Robots)
# print("Sources:")
# print(Sources)
# print("Dests:")
# print(Dests)


env.process(act())
env.run()
