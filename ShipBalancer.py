import numpy as np
import math
from datetime import datetime

# turns the file into a 2d array
def load_ship(filename):
    grid = np.full((8, 12), np.nan)
    with open(filename, "r") as f:
        for line in f:
            line = line.strip()
            if not line or not line.startswith("["):
                continue
            left, right = line.split("],")
            rc = left.strip()[1:]
            r_str, c_str = rc.split(",")
            r = int(r_str) - 1
            c = int(c_str) - 1
            weight_part, desc_part = right.split("},")
            weight_str = weight_part.strip().lstrip("{")
            desc = desc_part.strip()
            if weight_str == "NAN":
                grid[r, c] = np.nan
            else:
                w = int(weight_str)
                if desc.upper().startswith("UNUSED"):
                    grid[r, c] = 0
                else:
                    grid[r, c] = w
    return grid

def get_weight(val):
    return math.floor(val / 10) if not np.isnan(val) and val != 0 else 0

def compute_sides(grid):
    rows, cols = grid.shape
    mid = cols // 2
    left = grid[:, :mid]
    right = grid[:, mid:]
    w_left = sum(get_weight(x) for x in left.flatten())
    w_right = sum(get_weight(x) for x in right.flatten())
    return w_left, w_right

def find_cells(grid):
    rows, cols = grid.shape
    occupied = []
    empty = []
    for r in range(rows):
        for c in range(cols):
            if np.isnan(grid[r, c]):
                continue
            if grid[r, c] == 0:
                empty.append((r, c))
            else:
                occupied.append((r, c))
    return occupied, empty

def format_coord(r, c):
    return f"[{r+1:02d},{c+1:02d}]"

def move_cost(r1, c1, r2, c2):
    return abs(r1 - r2) + abs(c1 - c2)

def describe_move(r1, c1, r2, c2):
    # if r1 == -1 and c1 == -1:
    #     return "Move from PARK to " + format_coord(r2, c2)
    # if r2 == -1 and c2 == -1:
    #     return "Move from " + format_coord(r1, c1) + " to PARK"
    # return f"Move container in {format_coord(r1, c1)} to {format_coord(r2, c2)}"
    PARK_ROW, PARK_COL = 8, 1

    first_move_cost = move_cost(PARK_ROW, PARK_COL, r1, c1)
    second_move_cost = move_cost(r1, c1, r2, c2)
    third_move_cost = move_cost(r2, c2, PARK_ROW, PARK_COL)
    # total_cost = first_move_cost + second_move_cost + third_move_cost

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
    moves = []
    rows, cols = grid.shape
    w_left, w_right = compute_sides(grid)
    diff = w_left - w_right

    if abs(diff) <= 1:
        return moves

    occupied, empty = find_cells(grid)

    if diff > 1:
        left_containers = [(r, c) for (r, c) in occupied if side_of(c, cols) == "L"]
        right_empty = [(r, c) for (r, c) in empty if side_of(c, cols) == "R"]
        if not left_containers or not right_empty:
            return moves
        r1, c1 = left_containers[0]
        r2, c2 = right_empty[0]
        cost = move_cost(r1, c1, r2, c2)
        moves.append((r1, c1, r2, c2, cost))
        grid[r2, c2] = grid[r1, c1]
        grid[r1, c1] = 0

    elif diff < -1:
        right_containers = [(r, c) for (r, c) in occupied if side_of(c, cols) == "R"]
        left_empty = [(r, c) for (r, c) in empty if side_of(c, cols) == "L"]
        if not right_containers or not left_empty:
            return moves
        r1, c1 = right_containers[0]
        r2, c2 = left_empty[0]
        cost = move_cost(r1, c1, r2, c2)
        moves.append((r1, c1, r2, c2, cost))
        grid[r2, c2] = grid[r1, c1]
        grid[r1, c1] = 0

    return moves

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
    # total_minutes = 0
    # for (r1, c1, r2, c2, cost) in moves:
    #     steps = describe_move(r1, c1, r2, c2)
    #     for text, minutes in steps:
    #         total_minutes += minutes

    total_moves = len(moves)

    print(f"… solution was found, it will take {total_minutes} minutes and {total_moves} moves")

    for i, (r1, c1, r2, c2, cost) in enumerate(moves, start=1):
        steps = describe_move(r1, c1, r2, c2)
        # print(f"{i} of {total_moves}: {action}, {cost} minutes")
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
