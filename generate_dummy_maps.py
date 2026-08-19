import os
import random

def create_map(filepath, height, width, obstacle_prob=0.2):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        f.write("type octile\n")
        f.write(f"height {height}\n")
        f.write(f"width {width}\n")
        f.write("map\n")
        for _ in range(height):
            row = ''.join(['@' if random.random() < obstacle_prob else '.' for _ in range(width)])
            f.write(row + '\n')

if __name__ == "__main__":
    create_map("datasets/logistics/Berlin_1_256.map", 256, 256, 0.15)
    create_map("datasets/search_and_rescue/Boston_0_256.map", 256, 256, 0.25)
    create_map("datasets/disaster_relief/random-32-32-20.map", 32, 32, 0.20)
    print("Generated dummy MovingAI benchmark maps.")
