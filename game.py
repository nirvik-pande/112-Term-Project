"""
Pixel Putt-Putt: Top-down multiplayer mini-golf game 

KEY FEATURES
- Fully custom golf physics collision engine (friction, velocity decay, multi-step collision resolution)
- Wall-collision handling using per-axis normal correction and overlap resolution
- OOP design with Ball, Wall, Hole, Course, and Bunker classes
- Multiplayer mode with proper turn rotation
- Clean aiming system with drag-to-aime vector and preview
- In-game UI has a pixel theme (which is very pretty in my opinion :-) ) along with audio and animations

GRADER SHORTCUTS
- Press H: Return instantly to the Home Screen
- Press N: Skip directly to the next hole
- Press R: Reset the current hole state
- Press M: Toggle background music
- Press F: Force-complete the hole (debug shortcut to test transitions)

REFERENCES:
No AI or outside references were used in this project besides CMU CS Academy documentation and Gemini image generation for the golf-course backgrounds.
"""


from cmu_graphics import *
import math

class Ball:
    
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        self.dx = 0
        self.dy = 0
        
class Wall:
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
    def draw(self):
        drawRect(self.x,self.y,self.width,self.height)
        
class Hole:
    
    def __init__(self, x, y, radius):
        self.x = x
        self.y = y
        self.radius = radius
        
    def draw(self):
        drawCircle(self.x,self.y,self.radius)
        
class Course:
    
    def __init__(self, x, y, walls, hole, bunkers, par):
        self.x = x
        self.y = y
        self.walls = walls  
        self.hole = hole
        self.bunkers = bunkers
        self.par = par
    
    def draw(self):
        for wall in self.walls:
            drawRect(wall.x, wall.y, wall.width, wall.height)
        drawCircle(self.hole.x, self.hole.y, self.hole.radius)
        
class Bunker:
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
def clamp(val, min, max):
    if val < min: return min
    if val > max: return max
    return val
    
def getClosestPoint(ball, wall):
    x = clamp(ball.x, wall.x, wall.x + wall.width)
    y = clamp(ball.y, wall.y, wall.y + wall.height)
    dx = ball.x - x
    dy = ball.y - y
    return x, y, dx, dy
    
def circleRectOverlap(ball, wall):
    x, y, dx, dy = getClosestPoint(ball, wall)
    dist = dx**2 + dy**2
    return dist <= (ball.radius**2)
    
def collision(ball, wall):
    if not circleRectOverlap(ball, wall):
        return
    x, y, dx, dy = getClosestPoint(ball, wall)
    dist = dx**2 + dy**2
    r = ball.radius
    
    if abs(dx) > 0 and abs(dy) > 0:
        ball.dx = -ball.dx
        ball.dy = -ball.dy
        d = math.sqrt(dist) if dist != 0 else 0.0000000000001
        overlap = r - d
        ball.x += (dx/d) * overlap
        ball.y += (dy/d) * overlap
        return
    
    if abs(dx) > abs(dy):
        if dx > 0:
            ball.x = x + r
            ball.dx = abs(ball.dx)
        else:
            ball.x = x - r
            ball.dx = -abs(ball.dx)
    else:
        if dy > 0:
            ball.y = y + r
            ball.dy = abs(ball.dy)
        else:
            ball.y = y - r
            ball.dy = -abs(ball.dy)
            
def isBallinHole(ball,hole):
    return (math.sqrt((ball.x - hole.x)**2 + (ball.y - hole.y)**2) < (hole.radius - ball.radius/3))
    
def checkHole(app):
    if app.isMultiplayer:
        if app.currentPlayer == 1:
            if not app.p1HoleComplete and isBallinHole(app.ball, app.hole):
                app.p1HoleComplete = True
                app.p1Total += app.p1Strokes
                app.p1Ball.dx = 0
                app.p1Ball.dy = 0
        else:
            if not app.p2HoleComplete and isBallinHole(app.ball, app.hole):
                app.p2HoleComplete = True
                app.p2Total += app.p2Strokes
                app.p2Ball.dx = 0
                app.p2Ball.dy = 0
    else:
        if not app.holeComplete and isBallinHole(app.ball,app.hole):
            app.holeComplete = True
            app.ball.dx = 0
            app.ball.dy = 0
            app.totalStrokes += app.strokes
            app.holeScores.append(app.strokes)
            
def endPlayerTurn(app):
    nxt = nextActivePlayer(app)
    if nxt is not None:
        app.currentPlayer = nxt
        app.ball = app.p1Ball if nxt == 1 else app.p2Ball
    app.isAiming = False
    app.aimStart = None
    app.aimCurrent = None

