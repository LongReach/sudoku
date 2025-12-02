import random
from time import sleep
from typing import List, Dict, Any, Set, Tuple, Optional, Callable

class GridException(Exception):
    """Exception for unresolvable issues encountered during puzzle-creation"""

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class SpaceMarker:
    """Used in adding cells to a puzzle"""

    def __init__(self, x: int, y: int, old_val: int):
        self.x = x
        self.y = y
        self.old_val = old_val


class PuzzleGrid:

    """
    Represents a grid containing a Sudoku puzzle. At the moment of instantiation, the grid will be entirely
    empty. A call to populate_cells() will cause the grid to be filled with values that conform to the Sudoku
    rules (see README).
    """

    NUM_ROWS = 9
    NUM_COLUMNS = 9
    BOX_SIZE = 3
    NUM_BOXES_Y = int(NUM_ROWS / BOX_SIZE)
    NUM_BOXES_X = int(NUM_COLUMNS / BOX_SIZE)

    possible_values = [i + 1 for i in range(9)]

    def __init__(self):
        # Will contain values for initial puzzle. 1 to 9 for a provided value, 0 for a blank.
        self.cells: Optional[List[List[int]]] = None

        # The following are used in puzzle generation
        #
        # For each row, a set containing values definitely present in that row
        self.definite_values_per_row: Optional[List[Set[int]]] = None
        # For each column, a set containing values definitely present in that column
        self.definite_values_per_column: Optional[List[Set[int]]] = None
        # For each box, a set containing values definitely present in that box
        self.definite_values_per_box: Optional[List[List[Set[int]]]] = None

        self.max_spaces = 45
        self.solver_callback: Optional[Callable[[], bool]] = None
        self.grid_with_spaces = None

        self.reset()

    def reset(self):
        """Clears the puzzle grid to a blank state"""
        self.cells = [[0 for i in range(self.NUM_COLUMNS)] for j in range(self.NUM_ROWS)]
        self.definite_values_per_row = [set() for i in range(self.NUM_ROWS)]
        self.definite_values_per_column = [set() for i in range(self.NUM_COLUMNS)]
        # For each box, a set containing values definitely present in that box
        self.definite_values_per_box = [[set() for x in range(self.NUM_BOXES_X)] for y in range(self.NUM_BOXES_Y)]

    def copy(self, other):
        # TODO: exception
        other_grid: PuzzleGrid = other
        self.reset()
        for y in range(self.NUM_ROWS):
            for x in range(self.NUM_COLUMNS):
                val = other_grid.get_value(x, y)
                self.set_value(x, y, val)

    def populate_from_list(self, hard_coded: List[List[int]]):
        """
        Populates the puzzle from hardcoded values. Raises GridException if bad values.
        """
        self.reset()
        self.cells = hard_coded
        for y in range(self.NUM_ROWS):
            for x in range(self.NUM_COLUMNS):
                cell_val = self.cells[y][x]

                if cell_val < 0 or cell_val > 9:
                    raise GridException(f"Bad cell value {cell_val}")

                if cell_val > 0:
                    self.set_value(x, y, cell_val)

    def print_cells(self):
        """
        Prints out an attractive representation of the Sudoku puzzle. See README for examples.
        """

        def print_separator_row():
            row_str = "+"
            for x in range(self.NUM_COLUMNS):
                row_str += "--"
                if x % self.BOX_SIZE == self.BOX_SIZE - 1:
                    row_str += "-+"
            print(row_str)

        print_separator_row()
        for y, row in enumerate(self.cells):
            row_str = "|"
            for x, cell in enumerate(row):
                cell_str = " " if cell == 0 else f"{cell}"
                row_str += f" {cell_str}"
                if x % self.BOX_SIZE == self.BOX_SIZE - 1:
                    row_str += " |"
            print(row_str)
            if y % self.BOX_SIZE == self.BOX_SIZE - 1:
                print_separator_row()

    def get_value(self, x: int, y: int) -> int:
        """Gets the value at a particular cell, returning 0 if a blank cell"""
        # TODO: exception
        return self.cells[y][x]

    def set_value(self, x: int, y: int, val: int):
        """
        Assigns a value to a cell. Can be used in solving a puzzle, equivalent to player penciling
        in a value.

        :param x: x coordinate of cell
        :param y: y coordinate of cell
        :param val: 0 to clear cell, 1 - 9 to set a value
        """
        box_x, box_y = self.get_box_coordinates(x, y)
        box_definites = self.definite_values_per_box[box_y][box_x]

        if val == 0:
            existing_val = self.get_value(x, y)
            if existing_val > 0:
                box_definites.discard(existing_val)
                self.definite_values_per_row[y].discard(existing_val)
                self.definite_values_per_column[x].discard(existing_val)

        self.cells[y][x] = val

        if val > 0:
            if val in box_definites:
                raise GridException(f"Cell value {val} in box twice")
            box_definites.add(val)
            if val in self.definite_values_per_row[y]:
                raise GridException(f"Cell value {val} in row twice")
            self.definite_values_per_row[y].add(val)
            if val in self.definite_values_per_column[x]:
                raise GridException(f"Cell value {val} in column twice")
            self.definite_values_per_column[x].add(val)

    def get_possible_values(self, x: int, y: int) -> Tuple[bool, Set[int]]:
        """
        Gets the possible values that can go into a cell, if it's currently blank.
        :param x: x coordinate of cell
        :param y: y coordinate of cell
        :return: (True if blank cell, set of values that can possibly go into cell -- empty if non-blank cell)
        """
        box_x, box_y = self.get_box_coordinates(x, y)
        box_definites = self.definite_values_per_box[box_y][box_x]
        if self.cells[y][x] > 0:
            return False, set()
        return True, set(self.possible_values) - box_definites - self.definite_values_per_row[y] - self.definite_values_per_column[x]

    @staticmethod
    def get_box_coordinates(cell_x: int, cell_y: int) -> Tuple[int, int]:
        """
        Normally, a Sudoku puzzle contains nine boxes, each 3 x 3 cells. This function converts
        between cell coordinates and box coordinates. For example, cell coordinates of (4, 1) map
        to box coordinates of (1, 0), the box in the top middle.

        :param cell_x: cell coordinate, horizontal axis
        :param cell_y: cell coordinate, vertical axis
        :return: (box coordinate x, box coordinate y)
        """
        return int(cell_x / PuzzleGrid.BOX_SIZE), int(cell_y / PuzzleGrid.BOX_SIZE)

    def clear_row(self, y: int):
        """
        Clears a row of all values and updates accounting data accordingly
        :param y: row index
        """
        for x in range(self.NUM_COLUMNS):
            current_val = self.cells[y][x]
            self.definite_values_per_row[y].discard(current_val)
            self.definite_values_per_column[x].discard(current_val)

            box_x, box_y = self.get_box_coordinates(x, y)
            box_definite = self.definite_values_per_box[box_y][box_x]
            box_definite.discard(current_val)

            self.cells[y][x] = 0

    def clear_all_rows(self):
        """
        Clears all rows of values and updates accounting data accordingly
        """
        for y in range(self.NUM_ROWS):
            self.clear_row(y)

    def populate_cells(self):
        redo_count = 0
        while redo_count < 40:
            success = self.attempt_populate_cells()
            if success:
                break
            redo_count += 1

        if redo_count == 40:
            print("Failure!")
            raise GridException("Could not generate puzzle")

    def attempt_populate_cells(self) -> bool:
        """
        Attempts to populate the grid with values that conform to Sudoku rules. If the attempt isn't successful,
        the function returns False.
        """
        max_row_redos = 20
        failed = False
        for y in range(self.NUM_ROWS):
            redo_count = 0
            # Keep trying until we get a row that conforms to Sudoku rules
            while redo_count < max_row_redos:
                self.clear_row(y)
                row_options = set(self.possible_values)
                for x in range(self.NUM_COLUMNS):
                    # We must choose a value that:
                    # - isn't already in this column
                    # - isn't already in this box

                    box_x, box_y = self.get_box_coordinates(x, y)
                    box_definite = self.definite_values_per_box[box_y][box_x]

                    choices = row_options - self.definite_values_per_column[x] - box_definite
                    if len(choices) == 0:
                        # Oops, there's no value that will work in this cell, time to redo the whole
                        # row.
                        failed = True
                        break
                    choice = random.choice(list(choices))
                    self.cells[y][x] = choice
                    row_options.discard(choice)
                    self.definite_values_per_row[y].add(choice)
                    self.definite_values_per_column[x].add(choice)
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

    def add_spaces(self, solver_callback: Callable[[], bool], max_spaces: int = 45) -> bool:
        self.max_spaces = max_spaces
        self.solver_callback = solver_callback
        self.grid_with_spaces = None

        # Will contain shuffled list of all possible cell coordinates
        space_markers: List[SpaceMarker] = []
        for y in range(self.NUM_ROWS):
            for x in range(self.NUM_COLUMNS):
                old_val = self.get_value(x, y)
                marker = SpaceMarker(x, y, old_val)
                space_markers.append(marker)
        random.shuffle(space_markers)

        index = 0
        space_count = 0
        success = self._add_spaces_impl(space_markers, index, space_count)
        if success and self.grid_with_spaces:
            self.copy(self.grid_with_spaces)
        return success

    def _add_spaces_impl(self, space_markers: List[SpaceMarker], index: int, space_count: int) -> bool:
        if space_count >= self.max_spaces:
            # Is this version solvable?
            solvable = self.solver_callback()
            if solvable:
                self.grid_with_spaces = PuzzleGrid()
                self.grid_with_spaces.copy(self)
                return True
            sleep(0.01)
            return False

        # How many more spaces do we need? Is there room for them?
        needed_spaces = self.max_spaces - space_count
        if (len(space_markers) - index) < needed_spaces:
            return False

        for i in range(2):
            if i == 0:
                # Put a space here
                marker = space_markers[index]
                self.set_value(marker.x, marker.y, 0)
                success = self._add_spaces_impl(space_markers, index+1, space_count+1)
                if success:
                    return True

                # Restore the value that used to be there
                self.set_value(marker.x, marker.y, marker.old_val)
            else:
                # Don't put a space here. Just move on.
                success = self._add_spaces_impl(space_markers, index+1, space_count)
                if success:
                    return True

        return False

