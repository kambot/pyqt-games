from time import time, sleep
from random import choice
import sys, os
import math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeyEvent, QPainter,QImage, QPen, QIcon, QPixmap, QColor, QBrush, QCursor, QFont, QPalette, QTransform, QLinearGradient
from PyQt5.QtCore import Qt, QPoint, QPointF, QSize, QEvent, QTimer, QCoreApplication, QRect

def printf(fmt, *args):
    if(len(args) > 0):
        print(fmt % args, end="")
    else:
        print(fmt, end="")


class Bullet():
    def __init__(self, x, y, angle):
        self.spawnx, self.spawny = gui.adj_coords(x,y)
        self.fx = x
        self.fy = y
        self.x = x
        self.y = y
        self.x_prior = x
        self.y_prior = y
        self.r = 1 # radius
        self.angle = angle
        self.dist = 0
        self.delete = False

    def update(self):
        self.dist = .3
        ax, ay = gui.adj_coords(self.fx, self.fy)
        x = self.dist*math.cos(self.angle)+ax
        y = self.dist*math.sin(self.angle)+ay
        self.fx, self.fy = gui.win_coords(x,y)
        self.x_prior = self.x
        self.y_prior = self.y
        self.x = int(self.fx)
        self.y = int(self.fy)
        if(gui.off_window(self.x, self.y)):
            self.delete = True

