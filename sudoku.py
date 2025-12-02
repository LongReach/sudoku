from puzzle_grid import PuzzleGrid
from solver import solve_sample_puzzle, BruteForceSolver

def main():
    print("\nPopulating puzzle from hard-coded values:")
    solve_sample_puzzle()

    print("\nGenerating puzzle:\n")
    grid = PuzzleGrid()
    grid.populate_cells()
    grid.print_cells()

    solver = BruteForceSolver(grid)

    def solver_func() -> bool:
        solution_count, solution_grip = solver.solve()
        return solution_count == 1

    print("\nAdding spaces")
    num_spaces = 46
    success = grid.add_spaces(solver_func, num_spaces)
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

if __name__ == '__main__':
    main()
