# Game-of-life-Conway
An amateur implementation of Conway's Game of Life, written in [Python](https://www.python.org/) programming language.

The program offers a live graphical visualization of the simulation, as well as an animated GIF output.

The program has been designed for and should run on Debian-based Linux distributions and the Windows Operating System, however, it is provided as-is and no guarantees are made regarding its proper operation and future support.

## Usage
The program can be downloaded ready-to-run from the [Releases](</../../releases>) page, ran directly using Python or [built from source](#build-from-source) (in the latter 2 cases, note the [dependencies](#dependencies)).

It is ran via Command Line, with use of a [YAML](https://en.wikipedia.org/wiki/YAML) configuration file. See [configuration file format](#configuration-file-format) for information on how to create one, or [ready config files](#example-config-files) for examples.

### Command line
The simplest way to run the program is by only defining the path to your config file:
```bash
py-conway --config <config file>
```

You might also want to set the name for output GIF, if your config requests one:
```bash
py-conway --config <config file> --out <gif file>
```

The full list of command line options can be seen by running:
```bash
py-conway --help
```

### Interface
Inside the graphic window, various options can be regulated with use of mouse and keyboard:
- navigate the map – arrow / WASD keys or dragging with mouse
- zoom in/out – +/- (PLUS/MINUS) keys or mouse scroll
- increase/decrease simulation speed – PGUP / PGDN
- pause/unpause – SPACE
- quit the program – ESC

### Configuration file format
The input config file may contain the following YAML sections:
- ‘game’ – (dictionary) defines general rules of the simulation:
  - ‘width’ – (integer) width of the map in cells
  - ‘height’ – (integer) height of the map in cells 
  - ‘boundary_rule’ – (string, optional, default: "open") defines the boundary rules. One of:
    - “open” – cells may leave the map and are eventually deleted
    - “looped” – periodic rules, i.e. cells leaving on one side effectively enter from the other side

- ‘output’ – (dictionary, optional) controls GIF output: 
  - ‘gif’ – (boolean, optional, default: False) whether to create the GIF
  - ‘gif_length’ – (integer, optional, default: 100) number of generations to include in the GIF
  - ‘gif_frame_duration’ – (integer, optional, default: 100) time between frames of the GIF in milliseconds (how long each frame stays on-screen). Every frame corresponds to one generation

- ‘cells’ - (list) a list of cells alive in the beginning. Cell positions can be defined in 2 ways:
  - as a list of 2 numbers (integers) – x and y coordinates (1-indexed) of a single cell
  - as a list of 4 numbers (integers) – x and y coordinates of 2 opposite corners of a rectangle of cells, in the order [x1, y1, x2, y2]

### Example config files
- [chaotic.yaml](/configs/chaotic.yaml) - an example arbitrary arrangement on a periodical map, taking ~1400 generations to stabilize
- [still_life.yaml](/configs/still_life.yaml) - a static simulation with 3 examples of still life
- [oscillators.yaml](/configs/oscillators.yaml) - the oscillators 'Snacker' and 'Pentoad' together
- [gosper_double_barreled.yaml](/configs/gosper_double_barreled.yaml) - Gosper's double-barreled glider gun
- [acorn.yaml](/configs/acorn.yaml) - the 'acorn' methuselah (notably, for performance reasons, the map is too small to show its full area)

## Dependencies
Below is a list of software required to run the program directly using Python:
- Python >= 3.11
- PyYAML (Python library)
- Pygame (Python library)
- Pillow (Python library)

## Build from source
In order to build an executable from source, you need to install all the [Dependencies](#dependencies), as well as the [pyinstaller](https://pypi.org/project/pyinstaller/) Python library.

Clone (copy) the repository to your device and then run the following in its root directory:
```bash
python -m PyInstaller build.spec
```

After the command finishes running, a 'dist' folder should appear in your working directory - your executable file can be found inside.