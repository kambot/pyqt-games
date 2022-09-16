from time import time, sleep
from random import choice
import sys, os
import math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeyEvent, QPainter,QImage, QPen, QIcon, QPixmap, QColor, QBrush, QCursor, QFont, QPalette, QTransform, QLinearGradient, QFontMetrics
from PyQt5.QtCore import Qt, QPoint, QPointF, QSize, QEvent, QTimer, QCoreApplication, QRect


def bound(_val, _min, _max):
    return max(min(_val, _max), _min)

def printf(fmt, *args):
    if(len(args) > 0):
        print(fmt % args, end="")
    else:
        print(fmt, end="")

class ExplosionAnimation():
    def __init__(self, x, y):
        # self.spawnx, self.spawny = gui.adj_coords(x,y)
        self.x = x
        self.y = y
        self.r = 0
        self.dr = 1.8
        self.maxr = 30
        self.delete = False
        self.colors = [
                QColor(0xff, 0x00, 0x00),
                QColor(0xff, 0xff, 0xff),
                QColor(0xff, 0xff, 0x00),
                QColor(0xff, 0xa5, 0x00),
            ]
        self.color = choice(self.colors)

    def update(self):

        if(self.r >= self.maxr):
            self.dr *= -1

        self.r += self.dr
        self.color = choice(self.colors)

        if(self.r <= 0):
            self.delete = True

    def draw(self, painter):
        gui.draw_circle(painter, self.x, self.y, self.r, 0, gui.color_none, self.color)


class Bullet():

    # types
    # 0: small, weak, fast
    # 1: big, strong, slow

    def __init__(self, x, y, angle, _type):
        self.spawnx, self.spawny = gui.adj_coords(x,y)
        self.fx = x
        self.fy = y
        self.x = x
        self.y = y
        self.x_prior = x
        self.y_prior = y
        self.angle = angle
        self.delete = False
        self.type = _type
        # self.xs = []
        # self.ys = []

        if(self.type == 0):
            self.r = 2
            self.dist = 8
            self.color = Qt.cyan
        elif(self.type == 1):
            self.r = 6
            self.dist = 2.5
            self.color = Qt.green
        else:
            printf("Bullet invalid type: %d\n", self.type)


    def update(self):
        ax, ay = gui.adj_coords(self.fx, self.fy)
        x = self.dist*math.cos(self.angle)+ax
        y = self.dist*math.sin(self.angle)+ay
        self.fx, self.fy = gui.win_coords(x,y)
        self.x_prior = self.x
        self.y_prior = self.y
        self.x = int(self.fx)
        self.y = int(self.fy)
        # self.xs.append(self.x)
        # self.ys.append(self.y)
        # if(gui.off_window(self.x, self.y)):
        if(not gui.inside_arena(self.x, self.y)):
            self.delete = True
            # gui.spawn_explosion(self.x, self.y)

    def draw(self, painter):
        gui.draw_circle(painter, self.x, self.y, self.r, 0, gui.color_none, self.color)
        # for i in range(len(self.xs)):
        #     gui.draw_circle(painter, self.xs[i], self.ys[i], self.r, 0, gui.color_none, QColor(0,0,0))