def nextActivePlayer(app):
    if app.p1HoleComplete and app.p2HoleComplete:
        return None
    if app.currentPlayer == 1:
        if not app.p2HoleComplete:
            return 2
        return 1
    else:
        if not app.p1HoleComplete:
            return 1
        return 2

def loadHole(app, holeIndex):      
    app.currentHole = holeIndex
    course = app.courses[holeIndex]
    app.currentCourse = course
    app.startX = course.x
    app.startY = course.y
    app.ball.x = course.x
    app.ball.y = course.y
    app.ball.dx = 0
    app.ball.dy = 0
    app.walls = course.walls
    app.hole = course.hole
    app.strokes = 0
    app.holeComplete = False
    app.isAiming = False
    app.aimStart = None
    
    app.ball = app.p1Ball
    app.p1Ball.x = course.x
    app.p1Ball.y = course.y
    app.p1Ball.dx = 0
    app.p1Ball.dy = 0
    app.p2Ball.x = course.x
    app.p2Ball.y = course.y
    app.p2Ball.dx = 0
    app.p2Ball.dy = 0
    app.p1Strokes = 0
    app.p2Strokes = 0
    app.p1HoleComplete = False
    app.p2HoleComplete = False
    app.currentPlayer = 1
    
def onAppStart(app):
    app.mute = False
    app.music = Sound('cmu://1073260/43578054/pixelland.mp3')
    app.music.play(loop=True)
    
    app.currentPlayer = 1
    app.isMultiplayer = False
    
    app.screen = 'start'
    app.buttonWidth = 150
    app.buttonHeight = 50
    app.singleBtnCenter = (app.width/2, app.height/2 + 20)
    app.multiBtnCenter = (app.width/2, app.height/2 + 100)
    app.hoverS = False
    app.hoverM = False
    
    app.titleHeight = app.height/4
    app.titleD = 0.3
    app.windmillurlA = 'https://raw.githubusercontent.com/nirvik-pande/112/master/windmill1-removebg-preview.png'
    app.windmillurlB = 'https://raw.githubusercontent.com/nirvik-pande/112/master/windmill2-removebg-preview.png'
    app.currentWindmill = app.windmillurlA
    app.counter = 0  
    
    app.ballurl = 'https://raw.githubusercontent.com/nirvik-pande/112/master/ball-removebg-preview.png'
    app.startX = 345
    app.startY = 345
    app.ball = Ball(app.startX, app.startY, 5)
    app.p1Ball = Ball(app.startX, app.startY, 5)
    app.p2Ball = Ball(app.startX, app.startY, 5)
    
    app.walls_A = []
    app.bunkers_A = []
    app.bunkers_A.append(Bunker(166,134,110,120))
    app.walls_A.append(Wall(0,-10,400,10))
    app.walls_A.append(Wall(0,400,400,10))
    app.walls_A.append(Wall(-10,0,10,400))
    app.walls_A.append(Wall(410,0,10,400))
    app.walls_A.append(Wall(30,365,500,10))
    app.walls_A.append(Wall(63,324,500,10))
    app.walls_A.append(Wall(64,200,10,130))
    app.walls_A.append(Wall(21,25,10,345))
    app.walls_A.append(Wall(21,17,370,10))
    app.walls_A.append(Wall(382,25,10,175))
    app.walls_A.append(Wall(278,193,110,10))
    app.walls_A.append(Wall(278,193,10,60))
    app.walls_A.append(Wall(153,199,12,56))
    app.walls_A.append(Wall(152,252,140,10))
    app.walls_A.append(Wall(365,325,10,50))
    app.walls_A.append(Wall(64,200,100,10))
    app.walls_A.append(Wall(74,62,280,10))
    app.walls_A.append(Wall(64,61,10,105))
    app.walls_A.append(Wall(64,157,90,10))
    app.walls_A.append(Wall(150,115,12,50))
    app.walls_A.append(Wall(152,120,135,10))
    app.walls_A.append(Wall(277,130,10,28))
    app.walls_A.append(Wall(278,148,76,10))
    app.walls_A.append(Wall(345,70,10,80))
    app.walls_A.append(Wall(22,25,30,10)) 
    
    app.hole_A = Hole(368,52,10)
    app.holeComplete = False
    
    app.walls_B = []
    app.bunkers_B = []
    app.walls_B.append(Wall(271,20,5,90))
    app.walls_B.append(Wall(272,20,50,5))
    app.walls_B.append(Wall(300,20,5,63))
    app.walls_B.append(Wall(300,80,50,5))
    app.walls_B.append(Wall(345,80,5,260))
    app.walls_B.append(Wall(271,110,50,5))
    app.walls_B.append(Wall(317,110,5,201))
    app.walls_B.append(Wall(68,310,254,5))
    app.walls_B.append(Wall(40,338,313,5))
    app.walls_B.append(Wall(37,22,5,320)) 
    app.walls_B.append(Wall(37,22,29,19))
    app.walls_B.append(Wall(37,41,19,10))
    app.walls_B.append(Wall(37,51,12,7))
    app.walls_B.append(Wall(37,25,221,5))
    app.walls_B.append(Wall(65,79,10,236))
    app.walls_B.append(Wall(75,68,19,11))
    app.walls_B.append(Wall(86,58,10,20))
    app.walls_B.append(Wall(91,53,141,5))
    app.walls_B.append(Wall(229,54,5,83))
    app.walls_B.append(Wall(258,27,5,137))
    app.walls_B.append(Wall(86,81,120,5))
    app.walls_B.append(Wall(205,81,5,55))
    app.walls_B.append(Wall(205,132,26,5))
    app.walls_B.append(Wall(167,162,95,5))
    app.walls_B.append(Wall(167,164,5,58))
    app.walls_B.append(Wall(167,218,132,5))
    app.walls_B.append(Wall(117,270,153,5))
    app.walls_B.append(Wall(114,112,5,163))
    app.walls_B.append(Wall(114,111,62,5))
    app.walls_B.append(Wall(176,111,5,25))
    app.walls_B.append(Wall(269,249,5,26))
    app.walls_B.append(Wall(142,247,132,5))
    app.walls_B.append(Wall(138,134,5,117))
    app.walls_B.append(Wall(138,134,43,5))
    app.walls_B.append(Wall(90,298,210,5))
    app.walls_B.append(Wall(85,85,7,215))
    app.walls_B.append(Wall(297,220,5,81))
    
    app.hole_B = Hole(288,39,10)
    app.p1HoleComplete = False
    app.p2HoleComplete = False
    app.holeComplete = False
    
    app.par1 = 8
    app.par2 = 15
    
    app.course_A = Course(app.startX, app.startY, app.walls_A, app.hole_A, app.bunkers_A, app.par1)
    app.course_B = Course(105, 284, app.walls_B, app.hole_B, app.bunkers_B, app.par2)
    
    app.courses = [app.course_A, app.course_B]
    app.currentHole = 0
    app.currentCourse = app.courses[app.currentHole]
    
    app.strokes = 0
    app.p1Strokes = 0
    app.p2Strokes = 0
    app.isAiming = False
    app.aimStart = False
    app.aimCurrent = False
    app.shotProgress = False
    
    app.totalStrokes = 0
    app.p1Total = 0
    app.p2Total = 0
    app.totalPar = sum(course.par for course in app.courses)
    app.holeScores = []
    
    loadHole(app, 0)

