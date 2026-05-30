import os
import time
import argparse
import pathlib
import warnings
import yaml
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1" # Suppress pygame welcome message
import pygame

import conway_graphics as graphics
import game_of_life as gol

# Lambdas that add/subtract 2 vectors positionally
vectadd = lambda x, y: [x[i] + y[i] for i in range(min(len(x), len(y)))]
vectsub = lambda x, y: [x[i] - y[i] for i in range(min(len(x), len(y)))]

# Lambda multiplying vector by a scalar
vectscale = lambda X, s: [x * s for x in X]

# Create command line arguments parser for this program
# returns: an argparse.ArgumentParser object
def create_parser():
    parser = argparse.ArgumentParser(
        description="Simulator of Conway's Game of Life"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Path to a YAML config file defining the size of map, rules of the simulation and some other options.",
    )

    parser.add_argument(
        "-o",
        "--o",
        "--out",
        default="game.gif",
        type=pathlib.Path,
        dest="out",
        help="Optionally, path to an output GIF file which records the simulation (number of shown generations is configured through config file)"
    )

    parser.add_argument(
        "-s",
        "--s",
        "--speed",
        default=4,
        type=int,
        dest="speed",
        help="Simulation speed on a scale from 1 to 5.",
    )

    return parser


# Load configuration for this program from a YAML file
# Arguments:
#   config_file - (str) Path to file to be read
#
# returns: A dict representing validated config
def load_config(config_file):
    # Attempt to read the file
    try:
        f = open(config_file, 'r')
    except OSError: # This happens if file does not exist or cannot be read for other reasons
        raise ValueError(f"The config file \"{config_file}\" could not be opened. Please verify whether the path is valid and whether you have permissions necessary to open it.") from None

    # Attempt to parse YAML
    try:
        conf = yaml.safe_load(f)
    except yaml.YAMLError as e: # This happens if YAML syntax is violated
        suffix = ""
        if hasattr(e, "problem"):
            suffix += f"\nError description: \"{e.problem}\""
        if hasattr(e, "problem_mark"):
            suffix += f"\nYAML line {e.problem_mark.line+1}, column {e.problem_mark.column+1}"
        raise ValueError(f"Error while parsing YAML: the data contained within configuration file \"{config_file}\" does not appear to be a valid YAML!{suffix}") from None


    # If required sections are not present, raise errors
    if conf.get("game") is None:
        raise ValueError(f"In config file \"{config_file}\": Mandatory section \'game\' is not present!")
    if conf.get("cells") is None:
        raise ValueError(f"In config file \"{config_file}\": Mandatory section \'cells\' is not present!")


    # Ensure 'game' section options are valid
    game__width = conf["game"].get("width")
    game__height = conf["game"].get("height")
    game__boundary_rule = conf["game"].get("boundary_rule")
    if game__width is None:
        raise ValueError(f"In config file \"{config_file}\": Section \'game\': Mandatory option \'width\' is not present!")
    if game__height is None:
        raise ValueError(f"In config file \"{config_file}\": Section \'game\': Mandatory option \'height\' is not present!")
    if game__boundary_rule is None:
        conf["game"]["boundary_rule"] = "open"
    elif game__boundary_rule not in ["open", "looped"]:
        raise ValueError(f"In config file \"{config_file}\": Section \'game\': The only allowed values of \'boundary_rule\' are \'open\' (cells can escape the map area) or \'looped\' (leaving on one side is equivalent to entering on the other)")

    # Ensure 'output' section options are of valid type
    if conf.get("output") is not None:
        output__gif = conf["output"].get("gif")
        output__gif_length = conf["output"].get("gif_length")
        output__gif_frame_duration = conf["output"].get("gif_frame_duration")

        if output__gif is not None:
            assert type(output__gif) is bool
        if output__gif_length is not None:
            assert type(output__gif_length) is int
        if output__gif_frame_duration is not None:
            assert type(output__gif_frame_duration) is int
    else:
        conf["output"] = {}

    # Ensure 'cells' section entries are valid
    for idx, entry in enumerate(conf["cells"]):
        if type(entry) is not list:
            raise ValueError(f"In config file \"{config_file}\": Section \'cells\': All entries should be lists of integers! Entry number \'{idx+1}\' does not meet this requirement.")
        if len(entry) not in [2, 4]:
            raise ValueError(f"In config file \"{config_file}\": Section \'cells\': All entries should be lists of length 2 or 4! Entry number \'{idx+1}\' does not meet this requirement.")

    return conf


