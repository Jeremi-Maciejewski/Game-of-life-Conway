import itertools as itr

# Constant with all 1 cell offsets from a position
neighbour_vects = list(itr.product((-1, 0, 1), repeat=2))
neighbour_vects.remove((0,0))

vectadd = lambda x, y: [x[i] + y[i] for i in range(min(len(x), len(y)))]

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

    return map, {}


def next_generation(map, outsiders, boundary_rule):
    global neighbour_vects

    to_resurrect = []
    to_kill = []
    loop = False
    if boundary_rule == "looped":
        loop = True

    # Calculate which cells should be killed and which resurrected
    for x in range(len(map)):
        for y in range(len(map[x])):
            ncount = neighbour_count(map, outsiders, (x,y), loop=loop)

            if ncount < 2:
                to_kill.append((x,y))
            elif ncount == 3:
                to_resurrect.append((x,y))
            elif ncount > 3:
                to_kill.append((x,y))


    # If we're not looping, we also need to evaluate outsiders, i.e cells which escaped the map
    escaped = 0
    outsiders_new = {}
    if not loop:
        potential_outsiders = {}

        # Check neighbours of cells right on the boundary
        # top and bottom
        for x in range(len(map)):
            for y in [-1, len(map[x])]:
                if (x, y) in outsiders: continue

                ncount = neighbour_count(map, outsiders, (x,y), loop, False)
                if ncount > 0:
                    potential_outsiders[(x, y)] = (ncount, 1)

        # left and right
        for x in [-1, len(map)]:
            for y in range(len(map[0])):
                if (x, y) in outsiders: continue

                ncount = neighbour_count(map, outsiders, (x,y), loop, False)
                if ncount > 0:
                    potential_outsiders[(x, y)] = (ncount, 1)

        for outsider in outsiders:
            stage = float("Inf")
            ncount = neighbour_count(map, outsiders, outsider, loop, False) # Neighbours within map
            if ncount > 0:
                stage = 1

            neighbours = [vectadd(outsider, v) for v in neighbour_vects]
            for neighbour in neighbours:
                neighbour = tuple(neighbour)
                if is_valid_pos(neighbour, (len(map), len(map[0]))):
                    continue
                elif neighbour in outsiders:
                    ncount += 1
                    stage = min(stage, outsiders[neighbour]+1)
                else:
                    nghbr = potential_outsiders.get(neighbour, (0, float("Inf")))
                    potential_outsiders[neighbour] = (nghbr[0]+1, min(nghbr[1], outsiders[outsider]+1))

            if ncount in [2, 3]:
                if stage > 15:
                    escaped += 1
                else:
                    outsiders_new[outsider] = stage

        for poutsider in potential_outsiders:
            if potential_outsiders[poutsider][0] == 3:
                if potential_outsiders[poutsider][1] > 15:
                    escaped += 1
                else:
                    outsiders_new[poutsider] = potential_outsiders[poutsider][1]


    # Update the map
    for cell in to_kill:
        map[cell[0]][cell[1]] = 0
    for cell in to_resurrect:
        map[cell[0]][cell[1]] = 1

    # Update outsiders
    outsiders.clear()
    outsiders.update(outsiders_new)
    return escaped


def is_valid_pos(pos, mapsize):
    for i in range(len(pos)):
        if pos[i] < 0 or pos[i] >= mapsize[i]:
            return False

    return True


def neighbour_count(map, outsiders, pos, loop=False, include_outsiders=True):
    global neighbour_vects

    mapsize = (len(map), len(map[0]))

    ncount = 0
    for vect in neighbour_vects:
        npos = vectadd(pos, vect) # Neighbour position
        if loop: # If we're looping the map boundaries, wrap the coords
            npos = wrap_coords(npos, mapsize)

        elif not is_valid_pos(npos, mapsize): # This position is outside map
            if include_outsiders and tuple(npos) in outsiders: # Check if there is an outsider on that position
                ncount += 1
            continue

        ncount += map[npos[0]][npos[1]]

    return(ncount)


def wrap_coords(pos, mapsize):
    return [pos[i] % mapsize[i] for i in range(len(pos))]
