# DISCLAIMER: THIS CODE IS NOT FINISHED

from hub import light, port, light_matrix, button, motion_sensor, sound
import runloop, motor, time, force_sensor, math, heapq

#___________________________
# |                        | -> Move function
# |    MOVEMENT SYSTEM    | -> Rotate function
# |___________________________| -> Stop move function (Last resort, not currently in use)

class MovementSystem:
    yawAngle = 0
    speed = 800

    # Move Forward
    def move(self, distance):
        # Rotates wheels in oposite directions to go straight
        motor.run_for_degrees(port.C, -distance, self.speed)# Right wheel
        motor.run_for_degrees(port.D, distance, self.speed)# Left wheel

    # Rotate
    def rotate(self, degrees):
        self.yawAngle += degrees
        relDegrees = degrees * (200/90) # Correct amount to rotate motors
        motor.run_for_degrees(port.C, relDegrees, self.speed)# Right wheel
        motor.run_for_degrees(port.D, relDegrees, self.speed)# Left wheel

    # Stop movement
    def stopMove(self):
        motor.stop(port.C)
        motor.stop(port.D)


#________________________
# |                        | -> Get inputs function (Detects when buttons are pressed and released)
# |    INPUT MANAGER    | -> Update states function (Makes sure keys aren't "pressed" for more than one tick)
# |________________________| -> Button states dictionary

class InputManager:
    # Call getInput(key) to see if the key was *pressed this frame*.

    def __init__(self):
        # key states stored as: 0 = idle; 1 = pressed this tick; 2 = held
        self.states = {
            'green': 0,
            'red': 0,
            'left': 0,
            'right': 0
        }

        self.stateToNum = {
            0: 'green',
            1: 'red',
            2: 'left',
            3: 'right'
        }

    def getInputs(self):
        # GREEN BUTTON
        if force_sensor.force(port.A) >= 50 and self.states["green"] == 0:
            self.states["green"] = 1

        # RED BUTTON
        if force_sensor.force(port.B) >= 50 and self.states["red"] == 0:
            self.states["red"] = 1

        # LEFT BUTTON
        if button.pressed(button.LEFT) and self.states["left"] == 0:
            self.states["left"] = 1

        # RIGHT BUTTON
        if button.pressed(button.RIGHT) and self.states["right"] == 0:
            self.states["right"] = 1

    def updateStates(self):
        for key, value in self.states.items():
            if value == 1:
                self.states[key] = 2

            if key == "green" and force_sensor.force(port.A) < 50:
                self.states[key] = 0

            if key == "red" and force_sensor.force(port.B) < 50:
                self.states[key] = 0

            if key == "left" and not button.pressed(button.LEFT):
                self.states[key] = 0

            if key == "right" and not button.pressed(button.RIGHT):
                self.states[key] = 0



#________________________
# |                        | ->
# |    SCREEN MODULE    | -> Set lights
# |________________________| ->
class Screen:
    def setLights(self, matrix): # ONLY WORKS FOR SQUARE GRIDS
        gridSideLengths = len(matrix)
        light_matrix.clear() # Clears matrix for drawing
        # Draws matrix to screen
        for x in range(gridSideLengths):
            for y in range(gridSideLengths):
                if matrix[y][x] == 1:
                    light_matrix.set_pixel(x, y, 100)

