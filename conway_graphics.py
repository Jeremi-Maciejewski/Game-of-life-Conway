import os
import math
import random
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


# Prepare graphics assets for Game of Life simulation and store them in ConwayGraphics object, as well
# as initialize pygame (graphics library)
# Arguments:
#   width - (int) Width of the simulation map
#   height - (int) Height of the simulation map
#
# returns: A ConwayGraphics object storing required graphics assets
def init(width, height):
    pygame.init() # Initialize pygame

    info = pygame.display.Info() # Basic information about current display device
    scr_res = (info.current_w, info.current_h) # Screen resolution

    font = pygame.font.Font(size=24) # Small font

    cs = 10 # Cell size

    # The game window will be a square taking up 90% of shorter dimension of the screen,
    # rounded down to a round number of cells
    win_size = int(min(scr_res) * 0.9 // cs * cs)

    cells_visible = win_size // cs
    # Note that scroll is written down as movement of the map, rather than camera
    # (i.e. it might seem that the values are inverted)
    initial_scroll = ((width/2 - cells_visible/2)*cs /2*-1, (height/2 - cells_visible/2)*cs /2*-1)

    pygame.display.set_caption("Conway's Game of Life") # OS window title
    window = pygame.display.set_mode((win_size, win_size)) # Create the OS window

    # We need some margin for scrolling, hence 1 more cell past each border
    bg_size = (min(win_size+cs*2, width*cs), min(win_size+cs*2, height*cs))

    bg = pygame.Surface(bg_size) # Surface to draw the background on
    # Surface to draw the cells and some map elements on
    # x2 for better graphics on zoom
    cells = pygame.Surface(((win_size+cs*2)*2, (win_size+cs*2)*2)).convert_alpha()
    bg.fill((0,0,0)) # Fill with black

    # Draw cell border lines in background
    mesh_color = (50,50,50)
    for pos in range(0, bg_size[0], cs):
        # Vertical
        pygame.draw.line(bg, mesh_color, (pos-1, 0), (pos-1, win_size+cs*2), 2)

        # Horizontal
        pygame.draw.line(bg, mesh_color, (0, pos-1), (win_size+cs*2, pos-1), 2)


    # Draw a variety of cell sprites
    sprites = []
    for _ in range(25):
        csurf = pygame.Surface((cs*2-4, cs*2-4)).convert_alpha() # Surface to store the sprite
        R = csurf.get_rect() # Rect object representing Surface area

        # Randomized coordinates of top left corner of the cell's image
        cell_l = random.randint(0, R.center[0]//2)
        cell_t = random.randint(0, R.center[1]//2)

        # Maximum width and height of cell's image - such that it does not stick outside map cell
        max_w = min(R.width, R.right - cell_l)
        max_h = min(R.height, R.bottom - cell_t, max_w*5//3)

        # Randomized cell sprite width and height
        cell_w = random.randint(R.width*3//4, max_w)
        cell_h = random.randint(R.height*3//4, max_h)

        membrane = pygame.Rect(cell_l, cell_t, cell_w, cell_h) # Rect representing cell membrane
        cytoplasm = membrane.copy() # Rect representing cytoplasm

        # Cytoplasm is smaller
        cytoplasm.top += 2
        cytoplasm.left += 2
        cytoplasm.width -= 4
        cytoplasm.height -= 4

        csurf.fill((0,0,0,0)) # Fill the Surface with transparency
        pygame.draw.ellipse(csurf, (0, 200, 0, 200), membrane) # Draw membrane ellipsis
        pygame.draw.ellipse(csurf, (0, 255, 0, 255), cytoplasm) # Draw cytoplasm ellipsis inside it

        sprites.append(csurf)

    spritemap = [[0]*height for _ in range(width)] # Map recording which sprite every cell uses

    # Store the created assets in ConwayGraphics object
    cg = ConwayGraphics(win_size, {"window":window, "background":bg, "cells":cells,
                                    "background_scaled":bg},
                        {"map_size":(width, height), "resolution":scr_res, "scroll":initial_scroll,
                            "cell_size":cs, "last_scale":1, "font":font, "sprites":sprites,
                            "spritemap":spritemap})

    return cg


# Draw the map with current generation of cells
# Arguments:
#   graphics_data - (ConwayGraphics) An object storing graphics assets as returned by init()
#   map - (list[list[bool,],]) Map of the simulation (list of columns (lists of boolean cell states))
def draw_map(graphics_data, map):
    gd = graphics_data # Just a shorthand

    (gd@"cells").fill((0,0,0,0)) # Fill the cells Surface with transparency

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
            if map[x][y] == 1: # Draw if current cell is alive
                sprite = gd["sprites"][gd["spritemap"][x][y]] # Get its sprite

                # Calculate cell's position on the Surface
                cellpos = (round(x*gd["cell_size"] + gd["scroll"][0] +\
                                    gd["cell_size"]/2 - sprite.get_width()/4),
                            round(y*gd["cell_size"] + gd["scroll"][1] +\
                                    gd["cell_size"]/2 - sprite.get_height()/4))

                cellpos = vectscale(cellpos, 2) # Multiply to account for higher resolution
                (gd@"cells").blit(sprite, cellpos) # Draw it


# Draw info labels (counters of generations, cell population and escaped cells)
# Arguments:
#   graphics_data - (ConwayGraphics) An object storing graphics assets as returned by init()
#   generation - (int) (optional) If specified, draws a generation counter with specified number of generations
#   population - (int) (optional) If specified, draws a population counter with specified number of cells
#   escaped - (int) (optional) If specified, draws an escaped cells counter with specified number of cells
#   color - (tuple(int, int, int,)) Tuple of 3 or 4 integers specifying RGB(A) color of the drawn text.
#
# returns: tuple(int, int), the position in which next label would be drawn (x,y)
def info_labels(graphics_data, generation=None, population=None, escaped=None, color=(250,250,250,175)):
    gd = graphics_data # Just a shorthand

    pos = [10, 10] # Arbitrary initial position in top left corner of window

    # Draws the current label in current position and updates the position
    def draw_label(lab, pos):
        if len(color) > 3: lab.set_alpha(color[3])

        (gd@"window").blit(lab, (10, pos[1]))

        pos[1] += gd["font"].get_linesize()
        pos[0] = max(pos[0], lab.get_width())

    if generation is not None: # Draw generation counter
        txt = gd["font"].render(f"Generation: {generation}", True, color)
        draw_label(txt, pos)

    if population is not None: # Draw population counter
        txt = gd["font"].render(f"Population: {population}", True, color)
        draw_label(txt, pos)

    if escaped is not None: # Draw excaped cells counter
        txt = gd["font"].render(f"Escaped cells: {escaped}", True, color)
        draw_label(txt, pos)

    return pos


# Blits all graphics components (Surfaces) onto the main Surface.
# Note: this does not do pygame.display.flip() - you need to do that yourself after running this function!
# Arguments:
#   graphics_data - (ConwayGraphics) An object storing graphics assets as returned by init()
#   scale - (float) (optional) A multiplier to scale the graphics by (yielding zoom in/out effect) (default is 1)
def refresh_window(graphics_data, scale=1):
    gd = graphics_data # Just a shorthand

    (gd@"window").fill((0,0,0)) # Fill the main window with black

    # Well, that thing is a complex equation to calculate how to align background with other Surfaces,
    # which took me long to formulate and would take long to remember and properly describe...
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


    # Cells Surface needs to be scaled down by half by default since its resolution is twice higher
    cells_rescale = scale * 0.5

    # Rescaled background is cached in the graphics object when possible since scaling is expensive
    if gd["last_scale"] == scale:
        bg_scaled = gd@"background_scaled"
    else: # The scale changed so we need to rescale
        bg_scaled = pygame.transform.scale_by(gd@"background", scale)
        gd.setsurf("background_scaled", bg_scaled)

    # Rescale cells and blit it alongside background
    (gd@"window").blit(bg_scaled, (bg_x, bg_y))
    (gd@"window").blit(pygame.transform.scale_by(gd@"cells", cells_rescale),
                        (-gd["cell_size"]*scale, -gd["cell_size"]*scale))

    gd.setconst("last_scale", scale) # Remember which scale was used for caching purposes


# Store an image of a surface inside the graphics object for future use
# The image is stored as byte sequence
# Arguments:
#   graphics_data - (ConwayGraphics) An object storing graphics assets as returned by init()
#   surface - (str) Name (key in graphics object) of Surface to store as image
def store_image(graphics_data, surface="window"):
    gd = graphics_data

    if type(surface) is pygame.Surface:
        surf = surface
    else:
        surf = gd@surface

    if not gd["images"]:
        gd.setconst("images", [])

    gd["images"].append(pygame.image.tobytes(surf, "RGB"))


# Remove all stored images
# Arguments:
#   graphics_data - (ConwayGraphics) An object storing graphics assets as returned by init()
def clear_images(graphics_data):
    graphics_data["images"].clear()


# Generate a GIF image out of stored images and store it as file
# Arguments:
#   graphics_data - (ConwayGraphics) An object storing graphics assets as returned by init()
#   filename - (str) Path to file to which to save the GIF
#   duration - (int) (optional) Duration of every frame (time it stays on-screen) in milliseconds (default is 100)
def make_gif(graphics_data, filename, duration=100):
    gd = graphics_data # Just a shorthand

    imgs = [] # List of images, converted to PIL.Image
    for img in gd["images"]:
        imgs.append(Image.frombytes("RGB", (gd@"window").get_size(), img))

    # Compose the GIF
    imgs[0].save(filename, save_all=True, append_images=imgs[1:], duration=duration, loop=True)
