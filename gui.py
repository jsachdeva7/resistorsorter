import sys
sys.path.append(r"C:\Users\Jagat Sachdeva\AppData\Local\Programs\Python\Python312\Lib\site-packages")

import pygame
import math
import json
import serial
import time

WIDTH, HEIGHT = 1250, 750
SHIFT_DOWN = 17.5
CENTER = (WIDTH // 3, HEIGHT // 2 + SHIFT_DOWN)
RADIUS = 200
SQUARE_SIZE = 25
NUM_SIDES = 9
ANGLE = 360 / NUM_SIDES
COLORS = [(100, 150, 255)] * NUM_SIDES

input_box = pygame.Rect(300, 300, 200, 40)  # Position and size of the input box

# booleans for mouse value
region_hover = False
go_hover = False
go_pressed = False

# regions for resistors
regions = {}
editing_region = None

# Initialize cursor to be a hand (clicker)
clicker_cursor = pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_HAND)

rotation_angle = 0  # Initial rotation angle (in degrees)

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
    regions[str(i)] = {
        "index": i + 1,
        "resistance": resistance_value, 
        "points": []
    }

# Setup serial communication
SERIAL_PORT = "COM7"  # Change this to the appropriate port 
BAUD_RATE = 9600  # This should match the Arduino's baud rate

ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
time.sleep(2)

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Resistor Sorter GUI")
font = pygame.font.Font(None, 30)
bigger_font = pygame.font.Font(None, 45)

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

