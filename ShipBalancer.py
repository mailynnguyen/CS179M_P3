import numpy as np
import math
from datetime import datetime

# turns the file into a 2d array
def load_ship(filename):
    grid = np.full((8, 12), np.nan) # creates an 8 x 12 grid and fills every cell with nan
    with open(filename, "r") as f: # opens file for reading
        for line in f: # iterates through the file line by line
            line = line.strip() # gets rid of beginning and ending whitespaces in line
            left, right = line.split("],") # split the line up, left = [coord, right = {weight}, desc
            rc = left[1:] # get the row and column - format ex. -> 08,04
            r_str, c_str = rc.split(",")
            r = int(r_str) - 1
            c = int(c_str) - 1
            # cleans and strips the weight and desc
            weight_part, desc_part = right.split("},")
            weight_str = weight_part.strip().lstrip("{")
            desc = desc_part.strip()
            # fills grid with corresponding values
            if desc == "NAN":
                grid[r, c] = np.nan
            else:
                w = int(weight_str)
                if desc.upper().startswith("UNUSED"):
                    grid[r, c] = 0
                else:
                    grid[r, c] = w

    # grid is currently upside-down
    return grid

# gets the weight value of a cell
def get_weight(val):
    # return val // 10 if not np.isnan(val) and val != 0 else 0
    return val if not np.isnan(val) and val != 0 else 0

#computes the weights of the left and right side of the grid
def compute_sides(grid):
    rows, cols = grid.shape # extracts rows and cols from grid (8, 12)
    mid = cols // 2 # divides col by 2 and floors the result, ex. 17 // 2 = 8
    left = grid[:, :mid] # take every row and column starting at 0 until mid (not including mid) ex. 0,1,2,3,4,5
    right = grid[:, mid:] # take very row and column starting at mid until the end ex. 6,7,8,9,10,11
    w_left = sum(get_weight(x) for x in left.flatten()) # gets the weight of every value on the left side and add up the sum
    w_right = sum(get_weight(x) for x in right.flatten()) # gets the weight of every value on the right side and add up the sum
    return w_left, w_right # returns the left and right weight

def find_cells(grid):
    rows, cols = grid.shape # extracts the rows and cols from grid (8, 12)
    occupied = []
    empty = []
    for r in range(rows):
        for c in range(cols):
            if np.isnan(grid[r, c]): # if cell is nan, continue
                continue
            if grid[r, c] == 0: # if cell is 0, append the tuple value into the empty array
                empty.append((r, c))
            else: # else, append into the occupied array
                occupied.append((r, c))
    return occupied, empty

def format_coord(r, c):
    return f"[{r+1:02d},{c+1:02d}]"

def move_cost(r1, c1, r2, c2):
    PARK_ROW, PARK_COL = 7, 0
    return abs(PARK_ROW - r1) + abs(PARK_COL - c1) + abs(r1 - r2) + abs(c1 - c2) + abs(r2 - PARK_ROW) + abs(c2 - PARK_COL)

def describe_move(r1, c1, r2, c2):
    PARK_ROW, PARK_COL = 7, 0

    first_move_cost = abs(PARK_ROW - r1) + abs(PARK_COL - c1)
    second_move_cost = abs(r1 - r2) + abs(c1 - c2)
    third_move_cost = abs(PARK_ROW - r2) + abs(PARK_COL - c2)

    src = format_coord(r1, c1)
    dst = format_coord(r2, c2)

    return [
        f"Move from PARK to {src}, {first_move_cost} minutes",
        f"Move container in {src} to {dst}, {second_move_cost} minutes",
        f"Move from {dst} to PARK, {third_move_cost} minutes"
    ]

def side_of(c, total_cols):
    mid = total_cols // 2
    return "L" if c < mid else "R"

