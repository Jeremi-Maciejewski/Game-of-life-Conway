import itertools as itr
import random

# Constant with all 1 cell offsets from a position
neighbour_vects = list(itr.product((-1, 0, 1), repeat=2))
neighbour_vects.remove((0,0))

# Lambda to add vectors positionally
vectadd = lambda x, y: [x[i] + y[i] for i in range(min(len(x), len(y)))]


# Create the map for Game of Life algorithm
# Arguments:
#   width - (int) Width of the map in cells
#   height - (int) Height of the map in cells
#   cell_list - (list[list[int,],]) A list defining which cells should initially be alive, in following format:
#                   Every entry is a list of integers, of length:
#                       2 - numbers specify x and y coordinates (in cells) of a single cell
#                       4 - numbers specify coordinate of 2 corners of a rectangle of cells, like: x1, y1, x2, y2
#   graphics_data - (conway_graphics.ConwayGraphics) (optional) Object storing graphics data. If specified, the
#                       value 'spritemap' in object will also be updated, choosing random sprites
#                       (out of available in 'sprites') for the cells.
#
# returns: tuple(list, dict) where list is the map (list of map columns) and dict is a (for now empty)
#           record of outsiders (escaped cells)
def make_map(width, height, cell_list, graphics_data=None):
    map = [[0]*height for _ in range(width)] # List of columns (lists of cell statuses in that column of the map)

    # Apply cell_list entries one by one
    for cell in cell_list:
        if len(cell) == 2: # Format with 2 ints
            map[cell[0]-1][cell[1]-1] = 1 # Set the cell to alive

            if graphics_data is not None: # Choose random sprite for that cell
                graphics_data["spritemap"][cell[0]-1][cell[1]-1] = random.randrange(len(graphics_data["sprites"]))

        elif len(cell) == 4: # Format with 4 ints
            x1=cell[0]
            y1=cell[1]
            x2=cell[2]
            y2=cell[3]

            # Corners can be specified in any order, but Python's range() does not like that, so we
            # need to invert positions so that x1 < x2 and y1 < y2
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1

            # For every cell inside the specified rectangle
            for x in range(x1-1, x2):
                for y in range(y1-1, y2):
                    map[x][y] = 1 # Set that cell to alive

                    if graphics_data is not None: # Choose random sprite for that cell
                        graphics_data["spritemap"][x][y] = random.randrange(len(graphics_data["sprites"]))

    return map, {}


# Calculate the next generation of Game of Life (update the map and record of outsiders)
# If boundary_rule is "looped" ther will be no outsiders. Otherwise, any cell which escapes the map will
# be considered an outsider. An outsider (or any of its descendants) which remains outside map for too
# long is permanently deleted.
# Arguments:
#   map - (list[list[bool,],]) The map of the simulation. List of columns of cell states (0 - dead, 1 - alive).
#           Will be modified to match the state in next generation.
#   outsiders - (dict{tuple(int,int) : int}) A record of outsiders. Dictionary where key is tuple of
#               (x, y) coordinates and value is the stage of outsider (number of generations that this
#               cell and its ancestors have remained outside the map). Will be modified to match the
#               state in next generation.
#   boundary_rule - (str) (optional) Specify  what happens when a cell leaves (spawns outside) the map. There are 2
#                   possible values:
#                       "open" - the default - cells move through the border and are considered outsiders
#                       "looped" - cells leaving on one side enter from the opposite
#   graphics_data - (conway_graphics.ConwayGraphics) (optional) Object storing graphics data.
#                       If specified, its internal 'spritemap' value will be updated to set random sprites
#                       to newly spawned cells (out of those available in 'sprites')
#
# returns: int, number of outsiders which were permanently deleted this generation
def next_generation(map, outsiders, boundary_rule="open", graphics_data=None):
    global neighbour_vects # Constant defined on top of file

    to_resurrect = [] # Cells scheduled to become alive
    to_kill = [] # Cells scheduled to become dead

    if boundary_rule == "looped":
        loop = True
    elif boundary_rule == "open":
        loop = False
    else:
        raise ValueError(f"Unknown boundary rule: \"{boundary_rule}\"")

    # For every position on the map, calculate whether it should be killed or resurrected
    for x in range(len(map)):
        for y in range(len(map[x])):
            ncount = neighbour_count((x,y), map, outsiders, loop=loop) # Number of neighboring alive cells

            # As per classic Conway's Game of Life rules, living cells with < 2 or
            # > 3 nighbors are killed, dead cells with exactly 3 neighbors are resurrected,
            # and other cells keep their state
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
        # Dict of positions which might become outsiders in next generation
        # key is tuple of (x, y) coordinates and value is tuple(int, int) of
        # (number_of_neighbors, stage)
        potential_outsiders = {}

        # Check neighbours of cells right on the boundary
        # top and bottom boundaries
        for x in range(len(map)):
            for y in [-1, len(map[x])]:
                # Positions which already are outsiders will be evaluated later
                if (x, y) in outsiders: continue

                ncount = neighbour_count((x,y), map, outsiders, loop, False) # Number of neighbors on the map
                if ncount > 0:
                    # This potential outsider would be created including cells directly on the map,
                    # so its stage would be lowest possible, 1
                    potential_outsiders[(x, y)] = (ncount, 1)

        # Same for left and right boundaries
        for x in [-1, len(map)]:
            for y in range(len(map[0])):
                if (x, y) in outsiders: continue

                ncount = neighbour_count((x,y), map, outsiders, loop, False)
                if ncount > 0:
                    potential_outsiders[(x, y)] = (ncount, 1)

        # Check positions which are currently outsiders
        for outsider in outsiders:
            stage = float("Inf") # Just a placeholder for now
            ncount = neighbour_count(outsider, map, outsiders, loop, False) # Neighbours within map

            if ncount > 0:
                # This outsider would be kept alive by cells directly on the map,
                # so its stage would become lowest possible, 1
                stage = 1

            # list of this outsider's all neighbouring positions
            neighbours = [vectadd(outsider, v) for v in neighbour_vects]
            for neighbour in neighbours:
                neighbour = tuple(neighbour) # Ensure the position is stored in hashable type

                if is_valid_pos(neighbour, (len(map), len(map[0]))): # We have evaluated in-map neighbours already
                    continue
                elif neighbour in outsiders: # A living neighbour
                    ncount += 1
                    # Outsiders inherit stage of their lowest-stage neighbour, incremented by 1
                    stage = min(stage, outsiders[neighbour]+1)
                else:
                    # Neighbouring dead cell becomes a potential outsider, has its neighbour count
                    # incremented by 1 and possibly inherits current outsider's stage (incremented)
                    nghbr = potential_outsiders.get(neighbour, (0, float("Inf")))
                    potential_outsiders[neighbour] = (nghbr[0]+1, min(nghbr[1], outsiders[outsider]+1))

            if ncount in [2, 3]: # This cell survives...
                if stage > 15: # ...but we delete it since its stage is too high
                    escaped += 1
                else: # ...yeah, it survives (for now)
                    outsiders_new[outsider] = stage


        for poutsider in potential_outsiders:
            # This position has right number of neighbours...
            if potential_outsiders[poutsider][0] == 3: # ...but it is deleted since its stage is too high
                if potential_outsiders[poutsider][1] > 15:
                    escaped += 1
                else: # ...so it becomes an outsider
                    outsiders_new[poutsider] = potential_outsiders[poutsider][1]


    # Apply the scheduled changes to in-map cells
    for cell in to_kill:
        map[cell[0]][cell[1]] = 0
    for cell in to_resurrect:
        if map[cell[0]][cell[1]] == 1: continue # The cell was alive already

        map[cell[0]][cell[1]] = 1

        if graphics_data is not None: # Choose random sprite for that cell
            graphics_data["spritemap"][cell[0]][cell[1]] = random.randrange(len(graphics_data["sprites"]))

    # Update outsiders
    outsiders.clear()
    outsiders.update(outsiders_new)

    return escaped # Number of permanently removed outsiders