#________________________
# |                        |
# |    LOGIC MODULE    | -> Just brings everything together
# |________________________|
class Logic:
    screenUpdate = False
    mode = "grid"
    num = 0
    gridSideLengths = 5

    # 0 = empty space; 1 = obstical; 2 = start point; 3 = end point
    # All zero when program starts
    matrix = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ]

    # Converts mode strings to numbers that we can use to change the value of a cell in the matrix
    modeDict = {
        "grid" : 1, # main obstical adding mode
        "start" : 2, # Add the starting point
        "end" : 3, # add the ending point
        # Add more modes if needed e.g. - yes hayden I added these to the list but didn't make them, these could be useful and are really quite easy to make. :)
        # "remove" : 4, # lets the user remove points
        "clear" : 4, # clears the entire grid
        # "minorObstructions" : 6 - stuff like carpets and rugs
    }

    numToMode = {
        1 : "grid", # main obstical adding mode
        2 : "start", # Add the starting point
        3 : "end", # add the ending point
        4 : "clear", # clears the entire grid
    }

    def __init__(self, x, y):
        self.pointX = x
        self.pointY = y

        self.inputManager = InputManager()
        self.screen = Screen()
        self.movement = MovementSystem()

    # Main screen function: Gets inputs and acts upon them
    def tick(self):
        self.screenUpdate = False
        self.inputManager.updateStates()
        self.inputManager.getInputs()

        # GREEN BUTTON-Toggle/Set matrix pixels
        if self.inputManager.states["green"] == 1:
            value = self.modeDict[self.mode]
            self.matrix[self.pointY][self.pointX] = value

            if value == 4:
                self.matrix = [
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0],
                    [0, 0, 0, 0, 0]
                ]

            self.screenUpdate = True
            sound.beep(400, 550, 100)
            print('the matrix is now:', self.matrix)

        # RED BUTTON-Mode changer
        if self.inputManager.states["red"] == 1:
            self.num += 1
            if self.num >= max(self.numToMode.keys()): # loops back to the first mode if the number gets higher than the number of modes
                self.num = 1
            self.mode = self.numToMode[self.num]

            self.screenUpdate = True
            print('Red Pressed: the mode is now', self.mode)
            sound.beep(400, 550, 100)

        #LEFT BUTTON-Scrolls X-Axis
        if self.inputManager.states["left"] == 1:
            self.pointX += 1
            self.screenUpdate = True
            print('Left Pressed: the X is now', self.pointX)
            sound.beep(400, 550, 100)

        ## RIGHT BUTTON-Scrolls Y-Axis
        if self.inputManager.states["right"] == 1:
            self.pointY += 1
            self.screenUpdate = True
            print('Right Pressed: the Y is now', self.pointY)
            sound.beep(400, 550, 100)

        # Wraps values down to 0-4, preventing overflow and allowing scrolling
        self.pointX %= self.gridSideLengths
        self.pointY %= self.gridSideLengths

        self.screen.setLights(self.matrix)
        light_matrix.set_pixel(self.pointX, self.pointY, 100)
        print(self.matrix)


# Used to get manhattan distance between two points (used by astar)
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Pathfinding algorithim
def astar(grid, start, end):
    rows, cols = len(grid), len(grid[0])

    open_list = []
    heapq.heappush(open_list, (heuristic(start, end), 0, start)) # (f, g, node)

    came_from = {}
    g_scores = {start: 0}

    while open_list:
        f, g, current = heapq.heappop(open_list)

        if current == end:
            # Reconstruct the bloody path!
            path = []

            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = current[0] + dr, current[1] + dc # New row, new column
            neighbor = (nr, nc)

            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1: # Makes sure neighbor is walkable and inside grid
                tentative_g = g + 1 # G costs 1 per step
                if neighbor not in g_scores or tentative_g < g_scores[neighbor]:
                    g_scores[neighbor] = tentative_g
                    f_score = tentative_g + heuristic(neighbor, end)
                    heapq.heappush(open_list, (f_score, tentative_g, neighbor))
                    came_from[neighbor] = current
    return None

def pathToText(path):
    newPath = []
    for i in range(1, len(path)):
        diff = (path[i-1][0] - path[i][0], path[i-1][1] - path[i][1])
        if diff == (1, 0):
            newPath.append(0)
        elif diff == (-1, 0):
            newPath.append(180)
        elif diff == (0, 1):
            newPath.append(270)
        elif diff == (0, -1):
            newPath.append(90)
        else:
            return ["Error"]


    return newPath


def consoleLogDiscussion():
    print('BODHI! I like refactored everything for "Code readability"') # 19/11
    print('Also why the hell was detecting inputs NOT IN THE INPUT MANAGER -- Angry Hayden')

### MAIN ENTRY
async def main():
    logic = Logic(2, 2)
    while True:
        logic.tick()
        await runloop.sleep_ms(10)

runloop.run(main())