class Enemy():
    def __init__(self, x, y, _type=0):
        self.fx = x
        self.fy = y
        self.x = x
        self.y = y
        self.x_prior = x
        self.y_prior = y
        self.angle = 0
        # self.magnitude = 0
        self.delete = False
        self.type = _type

        self.angle_range = 60

        if(self.type == 0):
            self.r = 5
            self.dist = 2
            self.color = QColor(0xff, 0x00, 0x00)
            self.angle = gui.calc_angle(gui.player_x, self.fx, gui.player_y, self.fy)
        elif(self.type == 1):
            self.r = 15
            self.dist = 2
            self.color = QColor(0xff, 0xa5, 0x00)
            self.rand_angle()
        else:
            printf("Enemy invalid type: %d\n", self.type)

    def rand_angle(self):
        urange = int(self.angle_range/2)
        lrange = urange * -1
        rad = gui.calc_angle(gui.player_x, self.fx, gui.player_y, self.fy)
        deg = rad*180/math.pi
        deg += choice(range(lrange,urange))
        self.angle = deg*math.pi/180



    def update(self):
        # self.magnitude = gui.calc_magnitude(gui.player_x, self.fx, gui.player_y, self.fy)

        ax, ay = gui.adj_coords(self.fx, self.fy)
        x = self.dist*math.cos(self.angle)+ax
        y = self.dist*math.sin(self.angle)+ay
        self.fx, self.fy = gui.win_coords(x,y)
        self.x = int(self.fx)
        self.y = int(self.fy)

        hit_side = False

        if((self.x-self.r) < gui.tl_x):
            self.x = gui.tr_x-self.r-1
            self.fx = float(self.x)
            hit_side = True

        if((self.x+self.r) > gui.tr_x):
            self.x = gui.tl_x+self.r+1
            self.fx = float(self.x)
            hit_side = True

        if((self.y-self.r) < gui.tl_y):
            self.y = gui.bl_y-self.r-1
            self.fy = float(self.y)
            hit_side = True

        if((self.y+self.r) > gui.br_y):
            self.y = gui.tl_y+self.r+1
            self.fy = float(self.y)
            hit_side = True

        if(hit_side):
            self.angle_range = max(self.angle_range-10, 10)
            self.rand_angle()

    def draw(self, painter):
        gui.draw_circle(painter, self.x, self.y, self.r, 0, gui.color_none, self.color)

