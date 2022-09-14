from time import time, sleep
from random import choice
import sys, os
import math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeyEvent, QPainter,QImage, QPen, QIcon, QPixmap, QColor, QBrush, QCursor, QFont, QPalette, QTransform
from PyQt5.QtCore import Qt, QPoint, QPointF, QSize, QEvent, QTimer, QCoreApplication


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
        self.angle = angle
        self.dist = 0

        self.d = 2 # diameter

        self.delete = False

    def update(self):
        self.dist += 3
        x = self.dist*math.cos(self.angle)+self.spawnx
        y = self.dist*math.sin(self.angle)+self.spawny
        self.fx, self.fy = gui.win_coords(x,y)
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
        self.d = 10 # diameter
        self.angle = 0
        self.magnitude = 0

    def update(self):
        self.dist = 2
        self.angle = gui.calc_angle(gui.mouse_x, self.fx, gui.mouse_y, self.fy)
        self.magnitude = gui.calc_magnitude(gui.mouse_x, self.fx, gui.mouse_y, self.fy)

        ax, ay = gui.adj_coords(self.fx, self.fy)

        x = self.dist*math.cos(self.angle)+ax
        y = self.dist*math.sin(self.angle)+ay
        self.fx, self.fy = gui.win_coords(x,y)
        self.x = int(self.fx)
        self.y = int(self.fy)

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("SCUM")

        self.setCursor(Qt.BlankCursor)

        self.r = 128
        self.g = self.r
        self.b = self.r
        self.setStyleSheet("background-color: rgba(%d, %d, %d, 128);" % (self.r, self.g, self.b))

        self.mouse_x0 = None
        self.mouse_y0 = None
        self.mouse_x = None
        self.mouse_y = None
        self.player_off_window = False
        self.angle = 0
        self.curr_angle = 0

        self.player_color = Qt.red

        # mouse position list
        self.xs = []
        self.ys = []

        self.angles = []
        self.mags = []
        self.angle_list_max = 10


        self.timer_ms = 16

        # self.rat = QImage("rat.png","PNG")
        # self.rat2 = self.rat.scaledToHeight(int(100))

        # self.rat2.transformed(QMatrix().rotate(90.0))
        # print(self.rat.width(), self.rat.height())
        # balli.img = balli.img.scaledToHeight(int(balli.bw))



        # window size and placement
        self.ar = 16/9 #aspect ratio
        self.desktop = QDesktopWidget()
        self.screen_count = self.desktop.screenCount()

        self.screen_index = min(1,self.screen_count-1)
        self.screen = self.desktop.screenGeometry(self.screen_index) # select monitor if available

        self.screen_w = self.screen.width()
        self.screen_h = self.screen.height()

        # self.w = int(self.screen_w*0.8)
        self.w = min(1400,self.screen_w)
        self.h = min(int(self.w/self.ar),self.screen_h)

        top_left_x = int((self.screen_w-self.w)/2)
        top_left_y = int((self.screen_h-self.h)/2)
        # print(top_left_x, top_left_y)

        self.bullets = []

        self.enemies = [
            Enemy(0,0),
            Enemy(0,self.h),
            Enemy(self.w,0),
            Enemy(self.w,self.h)
        ]

        self.setGeometry(top_left_x, top_left_y, self.w, self.h)

        self.mouse_x = int(self.w/2)
        self.mouse_y = int(self.h/2)

        self.setFixedWidth(self.w)
        self.setFixedHeight(self.h)

        self.installEventFilter(self)
        self.setMouseTracking(True)

        self.repaint()

        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_cb)
        self.timer.start(self.timer_ms)

    def timer_cb(self):
        self.poll_cursor()

        self.update_enemies()
        count = self.update_bullets()
        # if(count > 0):
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

        painter.setPen(pen)
        painter.setBrush(bc)
        painter.drawEllipse(int(x-d/2),int(y-d/2),int(d),int(d))

    def draw_player(self):

        if(self.mouse_x is None or self.mouse_y is None):
            return

        pen = QPen()
        pen.setWidth(2)
        pen.setColor(Qt.black)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(Qt.black)

        l = 15

        adj_x, adj_y = self.adj_coords(self.mouse_x, self.mouse_y)

        # painter.drawLine(self.mouse_x0, self.mouse_y0, self.mouse_x, self.mouse_y)
        # painter.drawLine(self.mouse_x, self.mouse_y, self.mouse_x+l, self.mouse_y+l)

        # painter.rotate(45)
        # painter.drawImage(100, 100, self.rat2)
        # painter.rotate(0)

        a1 = self.angle + (180+15)*math.pi/180
        a2 = self.angle + (180-15)*math.pi/180

        _x1 = l*math.cos(a1) + adj_x
        _y1 = l*math.sin(a1) + adj_y
        x1, y1 = self.win_coords(_x1, _y1)

        _x2 = l*math.cos(a2) + adj_x
        _y2 = l*math.sin(a2) + adj_y
        x2, y2 = self.win_coords(_x2, _y2)

        painter.drawLine(int(x1), int(y1), self.mouse_x, self.mouse_y)
        painter.drawLine(int(x2), int(y2), self.mouse_x, self.mouse_y)

        # self.draw_circle(painter, self.mouse_x, self.mouse_y, 1, 1, Qt.red, Qt.red)


        # DEBUG
        # pen.setWidth(1)
        # pen.setColor(Qt.red)
        # painter.setPen(pen)
        # painter.setBrush(Qt.blue)
        # painter.drawEllipse(500,500,10,10)
        # pen.setWidth(1)
        # pen.setColor(Qt.black)
        # painter.setPen(pen)
        # painter.drawEllipse(500,500,1,1)


        # deg = self.angle*180/math.pi

        # a = adj_x - l*math.cos(self.angle)
        # b = adj_y - l*math.sin(self.angle)
        # x,y = self.win_coords(a,b)
        # painter.drawLine(int(x), int(y), self.mouse_x, self.mouse_y)

        # # # debug current mouse position
        # painter.setBrush(self.player_color)
        # painter.drawEllipse(self.mouse_x, self.mouse_y, 2, 2)


        # t = QTransform()
        # t.rotateRadians(self.angle)
        # self.rat2 = self.rat2.transformed(t)
        # painter.drawImage(self.mouse_x, self.mouse_y, self.rat2)


        # pen.setWidth(2)
        # pen.setColor(Qt.blue)
        # painter.setPen(pen)
        # offset=0
        # for i in range(len(self.xs)-offset):
        #     wx, wy = self.win_coords(self.xs[i+offset], self.ys[i+offset])
        #     painter.drawEllipse(wx, wy, 1, 1)

    def draw_angle(self):
        return

        if(self.mouse_x is None or self.mouse_y is None):
            return

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(Qt.gray)
        pen.setStyle(Qt.DashLine)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(Qt.gray)

        l = self.w

        adj_x, adj_y = self.adj_coords(self.mouse_x, self.mouse_y)

        _x2 = l*math.cos(self.angle) + adj_x
        _y2 = l*math.sin(self.angle) + adj_y
        x2, y2 = self.win_coords(_x2, _y2)

        painter.drawLine(int(x2), int(y2), self.mouse_x, self.mouse_y)


    def calc_magnitude(self, x, x1, y, y1):
        return math.sqrt((x-x1)**2 + (y-y1)**2)

    def calc_angle(self, x, x1, y, y1):
        ax, ay = self.adj_coords(x, y)
        ax1, ay1 = self.adj_coords(x1, y1)
        dx = ax-ax1
        dy = ay-ay1
        angle = math.atan2(dy, dx)
        deg0 = angle*180/math.pi
        deg = deg0
        if(deg < 0):
            deg += 360
        angle = deg*math.pi/180
        return angle

    def calc_angle_magnitude(self, x, x0, y, y0):
        mag = self.calc_magnitude(x, x0, y, y0)
        angle = self.calc_angle(x, x0, y, y0)
        return (angle, mag)

    def update_cursor(self, x, y):

        if(self.mouse_x is None):
            self.mouse_x = x
            self.mouse_y = y
            self.mouse_x0 = x
            self.mouse_y0 = y
            return

        if(x == self.mouse_x and y == self.mouse_y):
            return

        self.mouse_x0 = self.mouse_x
        self.mouse_y0 = self.mouse_y
        self.mouse_x = x
        self.mouse_y = y

        angle, mag = self.calc_angle_magnitude(self.mouse_x, self.mouse_x0, self.mouse_y, self.mouse_y0)

        if(mag > 1):

            self.list_add(self.angles, angle, self.angle_list_max)
            self.list_add(self.mags, mag, self.angle_list_max)


            ax, ay = self.adj_coords(self.mouse_x, self.mouse_y)
            # self.list_add(self.xs, ax, 10)
            # self.list_add(self.ys, ay, 10)

            # m,b,r2 = self.regress(self.xs, self.ys)
            r2=0

            if(r2 >= 0.9):

                self.angle = math.atan(m/1)
                self.player_color = Qt.green

            else:

                n = len(self.angles)

                degrees = [x*180/math.pi for x in self.angles]

                mind = min(degrees)
                maxd = max(degrees)
                ranged = maxd-mind

                ranged1 = mind - (maxd-360)

                if(ranged1 >= ranged):

                    self.player_color = Qt.red

                    num = 0
                    den = 0
                    for i in range(n):
                        a = degrees[i]
                        w = self.mags[i]

                        num += (w * a)
                        den += (w)

                    avg_angle = num/den
                    if(avg_angle < 0):
                        avg_angle = avg_angle+360


                else:
                    self.player_color = Qt.green
                    # printf("%.0f, %.0f    %.0f, %.0f\n", mind, maxd, ranged, ranged1)

                    num = 0
                    den = 0
                    for i in range(n):
                        a = degrees[i]
                        if(a > 270):
                            a = a-360
                        num += (a * self.mags[i])
                        den += (self.mags[i])

                    avg_angle = num/den
                    if(avg_angle < 0):
                        avg_angle = avg_angle+360

                avg_angle = avg_angle*math.pi/180

                self.angle = avg_angle

                # self.angle = (avg_angle+self.angles[i])/2

                # self.angle = num/den
                deg = self.angle*180/math.pi

                # printf("%.0f\n", self.angles[0]*180/math.pi)

                # DEBUG
                # printf("%.0f   ", deg)
                # for i in range(n):
                #     printf(" %.2f,%.0f | ", self.mags[i], self.angles[i]*180/math.pi)
                # printf("\n")


        self.repaint()

    def list_add(self, _list, value, max_len):
        n = len(_list)
        if(n > max_len):
            _list.pop(n-1)
        _list.insert(0,value)
        return _list


    def poll_cursor(self):
        pos = QCursor.pos()

        # print("poll",pos.x(),pos.y())
        gpos = self.mapFromGlobal(pos)
        x = gpos.x()
        y = gpos.y()

        self.player_off_window = self.off_window(x, y)
        if(not(self.player_off_window)):
            self.update_cursor(x,y)

        # print(gpos.x(),gpos.y())

    def mousePressEvent(self, QMouseEvent):
        # if event.button() == Qt.LeftButton:
        pos = QMouseEvent.pos()
        x = pos.x()
        y = pos.y()
        # print(x,y)

        b = Bullet(x,y,self.angle)
        self.bullets.append(b)

    def mouseMoveEvent(self, event):
        x = event.x()
        y = event.y()

        # print("%d -> %d     %d -> %d" % (self.mouse_x0, self.mouse_x, self.mouse_y0, self.mouse_y))
        self.update_cursor(x,y)

        # print("move event",x,y)
        # self.repaint()

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
            painter.drawEllipse(int(b.x-b.d/2), int(b.y-b.d/2), b.d, b.d)


    def update_bullets(self):
        bullets = self.bullets.copy()
        self.bullets = []

        for i in range(len(bullets)):
            b = bullets[i]
            b.update()
            if(not b.delete):
                self.bullets.append(b)

        return len(self.bullets)

    def update_enemies(self):
        for i in range(len(self.enemies)):
            e = self.enemies[i]
            e.update()

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
            painter.drawEllipse(int(e.x-e.d/2), int(e.y-e.d/2), e.d, e.d)

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






    def paintEvent(self, event):
        # print("paintevent")
        self.draw_angle()
        self.draw_bullets()
        self.draw_player()
        self.draw_enemy()



    def resizeEvent(self, event):
        # # qr = self.geometry()
        # # w = qr.width()
        # # h = qr.height()
        # self.w = min(w,self.screen_w)
        # self.h = min(int(self.w/self.ar),self.screen_h)
        # self.resize(self.w,self.h)
        return


    def center(self):
        # qr = self.frameGeometry()
        # cp = QDesktopWidget().availableGeometry().center()
        # qr.moveCenter(cp)
        # self.move(qr.topLeft())

        self.move(int((self.screen_w-self.w)/2), int((self.screen_h-self.h)/2))


    def custom_close(self):
        QCoreApplication.instance().quit()

    def reload_stuff(self):
        self.enemies = [
            Enemy(0,0),
            Enemy(0,self.h),
            Enemy(self.w,0),
            Enemy(self.w,self.h)
        ]




    def eventFilter(self,source,event):

        if(event.type() == QEvent.KeyPress):
            key = event.key()
            modifiers = QApplication.keyboardModifiers()

            if(modifiers == Qt.ControlModifier):
                if(key == Qt.Key_C):
                    self.custom_close()

            elif(modifiers == Qt.NoModifier):
                if(key == Qt.Key_R):
                    self.reload_stuff()


            # if event.key() == Qt.Key_Right:
            #     self.bs += self.speed_control
            #     self.set_bs()

        return 0

    def closeEvent(self, event):
        self.custom_close()





if __name__ == '__main__':

    # import ctypes
    # ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("bounce_gui_ctypes_thing")

    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)
    gui = MainWindow()
    gui.show()
    app.exec_()

