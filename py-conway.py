import os
import time
import argparse
import pathlib
import yaml
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1" # Suppress pygame welcome message
import pygame

import conway_graphics as graphics

# Lambda that adds 2 vectors positionally
vectadd = lambda x, y: [x[i] + y[i] for i in range(min(len(x), len(y)))]

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
    arrowsdown = [0,0,0,0] # left-top-right-bottom
    while running: # Main loop

        # Handle user events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                match event.key:
                    case pygame.K_ESCAPE:
                        running = False
                    case pygame.K_LEFT:
                        arrowsdown[0] = 1
                    case pygame.K_UP:
                        arrowsdown[1] = 1
                    case pygame.K_RIGHT:
                        arrowsdown[2] = 1
                    case pygame.K_DOWN:
                        arrowsdown[3] = 1

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

        # Update scroll (5px/tick)
        # Note that scroll is written down as movement of the map, rather than camera
        # (i.e. it might seem that the values are inverted)
        scrollchange = [0,0]
        if arrowsdown[0]:
            scrollchange[0] += 10
        if arrowsdown[1]:
            scrollchange[1] += 10
        if arrowsdown[2]:
            scrollchange[0] -= 10
        if arrowsdown[3]:
            scrollchange[1] -= 10

        cg.setconst("scroll", vectadd(cg["scroll"], scrollchange) )

        (cg@"window").blit(cg@"background", (-cg["cell_size"] + cg["scroll"][0]%cg["cell_size"],
                                                -cg["cell_size"] + cg["scroll"][1]%cg["cell_size"]))
        graphics.draw_map(cg, map)
        (cg@"window").blit(cg@"cells", (-cg["cell_size"], -cg["cell_size"]))
        pygame.display.flip()

        time.sleep(0.05)


if __name__ == "__main__":
    main()