# Run the program
# Arguments:
#   args - (list) an optional list of arguments for the command line parser, as accepted by
#                   argparse.ArgumentParser.parse_args(). If not specified or None, arguments are fetched
#                   from sys.argv (actual command line input).
def main(args=None):
    # Convert speed "points" to length (in program ticks) of a game tick (1 generation)
    # Each point of speed makes the time between generations twice smaller
    def calc_game_tick(speed):
        return 16 / 2**(speed-1)

    parser = create_parser() # Command line argument parser
    args = parser.parse_args(args) # Prepare command line arguments

    conf = load_config(args.config) # Parse and validate config

    # Create ConwayGraphics object for current device
    cg = graphics.init(conf["game"]["width"], conf["game"]["height"])
    cg.setconst("largefont", pygame.font.Font(size=40)) # Additional, large font

    # Create map
    map, outsiders = gol.make_map(conf["game"]["width"], conf["game"]["height"], conf["cells"], cg)

    # Configurable simulation settings
    boundary_rule = conf["game"]["boundary_rule"] # What happens when cell leaves map
    speed = max(min(args.speed, 5), 1) # Speed "points" in range 1-5
    gif = conf["output"].get("gif", False) # Whether to generate a gif
    gif_length = conf["output"].get("gif_length", 100) # How many frames (generations) should the gif show
    gif_frame_duration = max(conf["output"].get("gif_frame_duration", 100), 1) # Time between gif frames in milliseconds (not less than 1)

    if gif_length > 500: # That might be a bit many frames, may cause issues
        message = '''Very high gif length has been selected. Be warned that memory usage grows linearly as generations to be drawn are accumulated.
This might result in very high memory usage or even lead to system crashes!
Additionally, gif generation time will be lenghtened.'''
        warnings.warn(message)

    running = True # The program only runs as long as this is True

    generation = 0 # Generations counter
    time_since_generation = 0 # Active (non-paused) ticks since last map update

    Clock = pygame.time.Clock() # This controls tick speed (fps)
    framerate = 15 # Max 15 ticks per second
    game_tick = calc_game_tick(speed)
    pause = 1 # Start paused

    escaped = 0 # If boundary_rule is "open" this tracks number of cells which escaped the map

    arrowsdown = [0,0,0,0] # left-top-right-bottom
    mousestatus = [False, (0,0)] # [is_down, last_mouse_pos]
    screenscale=1.5 # Zoom multiplier

    ## Main loop
    while running:
        ## Handle user events
        arrowsclicked = [0,0,0,0] # left,top,right,bottom / A,W,D,S

        for event in pygame.event.get(): # Loop over every user event which happened since last tick
            if event.type == pygame.QUIT: # The 'X' in top right corner was clicked
                running = False # Terminate the program

            elif event.type == pygame.KEYDOWN: # A keyboard key was pressed

                match event.key: # Check which key
                    case pygame.K_ESCAPE: # ESC terminates the program
                        running = False

                    case pygame.K_SPACE: # Pause / unpause
                        pause = (pause + 1) % 2

                    case pygame.K_LEFT | pygame.K_a: # Start scrolling left
                        arrowsdown[0] = arrowsclicked[0] = 1
                    case pygame.K_UP | pygame.K_w: # Start scrolling up
                        arrowsdown[1] = arrowsclicked[1] = 1
                    case pygame.K_RIGHT | pygame.K_d: # Start scrolling right
                        arrowsdown[2] = arrowsclicked[2] = 1
                    case pygame.K_DOWN | pygame.K_s: # Start scrolling down
                        arrowsdown[3] = arrowsclicked[3] = 1

                    case pygame.K_MINUS: # Zoom out
                        screenscale_old = screenscale
                        screenscale = min(max(screenscale - 0.25, 1), 2)
                        cg.setconst("scroll", vectscale(cg["scroll"], screenscale_old/screenscale))
                    case pygame.K_EQUALS: # Zoom in
                        screenscale_old = screenscale
                        screenscale = min(max(screenscale + 0.25, 1), 2)
                        cg.setconst("scroll", vectscale(cg["scroll"], screenscale_old/screenscale))

                    case pygame.K_PAGEUP: # Increase simulation speed
                        speed = max(min(speed+1, 5), 1)
                        game_tick = calc_game_tick(speed)
                    case pygame.K_PAGEDOWN: # Decrease simulation speed
                        speed = max(min(speed-1, 5), 1)
                        game_tick = calc_game_tick(speed)


            elif event.type == pygame.KEYUP: # A keyboard key was released
                match event.key: # Check which key
                    case pygame.K_LEFT | pygame.K_a: # Stop scrolling left
                        arrowsdown[0] = 0
                    case pygame.K_UP | pygame.K_w: # Stop scrolling up
                        arrowsdown[1] = 0
                    case pygame.K_RIGHT | pygame.K_d: # Stop scrolling right
                        arrowsdown[2] = 0
                    case pygame.K_DOWN | pygame.K_s: # Stop scrolling down
                        arrowsdown[3] = 0

            # Some mouse button was clicked
            # Record click + start scroll via mouse dragging
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mousestatus[0] = True
                mousestatus[1] = event.pos

            # Some mouse button was released
            # Stop scroll via mouse dragging
            elif event.type == pygame.MOUSEBUTTONUP:
                mousestatus[0] = False

            # Mouse wheel movement
            # Zoom in/out via mouse wheel
            elif event.type == pygame.MOUSEWHEEL:
                screenscale_old = screenscale
                screenscale = min(max(screenscale + 0.25*event.y, 1), 2)
                cg.setconst("scroll", vectscale(cg["scroll"], screenscale_old/screenscale))


        # Update scroll position
        # Note that scroll is written down as movement of the map, rather than camera
        # (i.e. it might seem that the values are inverted)
        scrollchange = [0,0] # Total change in scroll after applying both keyboard and mouse input
        scrollspeed = 5 * screenscale # Rate of scrolling via keyboard

        if arrowsdown[0] or arrowsclicked[0]: # Scrolling left via keyboard
            scrollchange[0] += scrollspeed

        if arrowsdown[1] or arrowsclicked[1]: # Scrolling up via keyboard
            scrollchange[1] += scrollspeed

        if arrowsdown[2] or arrowsclicked[2]: # Scrolling right via keyboard
            scrollchange[0] -= scrollspeed

        if arrowsdown[3] or arrowsclicked[3]: # Scrolling down via keyboard
            scrollchange[1] -= scrollspeed

        if mousestatus[0]: # Scrolling by dragging with mouse
            mouse_pos = pygame.mouse.get_pos() # Current mouse position
            movement = vectsub(mousestatus[1], mouse_pos) # Difference from last recorded mouse position
            scrollchange = vectadd(scrollchange, vectscale(movement, -1/screenscale))

            mousestatus[1] = mouse_pos # Update last recorded mouse position

        cg.setconst("scroll", vectadd(cg["scroll"], scrollchange) ) # Set the new scroll value

        pop = sum([sum(col) for col in map]) # Calculate current population

        graphics.draw_map(cg, map) # Draw the cells and map details
        graphics.refresh_window(cg, screenscale) # Blit changes onto main window

        # Add generation, population and escaped cells counters
        esc = escaped + len(outsiders)
        if boundary_rule == "looped": esc = None
        info_end = graphics.info_labels(cg, generation = generation, population = pop, escaped = esc)

        if not pause and gif and time_since_generation == 0 and generation <= gif_length:
            graphics.store_image(cg) # Save the screen state so we can include it in GIF later

        # Simulation speed indicator
        # This is intentionally drawn AFTER storing the image, making this not visible on GIFs
        txt = cg["font"].render(f"Speed: {speed}", True, (250, 250, 250))
        txt.set_alpha(175)
        (cg@"window").blit(txt, (10, info_end[1]))
        info_end[0] = max(info_end[0], txt.get_width())
        info_end[1] += cg["font"].get_linesize()

        if pause: # Warn the user that the simulation is paused
            txt = cg["largefont"].render("The simulation is paused. Press SPACE to unpause.", True,
                                            (200, 200, 200))
            txt.set_alpha(175)
            (cg@"window").blit(txt, (((cg@"window").get_width()-txt.get_width())//2, max(50, info_end[1])))

        pygame.display.flip() # Update the screen


        # Update the map (this is actually done at the end of previous tick, before the one where next generation starts)
        if not pause and time_since_generation >= game_tick-1:
            escaped += gol.next_generation(map, outsiders, boundary_rule, cg) # Generate next iteration of Game of Life

            if gif and generation == gif_length: # Time to make the GIF
                # Let's tell the user what's happening, don't want them scratching their head over
                # random freeze if this takes a while
                txt = cg["font"].render("Generating GIF image, please wait...", True, (200, 120, 120))
                (cg@"window").blit(txt, (((cg@"window").get_width()-txt.get_width())//2,
                                            (cg@"window").get_height()-txt.get_height()-20))

                pygame.display.flip() # Update the screen so they can see our message

                graphics.make_gif(cg, args.out, duration=gif_frame_duration)
                print(f"\'{args.out}\' saved.")

                graphics.clear_images(cg) # We won't need those anymore, so let's not waste memory

            generation += 1
            time_since_generation = -1 # Reset this counter (-1 since we're 1 tick early)

        if not pause:
            time_since_generation += 1

        Clock.tick(framerate) # That ensures we don't exceed tick speed (fps) cap


# If the program was ran directly, (rather than imported) execute main
if __name__ == "__main__":
    main()
