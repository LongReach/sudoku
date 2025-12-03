from puzzle_grid import PuzzleGrid
from solver import solve_sample_puzzle, BruteForceSolver

import argparse


def run_test(which_test: int):
    if 1 <= which_test <= 3:
        print("\nPopulating puzzle from hard-coded values:")
        solve_sample_puzzle(which_test - 1)
    else:
        print(f"Unknown test {which_test}")


def main(num_spaces: int, forgiving_distribution: bool, solve: bool):
    print("Generating puzzle:")
    grid = PuzzleGrid()

    solver = BruteForceSolver(grid)

    def solver_func() -> bool:
        solution_count, solution_grip = solver.solve()
        return solution_count == 1

    print("\nAdding spaces...")
    success = grid.generate_puzzle(solver_func, num_spaces, forgiving_distribution=forgiving_distribution)
    if success:
        print(f"\nSuccessfully added {num_spaces} spaces!")
        grid.print_cells()
    else:
        print("\nFailed to add spaces.")
        return

    solver = BruteForceSolver(grid)
    if solve:
        print("\nSolving...")
        success_count, solved_grid = solver.solve()
        if success_count == 1 and solved_grid:
            print("Yay, solved")
            solved_grid.print_cells()
        else:
            print("What? Could not solve!")

    print("\nThe original puzzle again:")
    grid.super_print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", help="If given, run specified test", type=int, required=False, default=-1)
    parser.add_argument("--spaces", help="Number of spaces to put in puzzle (start with 45, more for harder puzzle)",
                        type=int, required=False, default=0)
    parser.add_argument("--clues", help="Number of clues to put in puzzle. Alternative to spaces argument (start with 36, fewer for harder puzzle).",
                        type=int, required=False, default=0)
    parser.add_argument("--forgiving", help="If given, use more forgiving space distribution. Use when it's taking too long to generate puzzles.", action="store_true")
    parser.add_argument("--solve", help="If given, solve puzzle", action="store_true")
    args = parser.parse_args()

    if args.test > -1:
        run_test(args.test)
    elif args.spaces > 0:
        main(args.spaces, args.forgiving, args.solve)
    elif args.clues > 0:
        main(PuzzleGrid.NUM_ROWS * PuzzleGrid.NUM_COLUMNS - args.clues, args.forgiving, args.solve)
    else:
        print("No valid argument given. Use --help argument for more info.")