def inButton(app, cx, cy, w, h, x, y):
    return (cx - w/2 <= x <= cx + w/2 and cy - h/2 <= y <= cy + h/2)

def ballInBunker(ball,bunker):
    return (bunker.x <= ball.x <= bunker.x + bunker.width and bunker.y <= ball.y <= bunker.y + bunker.height)
    
def onKeyPress(app, key):
    if key == 'r':
        loadHole(app, app.currentHole)
    if key == 'm':
        if app.mute:
            app.mute = False
            app.music.play(loop=True)
        else:
            app.mute = True
            app.music.pause()
    if key == 'n':
        if app.currentHole < len(app.courses) - 1:
            loadHole(app, app.currentHole + 1)
        else:
            app.screen = 'final'
    if key == 'f':
        app.totalStrokes += app.strokes
        app.holeComplete = True
    if key == 'h':
        app.music.pause()
        onAppStart(app)
            
    
def onMousePress(app, mouseX, mouseY):
    if app.screen == 'start':
        x1, y1 = app.singleBtnCenter
        x2, y2 = app.multiBtnCenter
        if inButton(app, x1-25, y1-50, app.buttonWidth, app.buttonHeight, mouseX, mouseY):
            app.screen = 'game'
            app.isMultiplayer = False
        if inButton(app, x2-25, y2-75, app.buttonWidth, app.buttonHeight, mouseX, mouseY):
            app.screen = 'game'
            app.isMultiplayer = True
    elif app.screen == 'game': 
        if app.ball.dx == 0 and app.ball.dy == 0:
            app.isAiming = True
            app.aimStart = (mouseX,mouseY)
            app.aimCurrent = (mouseX,mouseY)
        
