import random
from typing import List, Dict, Any, Set, Tuple

NUM_ROWS = 9
NUM_COLUMNS = 9
BOX_SIZE = 3
NUM_BOXES_Y = int(NUM_ROWS / BOX_SIZE)
NUM_BOXES_X = int(NUM_COLUMNS / BOX_SIZE)

possible_values = [i+1 for i in range(9)]

# Will contain values for initial puzzle. 1 to 9 for a provided value, 0 for a blank.
cells: List[List[int]] = [[0 for i in range(NUM_COLUMNS)] for j in range(NUM_ROWS)]

# The following are used in puzzle generation
#
# For each row, a set containing values definitely present in that row
definite_values_per_row: List[Set[int]] = [set() for i in range(NUM_ROWS)]
# For each column, a set containing values definitely present in that column
definite_values_per_column: List[Set[int]] = [set() for i in range(NUM_COLUMNS)]
# For each box, a set containing values definitely present in that box
definite_values_per_box: List[List[Set[int]]] = [[set() for x in range(NUM_BOXES_X)] for y in range(NUM_BOXES_Y)]

def print_cells():
    """
    Prints out an attractive representation of the Sudoku puzzle.
    """

    def print_separator_row():
        row_str = "+"
        for x in range(NUM_COLUMNS):
            row_str += "--"
            if x % BOX_SIZE == BOX_SIZE - 1:
                row_str += "-+"
        print(row_str)

    print_separator_row()
    for y, row in enumerate(cells):
        row_str = "|"
        for x, cell in enumerate(row):
            cell_str = " " if cell == 0 else f"{cell}"
            row_str += f" {cell_str}"
            if x % BOX_SIZE == BOX_SIZE - 1:
                row_str += " |"
        print(row_str)
        if y % BOX_SIZE == BOX_SIZE - 1:
            print_separator_row()

def get_box_coordinates(cell_x: int, cell_y: int) -> Tuple[int, int]:
    """
    Normally, a Sudoku puzzle contains nine boxes, each 3 x 3 cells. This function converts
    between cell coordinates and box coordinates. For example, cell coordinates of (4, 1) map
    to box coordinates of (1, 0), the box in the top middle.

    :param cell_x: cell coordinate
    :param cell_y: cell coordinate
    :return: (box coordinate x, box coordinate y)
    """
    return int(cell_x / BOX_SIZE), int(cell_y / BOX_SIZE)

def clear_row(y: int):
    """
    Clears a row of all values and updates accounting data accordingly
    :param y: row index
    """
    for x in range(NUM_COLUMNS):
        current_val = cells[y][x]
        definite_values_per_row[y].discard(current_val)
        definite_values_per_column[x].discard(current_val)

        box_x, box_y = get_box_coordinates(x, y)
        box_definite = definite_values_per_box[box_y][box_x]
        box_definite.discard(current_val)

        cells[y][x] = 0

def clear_all_rows():
    """
    Clears all rows of values and updates accounting data accordingly
    """
    for y in range(NUM_ROWS):
        clear_row(y)

def populate_cells():
    redo_count = 0
    while redo_count < 40:
        success = attempt_populate_cells()
        if success:
            break
        redo_count += 1

    if redo_count == 40:
        print("Failure!")

def attempt_populate_cells() -> bool:
    """
    Attempts to populate the grid with values that conform to Sudoku rules. If the attempt isn't successful,
    the function returns False.
    """
    max_row_redos = 20
    failed = False
    for y in range(NUM_ROWS):
        redo_count = 0
        # Keep trying until we get a row that conforms to Sudoku rules
        while redo_count < max_row_redos:
            clear_row(y)
            row_options = set(possible_values)
            for x in range(NUM_COLUMNS):
                # We must choose a value that:
                # - isn't already in this column
                # - isn't already in this box

                box_x, box_y = get_box_coordinates(x, y)
                box_definite = definite_values_per_box[box_y][box_x]

                choices = row_options - definite_values_per_column[x] - box_definite
                if len(choices) == 0:
                    # Oops, there's no value that will work in this cell, time to redo the whole
                    # row.
                    failed = True
                    break
                choice = random.choice(list(choices))
                cells[y][x] = choice
                row_options.discard(choice)
                definite_values_per_row[y].add(choice)
                definite_values_per_column[x].add(choice)
                box_definite.add(choice)
            if failed:
                # Generating the row failed due to duplicate values in a single box or single column.
                # So, we simply start the row over and try again
                failed = False
                redo_count += 1
            else:
                break
        if redo_count == max_row_redos:
            return False
    return True