class Enemy():
    def __init__(self, x, y):
        self.fx = x
        self.fy = y
        self.x = x
        self.y = y
        self.x_prior = x
        self.y_prior = y
        self.r = 5 # radius
        self.angle = 0
        self.magnitude = 0
        self.delete = False

    def update(self):
        self.dist = 2
        self.angle = gui.calc_angle(gui.player_x, self.fx, gui.player_y, self.fy)
        self.magnitude = gui.calc_magnitude(gui.player_x, self.fx, gui.player_y, self.fy)

        ax, ay = gui.adj_coords(self.fx, self.fy)

        x = self.dist*math.cos(self.angle)+ax
        y = self.dist*math.sin(self.angle)+ay
        self.fx, self.fy = gui.win_coords(x,y)
        self.x = int(self.fx)
        self.y = int(self.fy)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.debug = False
        self.show_mouse = False

        self.setWindowTitle("SCUM")

        self.setCursor(Qt.BlankCursor)

        self.r = 128
        self.g = self.r
        self.b = self.r
        self.setStyleSheet("background-color: rgba(%d, %d, %d, 128);" % (self.r, self.g, self.b))

        # held or not
        self.lclick = False
        self.rclick = False

        # fire period if held (ms)
        self.lclick_period = 0
        self.rclick_period = 500

        self.lclick_cooldown = 0
        self.rclick_cooldown = 0

        # self.rat = QImage("rat.png","PNG")
        # self.rat2 = self.rat.scaledToHeight(int(100))

        # self.rat2.transformed(QMatrix().rotate(90.0))
        # print(self.rat.width(), self.rat.height())
        # balli.img = balli.img.scaledToHeight(int(balli.bw))


        # window size and placement
        self.aspect_ratio = 16/9 #aspect ratio
        self.desktop = QDesktopWidget()
        self.screen_count = self.desktop.screenCount()

        self.screen_index = min(1,self.screen_count-1)
        self.screen = self.desktop.screenGeometry(self.screen_index) # select monitor if available

        self.screen_w = self.screen.width()
        self.screen_h = self.screen.height()

        # self.w = int(self.screen_w*0.8)
        self.w = min(1400,self.screen_w)
        self.h = min(int(self.w/self.aspect_ratio),self.screen_h)

        self.grad_thresh = 100
        self.grad_width = 25

        # self.w = 100
        # self.h = min(int(self.w/self.aspect_ratio),self.screen_h)

        top_left_x = int((self.screen_w-self.w)/2)
        top_left_y = int((self.screen_h-self.h)/2)
        # print(top_left_x, top_left_y)

        self.setGeometry(top_left_x, top_left_y, self.w, self.h)

        self.setFixedWidth(self.w)
        self.setFixedHeight(self.h)
        # self.showFullScreen()


        self.installEventFilter(self)
        self.setMouseTracking(True)


        self.bullets = []

        self.enemies = [
            # Enemy(0,0),
            # Enemy(0,self.h),
            # Enemy(self.w,0),
            # Enemy(self.w,self.h)
        ]

        self.mouse_x, self.mouse_y = self.get_cursor_pos()
        self.mouse_off_window = self.off_window(self.mouse_x, self.mouse_y)

        self.player_x = int(self.w/2)
        self.player_y = int(self.h/2)
        # tip, left leg, right leg, middle
        self.player_shape = []
        self.angle = 0

        self.player_diameter = 25
        self.update_player()


        self.time = 0
        self.timer_ms = 16
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_cb)
        self.timer.start(self.timer_ms)

        self.show()
        self.repaint()

    def reload(self):
        self.enemies = [
            Enemy(0,0),
            Enemy(0,self.h),
            Enemy(self.w,0),
            Enemy(self.w,self.h)
        ]

    def click_timer(self):

        if(self.lclick):
            self.lclick_cooldown -= self.timer_ms
            if(self.lclick_cooldown <= 0):
                b = Bullet(self.player_shape[0][0], self.player_shape[0][1], self.angle)    # spawn at player tip
                self.bullets.append(b)
                self.lclick_cooldown = self.lclick_period

        if(self.rclick):
            self.rclick_cooldown -= self.timer_ms
            if(self.rclick_cooldown <= 0):
                b = Bullet(self.player_shape[0][0], self.player_shape[0][1], self.angle)    # spawn at player tip
                self.bullets.append(b)
                self.rclick_cooldown = self.rclick_period


    def timer_cb(self):
        self.time += self.timer_ms

        self.lclick = True
        self.angle += 0.05

        self.update_player()

        self.click_timer()
        self.poll_cursor()

        self.bullets_update()
        self.bullets_delete()   # removes off-screen bullets



        self.repaint()

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

    def draw_circle(self, painter, x, y, d, pw, pc, bc):
        pen = QPen()
        pen.setWidth(pw)
        pen.setColor(pc)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(bc)
        painter.drawEllipse(int(x-d/2),int(y-d/2),int(d),int(d))

    def calc_player_shape(self):
        # player_x, player_y  -> center of the player

        adj_x, adj_y = self.adj_coords(self.player_x, self.player_y)

        _tip_x = (self.player_diameter/2) * math.cos(self.angle) + adj_x
        _tip_y = (self.player_diameter/2) * math.sin(self.angle) + adj_y

        a1 = self.angle + (180+40)*math.pi/180
        a2 = self.angle + (180-40)*math.pi/180

        _x1 = (self.player_diameter/2) * math.cos(a1) + adj_x
        _y1 = (self.player_diameter/2) * math.sin(a1) + adj_y

        _x2 = (self.player_diameter/2) * math.cos(a2) + adj_x
        _y2 = (self.player_diameter/2) * math.sin(a2) + adj_y

        _x3 = (self.player_diameter*0.75) * math.cos(self.angle+math.pi) + _tip_x
        _y3 = (self.player_diameter*0.75) * math.sin(self.angle+math.pi) + _tip_y

        tip_x, tip_y = self.win_coords(_tip_x, _tip_y)
        x1, y1 = self.win_coords(_x1, _y1)
        x2, y2 = self.win_coords(_x2, _y2)
        x3, y3 = self.win_coords(_x3, _y3)

        self.player_shape = [
            (tip_x, tip_y, x1, y1),
            (tip_x, tip_y, x2, y2),
            (x3, y3, x1, y1),
            (x3, y3, x2, y2),
        ]



    def draw_player(self):
        return

        painter = QPainter(self)

        if(self.debug):
            self.draw_circle(painter, self.player_x, self.player_y, self.player_diameter, 1, Qt.blue, QColor(0,0,0,0))


        pen = QPen()
        pen.setWidth(2)
        pen.setColor(Qt.black)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        c = QColor(0,0,0,0)
        painter.setBrush(c)
        # painter.setBrush(Qt.black)

        for i in range(0,len(self.player_shape)) :
            x0,y0,x1,y1 = self.player_shape[i]
            painter.drawLine(int(x1), int(y1), int(x0), int(y0))


    def draw_mouse(self):
        if(not(self.debug or self.show_mouse)): return
        painter = QPainter(self)
        self.draw_circle(painter, self.mouse_x, self.mouse_y, 4, 1, Qt.black, QColor(0,0,0,0))


    def draw_angle(self):
        if(not(self.debug)): return

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(Qt.gray)
        pen.setStyle(Qt.DashLine)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(Qt.gray)

        l = self.w

        adj_x, adj_y = self.adj_coords(self.player_x, self.player_y)

        _x2 = l*math.cos(self.angle) + adj_x
        _y2 = l*math.sin(self.angle) + adj_y
        x2, y2 = self.win_coords(_x2, _y2)

        painter.drawLine(int(x2), int(y2), self.player_x, self.player_y)


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
        # self.angle, mag = self.calc_angle_magnitude(self.mouse_x, self.player_x, self.mouse_y, self.player_y)
        self.calc_player_shape()


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

        # mouse_off_window = self.off_window(x, y)
        # if(mouse_off_window):
        #     gpos = self.mapToGlobal(QPoint(self.mouse_x, self.mouse_y))
        #     pa.moveTo(gpos.x(), gpos.y())

        self.mouse_off_window = self.off_window(x, y)
        if(self.mouse_off_window):
            self.mouse_x = x
            self.mouse_y = y
            self.update_player()
            self.repaint()


    def mouseMoveEvent(self, event):
        return
        x = event.x()
        y = event.y()

        if(x == self.mouse_x and y == self.mouse_y): return

        self.mouse_x = x
        self.mouse_y = y

        self.update_player()
        self.repaint()

    def mousePressEvent(self, event):
        return
        # QMouseEvent
        b = event.button()
        # print(b)

        if(b != Qt.RightButton and b != Qt.LeftButton):
            return

        if(b == Qt.LeftButton):
            self.lclick_cooldown = self.lclick_period
            self.lclick = True

        if(b == Qt.RightButton):
            self.rclick_cooldown = self.rclick_period
            self.rclick = True

        # pos = event.pos()
        # x = pos.x()
        # y = pos.y()
        # print(x,y)

        b = Bullet(self.player_shape[0][0], self.player_shape[0][1], self.angle)    # spawn at player tip
        # # b = Bullet(self.player_x, self.player_y, self.angle)
        self.bullets.append(b)

    def mouseReleaseEvent(self, event):
        return
        b = event.button()

        if(b == Qt.LeftButton):
            self.lclick = False

        if(b == Qt.RightButton):
            self.rclick = False

    # TODO: refactor
    def draw_bullets(self):

        pen = QPen()
        pen.setWidth(3)
        pen.setColor(Qt.cyan)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(Qt.black)

        for i in range(len(self.bullets)):
            b = self.bullets[i]
            painter.drawEllipse(int(b.x-b.r), int(b.y-b.r), b.r*2, b.r*2)


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
                    continue
        self.enemies_delete()
        self.bullets_delete()

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

    # TODO: refactor
    def draw_enemy(self):

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(Qt.black)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(Qt.red)

        for i in range(len(self.enemies)):
            e = self.enemies[i]
            painter.drawEllipse(int(e.x-e.r), int(e.y-e.r), e.r*2, e.r*2)

        # DEBUG
        # ax, ay = self.adj_coords(e.x,e.y)
        # ax1 = int(e.magnitude*math.cos(e.angle))+ax
        # ay1 = int(e.magnitude*math.sin(e.angle))+ay
        # x1, y1 = self.win_coords(ax1, ay1)
        # pen.setWidth(1)
        # pen.setColor(Qt.gray)
        # pen.setStyle(Qt.DashLine)
        # painter.setPen(pen)
        # painter.setBrush(Qt.gray)
        # painter.drawLine(int(x1), int(y1), e.x, e.y)

    def draw_gradient_left(self):
        if(self.mouse_x > self.grad_thresh):
            return

        alpha = (1 - self.mouse_x / self.grad_thresh) * 255
        if(self.mouse_x <= 0):
            alpha = 255

        pen = QPen()
        pen.setWidth(0)
        pen.setColor(QColor(0,0,0,0))

        rect = QRect(0, 0, self.grad_width, self.h)
        painter = QPainter(self)
        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        gradient.setColorAt(0, QColor(255, 0, 0, int(alpha)))
        gradient.setColorAt(1, QColor(255, 0, 0, 0))
        painter.setBrush(gradient)
        painter.setPen(pen)
        painter.drawRect(rect)

    def draw_gradient_right(self):
        if((self.w-self.mouse_x) > self.grad_thresh):
            return

        alpha = (1 - (self.w-self.mouse_x) / self.grad_thresh) * 255
        if(self.mouse_x >= self.w):
            alpha = 255

        pen = QPen()
        pen.setWidth(0)
        pen.setColor(QColor(0,0,0,0))

        rect = QRect(self.w-self.grad_width, 0, self.grad_width, self.h)
        painter = QPainter(self)
        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        gradient.setColorAt(1, QColor(255, 0, 0, int(alpha)))
        gradient.setColorAt(0, QColor(255, 0, 0, 0))
        painter.setBrush(gradient)
        painter.setPen(pen)
        painter.drawRect(rect)

    def draw_gradient_top(self):
        if(self.mouse_y > self.grad_thresh):
            return

        alpha = (1 - self.mouse_y / self.grad_thresh) * 255
        if(self.mouse_y <= 0):
            alpha = 255

        pen = QPen()
        pen.setWidth(0)
        pen.setColor(QColor(0,0,0,0))

        rect = QRect(0, 0, self.w, self.grad_width)
        painter = QPainter(self)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0, QColor(255, 0, 0, int(alpha)))
        gradient.setColorAt(1, QColor(255, 0, 0, 0))
        painter.setBrush(gradient)
        painter.setPen(pen)
        painter.drawRect(rect)

    def draw_gradient_bottom(self):
        if((self.h-self.mouse_y) > self.grad_thresh):
            return

        alpha = (1 - (self.h-self.mouse_y) / self.grad_thresh) * 255
        if(self.mouse_y <= 0):
            alpha = 255

        pen = QPen()
        pen.setWidth(0)
        pen.setColor(QColor(0,0,0,0))

        rect = QRect(0, self.h-self.grad_width, self.w, self.grad_width)
        painter = QPainter(self)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(1, QColor(255, 0, 0, int(alpha)))
        gradient.setColorAt(0, QColor(255, 0, 0, 0))
        painter.setBrush(gradient)
        painter.setPen(pen)
        painter.drawRect(rect)


    def paintEvent(self, event):

        self.draw_bullets()
        self.draw_player()
        self.draw_enemy()
        self.draw_mouse()


        # ql = QLinearGradient(10, 10, 20, 20)
        # ql.setStart(0, 10)
        # ql.setFinalStop(0, 50)
        # ql.setColorAt(0.1, QColor(14, 179, 255));
        # ql.setColorAt(0.8, QColor(255, 179, 255));
        # ql.start()

        # yellow = 0.5
        # red = 0.5
        # painter = QPainter(self)
        # self.grad = QLinearGradient()
        # # self.grad.setColorAt(yellow, QColor(255, 255, 0))     # Yellow
        # self.grad.setColorAt(red, QColor(255, 0, 0, 50))          # Red
        # self.grad.setStart(0,10)
        # painter.setBrush(self.grad)
        # painter.drawRect(0,0,100,100)




    def resizeEvent(self, event):
        # # qr = self.geometry()
        # # w = qr.width()
        # # h = qr.height()
        # self.w = min(w,self.screen_w)
        # self.h = min(int(self.w/self.aspect_ratio),self.screen_h)
        # self.resize(self.w,self.h)
        return


    def center(self):
        # qr = self.frameGeometry()
        # cp = QDesktopWidget().availableGeometry().center()
        # qr.moveCenter(cp)
        # self.move(qr.topLeft())

        self.move(int((self.screen_w-self.w)/2), int((self.screen_h-self.h)/2))



    def list_add(self, _list, value, max_len):
        n = len(_list)
        if(n > max_len):
            _list.pop(n-1)
        _list.insert(0,value)
        return _list


    def custom_close(self):
        QCoreApplication.instance().quit()




    def eventFilter(self,source,event):

        if(event.type() == QEvent.KeyPress):
            key = event.key()
            modifiers = QApplication.keyboardModifiers()

            if(modifiers == Qt.ControlModifier):
                if(key == Qt.Key_C):
                    self.custom_close()

            elif(modifiers == Qt.NoModifier):
                if(key == Qt.Key_R):
                    self.reload()
                elif(key == Qt.Key_D):
                    self.debug = not(self.debug)

        return 0

    def closeEvent(self, event):
        self.custom_close()



if __name__ == '__main__':

    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)
    gui = MainWindow()
    # gui.show()
    app.exec_()