def onMouseDrag(app, mouseX, mouseY):
    if app.isAiming:
        app.aimCurrent = (mouseX,mouseY)
        
def onMouseRelease(app, mouseX, mouseY):
    if app.isAiming:
        vx = app.ball.x - app.aimCurrent[0]
        vy = app.ball.y - app.aimCurrent[1]
        app.ball.dx = vx * 0.1
        app.ball.dy = vy * 0.1
        app.strokes += 1
        app.isAiming = False
        app.aimStart = None
        app.aimCurrent = None
        if app.isMultiplayer:
            if app.currentPlayer == 1:
                app.p1Strokes += 1
            else:
                app.p2Strokes += 1
            app.shotProgress = True

def onStep(app):
    app.counter += 1
    if 0 < (app.counter % 51) < 25:
        app.currentWindmill = app.windmillurlA
    else:
        app.currentWindmill = app.windmillurlB
        
    app.ball.dx *= 0.95
    app.ball.dy *= 0.95
    
    for bunker in app.currentCourse.bunkers:
        if ballInBunker(app.ball, bunker):
            app.ball.dx *= 0.75
            app.ball.dy *= 0.75
            
    steps = int(max(abs(app.ball.dx), abs(app.ball.dy))) + 1
    step_dx = app.ball.dx/steps
    step_dy = app.ball.dy/steps
    for i in range(steps):
        app.ball.x += step_dx
        app.ball.y += step_dy
        for wall in app.walls:
            collision(app.ball,wall)
    
    speed = math.sqrt(app.ball.dx**2 + app.ball.dy**2)
    if speed < 0.2:
        app.ball.dx = 0
        app.ball.dy = 0
    
    if app.isMultiplayer:
        if app.shotProgress and app.ball.dx == 0 and app.ball.dy == 0:
            endPlayerTurn(app)
            app.shotProgress = False
        if app.p1HoleComplete and app.p2HoleComplete:
            if app.currentHole < len(app.courses) - 1:
                loadHole(app, app.currentHole + 1)
            else:
                app.screen = 'final'
        
    checkHole(app)
    
def drawGame(app):
    holeNumber = app.currentHole + 1
    totalHoles = len(app.courses)
    
    if holeNumber == 1:
        app.currentCourse.draw()
        drawImage('https://raw.githubusercontent.com/nirvik-pande/112/master/bg1.png', app.width/2, app.height/2, width = 400, height = 400, align='center')
        drawLabel(f'Hole {holeNumber} / {totalHoles} | Par: {app.currentCourse.par} | Strokes: {app.strokes}', 105, 10, font='cinzel', bold = True)

    if holeNumber == 2:
        app.currentCourse.draw()
        drawImage('https://raw.githubusercontent.com/nirvik-pande/112/master/course2.png', app.width/2, app.height/2, width = 400, height = 400, align='center')
        drawRect(0,0,215,20,fill='white')
        drawLabel(f'Hole {holeNumber} / {totalHoles} | Par: {app.currentCourse.par} | Strokes: {app.strokes}', 105, 10, font='cinzel', bold = True)
    
    imageWidth, imageHeight = getImageSize(app.ballurl)
    if app.isMultiplayer:
        drawImage(app.ballurl, app.p1Ball.x, app.p1Ball.y, align = 'center', width = imageWidth/30, height = imageHeight/30)
        drawCircle(app.p1Ball.x, app.p1Ball.y, 7, fill = 'blue', opacity = 10)
        drawImage(app.ballurl, app.p2Ball.x, app.p2Ball.y, align = 'center', width = imageWidth/30, height = imageHeight/30)
        drawCircle(app.p1Ball.x, app.p1Ball.y, 7, fill = 'green', opacity = 10)
        if holeNumber == 1:
            drawLabel(f"Player {app.currentPlayer}'s turn", 200, 390, size = 12, bold = True, font = 'cinzel')
        else:
            drawRect(app.width/2, 390, 150, 15, fill = 'white', align = 'center')
            drawLabel(f"Player {app.currentPlayer}'s turn", 200, 390, size = 12, bold = True, font = 'cinzel')
    else:
        drawImage(app.ballurl, app.ball.x, app.ball.y, align = 'center', width = imageWidth/30, height = imageHeight/30)
    
    if app.holeComplete:
        if holeNumber == 1:
            drawRect(app.width/2, 40, 250, 40, align = 'center', fill = 'white')
            drawLabel(f'Hole Complete! Score: {app.strokes} | Par: {app.currentCourse.par}', app.width/2,30, font='cinzel', bold = True)
            drawLabel('Press N for next hole', app.width/2, 50, font='cinzel', bold = True)
        if holeNumber == 2:
            drawRect(app.width/2, 40, 250, 40, align = 'center', fill = 'white')
            drawLabel(f'Hole Complete! Score: {app.strokes} | Par: {app.currentCourse.par}', app.width/2,30, font='cinzel', bold = True)
            drawLabel('Press N for final score!', app.width/2, 50, font='cinzel', bold = True)
    if app.isAiming:
        start = (app.ball.x,app.ball.y)
        end = app.aimCurrent
        sx, sy = start
        ex, ey = end
        drawLine(sx, sy, ex, ey, fill='red', lineWidth = 3)
        drawCircle(ex,ey,5,fill='red')

