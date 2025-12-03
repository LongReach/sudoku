from puzzle_grid import PuzzleGrid
from solver import solve_sample_puzzle, BruteForceSolver

import argparse

def run_test(which_test: int):
    if 1 <= which_test <= 3:
        print("\nPopulating puzzle from hard-coded values:")
        solve_sample_puzzle(which_test - 1)
    else:
        print(f"Unknown test {which_test}")

def main(num_spaces: int):
    print("Generating puzzle:")
    grid = PuzzleGrid()

    solver = BruteForceSolver(grid)

    def solver_func() -> bool:
        solution_count, solution_grip = solver.solve()
        return solution_count == 1

    print("\nAdding spaces...")
    success = grid.generate_puzzle(solver_func, num_spaces)
    if success:
        print(f"\nSuccessfully added {num_spaces} spaces!")
        grid.print_cells()
    else:
        print("\nFailed to add spaces.")
        return

    solver = BruteForceSolver(grid)
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
    parser.add_argument("--spaces", help="Number of spaces to put in puzzle (more for harder puzzle)", type=int, required=False, default=0)
    args = parser.parse_args()

    if args.test > -1:
        run_test(args.test)
    elif args.spaces > 0:
        main(args.spaces)
    else:
        print("No valid argument given. Use --help argument for more info.")
