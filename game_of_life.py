import itertools as itr

def make_map(width, height, cell_list):
    map = [[0]*height for _ in range(width)] # List of columns (lists of cell statuses in that column o>
    for cell in cell_list:
        if len(cell) == 2:
            map[cell[0]-1][cell[1]-1] = 1
        elif len(cell) == 4:
            x1=cell[0]
            y1=cell[1]
            x2=cell[2]
            y2=cell[3]

            for x in range(x1-1, x2):
                for y in range(y1-1, y2):
                    map[x][y] = 1

    return map


def next_generation(map):
    to_resurrect = []
    to_kill = []

    # Calculate which cells should be killed and which resurrected
    for x in range(len(map)):
        for y in range(len(map[x])):
            ncount = neighbour_count(map, (x,y))

            if ncount < 2:
                to_kill.append((x,y))
            elif ncount == 3:
                to_resurrect.append((x,y))
            elif ncount > 3:
                to_kill.append((x,y))

    for cell in to_kill:
        map[cell[0]][cell[1]] = 0

    for cell in to_resurrect:
        map[cell[0]][cell[1]] = 1


def neighbour_count(map, pos):
    vectadd = lambda x, y: [x[i] + y[i] for i in range(min(len(x), len(y)))]

    neighbour_vects = itr.product((-1, 0, 1), repeat=2)

    ncount = 0
    for vect in neighbour_vects:
        if vect == (0,0): continue
        npos = wrap_coords(vectadd(pos, vect), (len(map), len(map[0])))

        ncount += map[npos[0]][npos[1]]

    return(ncount)


def wrap_coords(pos, mapsize):
    return [pos[i] % mapsize[i] for i in range(len(pos))]