def drawStart(app):
    drawImage('https://raw.githubusercontent.com/nirvik-pande/112/master/titlebackground.png', app.width/2, app.height/2, width = 400, height = 400, align='center')
    drawImage(app.currentWindmill, app.width/2 + 140, app.height/2 + 43, width = 380, height = 380, align='center')
    drawImage('https://raw.githubusercontent.com/nirvik-pande/112/master/title112-removebg-preview.png',app.width/2, app.height/6, align='center')
    x1, y1 = app.singleBtnCenter
    x2, y2 = app.multiBtnCenter
    h, w = app.buttonHeight, app.buttonWidth
    
    drawRect(x1 - w/2 - 25, y1 - h/2 - 50, w, h, fill='black', border='white', borderWidth=3)
    drawImage('https://raw.githubusercontent.com/nirvik-pande/112/master/singleplayer.png', x1 - 25, y1 - 50, align = 'center', height = 25, width = 140)
    
    drawRect(x2 - w/2 - 25, y2 - h/2 - 75, w, h, fill='black', border='white', borderWidth=3)
    drawImage('https://raw.githubusercontent.com/nirvik-pande/112/master/multiplayer.png', x2 - 25, y2 - 75, align = 'center', height = 25, width = 140)
    
def drawFinal(app):
    drawImage('https://raw.githubusercontent.com/nirvik-pande/112/master/bgfinal.png', app.width/2, app.height/2, width = 400, height = 400, align='center')
    if not app.isMultiplayer:
        drawLabel("FINAL SCORE", app.width/2, app.height/2 - 20, size=25,bold=True,font='cinzel')
        drawLabel(f"Total Strokes: {app.totalStrokes}", app.width/2, app.height/2 + 20, size=16,bold=True,font='cinzel')
        drawLabel(f"Total Par: {app.totalPar}", app.width/2, app.height/2 + 40, size=16,bold=True,font='cinzel')
        
        diff = app.totalStrokes - app.totalPar
        if diff < 0:
            txt = f'{abs(diff)} under par!'
        elif diff > 0:
            txt = f'{diff} over par!'
        else:
            txt = 'Even par!'
        drawLabel(txt,app.width/2,app.height/2 + 60,size=18,bold=True,font='cinzel')
        drawLabel("Press h to go back to the home screen!",app.width/2,app.height/2 + 100,size=9,bold=True,font='cinzel')
    else:
        drawLabel("FINAL SCORE", app.width/2, app.height/2 - 20, size=25,bold=True,font='cinzel')
        drawLabel(f"Player 1: {app.p1Total} strokes", app.width/2, app.height/2 + 20, size=16,bold=True,font='cinzel')
        drawLabel(f"Player 2: {app.p2Total} strokes", app.width/2, app.height/2 + 40, size=16,bold=True,font='cinzel')
        
        if app.p1Total < app.p2Total:
            winner = 'PLAYER 1 WINS!'
        elif app.p1Total > app.p2Total:
            winner = 'PLAYER 2 WINS!'
        else:
            winner = 'TIE GAME!'
        drawLabel(winner,app.width/2,app.height/2 + 60,size=18,bold=True,font='cinzel')
        drawLabel("Press h to go back to the home screen!",app.width/2,app.height/2 + 100,size=9,bold=True,font='cinzel')
    
def redrawAll(app):
        if app.screen == 'start':
            drawStart(app)
        if app.screen == 'game':
            drawGame(app)
        if app.screen == 'final':
            drawFinal(app)

def main():
    runApp()

main()
