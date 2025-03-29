import sys
sys.path.append(r"C:\Users\Jagat Sachdeva\AppData\Local\Programs\Python\Python312\Lib\site-packages")

import pygame
import math
import json

WIDTH, HEIGHT = 750, 750
CENTER = (WIDTH // 2, HEIGHT // 2)
RADIUS = 200
SQUARE_SIZE = 25
NUM_SIDES = 9
ANGLE = 360 / NUM_SIDES
COLORS = [(100, 150, 255)] * NUM_SIDES

DATA_FILE = "slice_values.json"
try:
    with open(DATA_FILE, "r") as file:
        slice_values = json.load(file)
except FileNotFoundError:
    slice_values = {str(i): None for i in range(NUM_SIDES)}


# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Resistor Sorter GUI")
font = pygame.font.Font(None, 30)

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def draw_pie():
    screen.fill((255, 255, 255))

    nonagon_points = []
    for i in range(NUM_SIDES):
        angle = math.radians(i * ANGLE)  # Calculate angle in radians
        x = CENTER[0] + RADIUS * math.cos(angle)  # X-coordinate
        y = CENTER[1] + RADIUS * math.sin(angle)  # Y-coordinate
        nonagon_points.append((x, y))  # Add vertex to the points list

    side_length = distance(nonagon_points[0], nonagon_points[1])

    # Draw the nonagon (connect the vertices)
    pygame.draw.polygon(screen, (255, 255, 255), nonagon_points)  # White color
    pygame.draw.polygon(screen, (0, 0, 0), nonagon_points, 2)  # Black border

    # Draw squares extending from each edge of the nonagon
    for i in range(NUM_SIDES):
        # Get the start and end points of the current edge
        x1, y1 = nonagon_points[i]
        x2, y2 = nonagon_points[(i + 1) % NUM_SIDES]

        # Calculate the direction of the edge (unit vector)
        edge_dx = x2 - x1
        edge_dy = y2 - y1
        length = math.sqrt(edge_dx**2 + edge_dy**2)

        # Normalize the direction vector (so it only represents direction)
        unit_dx = edge_dx / length
        unit_dy = edge_dy / length

        # Perpendicular vector (rotate the direction 90 degrees)
        perp_dx = -unit_dy
        perp_dy = unit_dx

        # Calculate the positions of the four corners of the square
        square_points = [
            (x2, y2),  # 1st corner (extends out)
            (x1, y1),  # 2nd corner (extends out)
            (x1 - perp_dx * side_length, y1 - perp_dy * side_length),  # 3rd corner (back to nonagon)
            (x2 - perp_dx * side_length, y2 - perp_dy * side_length),  # 4th corner (back to nonagon)
        ]
        
        # Draw the square
        # pygame.draw.polygon(screen, (255, 255, 255), square_points)
        pygame.draw.polygon(screen, (0, 0, 0), square_points, 2)  # Black border for square
        

# Main loop
running = True
while running:
    draw_pie()
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # elif event.type == pygame.MOUSEBUTTONDOWN:
        #     x, y = event.pos
        #     distance = math.hypot(x - CENTER[0], y - CENTER[1])

        #     if distance <= RADIUS:  # Click inside the circle
        #         index = get_slice_index(x, y)
        #         new_value = input(f"Enter value for slice {index}: ")
                
        #         if new_value.isdigit():
        #             slice_values[str(index)] = int(new_value)
        #             COLORS[index] = (0, 200, 100)  # Change color to green
        #             with open(DATA_FILE, "w") as f:
        #                 json.dump(slice_values, f)
pygame.quit()