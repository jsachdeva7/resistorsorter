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

input_box = pygame.Rect(300, 300, 200, 40)  # Position and size of the input box

# regions for resistors
regions = {}
editing_region = None


# Initialize cursor to be a hand (clicker)
clicker_cursor = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND)

# Try loading slice values from the JSON file
DATA_FILE = "slice_values.json"
try:
    with open(DATA_FILE, "r") as file:
        slice_values = json.load(file)
except FileNotFoundError:
    slice_values = {str(i): None for i in range(NUM_SIDES)}

# Initialize regions dictionary with resistances from slice_values
for i in range(NUM_SIDES):
    resistance_value = slice_values.get(str(i), None)  # Get the resistance value
    regions[str(i)] = {"resistance": resistance_value, "points": []}

print("Regions at mouse click:", regions)



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
        # Ensure the resistance_value is correctly fetched for each region
        resistance_value = slice_values.get(str(i), None)  # Retrieve resistance value for the current region

        # Update the regions dictionary with the square points for the region
        regions[str(i)] = {"resistance": resistance_value, "points": square_points}

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
        resistance = regions.get(str(i), {}).get("resistance", slice_values.get(str(i), None))

        # Draw the square
        pygame.draw.polygon(screen, (0, 0, 0), square_points, 2)  # Black border for square

        # Get the center of the square to position the text
        center_x = (x1 + x2) / 2 - perp_dx * side_length / 2
        center_y = (y1 + y2) / 2 - perp_dy * side_length / 2

        # Display the resistance value as text in the center of the square
        resistance_text = font.render(f"{resistance} Ω", True, (0, 0, 0))  # Black color text
        screen.blit(resistance_text, (center_x - resistance_text.get_width() // 2, center_y - resistance_text.get_height() // 2))

    # If the user is editing a region, display a text box for input
    if editing_region is not None and active:
        pygame.draw.rect(screen, (0, 0, 0), input_box, 2)  # Input box border
        input_text = font.render(user_input, True, (0, 0, 0))  # Render user input
        screen.blit(input_text, (input_box.x + 5, input_box.y + 5))  # Display the input text

    # Change the cursor to a hand (clicker) if hovering over a region
    if hovered_region is not None:
        pygame.mouse.set_cursor(clicker_cursor)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

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
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # If mouse click on region, start editing that region
            mouse_x, mouse_y = pygame.mouse.get_pos()
            for region_id, region_data in regions.items():
                square_points = region_data["points"]
                if point_in_polygon((mouse_x, mouse_y), square_points):
                    editing_region = region_id
                    user_input = str(slice_values.get(region_id, ""))  # Retrieve initial resistance value
                    active = True  # Activate text input
                    break
            
            # Print regions for debugging
            print("Regions at mouse click:", regions)
        elif event.type == pygame.KEYDOWN:
            if active:
                if event.key == pygame.K_RETURN:  # When Enter is pressed, save the value
                    try:
                        resistance_value = float(user_input)
                        regions[editing_region]["resistance"] = resistance_value  # Update dictionary for the specific region
                        slice_values[editing_region] = resistance_value  # Update dictionary
                    except ValueError:
                        pass  # Handle invalid input gracefully
                    active = False  # Deactivate input box
                    user_input = ""  # Clear the input box
                elif event.key == pygame.K_BACKSPACE:
                    user_input = user_input[:-1]  # Remove last character
                else:
                    user_input += event.unicode  # Add typed character to the input string
    draw_pie()
    pygame.display.flip()
pygame.quit()