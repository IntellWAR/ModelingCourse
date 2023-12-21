import csv
mapfile = 'Map.csv'

def mapInput(mapfile):
    with open(mapfile, newline='') as csvfile:
        data = list(csv.reader(csvfile))
    print(data)
    #print(data[0].index('Border of the Map -'))
    #print(' '.join(format(ord(data[0][6]), 'b') for x in data[0][6]))
    for i in range(data[0].index('Border of the Map -')+1):
        for row in data:
            del row[0]

    #Delete empty cells
    for i in range (len(data)):
        data[i] = [x for x in data[i] if x]
    data = [x for x in data if x]

    print(data)

mapInput(mapfile)