import cv2
import pygame
import sys
from gaze_tracking import GazeTracking
import random
import math
from typing import Union
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)


class GazeTracker:
    """
    Gaze Tracker class allowing a single calibration to do multiple tasks

    Attributes
    ----------
    calibration_data : dict, None
        allow the passing of custom calibration data
    max_positions : str
        max positions that will be stored for smoothing of the eye tracking

    Methods
    -------
    run_calibration()
        run the calibration function if there is no calibration passes

    get_gaze_position(horizontal_ratio, vertical_ratio)
        convert the data from the camera to the pixels that the user is looking at

    smooth_calibration()
        smooth the calibration data, slightly expanding the viewport so the eye has more travel

    gaze_tracking_mode()
        freestyle mode made for testing where the gaze is converted to a cursor on a blank background

    spawn_random_bubbles(num_bubbles=20)
        target shooting mode allowing the user to spawn n number of bubbles one after another

    """
    def __init__(self, calibration_data: Union[dict, None]=None, max_positions: int=3):
        self.bubbles = []

        self.num_bubbles = 5
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN, display=1)

        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = self.screen.get_size()

        for i in range(self.num_bubbles):
            self.bubbles.append([(self.SCREEN_WIDTH // (self.num_bubbles + 1)) * (i + 1), 0])
            self.bubbles.append([0, (self.SCREEN_HEIGHT // (self.num_bubbles + 1)) * (i + 1)])
            self.bubbles.append([self.SCREEN_WIDTH, (self.SCREEN_HEIGHT // (self.num_bubbles + 1)) * (i + 1)])
            self.bubbles.append([(self.SCREEN_WIDTH // (self.num_bubbles + 1)) * (i + 1), self.SCREEN_HEIGHT])

        self.gaze = GazeTracking()
        self.webcam = cv2.VideoCapture(0)

        pygame.init()

        self.font = pygame.font.Font(None, 36)


        self.max_positions = max_positions
        self.last_positions = []


        self.calibration_data = calibration_data
        if self.calibration_data is None:
            self.calibration_data = {"top": 0, "left": 0, "right": 0, "bottom": 0}
            self.run_calibration()
            print(self.calibration_data)


    def run_calibration(self):
        """
        calibrates the size of the screen with the pupil location in the eye socket
        """
        clock = pygame.time.Clock()
        current_bubble_index = 0
        calibration_location = list(self.calibration_data.keys())

        while current_bubble_index < len(self.bubbles):
            self.screen.fill(BLACK)

            # Capture webcam frame and process gaze
            _, frame = self.webcam.read()
            self.gaze.refresh(frame)

            # Draw current bubble
            BUBBLE_RADIUS = 50
            pygame.draw.circle(self.screen, BLUE, self.bubbles[current_bubble_index], BUBBLE_RADIUS)

            # Display instruction
            instruction = "Focus on the bubble and press SPACE"
            text_surface = self.font.render(instruction, True, (255, 255, 255))
            self.screen.blit(text_surface, (self.SCREEN_WIDTH // 2 - text_surface.get_width() // 2, self.SCREEN_HEIGHT - 50))

            # Show video frame in a separate window for reference
            annotated_frame = self.gaze.annotated_frame()
            cv2.imshow("Gaze Tracking", annotated_frame)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.webcam.release()
                    cv2.destroyAllWindows()
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # Capture gaze ratios for the current bubble
                        current_bubble_name = calibration_location[current_bubble_index // self.num_bubbles]
                        if self.gaze.horizontal_ratio() is not None:
                            current_bubble_index += 1
                        else:
                            continue

                        if current_bubble_name == "top" or current_bubble_name == "bottom":
                            self.calibration_data[current_bubble_name] += ((self.gaze.pupil_left_coords()[1] + self.gaze.pupil_right_coords()[1]) / 2) / self.num_bubbles
                        elif current_bubble_name == "left" or current_bubble_name == "right":
                            self.calibration_data[current_bubble_name] += ((self.gaze.pupil_left_coords()[0] + self.gaze.pupil_right_coords()[0]) / 2) / self.num_bubbles

                        print(f"Calibrated {current_bubble_name}: {self.calibration_data[current_bubble_name]}")


            # Update display
            pygame.display.flip()
            clock.tick(30)


    def get_gaze_position(self, horizontal_ratio: float, vertical_ratio: float):
        """
        Calculate the gaze position on the screen using calibration data and gaze ratios.

        Parameters:
            horizontal_ratio: float:
                Current horizontal gaze ratio
            vertical_ratio: float
                Current vertical gaze ratio

        Returns:
            x_avg, y_avg, (normalized_horizontal, normalized_vertical)

        where x and y avg are the average of the last max_positions pupil locations to allow for smoothing
        """
        # Ensure ratios are within bounds
        horizontal_ratio = max(self.calibration_data['right'], min(horizontal_ratio, self.calibration_data['left']))
        vertical_ratio = max(self.calibration_data['top'], min(vertical_ratio, self.calibration_data['bottom']))

        # Normalize ratios
        normalized_horizontal = 1 - (horizontal_ratio - self.calibration_data['right']) / (
                    (self.calibration_data['left'] - self.calibration_data['right']))
        normalized_vertical = (vertical_ratio - self.calibration_data['top']) / (
                    (self.calibration_data['bottom'] - self.calibration_data['top']))

        # Convert to screen coordinates
        x = normalized_horizontal * self.SCREEN_WIDTH
        y = normalized_vertical * self.SCREEN_HEIGHT

        self.last_positions.append((x, y))

        self.last_positions = self.last_positions[-self.max_positions:]

        x_sum, y_sum = 0, 0

        for x, y in self.last_positions:
            x_sum += x
            y_sum += y

        return x_sum/self.max_positions, y_sum/self.max_positions, (normalized_horizontal, normalized_vertical)

    def smooth_calibration(self):
        """
        smooth the calibration data, slightly expanding the viewport so the eye has more travel
        """

        vertical_middle = (self.calibration_data['top'] + self.calibration_data['bottom']) / 2
        vertical_delta = vertical_middle * 0.020
        self.calibration_data['top'] = vertical_middle - vertical_delta
        self.calibration_data['bottom'] = vertical_middle + vertical_delta

        horizontal_middle = (self.calibration_data['left'] + self.calibration_data['right']) / 2
        horizontal_delta = vertical_middle * 0.030
        self.calibration_data['right'] = horizontal_middle - horizontal_delta
        self.calibration_data['left'] = horizontal_middle + horizontal_delta

    def gaze_tracking_mode(self):
        """
        freestyle mode made for testing where the gaze is converted to a cursor on a blank background
        """

        while True:
            _, frame = self.webcam.read()
            self.gaze.refresh(frame)

            self.screen.fill(BLACK)

            if self.gaze.pupil_left_coords() is None or self.gaze.pupil_right_coords() is None:
                continue

            # Get current gaze ratios
            horizontal_coordinates = (self.gaze.pupil_left_coords()[0] + self.gaze.pupil_right_coords()[0]) / 2
            vertical_coordinates = (self.gaze.pupil_left_coords()[1] + self.gaze.pupil_right_coords()[1]) / 2

            # Map the gaze ratios to screen coordinates
            gaze_x, gaze_y, multipliers = self.get_gaze_position(horizontal_coordinates, vertical_coordinates)

            # Draw a red circle at the calculated gaze point
            pygame.draw.circle(screen, RED, (gaze_x, gaze_y), 30)

            instruction = f"{horizontal_coordinates}, {vertical_coordinates}, {multipliers}"
            text_surface = self.font.render(instruction, True, (255, 255, 255))
            self.screen.blit(text_surface, (SCREEN_WIDTH // 2 - text_surface.get_width() // 2, self.SCREEN_HEIGHT - 50))

            # Show video frame in a separate window for reference
            annotated_frame = self.gaze.annotated_frame()
            cv2.imshow("Gaze Tracking", annotated_frame)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    webcam.release()
                    cv2.destroyAllWindows()
                    pygame.quit()
                    sys.exit()

            # Update display
            pygame.display.flip()


    # Function to spawn and track bubbles
    def spawn_random_bubbles(self, total_bubbles: int=20):
        """
        target shooting mode allowing the user to spawn n number of bubbles one after another

        Parameters:
            total_bubbles: int:
                number of bubbles to spawn.
        """
        clock = pygame.time.Clock()
        bubbles_left = total_bubbles
        bubble_position = None

        gaze_on_bubble = False

        while bubbles_left > 0:
            _, frame = self.webcam.read()
            self.gaze.refresh(frame)

            self.screen.fill(BLACK)

            # Generate a new random bubble position if needed
            if bubble_position is None:
                bubble_position = (
                    random.randint(50, self.SCREEN_WIDTH - 50),
                    random.randint(50, self.SCREEN_HEIGHT - 50),
                )

            # Draw the bubble
            pygame.draw.circle(self.screen, BLUE, bubble_position, 50)

            if (gaze_on_bubble and self.gaze.is_blinking()) or (gaze_on_bubble and self.gaze.pupil_left_coords() is None):
                print(f"Bubble {total_bubbles - bubbles_left + 1} hit!")
                bubble_position = None  # Reset for the next bubble
                bubbles_left -= 1
                gaze_on_bubble = False
                continue

            if self.gaze.pupil_left_coords() is None or self.gaze.pupil_right_coords() is None:
                continue

            # Get current gaze ratios
            horizontal_coordinates = (self.gaze.pupil_left_coords()[0] + self.gaze.pupil_right_coords()[0]) / 2
            vertical_coordinates = (self.gaze.pupil_left_coords()[1] + self.gaze.pupil_right_coords()[1]) / 2

            # Map the gaze ratios to screen coordinates
            gaze_x, gaze_y, multipliers = self.get_gaze_position(horizontal_coordinates, vertical_coordinates)

            # Draw a red circle to indicate gaze position
            pygame.draw.circle(self.screen, (255, 0, 0), (int(gaze_x), int(gaze_y)), 5)

            # Check if gaze intersects the bubble
            dist = math.sqrt((gaze_x - bubble_position[0]) ** 2 + (gaze_y - bubble_position[1]) ** 2)
            gaze_on_bubble = dist <= 50

            # Display instruction
            instruction = "Look at the bubble and press blink!"
            text_surface = self.font.render(instruction, True, (255, 255, 255))
            self.screen.blit(text_surface, (self.SCREEN_WIDTH // 2 - text_surface.get_width() // 2, self.SCREEN_HEIGHT - 50))

            annotated_frame = self.gaze.annotated_frame()
            cv2.imshow("Gaze Tracking", annotated_frame)

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                # Testing for space bar instead of blinks
                # elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                #     if gaze_on_bubble:
                #         print(f"Bubble {total_bubbles - bubbles_left + 1} hit!")
                #         bubble_position = None  # Reset for the next bubble
                #         bubbles_left -= 1

            # Update the display
            pygame.display.flip()
            clock.tick(30)


# Main program
if __name__ == "__main__":
    # Optional if you don't want to calibrate
    # You should always calibrate on a new computer
    # calibration_data = {'top': 234.8, 'left': 316.9, 'right': 316.09999999999997, 'bottom': 238.2}
    # tracker = GazeTracker(calibration_data)

    # Otherwise to have a bare setup
    tracker = GazeTracker()

    tracker.smooth_calibration()
    print("Calibration complete. Data:", tracker.calibration_data) # Calibration after smoothing
    tracker.spawn_random_bubbles()  # Start target shooting mode after calibration
