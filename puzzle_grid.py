import random
from time import sleep
from typing import List, Dict, Any, Set, Tuple, Optional, Callable

class GridException(Exception):
    """Exception for unresolvable issues encountered during puzzle-creation"""

    def __init__(self, message):
        self.message = message
        super().__init__(message)


class SpaceMarker:
    """Used in adding blank cells to a puzzle"""

    def __init__(self, x: int, y: int, old_val: int):
        self.x = x
        self.y = y
        self.old_val = old_val


class PuzzleGrid:

    """
    Represents a grid containing a Sudoku puzzle. At the moment of instantiation, the grid will be entirely
    empty. A call to populate_cells() will cause the grid to be filled with values that conform to the Sudoku
    rules (see README). The function add_spaces() populates the grid with the blanks that a player must fill
    in.

    Note that a PuzzleGrid can be filled in by a Solver class, as it works to solve the puzzle. The Solver
    might temporarily "write in" values, then remove them later.
    """

    NUM_ROWS = 9
    NUM_COLUMNS = 9
    BOX_SIZE = 3
    NUM_BOXES_Y = int(NUM_ROWS / BOX_SIZE)
    NUM_BOXES_X = int(NUM_COLUMNS / BOX_SIZE)

    # We try many different configurations of blanks on a grid of numbers. If we get through some
    # number of failed configurations without success, we might as well just start over with a
    # new grid of numbers.
    MAX_FAILED_SPACE_CONFIGURATIONS = 500

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

        self.required_spaces = 45
        self.solver_callback: Optional[Callable[[], bool]] = None
        self.grid_with_spaces = None
        self.max_spaces_per_box = 1000
        self.min_spaces_per_box = 0
        self.space_failure_count = 0

        self.reset()

    def reset(self):
        """Clears the puzzle grid to a blank state"""
        self.cells = [[0 for i in range(self.NUM_COLUMNS)] for j in range(self.NUM_ROWS)]
        self.definite_values_per_row = [set() for i in range(self.NUM_ROWS)]
        self.definite_values_per_column = [set() for i in range(self.NUM_COLUMNS)]
        # For each box, a set containing values definitely present in that box
        self.definite_values_per_box = [[set() for x in range(self.NUM_BOXES_X)] for y in range(self.NUM_BOXES_Y)]

    def copy(self, other):
        """
        Copies another PuzzleGrid into this one.
        :param other: the PuzzleGrid to make a copy of
        :raises GridException: if error encountered during copy
        """
        if not isinstance(other, PuzzleGrid):
            raise GridException("Can't copy object that's not a PuzzleGrid")

        other_grid: PuzzleGrid = other
        self.reset()
        for y in range(self.NUM_ROWS):
            for x in range(self.NUM_COLUMNS):
                val = other_grid.get_value(x, y)
                self.set_value(x, y, val)

    def populate_from_list(self, hard_coded: List[List[int]]):
        """
        Populates the puzzle from hardcoded values.
        :raises GridException: if bad values
        """
        if len(hard_coded) != self.NUM_ROWS:
            raise GridException(f"Wrong number of rows: {len(hard_coded)}")

        self.reset()
        self.cells = hard_coded
        for y in range(self.NUM_ROWS):
            hard_coded_row = hard_coded[y]
            if len(hard_coded_row) != self.NUM_COLUMNS:
                raise GridException(f"Wrong number of entries ({len(hard_coded_row)}) in row {y}")

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

    def super_print(self):
        """
        Prints a larger representation of the Sudoku puzzle, one that could be printed out on a
        printer and given to a player.
        """

        def _make_cell(x: int, y: int, val: int) -> List[str]:
            """
            Makes a list of strings representing a single cell. Each string in the list is a row
            of the printed cell (not the same concept of rows as for the puzzle itself).
            """
            lines = []
            # True if this cell is on the left side of its box. Same idea with "top of"
            left_of_box = (x % self.BOX_SIZE) == 0
            top_of_box = (y % self.BOX_SIZE) == 0
            val_as_str = " " if val == 0 else f"{val}"

            # True if this cell is on very right of whole grid
            right_of_grid = x == self.NUM_COLUMNS - 1
            bottom_of_grid = y == self.NUM_ROWS - 1

            # Generate top line of text for cell representation
            if top_of_box:
                if left_of_box:
                    line = "O======="
                else:
                    line = "========"
            else:
                if left_of_box:
                    line = "‖-------"
                else:
                    line = "+-------"
            lines.append(line)
            # Generate next three lines of text
            if left_of_box:
                lines.append("‖       ")
                lines.append(f"‖   {val_as_str}   ")
                lines.append("‖       ")
            else:
                lines.append("|       ")
                lines.append(f"|   {val_as_str}   ")
                lines.append("|       ")

            if bottom_of_grid:
                # An additional line of text is added to bottom of cell if it's at the bottom of grid
                if left_of_box:
                    lines.append("O=======")
                else:
                    lines.append("========")
            if right_of_grid:
                new_lines = []
                for idx, line in enumerate(lines):
                    add_char = "O" if top_of_box and idx == 0 else "‖"
                    new_lines.append(f"{line}{add_char}")
                lines = new_lines
            return lines

        for y in range(self.NUM_ROWS):
            # All the row strings from each cell will be appended to these
            row_strs = ["", "", "", "", ""]
            for x in range(self.NUM_COLUMNS):
                val = self.cells[y][x]
                lines = _make_cell(x, y, val)
                for idx, line in enumerate(lines):
                    row_strs[idx] = row_strs[idx] + line
            for row in row_strs:
                if len(row) > 0:
                    print(row)

    def get_value(self, x: int, y: int) -> int:
        """Gets the value at a particular cell, returning 0 if a blank cell"""
        if x < 0 or x >= self.NUM_COLUMNS or y < 0 or y >= self.NUM_ROWS:
            raise GridException(f"Bad coordinates ({x},{y})")
        return self.cells[y][x]

    def set_value(self, x: int, y: int, val: int):
        """
        Assigns a value to a cell. Can be used in solving a puzzle, equivalent to player penciling
        in a value.

        :param x: x coordinate of cell
        :param y: y coordinate of cell
        :param val: 0 to clear cell, 1 - 9 to set a value
        :raises GridException: if bad value or coordinates given
        """
        if x < 0 or x >= self.NUM_COLUMNS or y < 0 or y >= self.NUM_ROWS:
            raise GridException(f"Bad coordinates ({x},{y})")
        if val < 0 or val > 9:
            raise GridException(f"Bad value {val}")

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
        if x < 0 or x >= self.NUM_COLUMNS or y < 0 or y >= self.NUM_ROWS:
            raise GridException(f"Bad coordinates ({x},{y})")

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
        if cell_x < 0 or cell_x >= PuzzleGrid.NUM_COLUMNS or cell_y < 0 or cell_y >= PuzzleGrid.NUM_ROWS:
            raise GridException(f"Bad coordinates ({cell_x},{cell_y})")
        return int(cell_x / PuzzleGrid.BOX_SIZE), int(cell_y / PuzzleGrid.BOX_SIZE)

    def clear_row(self, y: int):
        """
        Clears a row of all values and updates accounting data accordingly
        :param y: row index
        """
        if y < 0 or y >= self.NUM_ROWS:
            raise GridException(f"Bad coordinate {y}")
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
        """Populates grid with values that conform to Sudoku rules. There will be no blanks (yet)."""
        redo_count = 0
        max_redos = 40
        while redo_count < max_redos:
            success = self._attempt_populate_cells()
            if success:
                break
            redo_count += 1

        if redo_count == max_redos:
            print("Failure!")
            raise GridException("Could not generate puzzle")

    def add_spaces(self, solver_callback: Callable[[], bool], required_spaces: int = 45) -> bool:
        """
        This function is to be called after the grid has been populated with numbers. It adds the blanks
        that are necessary to make the puzzle interesting to the player. It attempts to keep the spaces
        well-distributed among the boxes, so that we don't have, say, only one blank in the top-left box
        and nine in the bottom-right box.

        :param solver_callback: periodically, the generated puzzle must be tested for solve-ability, which means
            that there must be one solution and one solution only. This callback performs that task, returning
            True if the requirement is met.
        :param required_spaces: the number of spaces that must be added to the grid
        :return: True if success
        """
        self.required_spaces = required_spaces
        self.solver_callback = solver_callback
        self.grid_with_spaces = None
        avg_spaces_per_box = int(required_spaces / (self.NUM_BOXES_X * self.NUM_BOXES_Y))
        # print(f"Average spaces per box: {avg_spaces_per_box}")
        self.min_spaces_per_box = avg_spaces_per_box - 1
        self.max_spaces_per_box = avg_spaces_per_box + 1
        self.space_failure_count = 0

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

    def generate_puzzle(self, solver_callback: Callable[[], bool], required_spaces: int = 45) -> bool:
        """
        Generates a complete puzzle, calling both populate_cells() and add_spaces() in one step.
        :param solver_callback: see add_spaces()
        :param required_spaces: see add_spaces()
        :return: True if puzzle generated successfully
        """
        num_tries = 30
        for _try in range(num_tries):
            self.reset()
            try:
                self.populate_cells()
            except GridException as ex:
                print("Could not populate cells")
                break

            try:
                self.add_spaces(solver_callback, required_spaces)
            except GridException as ex:
                print(f"Failed to add spaces successfully on try number {_try+1}")
            else:
                # Success!
                return True

        return False

    def _attempt_populate_cells(self) -> bool:
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

    def _add_spaces_impl(self, space_markers: List[SpaceMarker], index: int, space_count: int) -> bool:
        """
        This recursive function does the work of adding spaces to the grid. We keep recursing until we find
        a solution that works. If we hit a point of failure, we backtrack and try another path. Standard
        depth-first stuff.

        :param space_markers: a randomized list of unique cells. Each marker includes the value that will
            ultimately appear in the final, solved puzzle.
        :param index: how far we've recursed into the space_markers list
        :param space_count: how many spaces have been added to the grid thus far, through all the
            recursion steps
        :return: True if a solution was found
        """
        if space_count >= self.required_spaces:
            # We've recursed far enough as to have added the required number of spaces, but
            # can we USE this configuration of spaces?
            if not self._check_space_distribution():
                self.space_failure_count += 1
                if self.space_failure_count >= self.MAX_FAILED_SPACE_CONFIGURATIONS:
                    raise GridException(f"Too many failed space configurations. Number tried: {self.space_failure_count}")
                return False

            self.grid_with_spaces = PuzzleGrid()
            self.grid_with_spaces.copy(self)
            return True

        # How many more spaces do we need? Is there room for them?
        needed_spaces = self.required_spaces - space_count
        if (len(space_markers) - index) < needed_spaces:
            # Nope, halt further recursion
            return False

        for i in range(2):
            if i == 0:
                # Put a space here
                marker = space_markers[index]
                self.set_value(marker.x, marker.y, 0)

                # Are spaces properly distributed? We can only have so many per box.
                box_x, box_y = self.get_box_coordinates(marker.x, marker.y)
                box_definites = self.definite_values_per_box[box_y][box_x]
                spaces_in_box = self.BOX_SIZE * self.BOX_SIZE - len(box_definites)

                # We must have an acceptable number of spaces in this box to proceed with recursion
                # (Reminder: a box is different from a cell)
                if spaces_in_box <= self.max_spaces_per_box:
                    # Is the grid solvable from here? If not, no point to adding more spaces.
                    solvable = self.solver_callback()
                    if solvable:
                        success = self._add_spaces_impl(space_markers, index+1, space_count+1)
                        if success:
                            return True

                # Restore the value that used to be there
                self.set_value(marker.x, marker.y, marker.old_val)
            else:
                # Don't put a space here. Just move on with the recursion.
                success = self._add_spaces_impl(space_markers, index+1, space_count)
                if success:
                    return True

        return False

    def _check_space_distribution(self) -> bool:
        """
        Checks that spaces in a proposed puzzle are well-distributed. That is, there's nearly the same
        number of them in each box, plus or minus 1. I can see the importance of this simply by leafing
        through a book of Sudoku puzzles.

        :return: True if the spaces are well-distributed.
        """
        average_spaces_per_box = int(self.required_spaces / (self.NUM_BOXES_X * self.NUM_BOXES_Y))
        boxes_with_avg_num_spaces = 0
        for box_y in range(self.NUM_BOXES_Y):
            for box_x in range(self.NUM_BOXES_X):
                box_definites = self.definite_values_per_box[box_y][box_x]
                spaces_in_box = self.BOX_SIZE * self.BOX_SIZE - len(box_definites)
                if spaces_in_box == average_spaces_per_box:
                    boxes_with_avg_num_spaces += 1
                # We must have an acceptable number of spaces in this box to proceed
                if spaces_in_box > self.max_spaces_per_box or spaces_in_box < self.min_spaces_per_box:
                    return False
        return boxes_with_avg_num_spaces >= 5