class MainWindow(QMainWindow):

    def init_game_objects(self):
        self.exp_anims = []
        self.bullets = []
        self.enemies = []

        self.mouse_x, self.mouse_y = self.get_cursor_pos()
        self.mouse_off_window = self.off_window(self.mouse_x, self.mouse_y)

        self.player_lives = 3
        self.player_x = self.center_x
        self.player_y = self.center_y
        # tip, left leg, right leg, middle
        self.player_shape = []
        self.player_angle = 0

        self.player_radius = 12.5
        self.update_player()

    def init(self):

        print("init")

        self.w = self.width()
        self.h = self.height()
        self.setGeometry(0, 0, self.w, self.h)
        # self.setFixedWidth(self.w)
        # self.setFixedHeight(self.h)
        # print(self.desktop.devicePixelRatio())
        # print(self.w, self.h)

        self.center_x = int(self.w/2)
        self.center_y = int(self.h/2)

        # minimum margins
        self.margin_left = 200
        self.margin_right = 200
        self.margin_top = 200
        self.margin_bottom = 200


        # arena info
        self.tl_x = int(self.margin_left)
        self.tl_y = int(self.margin_top)
        self.tr_x = int(self.w-self.margin_right)
        self.tr_y = self.tl_y

        self.bl_x = self.tl_x
        self.bl_y = self.h - self.margin_bottom
        self.br_x = self.tr_x
        self.br_y = self.bl_y

        self.arena_w = self.tr_x - self.tl_x
        self.arena_h = self.br_y - self.tr_y


        # held or not
        self.lclick = False
        self.rclick = False

        # fire period if held (ms)
        self.lclick_period = 60
        self.rclick_period = 500

        self.lclick_cooldown = 0
        self.rclick_cooldown = 0


        # edge detection
        self.grad_thresh = 100
        self.grad_width = 25

        self.init_game_objects()

        self.installEventFilter(self)
        self.setMouseTracking(True)

        self.time = 0
        self.timer_ms = 16
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_cb)
        self.timer.start(self.timer_ms)

        self.initialized = True
        self.repaint()

    def __init__(self):
        super().__init__()

        print("_init_")
        self.initialized = False
        self.color_none = QColor(0,0,0,0)
        self.paused = False
        self.debug = False
        self.show_mouse = True

        self.setWindowTitle("SCUM")

        self.setCursor(Qt.BlankCursor)

        self.r = 128
        self.g = self.r
        self.b = self.r
        self.setStyleSheet("background-color: rgba(%d, %d, %d, 128);" % (self.r, self.g, self.b))

        self.aspect_ratio = 16/9
        self.desktop = QDesktopWidget()
        self.screen_count = self.desktop.screenCount()

        self.screen_index = min(1,self.screen_count-1)
        self.screen = self.desktop.screenGeometry(self.screen_index) # select monitor if available
        self.desktop.activateWindow()

        self.show()
        self.setWindowState(Qt.WindowMaximized)

    def reload(self):
        self.init_game_objects()
        self.enemies = []
        self.bullets = []
        self.exp_anims = []



    def timer_cb(self):

        if(not(self.paused)):

            self.time += self.timer_ms

            # if(self.time % 992 == 0):
            #     print(self.time)

            # self.poll_cursor(True)
            self.click_timer()

            self.bullets_update()
            self.bullets_delete()   # removes off-screen bullets

            self.enemies_update()
            self.bullets_check_collision() # bullets/enemies
            self.enemies_check_collision() # player/enemies

            self.exp_anims_update()
            self.exp_anims_delete()

        # else:
        #     self.poll_cursor_paused()

        self.repaint()

    def paintEvent(self, event):

        if(not(self.initialized)): return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        self.draw_gradient_left(painter)
        self.draw_gradient_right(painter)
        self.draw_gradient_top(painter)
        self.draw_gradient_bottom(painter)

        self.draw_angle(painter)
        self.draw_bullets(painter)
        self.draw_player(painter)
        self.draw_enemies(painter)
        self.exp_anims_draw(painter)
        self.draw_mouse(painter)

        self.draw_arena(painter)
        self.draw_player_lives(painter)

        self.draw_pause(painter)


    def click_timer(self):

        if(self.lclick):
            self.lclick_cooldown -= self.timer_ms
            if(self.lclick_cooldown <= 0):
                b = Bullet(self.player_shape[0][0], self.player_shape[0][1], self.player_angle, 0)    # spawn at player tip
                self.bullets.append(b)
                self.lclick_cooldown = self.lclick_period

        if(self.rclick):
            self.rclick_cooldown -= self.timer_ms
            if(self.rclick_cooldown <= 0):
                b = Bullet(self.player_shape[0][0], self.player_shape[0][1], self.player_angle, 1)    # spawn at player tip
                self.bullets.append(b)
                self.rclick_cooldown = self.rclick_period

    # bottom left is origin
    def adj_coords(self, window_x, window_y):
        adj_x = window_x
        adj_y = self.h - window_y
        return (adj_x, adj_y)

    # top left is origin
    def win_coords(self, adj_x, adj_y):
        window_x = adj_x
        window_y = self.h - adj_y
        return (window_x, window_y)

    def clamp_coords(self, window_x, window_y):
        clamp_x = max(min(self.w, window_x), 0)
        clamp_y = max(min(self.h, window_y), 0)
        return (clamp_x, clamp_y)

    def off_window(self, window_x, window_y):
        if(window_x < 0 or window_x > self.w):
            return True
        if(window_y < 0 or window_y > self.h):
            return True
        return False

    def inside_arena(self, window_x, window_y):
        if(window_x < self.tr_x and window_x > self.tl_x):
            if(window_y < self.br_y and window_y > self.tr_y):
                return True
        return False


    def draw_circle(self, painter, x, y, r, pw, pc, bc):
        pen = QPen()
        pen.setWidth(pw)
        pen.setColor(pc)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(bc)
        painter.drawEllipse(int(x-r),int(y-r),int(r*2),int(r*2))

    def calc_player_shape(self, x, y, radius, angle):

        adj_x, adj_y = self.adj_coords(x, y)

        _tip_x = (radius) * math.cos(angle) + adj_x
        _tip_y = (radius) * math.sin(angle) + adj_y

        a1 = angle + (180+40)*math.pi/180
        a2 = angle + (180-40)*math.pi/180

        _x1 = (radius) * math.cos(a1) + adj_x
        _y1 = (radius) * math.sin(a1) + adj_y

        _x2 = (radius) * math.cos(a2) + adj_x
        _y2 = (radius) * math.sin(a2) + adj_y

        _x3 = (radius*1.5) * math.cos(angle+math.pi) + _tip_x
        _y3 = (radius*1.5) * math.sin(angle+math.pi) + _tip_y

        tip_x, tip_y = self.win_coords(_tip_x, _tip_y)
        x1, y1 = self.win_coords(_x1, _y1)
        x2, y2 = self.win_coords(_x2, _y2)
        x3, y3 = self.win_coords(_x3, _y3)

        player_shape = [
            (tip_x, tip_y, x1, y1),
            (tip_x, tip_y, x2, y2),
            (x3, y3, x1, y1),
            (x3, y3, x2, y2),
        ]

        return player_shape

    def translate_player_shape(self, shape, delta_x, delta_y):
        new_shape = []
        for i in range(0,len(shape)) :
            new_shape.append(
                (
                shape[i][0] + delta_x,
                shape[i][1] + delta_y,
                shape[i][2] + delta_x,
                shape[i][3] + delta_y
                )
            )
        return new_shape

    def draw_player_shape(self, painter, shape):
        pen = QPen()
        pen.setWidth(2)
        pen.setColor(Qt.black)

        painter.setPen(pen)
        c = self.color_none
        painter.setBrush(c)
        # painter.setBrush(Qt.black)

        for i in range(0,len(shape)) :
            x0,y0,x1,y1 = shape[i]
            painter.drawLine(int(x1), int(y1), int(x0), int(y0))

    def draw_player_lives(self, painter):

        if(self.player_lives <= 0):
            return

        y = self.tl_y - self.player_radius - 5
        x = self.tl_x + self.player_radius

        shape = self.calc_player_shape(x, y, self.player_radius, math.pi/2)

        for i in range(self.player_lives):
            self.draw_player_shape(painter, shape)
            shape = self.translate_player_shape(shape, self.player_radius*2+10, 0)

        return


    def draw_player(self, painter):

        if(self.debug):
            self.draw_circle(painter, self.player_x, self.player_y, self.player_radius, 1, Qt.blue, self.color_none)

        self.draw_player_shape(painter, self.player_shape)

        # pen = QPen()
        # pen.setWidth(2)
        # pen.setColor(Qt.black)

        # painter.setPen(pen)
        # c = self.color_none
        # painter.setBrush(c)
        # # painter.setBrush(Qt.black)

        # for i in range(0,len(self.player_shape)) :
        #     x0,y0,x1,y1 = self.player_shape[i]
        #     painter.drawLine(int(x1), int(y1), int(x0), int(y0))


    def draw_pause(self, painter):
        if(self.paused):
            pen = QPen()
            pen.setWidth(1)
            pen.setColor(Qt.black)
            painter.setPen(pen)
            painter.setBrush(Qt.black)
            # painter.drawLine(int(self.center_x), 0, int(self.center_x), self.h)
            font = QFont("arial")
            font.setPixelSize(24)
            fm = QFontMetrics(font)
            x = int(self.center_x - fm.width("PAUSED")/2)
            y = int((self.center_y-self.player_radius)*0.9)
            painter.setFont(font)
            painter.drawText(x, y, "PAUSED")



    def draw_mouse(self, painter):
        if(not(self.debug or self.show_mouse)): return
        self.draw_circle(painter, self.mouse_x, self.mouse_y, 2, 1, Qt.black, self.color_none)


    def draw_angle(self, painter):
        if(not(self.debug)): return

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(Qt.gray)
        pen.setStyle(Qt.DashLine)

        painter.setPen(pen)
        painter.setBrush(Qt.gray)

        l = self.w

        adj_x, adj_y = self.adj_coords(self.player_shape[0][0], self.player_shape[0][1])
        x1, y1 = self.win_coords(adj_x, adj_y)

        _x2 = l*math.cos(self.player_angle) + adj_x
        _y2 = l*math.sin(self.player_angle) + adj_y
        x2, y2 = self.win_coords(_x2, _y2)

        painter.drawLine(int(x2), int(y2), int(x1), int(y1))


    def calc_magnitude(self, x, x1, y, y1):
        return math.sqrt((x-x1)**2 + (y-y1)**2)

    def calc_angle(self, x, x1, y, y1):
        ax, ay = self.adj_coords(x, y)
        ax1, ay1 = self.adj_coords(x1, y1)
        dx = ax-ax1
        dy = ay-ay1
        angle = math.atan2(dy, dx)
        deg = angle*180/math.pi
        if(deg < 0):
            deg += 360
        angle = deg*math.pi/180
        return angle

    def calc_angle_magnitude(self, x, x0, y, y0):
        mag = self.calc_magnitude(x, x0, y, y0)
        angle = self.calc_angle(x, x0, y, y0)
        return (angle, mag)

    def update_player(self):
        self.player_angle = self.calc_angle(self.mouse_x, self.player_x, self.mouse_y, self.player_y)
        # self.player_angle, mag = self.calc_angle_magnitude(self.mouse_x, self.player_x, self.mouse_y, self.player_y)
        self.player_shape = self.calc_player_shape(self.player_x, self.player_y, self.player_radius, self.player_angle)


    def get_cursor_pos(self):
        gpos = QCursor.pos()
        pos = self.mapFromGlobal(gpos)
        x = pos.x()
        y = pos.y()
        return x,y

    def poll_cursor(self):
        return
        x,y = self.get_cursor_pos()
        if(x == self.mouse_x and y == self.mouse_y): return

        if(self.paused):
            self.mouse_x = x
            self.mouse_y = y
        # else:
        # # mouse_off_window = self.off_window(x, y)
        # # if(mouse_off_window):
        # #     gpos = self.mapToGlobal(QPoint(self.mouse_x, self.mouse_y))
        # #     pa.moveTo(gpos.x(), gpos.y())

        # self.mouse_off_window = self.off_window(x, y)

        # # if(self.mouse_off_window):
        # if((off_window_condition and self.mouse_off_window) or not(off_window_condition)):
        #     self.mouse_x = x
        #     self.mouse_y = y
        #     self.update_player()
        #     # self.repaint()


    def poll_cursor_paused(self):
        x,y = self.get_cursor_pos()
        if(x == self.mouse_x and y == self.mouse_y): return
        self.mouse_x = x
        self.mouse_y = y


    def mouseMoveEvent(self, event):

        x = event.x()
        y = event.y()

        if(x == self.mouse_x and y == self.mouse_y): return

        self.mouse_x = x
        self.mouse_y = y

        # print("move",x,y)

        if(self.paused): return

        self.update_player()
        self.repaint()

    def mousePressEvent(self, event):
        if(self.paused): return

        # QMouseEvent
        b = event.button()
        # print(b)

        if(b != Qt.RightButton and b != Qt.LeftButton):
            return

        if(b == Qt.LeftButton):
            self.lclick_cooldown = self.lclick_period+60
            self.lclick = True
            t = 0

        if(b == Qt.RightButton):
            self.rclick_cooldown = self.rclick_period
            self.rclick = True
            t = 1

        # pos = event.pos()
        # x = pos.x()
        # y = pos.y()
        # print(x,y)

        b = Bullet(self.player_shape[0][0], self.player_shape[0][1], self.player_angle, t)    # spawn at player tip
        # # b = Bullet(self.player_x, self.player_y, self.player_angle)
        self.bullets.append(b)

    def mouseReleaseEvent(self, event):
        b = event.button()

        if(b == Qt.LeftButton):
            self.lclick = False

        if(b == Qt.RightButton):
            self.rclick = False



    def eventFilter(self,source,event):

        if(event is None): return 0

        if(event.type() == QEvent.KeyPress):

            key = event.key()
            modifiers = QApplication.keyboardModifiers()

            if(modifiers == Qt.ControlModifier):
                if(key == Qt.Key_C):
                    self.custom_close()

            elif(modifiers == Qt.NoModifier):

                if(key == Qt.Key_P):
                    self.paused = not(self.paused)
                    if(self.paused):
                        # self.show_mouse = True
                        self.lclick = False
                        self.rclick = False
                    else:
                        # self.show_mouse = False
                        # self.poll_cursor()
                        self.update_player()
                        # self.repaint()

                if(self.paused): return 0

                if(key == Qt.Key_R):
                    self.reload()

                elif(key == Qt.Key_D):
                    self.debug = not(self.debug)

                elif(key == Qt.Key_X):
                    x,y = self.get_cursor_pos()
                    self.spawn_explosion(x,y)
                
                elif(key == Qt.Key_E):
                    x,y = self.get_cursor_pos()
                    # self.spawn_enemy(x,y,choice([0,1]))
                    self.spawn_enemy(x,y,1)

                elif(key == Qt.Key_M):
                    self.show_mouse = not(self.show_mouse)

                # elif(key == Qt.Key_F11):
                #     if(self.isFullScreen()):
                #         # self.hide()
                #         self.showNormal()
                #         self.setWindowState(Qt.WindowMaximized)
                #         # self.show()
                #     else:
                #         self.showFullScreen()
                #         # self.setWindowState(Qt.WindowMaximized)

                elif(key == Qt.Key_Escape):
                    pass

        return 0

    def draw_bullets(self, painter):
        for i in range(len(self.bullets)):
            b = self.bullets[i]
            b.draw(painter)

    def bullets_update(self):
        for i in range(len(self.bullets)):
            b = self.bullets[i]
            b.update()

    def bullets_delete(self):
        bullets = self.bullets.copy()
        self.bullets = []
        for i in range(len(bullets)):
            b = bullets[i]
            if(not b.delete):
                self.bullets.append(b)
        return len(self.bullets)

    def bullets_check_collision(self):
        for i in range(len(self.bullets)):
            b = self.bullets[i]
            for j in range(len(self.enemies)):
                e = self.enemies[j]
                if(e.delete): continue
                dist = self.calc_magnitude(b.x, e.x, b.y, e.y)
                if(dist < (e.r + b.r)):
                    e.delete = True
                    b.delete = True
                    ea = ExplosionAnimation(b.x,b.y)
                    self.exp_anims.append(ea)
                    continue
        self.enemies_delete()
        self.bullets_delete()

    def enemies_check_collision(self):
        for i in range(len(self.enemies)):
            e = self.enemies[i]
            dist = self.calc_magnitude(self.player_x, e.x, self.player_y, e.y)
            if(dist < (e.r + self.player_radius)):
                e.delete = True
                ea = ExplosionAnimation(e.x, e.y)
                self.exp_anims.append(ea)
                self.player_lives -= 1
                continue
        self.bullets_delete()

    def spawn_enemy(self,x,y,_type):
        e = Enemy(x,y,_type)
        self.enemies.append(e)

    def enemies_update(self):
        for i in range(len(self.enemies)):
            e = self.enemies[i]
            e.update()

    def enemies_delete(self):
        enemies = self.enemies.copy()
        self.enemies = []
        for i in range(len(enemies)):
            e = enemies[i]
            if(not e.delete):
                self.enemies.append(e)
        return len(self.enemies)

    def draw_enemies(self, painter):
        for i in range(len(self.enemies)):
            e = self.enemies[i]
            e.draw(painter)

    def exp_anims_update(self):
        for i in range(len(self.exp_anims)):
            e = self.exp_anims[i]
            e.update()

    def exp_anims_delete(self):
        exp_anims = self.exp_anims.copy()
        self.exp_anims = []
        for i in range(len(exp_anims)):
            e = exp_anims[i]
            if(not e.delete):
                self.exp_anims.append(e)
        return len(self.exp_anims)

    def exp_anims_draw(self, painter):
        for i in range(len(self.exp_anims)):
            e = self.exp_anims[i]
            e.draw(painter)

    def spawn_explosion(self, x, y):
        e = ExplosionAnimation(x,y)
        self.exp_anims.append(e)


    def draw_gradient_rect(self, painter, rect, lgradient, color, alpha):
        pen = QPen()
        pen.setWidth(0)
        pen.setColor(self.color_none)

        c1 = QColor(color.red(), color.green(), color.blue(), int(alpha))
        c2 = QColor(color.red(), color.green(), color.blue(), 0)

        lgradient.setColorAt(0, c1)
        lgradient.setColorAt(1, c2)
        painter.setBrush(lgradient)
        painter.setPen(pen)
        painter.drawRect(rect)

    def draw_gradient_left(self, painter):
        if(self.mouse_x > self.grad_thresh):
            return

        alpha = (1 - self.mouse_x / self.grad_thresh) * 255
        if(self.mouse_x <= 0):
            alpha = 255

        color = QColor(0xff, 0, 0)
        rect = QRect(0, 0, self.grad_width, self.h)
        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        self.draw_gradient_rect(painter, rect, gradient, color, alpha)

    def draw_gradient_right(self, painter):
        if((self.w-self.mouse_x) > self.grad_thresh):
            return

        alpha = (1 - (self.w-self.mouse_x) / self.grad_thresh) * 255
        if(self.mouse_x >= self.w):
            alpha = 255

        color = QColor(0xff, 0, 0)
        rect = QRect(self.w-self.grad_width, 0, self.grad_width, self.h)
        gradient = QLinearGradient(rect.topRight(), rect.topLeft())
        self.draw_gradient_rect(painter, rect, gradient, color, alpha)

    def draw_gradient_top(self, painter):
        if(self.mouse_y > self.grad_thresh):
            return

        alpha = (1 - self.mouse_y / self.grad_thresh) * 255
        if(self.mouse_y <= 0):
            alpha = 255

        color = QColor(0xff, 0, 0)
        rect = QRect(0, 0, self.w, self.grad_width)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        self.draw_gradient_rect(painter, rect, gradient, color, alpha)

    def draw_gradient_bottom(self, painter):
        if((self.h-self.mouse_y) > self.grad_thresh):
            return

        alpha = (1 - (self.h-self.mouse_y) / self.grad_thresh) * 255
        if(self.mouse_y > self.h):
            alpha = 255

        color = QColor(0xff, 0, 0)
        rect = QRect(0, self.h-self.grad_width, self.w, self.grad_width)
        gradient = QLinearGradient(rect.bottomLeft(), rect.topLeft())
        self.draw_gradient_rect(painter, rect, gradient, color, alpha)

    def draw_arena(self, painter):

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(Qt.black)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(self.color_none)

        rect = QRect(QPoint(self.tl_x, self.tl_y), QPoint(self.br_x, self.br_y))

        painter.drawRect(rect)


    def resizeEvent(self, event):
        print("resize", self.width(), self.height())
        if(self.isMaximized() and not(self.initialized)):
            self.init()

    def center(self):
        self.move(int((self.screen_w-self.w)/2), int((self.screen_h-self.h)/2))


    def list_add(self, _list, value, max_len):
        n = len(_list)
        if(n > max_len):
            _list.pop(n-1)
        _list.insert(0,value)
        return _list


    def custom_close(self):
        QCoreApplication.instance().quit()


    def closeEvent(self, event):
        self.custom_close()



if __name__ == '__main__':

    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)
    gui = MainWindow()
    # gui.show()
    app.exec_()