def draw_pie():
    global region_hover

    nonagon_points = []

    # Apply rotation based on the current angle
    for i in range(NUM_SIDES):
        angle = math.radians(i * ANGLE + rotation_angle)  # Apply rotation to each point
        x = CENTER[0] + RADIUS * math.cos(angle)  # X-coordinate
        y = CENTER[1] + RADIUS * math.sin(angle)  # Y-coordinate
        nonagon_points.append((x, y))  # Add rotated vertex to the points list

    # Rest of the code remains the same, just using `nonagon_points` for drawing
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
        
        # Update the regions dictionary with the square points for the region
        resistance_value = slice_values.get(str(i), None)  # Retrieve resistance value for the current region

        regions[str(i)] = {
            "resistance": resistance_value, 
            "points": square_points,
            "index": i + 1
        }

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

        # Now calculate the opposite position to place the region index number
        opposite_x = center_x + perp_dx * 2 * side_length / 3  # Move away from the square along the perpendicular
        opposite_y = center_y + perp_dy * 2 * side_length / 3

        # Display the region index number at the opposite side of the nonagon edge
        index_text = bigger_font.render(f"{regions[str(i)]['index']}", True, (0, 0, 0))  # Black color text for index
        screen.blit(index_text, (opposite_x - index_text.get_width() // 2, opposite_y - index_text.get_height() // 2))
        
    # Calculate the position to center the input box on the screen
    input_box_width, input_box_height = input_box.width, input_box.height
    input_box.x = (WIDTH / 1.5 - input_box_width) // 2
    input_box.y = (HEIGHT - input_box_height) // 2 + SHIFT_DOWN

    # If the user is editing a region, display a text box for input
    if editing_region is not None and active:
        # Draw the input box border
        pygame.draw.rect(screen, (0, 0, 0), input_box, 2)

        # Render the user input text
        input_text = font.render(user_input, True, (0, 0, 0))

        # Calculate the position to center the text inside the input box
        text_x = input_box.x + (input_box.width - input_text.get_width()) // 2
        text_y = input_box.y + (input_box.height - input_text.get_height()) // 2

        # Display the centered input text
        screen.blit(input_text, (text_x, text_y))

    # Change the cursor to a hand (clicker) if hovering over a region
    if hovered_region is not None:
        region_hover = True
    else:
        region_hover = False
        
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

def draw_table():
    # Table dimensions
    row_height = 40
    col_widths = [80, 160, 80]  # Column widths for Box Number, Resistance, and Count
    table_width = sum(col_widths)  # Total width of table
    table_height = (NUM_SIDES + 1) * row_height  # Total height of table (including header)

    # Define center-based position
    center_x = (4 * WIDTH) // 5
    center_y = HEIGHT // 2

    # Adjust table position based on center
    table_x = center_x - (table_width // 2)
    table_y = center_y - (table_height // 2)

    # Render table headers
    headers = ["Box", "Resistance (Ω)", "Count"]
    for j, header in enumerate(headers):
        text = font.render(header, True, (0, 0, 0))
        text_rect = text.get_rect()
        column_center_x = table_x + sum(col_widths[:j]) + (col_widths[j] // 2)
        text_rect.center = (column_center_x, table_y + row_height // 2)
        screen.blit(text, text_rect)

    # Draw table rows
    for i in range(NUM_SIDES):
        box_num = str(i + 1)
        resistance = str(regions.get(str(i), {}).get("resistance", "N/A"))  # Get resistance
        count = "0"  # Placeholder for number of resistors (modify as needed)

        values = [box_num, resistance, count]
        for j, value in enumerate(values):
            text = font.render(value, True, (0, 0, 0))
            text_rect = text.get_rect()
            column_center_x = table_x + sum(col_widths[:j]) + (col_widths[j] // 2)
            row_center_y = table_y + (i + 1) * row_height + (row_height // 2)
            text_rect.center = (column_center_x, row_center_y)
            screen.blit(text, text_rect)

        # Draw row separator lines
        pygame.draw.line(screen, (0, 0, 0), (table_x, table_y + (i + 1) * row_height),
                         (table_x + table_width, table_y + (i + 1) * row_height), 1)

    # Draw column separator lines
    x_offset = table_x
    pygame.draw.line(screen, (0, 0, 0), (x_offset, table_y), (x_offset, table_y + table_height), 1)
    for width in col_widths:
        x_offset += width
        pygame.draw.line(screen, (0, 0, 0), (x_offset, table_y), (x_offset, table_y + table_height), 1)


def draw_go_button():
    global go_hover 
    global go_pressed

    button_width = 200
    button_height = 40
    button_x = (WIDTH / 1.5 - button_width) // 2  # Center horizontally
    button_y = (HEIGHT - button_height) // 2 + SHIFT_DOWN  # Center vertically

    # Define the button rectangle
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Draw the button (light gray background)
    pygame.draw.rect(screen, (221, 255, 209), button_rect)

    # Render the "GO!" text on the button
    button_text = font.render({"GO!" if not go_pressed else "Starting..."}, True, (0, 0, 0))  # Black text

    # Check for mouse click on the button
    mouse_x, mouse_y = pygame.mouse.get_pos()
    if button_rect.collidepoint(mouse_x, mouse_y):
        go_hover = True
        pygame.draw.rect(screen, (195, 227, 184), button_rect)
        if pygame.mouse.get_pressed()[0]:  # Left mouse button
            print("Sending data to Arduino...")

            filtered_regions = {
                key: {k: v for k, v in region.items() if k != "points"}
                for key, region in regions.items()
            }

            json_data = json.dumps(filtered_regions)
            ser.write(json_data.encode())
            ser.flush()
            time.sleep(1)
    else:
        go_hover = False

    pygame.draw.rect(screen, (0, 0, 0), button_rect, 2)  # Button border (black)
    screen.blit(button_text, (button_x + (button_width - button_text.get_width()) // 2,
                                button_y + (button_height - button_text.get_height()) // 2))

# Main loop
running = True
active = False

while running:    
    screen.fill((255, 255, 255))
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
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                rotation_angle -= 2.5  # Rotate left by 5 degrees
            elif event.key == pygame.K_RIGHT:
                rotation_angle += 2.5  # Rotate right by 5 degrees
                
            if active:
                if event.key == pygame.K_RETURN:  # When Enter is pressed, save the value
                    try:
                        resistance_value = int(user_input)
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
    
    # Render instruction text
    instruction_text = font.render("Click on a box to set the resistance values for sorting, and GO when all ready to sort!", True, (0, 0, 0))

    # Calculate the center position
    text_x = (WIDTH - instruction_text.get_width()) // 2  # Center horizontally
    text_y = 20  # Position near the top

    # Draw the text on the screen
    screen.blit(instruction_text, (text_x, text_y))
    

    
    draw_pie()
    draw_table()
    if not active:
        draw_go_button()
    
    if go_hover or region_hover:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    pygame.display.flip()
pygame.quit()