def compute_balance_moves(grid):
    moves = [] # empty array to hold moves
    rows, cols = grid.shape # extract the rows and cols from grid (8, 12)
    w_left, w_right = compute_sides(grid) # gets the left and right weights
    diff = w_left - w_right # find the difference between left side and right side

    sum = w_left + w_right
    right_side_formula = sum // 10
    
    # if abs(diff) <= 1:
    #     return moves
    if abs(diff) <= right_side_formula:
        return moves
    
    # occupied holds the tuple of the weighted cells, ex. (r, c)
    # empty holds the tuple of 0 weighted cells, ex. (r, c)
    occupied, empty = find_cells(grid)

    if diff > 1: # if diff is positive, left side is heavier
        left_containers = [(r, c) for (r, c) in occupied if side_of(c, cols) == "L"] # gets the left containers
        right_empty = [(r, c) for (r, c) in empty if side_of(c, cols) == "R"] # gets the right cells that are empty
        if not left_containers or not right_empty: # if there is no space or no containers to move
            return moves
        
        # checks for the best move using Manhattan Distance
        best = None
        best_cost = float('inf')
        for (r1, c1) in left_containers:
            for (r2, c2) in right_empty:
                cost = move_cost(r1, c1, r2, c2)
                if cost < best_cost:
                    best = (r1, c1, r2, c2)
                    best_cost = cost
 
        # once found append the move with the cost to moves array
        r1, c1, r2, c2 = best
        moves.append((r1, c1, r2, c2, best_cost))
        # swap the cells
        grid[r2, c2] = grid[r1, c1]
        grid[r1, c1] = 0

    elif diff < -1:
        right_containers = [(r, c) for (r, c) in occupied if side_of(c, cols) == "R"]
        left_empty = [(r, c) for (r, c) in empty if side_of(c, cols) == "L"]
        if not right_containers or not left_empty:
            return moves
        
        best = None
        best_cost = float('inf')
        for (r1, c1) in right_containers:
            for (r2, c2) in left_empty:
                cost = move_cost(r1, c1, r2, c2)
                if cost < best_cost:
                    best = (r1, c1, r2, c2)
                    best_cost = cost

        r1, c1, r2, c2 = best
        moves.append((r1, c1, r2, c2, best_cost))
        grid[r2, c2] = grid[r1, c1]
        grid[r1, c1] = 0

    return moves # will have only one move

def write_output_file(infile, grid):
    out = infile.replace(".txt", "OUTBOUND.txt")
    with open(out, "w") as f:
        rows, cols = grid.shape
        for r in range(rows):
            line = ""
            for c in range(cols):
                if np.isnan(grid[r, c]):
                    line += "NaN "
                else:
                    line += f"{int(grid[r, c])} "
            f.write(line.strip() + "\n")
    return out

def make_logfile_name(input_file, start_time):
    new_filename = input_file.replace(".txt", "")
    return f"{new_filename}{start_time.month:02d}_{start_time.year}_{start_time.hour:02d}{start_time.minute:02d}.txt"

def log_line(log_file, curr_time, line):
    timestamp = curr_time.strftime("%m %d %Y: %H:%M ")
    log_file.write(timestamp + line + "\n")

def print_solution(moves, outfile_name):
    total_steps = len(moves) * 3
    step_num = 1

    total_minutes = sum(m[4] for m in moves)
    total_moves = len(moves)

    print(f"… solution was found, it will take {total_minutes} minutes and {total_moves} moves")

    for i, (r1, c1, r2, c2, cost) in enumerate(moves, start=1):
        steps = describe_move(r1, c1, r2, c2)
        for step in steps:
            print(f"{step_num} of {total_steps}: {step}")
            step_num += 1

    print(f"Done! {outfile_name} was written to the desktop")

def main():
    curr_time = datetime.now().strftime("%H%M")
    print(curr_time)
    infile = input("Enter ship file name: ")
    grid = load_ship(infile)
    moves = compute_balance_moves(grid)
    outfile = write_output_file(infile, grid)
    print_solution(moves, outfile)

if __name__ == "__main__":
    main()
