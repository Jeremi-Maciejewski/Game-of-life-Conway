import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1" # Suppress pygame welcome message
import pygame

# Class for storing graphics state
class ConwayGraphics:
    def __init__(self, window_size, surfaces = dict(), consts = dict()):
        self.window_size = window_size
        self.surfaces = surfaces
        self.consts = consts

    # ConwayGraphics[key] is synonymous to ConwayGraphics.consts[key]
    def __getitem__(self, subscript):
        try:
            return self.consts[subscript]
        except (TypeError, LookupError, KeyError) as e:
            raise e

    # ConwayGraphics@key is synonymous to ConwayGraphics.surfaces[key]
    # Note that this operator has lower precedence, though
    def __matmul__(self, subscript):
        try:
            return self.surfaces[subscript]
        except (TypeError, LookupError, KeyError) as e:
            raise e


def init():
    pygame.init()

    info = pygame.display.Info()
    scr_res = (info.current_w, info.current_h) # Screen resolution

    cs = 20 # Cell size

    # The game window will be a square taking up 90% of shorter dimension of the screen,
    # rounded down to a round number of cells
    win_size = int(min(scr_res) * 0.9 // cs * cs)

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
                        {"resolution":scr_res, "scroll":(0,0), "cell_size":cs})

    return cg
