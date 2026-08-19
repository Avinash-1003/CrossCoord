import numpy as np
import os

class GridParser:
    """
    Parses MovingAI format .map files into 2D NumPy arrays.
    Standard characters:
    . or G or S = passable (0)
    @, O, T, W = impassable obstacle (1)
    """
    PASSABLE_CHARS = {'.', 'G', 'S'}

    @staticmethod
    def parse_map(filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Map file not found: {filepath}")

        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            
        # Parse header
        # type octile
        # height x
        # width y
        # map
        if len(lines) < 4 or not lines[3].startswith('map'):
            raise ValueError("Invalid MovingAI map file format.")

        height = int(lines[1].split()[1])
        width = int(lines[2].split()[1])
        
        grid = np.zeros((height, width), dtype=np.int8)

        # Parse map data
        for i in range(height):
            row_str = lines[4 + i]
            for j in range(width):
                char = row_str[j]
                if char not in GridParser.PASSABLE_CHARS:
                    grid[i, j] = 1  # Obstacle

        return grid, height, width

if __name__ == "__main__":
    # Test loading a map
    try:
        grid, h, w = GridParser.parse_map("datasets/disaster_relief/random-32-32-20.map")
        print(f"Successfully loaded map of size {h}x{w}")
        print(f"Obstacles count: {np.sum(grid)}")
        print(f"Passable count: {(h*w) - np.sum(grid)}")
    except Exception as e:
        print(f"Error: {e}")
