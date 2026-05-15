import os
import math
from PIL import Image
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


# Lambda multiplying vector by a scalar
vectscale = lambda X, s: [x * s for x in X]


def init(width, height):
    pygame.init()

    info = pygame.display.Info()
    scr_res = (info.current_w, info.current_h) # Screen resolution

    cs = 10 # Cell size

    # The game window will be a square taking up 90% of shorter dimension of the screen,
    # rounded down to a round number of cells
    win_size = int(min(scr_res) * 0.9 // cs * cs)

    cells_visible = win_size // cs
    # Note that scroll is written down as movement of the map, rather than camera
    # (i.e. it might seem that the values are inverted)
    initial_scroll = ((width/2 - cells_visible/2)*cs /2*-1, (height/2 - cells_visible/2)*cs /2*-1)

    pygame.display.set_caption("Conway's Game of Life")
    window = pygame.display.set_mode((win_size, win_size))

    # We need some margin for scrolling, hence 1 more cell past each border
    bg_size = (min(win_size+cs*2, width*cs), min(win_size+cs*2, height*cs))

    bg = pygame.Surface(bg_size)
    cells = pygame.Surface(((win_size+cs*2)*2, (win_size+cs*2)*2)).convert_alpha() # x2 for better graphics on zoom
    bg.fill((0,0,0))

    # Draw cell borders in background
    mesh_color = (50,50,50)
    for pos in range(0, bg_size[0], cs):
        # Vertical
        pygame.draw.line(bg, mesh_color, (pos-1, 0), (pos-1, win_size+cs*2), 2)

        # Horizontal
        pygame.draw.line(bg, mesh_color, (0, pos-1), (win_size+cs*2, pos-1), 2)

    cg = ConwayGraphics(win_size, {"window":window, "background":bg, "cells":cells,
                                    "background_scaled":bg},
                        {"map_size":(width, height), "resolution":scr_res, "scroll":initial_scroll,
                            "cell_size":cs, "last_scale":1})

    return cg


def draw_map(graphics_data, map):
    gd = graphics_data

    (gd@"cells").fill((0,0,0,0))
    # Draw map borders
    # Left
    r=pygame.draw.line(gd@"cells",
                        (255,0,0,255),
                        vectscale((gd["scroll"][0]-1, gd["scroll"][1]), 2),
                        vectscale((gd["scroll"][0]-1, gd["map_size"][1]*gd["cell_size"] + gd["scroll"][1]), 2),
                        4)
    # Top
    pygame.draw.line(gd@"cells",
                        (255,0,0,255),
                        vectscale((gd["scroll"][0], gd["scroll"][1]-1), 2),
                        vectscale((gd["map_size"][0]*gd["cell_size"] + gd["scroll"][0], gd["scroll"][1]-1), 2),
                        4)
    # Right
    pygame.draw.line(gd@"cells",
                        (255,0,0,255),
                        vectscale((gd["map_size"][0]*gd["cell_size"] + gd["scroll"][0]-1, gd["scroll"][1]), 2),
                        vectscale((gd["map_size"][0]*gd["cell_size"] + gd["scroll"][0]-1, gd["map_size"][1]*gd["cell_size"] + gd["scroll"][1]), 2),
                        4)
    # Bottom
    pygame.draw.line(gd@"cells",
                        (255,0,0,255),
                        vectscale((gd["scroll"][0]-1, gd["map_size"][1]*gd["cell_size"] + gd["scroll"][1]), 2),
                        vectscale((gd["map_size"][0]*gd["cell_size"] + gd["scroll"][0]-1, gd["map_size"][1]*gd["cell_size"] + gd["scroll"][1]), 2),
                        4)

    # Draw the cells
    for x in range(len(map)):
        for y in range(len(map[x])):
            if map[x][y] == 1:
                cellpos = (round(x*gd["cell_size"] + gd["cell_size"]/2 + gd["scroll"][0]),
                            round(y*gd["cell_size"] + gd["cell_size"]/2 + gd["scroll"][1]))
                cellpos = vectscale(cellpos, 2) # Multiply to account for higher resolution
                pygame.draw.circle(gd@"cells", (0,255,0,255), cellpos, gd["cell_size"]-2)


# Blits all graphics components onto the main Surface.
# Note: this does not do pygame.display.flip() - you need to do that yourself after running this function!
def refresh_window(graphics_data, scale=1, save_image=False):
    gd = graphics_data

    (gd@"window").fill((0,0,0))

    cutoff = (gd["map_size"][0]*gd["cell_size"] - (gd@"background").get_width(),
                gd["map_size"][1]*gd["cell_size"] - (gd@"background").get_height())

    bg_x = math.floor(
            (-gd["cell_size"] +\
                min(gd["scroll"][0], 0)*(gd["scroll"][0] > cutoff[0]*-1) % gd["cell_size"] +\
                max(gd["scroll"][0], 0) +\
                min(gd["scroll"][0] + cutoff[0], 0) )*\
            scale)

    bg_y = math.floor(
            (-gd["cell_size"] +\
                min(gd["scroll"][1], 0)*(gd["scroll"][1] > cutoff[1]*-1) % gd["cell_size"] +\
                max(gd["scroll"][1], 0) +\
                min(gd["scroll"][1] + cutoff[1], 0) )*\
            scale)


    cells_rescale = scale * 0.5

    if gd["last_scale"] == scale:
        bg_scaled = gd@"background_scaled"
    else:
        bg_scaled = pygame.transform.scale_by(gd@"background", scale)
        gd.setsurf("background_scaled", bg_scaled)

    (gd@"window").blit(bg_scaled, (bg_x, bg_y))
    (gd@"window").blit(pygame.transform.scale_by(gd@"cells", cells_rescale),
                        (-gd["cell_size"]*scale, -gd["cell_size"]*scale))

    gd.setconst("last_scale", scale)

    if save_image:
        if not gd["images"]:
            gd.setconst("images", [])

        gd["images"].append(pygame.image.tobytes(gd@"window", "RGB"))


def make_gif(graphics_data, filename, duration=100):
    gd = graphics_data

    imgs = []
    for img in gd["images"]:
        imgs.append(Image.frombytes("RGB", (gd@"window").get_size(), img))

    imgs[0].save(filename, save_all=True, append_images=imgs[1:], duration=duration, loop=True)
