import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1" # Suppress pygame welcome message
import pygame

# Class for storing graphics state
class ConwayGraphics:
    def __init__(self, window_size, surfaces = dict(), consts = dict()):
        self.window_size = window_size
        self.surfaces = surfaces
        self.consts = consts

    # ConwayGraphics[key] is synonymous to ConwayGraphics.consts.get(key, None)
    # Note that this does not allow for assigning/modifying - use ConwayGraphics.setsurf() for that
    def __getitem__(self, subscript):
        try:
            return self.consts.get(subscript, None)
        except (TypeError, LookupError, KeyError) as e:
            raise e

    # ConwayGraphics@key is synonymous to ConwayGraphics.surfaces.get(key, None)
    # Note that this operator has lower precedence and this does not allow for assigning (use
    # ConwayGraphics.setconst() for that)
    def __matmul__(self, subscript):
        try:
            return self.surfaces.get(subscript, None)
        except (TypeError, LookupError, KeyError) as e:
            raise e

    def setsurf(self, subscript, value):
        self.surfaces[subscript] = value

    def setconst(self, subscript, value):
        self.consts[subscript] = value


def init(width, height):
    pygame.init()

    info = pygame.display.Info()
    scr_res = (info.current_w, info.current_h) # Screen resolution

    cs = 20 # Cell size

    # The game window will be a square taking up 90% of shorter dimension of the screen,
    # rounded down to a round number of cells
    win_size = int(min(scr_res) * 0.9 // cs * cs)
    cells_visible = win_size // cs
    # Note that scroll is written down as movement of the map, rather than camera
    # (i.e. it might seem that the values are inverted)
    initial_scroll = ((width/2 - cells_visible/2)*cs*-1, (height/2 - cells_visible/2)*cs*-1)

    pygame.display.set_caption("Conway's Game of Life")
    window = pygame.display.set_mode((win_size, win_size))

    # Draw cell borders in background
    # We need some margin for scrolling, hence 1 more cell past each border
    bg = pygame.Surface((win_size+cs*2, win_size+cs*2))
    bg.fill((0,0,0))

    mesh_color = (75,75,75)
    for pos in range(0, win_size+cs*2, cs):
        # Vertical
        pygame.draw.line(bg, mesh_color, (pos-1, 0), (pos-1, win_size+cs*2), 2)

        # Horizontal
        pygame.draw.line(bg, mesh_color, (0, pos-1), (win_size+cs*2, pos-1), 2)

    cg = ConwayGraphics(win_size, {"window":window, "background":bg},
                        {"resolution":scr_res, "scroll":initial_scroll, "cell_size":cs})

    return cg


def draw_map(graphics_data, map):
    gd = graphics_data
    if not gd@"cells":
        gd.setsurf("cells", pygame.Surface((gd@"background").get_size()).convert_alpha())

    (gd@"cells").fill((0,0,0,0))

    for x in range(len(map)):
        for y in range(len(map[x])):
            if map[x][y] == 1:
                cellpos = (round(x*gd["cell_size"] + gd["cell_size"]/2 + gd["scroll"][0]),
                            round(y*gd["cell_size"] + gd["cell_size"]/2 + gd["scroll"][1]))
                pygame.draw.circle(gd@"cells", (255,0,0,255), cellpos, 5)
