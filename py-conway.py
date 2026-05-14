import os
import argparse
import pathlib
import yaml
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1" # Suppress pygame welcome message
import pygame

import conway_graphics as graphics

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

    # TODO: Check data validity

    return parser


def load_config(config_file):
    f = open(config_file, 'r')
    conf = yaml.safe_load(f)

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

    #for y in range(conf["game"]["height"]):
    #    [print(str(map[x][y])+' ', end='') for x in range(conf["game"]["width"])]
    #    print()

    # Create ConwayGraphics object for current device
    cg = graphics.init()

    running = True
    while running: # Main loop

        # Handle user events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False


        (cg@"window").blit(cg@"background", (-cg["cell_size"],-cg["cell_size"]))
        pygame.display.flip()


if __name__ == "__main__":
    main()