# Check whether a position is contained within a map
# Arguments:
#   pos - (tuple(int, int,)) The position to check (x, y,)
#   mapsize - (tuple(int, int,)) Size of the map (width, height, other_dimensions?,)
#
#   returns: bool, whether it is or not
def is_valid_pos(pos, mapsize):
    # For every coordinate check if it is contained within map's span along this axis
    for i in range(len(pos)):
        if pos[i] < 0 or pos[i] >= mapsize[i]:
            return False

    return True


# Calculate the number of living neighbours of a position
# Arguments:
#   pos - (tuple(int, int)) the position, whose neighbours are to be counted (x,y)
#   map - (list[list[bool,],]) The map of the simulation. List of columns of cell states (0 - dead, 1 - alive).
#   outsiders - (dict{tuple(int,int) : int}) A record of outsiders. Dictionary where key is tuple of
#               (x, y) coordinates and value is the stage of outsider
#   loop - (bool) (optional) Whether the coordinates are to be looped, i.e. a cell outside one border
#           is synonymous with cell near opposite border
#   include_outsiders - (bool) (optional) Whether neigbours-outsiders are to be counted (defaults to True)
#
# returns: int, number of living neighbours
def neighbour_count(pos, map, outsiders, loop=False, include_outsiders=True):
    global neighbour_vects # Constant defined on top of file

    mapsize = (len(map), len(map[0]))

    ncount = 0 # Neighbour count
    for vect in neighbour_vects: # For every neighbouring position
        npos = vectadd(pos, vect) # Neighbour position

        if loop: # If we're looping the map boundaries, wrap the coords
            npos = wrap_coords(npos, mapsize)

        elif not is_valid_pos(npos, mapsize): # This position is outside map
            if include_outsiders and tuple(npos) in outsiders: # Check if there is an outsider on that position
                ncount += 1
            continue

        ncount += map[npos[0]][npos[1]] # Increment number of neighbours if this cell is alive

    return(ncount)


# Wraps the specified coordinates to the map's span, such that e.g. coordinate x of -3 becomes
# map size (on x axis) - 3
# Arguments:
#   pos - (tuple(int, int, )) Coordinates to wrap (x, y, other_dimensions?)
#   mapsize - (tuple(int, int, )) Size of the map (x, y, other_dimenstions?)
#
# return: tuple(int, int, ) The coordinates after wrapping
def wrap_coords(pos, mapsize):
    return [pos[i] % mapsize[i] for i in range(len(pos))]
