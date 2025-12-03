from puzzle_grid import PuzzleGrid, GridException
from typing import List, Any, Set, Tuple, Optional

sample_puzzle = [
    [8, 5, 0, 0, 0, 1, 0, 0, 6],
    [0, 0, 7, 0, 6, 4, 1, 0, 0],
    [0, 0, 4, 0, 7, 0, 5, 9, 0],
    [2, 0, 0, 0, 5, 6, 0, 0, 4],
    [6, 0, 0, 1, 0, 9, 0, 7, 0],
    [7, 0, 1, 0, 4, 0, 0, 0, 9],
    [0, 1, 0, 9, 0, 0, 4, 6, 0],
    [0, 9, 6, 0, 0, 8, 0, 0, 7],
    [0, 7, 0, 6, 0, 0, 0, 0, 1]
]

# Contains overly-long row
bad_puzzle_1 = [
    [8, 5, 0, 0, 0, 1, 0, 0, 6],
    [0, 0, 7, 0, 6, 4, 1, 0, 0],
    [0, 0, 4, 0, 7, 0, 5, 9, 0],
    [2, 0, 0, 0, 5, 6, 0, 0, 4, 3],
    [6, 0, 0, 1, 0, 9, 0, 7, 0],
    [7, 0, 1, 0, 4, 0, 0, 0, 9],
    [0, 1, 0, 9, 0, 0, 4, 6, 0],
    [0, 9, 6, 0, 0, 8, 0, 0, 7],
    [0, 7, 0, 6, 0, 0, 0, 0, 1]
]

# Contains unacceptable value
bad_puzzle_2 = [
    [111, 5, 0, 0, 0, 1, 0, 0, 6],
    [0, 0, 7, 0, 6, 4, 1, 0, 0],
    [0, 0, 4, 0, 7, 0, 5, 9, 0],
    [2, 0, 0, 0, 5, 6, 0, 0, 4],
    [6, 0, 0, 1, 0, 9, 0, 7, 0],
    [7, 0, 1, 0, 4, 0, 0, 0, 9],
    [0, 1, 0, 9, 0, 0, 4, 6, 0],
    [0, 9, 6, 0, 0, 8, 0, 0, 7],
    [0, 7, 0, 6, 0, 0, 0, 0, 1]
]

class BruteForceSolver:
    """
    A class that solves a Sudoku puzzle by brute force. See README for more info.
    """

    def __init__(self, grid: PuzzleGrid):
        self.grid: PuzzleGrid = grid
        # This will be a two-dimensional list. For each cell, there's a list containing values that
        # would work in that call, if it's blank. If not blank, the list will be empty.
        self.options: List[List[List[int]]] = []

        for y in range(PuzzleGrid.NUM_ROWS):
            options_row: List[List[int]] = []
            for x in range(PuzzleGrid.NUM_COLUMNS):
                empty_cell, options = self.grid.get_possible_values(x, y)
                options_row.append(list(options))
            self.options.append(options_row)

        self.solved_puzzle: Optional[PuzzleGrid] = None

    def set_value(self, x: int, y: int, val: int):
        """
        Equivalent to penciling in a value while solving puzzle. Or making cell empty again.
        :param x: --
        :param y: --
        :param val: 0 for blank cell, 1 - 9 otherwise
        """
        options_list = self.options[y][x]
        options_list.clear()
        self.grid.set_value(x, y, val)
        if val == 0:
            empty_cell, options = self.grid.get_possible_values(x, y)
            options_list.extend(options)

    def solve(self) -> Tuple[int, Optional[PuzzleGrid]]:
        """
        Tries to solve the puzzle.
        :return: (number of possible solutions, a PuzzleGrid containing a solution that works (or None))
        """
        success_count = self._solve_impl(0)
        return success_count, self.solved_puzzle

    def _solve_impl(self, index: int) -> int:
        """
        Recursive solve function. Think of the grid being converted to a one-dimensional list
        of cells (from top-left to bottom-right, typewriter style). The index marks how far
        we've recursed into that list.

        :param index: --
        :return: number of solutions recursively found, or 0
        """
        if index >= PuzzleGrid.NUM_ROWS * PuzzleGrid.NUM_COLUMNS:
            # We've recursed all the way to the end of the one-dimensional list, therefore a
            # solution has been found.
            if self.solved_puzzle is None:
                self.solved_puzzle = PuzzleGrid()
            self.solved_puzzle.copy(self.grid)
            return 1
        x, y = self._index_to_coordinate(index)
        empty_cell, options = self.grid.get_possible_values(x, y)
        if empty_cell and len(options) == 0:
            # There are no possible options that would work, return failure
            return 0
        if not empty_cell:
            # This is not a blank cell, recursively advance to next cell
            return self._solve_impl(index+1)
        success_count = 0
        for val in options:
            # Let's try this value, then recursively advance to next cell
            self.set_value(x, y, val)
            recursive_success_count = self._solve_impl(index+1)
            success_count += recursive_success_count
            self.set_value(x, y, 0)
        return success_count

    @staticmethod
    def _index_to_coordinate(index: int) -> Tuple[int, int]:
        """
        If the grid is "unrolled" into a one-dimensional list, this function takes an index into
        that list and returns the corresponding two-dimensional coordinates.
        """
        row = int(index / PuzzleGrid.NUM_COLUMNS)
        column = index % PuzzleGrid.NUM_COLUMNS
        return column, row

def solve_sample_puzzle(which_sample: int):
    """Solves one of the sample puzzles found at the top of this file."""
    puzzle_to_use = sample_puzzle
    exception_expected = False
    if which_sample == 1:
        puzzle_to_use = bad_puzzle_1
        exception_expected = True
    if which_sample == 2:
        puzzle_to_use = bad_puzzle_2
        exception_expected = True

    grid = PuzzleGrid()
    try:
        grid.populate_from_list(puzzle_to_use)
    except GridException as ex:
        print(f"Got exception: {ex}")
        if exception_expected:
            print("(An expected exception)")
        else:
            print("NOT an expected exception!")
        return
    grid.print_cells()

    solver = BruteForceSolver(grid)
    success_count, solved_grid = solver.solve()
    if success_count > 0:
        print("\nSolved puzzle:")
        solved_grid.print_cells()