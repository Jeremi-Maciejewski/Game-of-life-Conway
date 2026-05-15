import os
import time
import argparse
import pathlib
import yaml
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1" # Suppress pygame welcome message
import pygame

import conway_graphics as graphics
import game_of_life as gol

# Lambdas that adds/subtract 2 vectors positionally
vectadd = lambda x, y: [x[i] + y[i] for i in range(min(len(x), len(y)))]
vectsub = lambda x, y: [x[i] - y[i] for i in range(min(len(x), len(y)))]

# Lambda multiplying vector by a scalar
vectscale = lambda X, s: [x * s for x in X]

def create_parser():
    parser = argparse.ArgumentParser(
        description="Symulator Gry w Życie Conwaya"
    )

    parser.add_argument( "--config", required=True, help="Ścieżka do pliku YAML definiującego wymiary i układ siatki gry.",
    )

    parser.add_argument(
        "--out",
        default="game.gif",
        type=pathlib.Path,
        help="Opcjonalnie, ścieżka do wynikowego pliku GIF dokumentującego przebieg symulacji (liczba wynikowych iteracji jest ograniczana poprzez plik konfiguracyjny).",
    )

    return parser


def load_config(config_file):
    try:
        f = open(config_file, 'r')
    except OSError:
        raise ValueError(f"The config file \"{config_file}\" could not be opened. Please verify whether the path is valid and whether you have permissions necessary to open it.") from None

    try:
        conf = yaml.safe_load(f)
    except yaml.YAMLError as e:
        suffix = ""
        if hasattr(e, "problem"):
            suffix += f"\nError description: \"{e.problem}\""
        if hasattr(e, "problem_mark"):
            suffix += f"\nYAML line {e.problem_mark.line+1}, column {e.problem_mark.column+1}"
        raise ValueError(f"Error while parsing YAML: the data contained within configuration file \"{config_file}\" does not appear to be a valid YAML!{suffix}") from None

    return conf


def make_map(width, height, cell_list):
    map = [[0]*height for _ in range(width)] # List of columns (lists of cell statuses in that column of map, 0 -> dead, 1 -> alive)
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


def main(args=None):
    parser = create_parser()
    args = parser.parse_args(args)

    conf = load_config(args.config)
    map = make_map(conf["game"]["width"], conf["game"]["height"], conf["cells"])

    # Create ConwayGraphics object for current device
    cg = graphics.init(conf["game"]["width"], conf["game"]["height"])

    running = True
    clock = 0
    game_tick = 1
    pause = 1

    arrowsdown = [0,0,0,0] # left-top-right-bottom
    mousestatus = [False, (0,0)] # [is_down, last_mouse_pos]
    screenscale=1.5
    while running: # Main loop

        # Handle user events
        arrowsclicked = [0,0,0,0]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        running = False
                    case pygame.K_SPACE:
                        pause = (pause + 1) % 2
                    case pygame.K_LEFT:
                        arrowsdown[0] = arrowsclicked[0] = 1
                    case pygame.K_UP:
                        arrowsdown[1] = arrowsclicked[1] = 1
                    case pygame.K_RIGHT:
                        arrowsdown[2] = arrowsclicked[2] = 1
                    case pygame.K_DOWN:
                        arrowsdown[3] = arrowsclicked[3] = 1

            elif event.type == pygame.KEYUP:
                match event.key:
                    case pygame.K_LEFT:
                        arrowsdown[0] = 0
                    case pygame.K_UP:
                        arrowsdown[1] = 0
                    case pygame.K_RIGHT:
                        arrowsdown[2] = 0
                    case pygame.K_DOWN:
                        arrowsdown[3] = 0

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mousestatus[0] = True
                mousestatus[1] = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                mousestatus[0] = False

            elif event.type == pygame.MOUSEWHEEL:
                screenscale_old = screenscale
                screenscale = min(max(screenscale + 0.25*event.y, 1), 2)
                cg.setconst("scroll", vectscale(cg["scroll"], screenscale_old/screenscale))

        # Update scroll position
        # Note that scroll is written down as movement of the map, rather than camera
        # (i.e. it might seem that the values are inverted)
        scrollchange = [0,0]
        scrollspeed = 5 * screenscale
        if arrowsdown[0] or arrowsclicked[0]:
            scrollchange[0] += scrollspeed

        if arrowsdown[1] or arrowsclicked[1]:
            scrollchange[1] += scrollspeed

        if arrowsdown[2] or arrowsclicked[2]:
            scrollchange[0] -= scrollspeed

        if arrowsdown[3] or arrowsclicked[3]:
            scrollchange[1] -= scrollspeed

        if mousestatus[0]:
            mouse_pos = pygame.mouse.get_pos()
            movement = vectsub(mousestatus[1], mouse_pos)
            scrollchange = vectadd(scrollchange, vectscale(movement, -1/screenscale))

            mousestatus[1] = mouse_pos

        cg.setconst("scroll", vectadd(cg["scroll"], scrollchange) )

        graphics.draw_map(cg, map)

        save = False
        if not pause and clock % game_tick == 0 and clock <= conf["game"]["gif_length"]:
            save = True

        graphics.refresh_window(cg, screenscale, save_image=save)
        pygame.display.flip()

        # Update the map
        if not pause and clock % game_tick == 0:
            gol.next_generation(map)
            if clock/game_tick == conf["game"]["gif_length"]:
                print("Generating GIF image, please wait...")
                fname = "data/test.gif"
                graphics.make_gif(cg, fname)
                print(f"\'{fname}\' saved.")

        if not pause:
            clock += 1
        time.sleep(0.1)


if __name__ == "__main__":
    main()
