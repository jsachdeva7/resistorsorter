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

# regions for resistors
regions = {}

# Initialize cursor to be a hand (clicker)
clicker_cursor = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND)

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

    hovered_region = None  # To track which region the mouse is hovering over

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

        # Check if the mouse is over this region (square)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if point_in_polygon((mouse_x, mouse_y), square_points):
            hovered_region = i  # Track which region is hovered over
            # Change the color of the square to yellow
            pygame.draw.polygon(screen, (255, 254, 179), square_points)
        else:
            # Draw the square in the normal color
            pygame.draw.polygon(screen, (0, 0, 0), square_points, 2)  # Black border for square

        # Get resistance for the region
        resistance = slice_values.get(str(i), None)

        # Store the square region in the dictioniary w/ resistance as the key
        regions[resistance] = square_points


        # Draw the square
        pygame.draw.polygon(screen, (0, 0, 0), square_points, 2)  # Black border for square

        # Get the center of the square to position the text
        center_x = (x1 + x2) / 2 - perp_dx * side_length / 2
        center_y = (y1 + y2) / 2 - perp_dy * side_length / 2

        # Display the resistance value as text in the center of the square
        resistance_text = font.render(f"{resistance} Ω", True, (0, 0, 0))  # Black color text
        screen.blit(resistance_text, (center_x - resistance_text.get_width() // 2, center_y - resistance_text.get_height() // 2))

    # # For testing purposes, let's print the dictionary (show the regions and their corresponding resistance values)
    # print("Regions with Resistances:")
    # for resistance, region in regions.items():
    #     print(f"Resistance: {resistance}, Region: {region}")
    # Change the cursor to a hand (clicker) if hovering over a region

    if hovered_region is not None:
        pygame.mouse.set_cursor(clicker_cursor)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        
# Helper function to check if a point is inside a polygon
def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    n = len(polygon)
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

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