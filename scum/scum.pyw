from time import time, sleep
from random import choice
import sys, os
import math
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QKeyEvent, QPainter,QImage, QPen, QIcon, QPixmap, QColor, QBrush, QCursor, QFont, QPalette, QTransform, QLinearGradient, QFontMetrics, QStaticText
from PyQt5.QtCore import Qt, QPoint, QPointF, QSize, QEvent, QTimer, QCoreApplication, QRect
from datetime import datetime

def bound(_val, _min, _max):
    return max(min(_val, _max), _min)

def printf(fmt, *args):
    if(len(args) > 0):
        print(fmt % args, end="")
    else:
        print(fmt, end="")

class Explosion():
    def __init__(self, x, y, max_r, duration, damaging, can_spawn_powerup):
        # self.spawnx, self.spawny = gui.adj_coords(x,y)
        self.x = x
        self.y = y
        self.r = 0
        self.max_r = max_r
        self.delta_r = (self.max_r*2*16)/duration
        self.delete = False
        self.colors = [
                QColor(0xff, 0x00, 0x00),
                QColor(0xff, 0xff, 0xff),
                QColor(0xff, 0xff, 0x00),
                QColor(0xff, 0xa5, 0x00),
            ]
        self.color = choice(self.colors)
        self.damaging = damaging
        self.can_spawn_powerup = can_spawn_powerup

    def update(self):

        if(self.r >= self.max_r):
            self.delta_r *= -1

        self.r += self.delta_r
        self.color = choice(self.colors)

        if(self.r <= 0):
            if(self.can_spawn_powerup):
                gui.spawn_rand_power_up(self.x, self.y)
            self.delete = True

    def draw(self, painter):
        gui.draw_circle(painter, self.x, self.y, self.r, 0, gui.color_none, self.color)


class Bullet():
    def __init__(self, params, _type, x, y, angle, explosive, penetrating):
        self.params = params
        self.fx = x
        self.fy = y
        self.x = x
        self.y = y
        self.angle = angle
        self.delete = False
        self.type = _type
        self.explosive = explosive or params["explosive"]
        self.penetrating = penetrating or params["penetrating"]
        self.speed = params["speed"]
        # self.xs = []
        # self.ys = []
        self.r = params["radius"]
        self.color = QColor(params["color"])


        # self.explosive = True
        # self.penetrating = True

        r = self.r+1
        self.lx0 = r*math.cos(self.angle)
        self.ly0 = r*math.sin(self.angle)
        self.lx1 = r*math.cos(self.angle+math.pi)
        self.ly1 = r*math.sin(self.angle+math.pi)

        self.lx0 = int(self.lx0)
        self.ly0 = int(self.ly0)
        self.lx1 = int(self.lx1)
        self.ly1 = int(self.ly1)

        if(self.explosive):
            self.color = QColor(0x800000)


    def on_enemy_collision(self): # and power ups
        if(not(self.penetrating)):
            self.delete = True

    def update(self):
        ax, ay = gui.adj_coords(self.fx, self.fy)
        x = self.speed*math.cos(self.angle)+ax
        y = self.speed*math.sin(self.angle)+ay
        self.fx, self.fy = gui.win_coords(x,y)
        self.x = int(self.fx)
        self.y = int(self.fy)
        # self.xs.append(self.x)
        # self.ys.append(self.y)
        # if(gui.off_window(self.x, self.y)):
        if(not gui.inside_arena(self.x, self.y, self.r)):
            self.delete = True
            # gui.spawn_explosion(self.x, self.y)

    def draw(self, painter):
        if(self.penetrating):
            gui.draw_line(painter, self.lx0+self.x, self.y-self.ly0, self.lx1+self.x, self.y-self.ly1, 2, self.color, Qt.black)
        else:
            gui.draw_circle(painter, self.x, self.y, self.r, 0, gui.color_none, self.color)

class Enemy():
    def __init__(self, params, _type, x=None, y=None):

        self.params = params

        self.r = gui.rand_range(params["min_radius"],params["max_radius"])

        if(x is None or y is None):
            x,y = gui.rand_border_coords([0,1,2,3], self.r)

        self.speed = gui.rand_range(params["min_speed"], params["max_speed"])

        self.fx = x
        self.fy = y
        self.x = x
        self.y = y
        self.angle = 0
        self.delete = False
        self.type = _type
        self.color = QColor(params["color"])
        self.angle_range = 60
        self.t0 = gui.time
        self.tracking_state = 0

        self.update_angle()


    def rand_angle(self):
        urange = int(self.angle_range/2)
        lrange = urange * -1
        rad = gui.calc_angle(gui.player_x, self.fx, gui.player_y, self.fy)
        deg = rad*180/math.pi
        deg += choice(range(lrange,urange))
        self.angle = deg*math.pi/180

    def player_angle(self):
        self.angle = gui.calc_angle(gui.player_x, self.fx, gui.player_y, self.fy)

    def update_angle(self):
        if(self.params["tracking"]):
            self.angle_range = 30
            if(self.tracking_state == 0):
                self.tracking_state = 1
                self.player_angle()
            else:
                self.tracking_state = 0
                self.rand_angle()
        else:
            self.rand_angle()

    def on_bullet_collision(self, bullet):
        gui.spawn_explosion(self.x, self.y, self.r*3, 500, bullet.explosive, True)
        self.delete = True

    def on_player_collision(self):
        gui.spawn_explosion(self.x, self.y, self.r*3, 500, False, False)
        self.delete = True

    def update(self):

        speed = self.speed
        if(gui.power_params[gui.SLOW]["active"]):
            speed *= gui.slow_mult

        ax, ay = gui.adj_coords(self.fx, self.fy)
        x = speed*math.cos(self.angle)+ax
        y = speed*math.sin(self.angle)+ay
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
            self.update_angle()

        if(self.params["tracking"]):
            dt = gui.time-self.t0
            if(dt >= 1000):
                self.update_angle()
                self.t0 = gui.time

    def draw(self, painter):
        gui.draw_circle(painter, self.x, self.y, self.r, 0, gui.color_none, self.color)

class PowerUp():
    def __init__(self, params, x, y, r, duration):
        self.params = params
        self.x = x
        self.y = y
        self.r = r
        self.duration = duration
        self.color = QColor(self.params["color"])
        self.delete = False

        self.text_size = 0
        for i in range(1,100):
            self.text_size = i
            w,h,fm = gui.get_text_wh(self.text_size, self.params["symbol"])
            d = fm.descent()
            # if(abs((h-d) - r*2) <= 1):
            if(abs((h) - r*2) <= 2):
                break

        # print(self.text_size)

    def on_bullet_collision(self):
        idx = self.params["idx"]
        p = gui.power_params[idx]

        if(idx == gui.LIFE):
            gui.player_lives = min(gui.player_lives+1, gui.max_player_lives)
        elif(idx == gui.GUN):
            p["active"] = True
            gui.set_click_selection(False, 2)
        else:
            if(not(p["perm"])):
                p["countdown"] += p["duration"]
                p["total_duration"] += p["duration"]
            p["active"] = True
            # print(gui.power_params)

            if(idx == gui.RAPID):
                gui.set_fire_period()

        gui.spawn_explosion(self.x, self.y, self.r*2, 300, False, False)
        self.delete = True

    def update(self):
        self.duration -= gui.timer_ms
        if(self.duration <= 0):
            self.delete = True

    def draw_power_up(self, painter, x, y, r, size=None):

        idx = self.params["idx"]

        if(idx == gui.LIFE):
            gui.draw_text(painter, int(x-r-5), y, gui.CENTERED, Qt.black, 16, "+")
            shape = gui.calc_player_shape(x, y, self.r, math.pi/2)
            gui.draw_player_shape(painter, shape, 2)

        elif(idx == gui.GUN): #TODO: make this look better
            white = QColor(0xffffff)
            black = QColor(0x000000)
            gui.draw_circle(painter, x, y, r, 1, black, black)
            gui.draw_circle(painter, x-0, y-4, 1, 1, white, gui.color_none)
            gui.draw_circle(painter, x-4, y-3, 1, 1, white, gui.color_none)
            gui.draw_circle(painter, x+4, y-3, 1, 1, white, gui.color_none)

        else:
            if(size == None):
                for i in range(1,100):
                    size = i
                    w,h,fm = gui.get_text_wh(size, self.params["symbol"])
                    d = fm.descent()
                    # if(abs((h-d) - r*2) <= 1):
                    if(abs((h) - r*2) <= 2):
                        break

            _str = self.params["symbol"]
            # gui.draw_circle(painter, x, y, r, 1, QColor(0x000000), gui.color_none)
            gui.draw_text(painter, x, y, gui.CENTERED, self.color, size, _str)

    def draw(self, painter):
        self.draw_power_up(painter, self.x, self.y, self.r, self.text_size)




class MainWindow(QMainWindow):

    def init_game_objects(self):

        print("init_game_objects")

        self.game_over = False

        self.INV = 0
        self.SLOW = 1
        self.EXP = 2
        self.RAPID = 3
        self.PEN = 4
        self.LIFE = 5
        self.GUN = 6

        color = 0x004000

        # types of power ups
        self.power_params = [
            # 0
            {
                "idx": self.INV,
                "special": False,
                "description": "Invincibility",
                "active": False,
                "symbol": "I",
                "perm": False,
                "duration": 5000,
                "countdown": 0,
                "total_duration":0,
                "color":color,
                "p":[1] #TODO
            },
            # 1
            {
                "idx": self.SLOW,
                "special": False,
                "description": "Slow Time",
                "active": False,
                "symbol": "S",
                "perm": False,
                "duration": 5000,
                "countdown": 0,
                "total_duration":0,
                "color":color,
                "p":[1] #TODO
            },
            # 2
            {
                "idx": self.EXP,
                "special": False,
                "description": "Explosive Bullets",
                "active": False,
                "symbol": "E",
                "perm": True,
                "duration": 0,
                "countdown": 0,
                "total_duration":0,
                "color":color,
                "p":[1] #TODO
            },
            # 3
            {
                "idx": self.RAPID,
                "special": False,
                "description": "Rapid Fire",
                "active": False,
                "symbol": "R",
                "perm": True,
                "duration": 0,
                "countdown": 0,
                "total_duration":0,
                "color":color,
                "p":[1] #TODO
            },
            # 4
            {
                "idx": self.PEN,
                "special": False,
                "description": "Penetrating Bullets",
                "active": False,
                "symbol": "P",
                "perm": True,
                "duration": 0,
                "countdown": 0,
                "total_duration":0,
                "color":color,
                "p":[1] #TODO
            },

            # 5
            {
                "idx": self.LIFE,
                "special": True,
                "description": "Extra Life",
                "active": False,
                "symbol": "e",
                "perm": True,
                "duration": 0,
                "countdown": 0,
                "total_duration":0,
                "color":color,
                "p":[1] #TODO
            },

            # 6
            {
                "idx": self.GUN,
                "special": True,
                "description": "Secondary",
                "active": False,
                "symbol": "S",
                "perm": True,
                "duration": 0,
                "countdown": 0,
                "total_duration":0,
                "color":color,
                "p":[1] #TODO
            },
        ]

        self.slow_mult = 1/3

        self.power_ups = []
        self.explosions = []
        self.bullets = []
        self.enemies = []

        self.mouse_x, self.mouse_y = self.get_cursor_pos()
        self.mouse_off_window = self.off_window(self.mouse_x, self.mouse_y)

        self.player_lives = 3+1
        self.max_player_lives = 10
        self.player_kills = 0
        self.player_x = self.center_x
        self.player_y = self.center_y
        # tip, left leg, right leg, middle
        self.player_shape = []
        self.player_angle = 0
        self.player_radius = 12.5
        # self.player_radius = min(self.scale_w,self.scale_h)*self.player_radius

        self.enemy_spawn_t0 = 0
        self.max_enemies = [10,1,30,100]
        self.enemy_spawn_time = [1000,800,500,200]
        self.game_stage = 0
        self.game_stage_times = [15000,30000,15000,15000]
        # self.game_stage_times = [1,1,1,1]
        self.power_up_probs = [5, 25, 50, 100]
        self.power_up_probs = [100]
        self.max_power_ups = 10
        self.game_stage_max = len(self.max_enemies)-1
        self.game_stage_timer = self.get_game_stage_param(self.game_stage_times)


        self.set_click_selection(True, 0)
        self.set_click_selection(False, -1)

        self.game_time = 0
        self.t0 = datetime.now()
        self.dt = 0

        # for gradients
        self.damage_counter = 0
        self.damage_counter_max = 100
        self.damage_counter_incr_value = 5
        self.damage_counter_incr = 0

        self.update_player()

    def init(self):

        print("init")

        self.w = self.width()
        self.h = self.height()
        # self.setGeometry(0, 0, self.w, self.h)
        # self.setFixedWidth(self.w)
        # self.setFixedHeight(self.h)
        # print(self.desktop.devicePixelRatio())

        self.kam_w = 2560
        self.kam_h = 1359

        self.scale_w = self.w/self.kam_w
        self.scale_h = self.h/self.kam_h

        self.center_x = int(self.w/2)
        self.center_y = int(self.h/2)

        self.margin_left = int(300 * self.scale_w)
        self.margin_right = int(300 * self.scale_w)
        self.margin_top = int(200 * self.scale_h)
        self.margin_bottom = int(200 * self.scale_h)

        self.hud_y_offset = int(5 * self.scale_h)

        # self.margin_left = 300
        # self.margin_right = 300
        # self.margin_top = 200
        # self.margin_bottom = 200
        # self.hud_y_offset = 5

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

        # "color":0x00ffff,
        bullet_color = 0x0000a0

        # types of bullets
        self.bullet_params = [
            # 0
            {
                "fire_period":140,
                "rapid_fire_period":80,
                "radius":2,
                "speed":8,
                "color":bullet_color,
                "num":1,
                "spread":0,
                "explosive":False,
                "penetrating":False,
            },

            # 1
            {
                "fire_period":500,
                "rapid_fire_period":200,
                "radius":10,
                "speed":2.5,
                "color":bullet_color,
                "num":1,
                "spread":0,
                "explosive":False,
                "penetrating":False,
            },

            # 2
            {
                "fire_period":1000,
                "rapid_fire_period":800,
                "radius":2,
                "speed":5,
                "color":bullet_color,
                "num":5,
                "spread":20,
                "explosive":False,
                "penetrating":False,
            },

            # 3
            {
                "fire_period":140,
                "rapid_fire_period":200,
                "radius":2,
                "speed":8,
                "color":bullet_color,
                "num":50,
                "spread":90,
                "explosive":True,
                "penetrating":True,
            },

            # 4
            {
                "fire_period":140,
                "rapid_fire_period":80,
                "radius":2,
                "speed":8,
                "color":bullet_color,
                "num":2,
                "spread":2,
                "explosive":False,
                "penetrating":False,
            },
        ]



        # types of enemies
        self.enemy_params = [
            # 0
            {
                "tracking": True,
                "min_radius":5,
                "max_radius":10,
                "min_speed":2,
                "max_speed":3,
                "color":0xb00000,
                "p":[10,30,50]
            },

            # 1
            {
                "tracking": False,
                "min_radius":10,
                "max_radius":28,
                "min_speed":2,
                "max_speed":4,
                # "color":0xffa000,
                "color":0xf07000,
                "p":[90,70,50]
            },

        ]

        self.click_params = {

            "l":
            {
                "held":False,
                "fire_period":0,
                "cooldown":0,
                "selection":0
            },

            "r":
            {
                "held":False,
                "fire_period":0,
                "cooldown":0,
                "selection":0
            }
        }

        # text orientation
        self.NONE = -1
        self.CENTERED = 0
        self.TOP_LEFT = 1
        self.TOP_RIGHT = 2
        self.BOTTOM_LEFT = 3
        self.BOTTOM_RIGHT = 4
        self.CENTERED_TOP = 5
        self.CENTERED_BOTTOM = 6
        self.CENTERED_LEFT = 7

        # edge detection
        self.grad_thresh = 100
        self.grad_width = 25

        # self.font_name = "arial"
        self.font_name = "courier"

        self.auto_aim = False
        self.init_game_objects()

        self.installEventFilter(self)
        self.setMouseTracking(True)

        self.loop_count = 0
        self.time = 0
        self.timer_ms = 16
        # self.timer_ms = 500
        self.timer = QTimer()
        self.timer.timeout.connect(self.timer_cb)
        self.timer.start(self.timer_ms)

        self.game_time = 0
        self.t0 = datetime.now()
        self.dt = 0

        self.fps_t0 = datetime.now()
        self.fps = 0
        self.fps_display = 0

        self.initialized = True
        self.repaint()

    # def wheelEvent(self,event):
    #     adj = (event.angleDelta().y() / 120)
    #     self.player_radius = bound(self.player_radius + adj, 1, 100000)

    def __init__(self):
        super().__init__()

        print("_init_")
        self.initialized = False
        self.color_none = QColor(0,0,0,0)
        self.paused = False
        # self.game_over = False
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

        self.screen_w = self.screen.width()
        self.screen_h = self.screen.height()

        self.show()
        self.setWindowState(Qt.WindowMaximized)
        # self.setGeometry(0, 0, int(2560/4), int(1359/2))
        # self.setGeometry(0, 0, self.screen_w, self.screen_h)


    def reload(self):
        self.init_game_objects()


    def timer_cb(self):

        self.loop_count += 1

        t = datetime.now()
        dt = (t-self.fps_t0).microseconds/1000
        fps = 1000/dt
        smooth = 0.7
        self.fps = (fps * smooth) + (self.fps * (1.0-smooth))
        self.fps_t0 = t
        if((self.loop_count % 10) == 0 or self.fps_display == 0):
            self.fps_display = self.fps+0

        if(not(self.paused)):

            dt = (t-self.t0).microseconds/1000
            if(not(self.game_over)):
                self.game_time += dt
            self.t0 = t
            self.dt = int(dt)
            self.time += self.timer_ms


            if(not(self.game_over)):
                self.game_stage_timer -= dt
                if(self.game_stage_timer <= 0):
                    self.game_stage += 1
                    # self.game_stage = min(self.game_stage_max, self.game_stage+1)
                    self.game_stage_timer = self.get_game_stage_param(self.game_stage_times)


            # print(self.time, self.game_time, self.dt)
            # print(self.time)

            if(self.auto_aim):
                self.update_player()

            self.player_timer()
            self.click_timer()
            self.enemy_timer()

            self.bullets_update()
            self.bullets_delete()   # removes off-screen bullets

            self.enemies_update()
            self.bullets_check_collision() # bullets/enemies
            self.enemies_check_collision() # player/enemies
            self.explosions_check_collision()

            self.power_ups_update()
            self.power_ups_check_collision()

            self.explosions_update()
            self.explosions_delete()

        self.repaint()


    def get_game_stage_param(self, lst):
        return lst[min(len(lst)-1, self.game_stage)]


    def enemy_timer(self):

        max_enemies = self.get_game_stage_param(self.max_enemies)
        spawn_time = self.get_game_stage_param(self.enemy_spawn_time)

        num_enemy_types = len(self.enemy_params)

        if(self.time - self.enemy_spawn_t0 >= spawn_time and len(self.enemies) < max_enemies):

            self.enemy_spawn_t0 = self.time

            ps = [] # probabilities
            p_sum = 0
            for i in range(num_enemy_types):
                p_sum += self.get_game_stage_param(self.enemy_params[i]["p"])
                ps.append(p_sum)

            r = self.rand_range(1,max(ps))
            for i in range(num_enemy_types):
                if(r <= ps[i]):
                    self.spawn_enemy(i)
                    break

    def paintEvent(self, event):

        if(not(self.initialized)): return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        self.draw_gradients(painter)

        self.draw_debug_info(painter)

        self.draw_power_ups(painter)
        self.draw_bullets(painter)
        self.draw_player(painter)
        self.draw_enemies(painter)
        self.draw_explosions(painter)
        self.draw_mouse(painter)

        self.draw_arena(painter)
        self.draw_player_hud(painter)

        self.draw_pause(painter)
        self.draw_game_over(painter)



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

    def inside_arena(self, window_x, window_y, r):
        if((window_x+r) < self.tr_x and (window_x-r) > self.tl_x):
            if((window_y+r) < self.br_y and (window_y-r) > self.tr_y):
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

    def draw_line(self, painter, x1, y1, x2, y2, pw, pc, bc):
        pen = QPen()
        pen.setWidth(pw)
        pen.setColor(pc)

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(pen)
        painter.setBrush(bc)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))

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

    def draw_player_shape(self, painter, shape, pw):
        pen = QPen()
        pen.setWidth(pw)
        pen.setColor(Qt.black)

        painter.setPen(pen)
        c = self.color_none
        painter.setBrush(c)

        for i in range(0,len(shape)):
            x0,y0,x1,y1 = shape[i]
            painter.drawLine(int(x1), int(y1), int(x0), int(y0))


    def get_text_wh(self, size, fmt, *args):
        if(len(args) > 0):
            _str = fmt % args
        else:
            _str = fmt

        if(len(_str) == 0):
            return 0,0,None

        font = QFont(self.font_name)
        font.setPixelSize(size)
        fm = QFontMetrics(font)
        rect = fm.tightBoundingRect(_str)
        w = rect.topRight().x() - rect.topLeft().x()
        h = rect.bottomLeft().y() - rect.topLeft().y()
        # w = fm.width(_str)
        # h = fm.height()
        return w,h,fm


    def draw_text(self, painter, x, y, orientation, color, size, fmt, *args):

        if(len(args) > 0):
            _str = fmt % args
        else:
            _str = fmt

        if(len(_str) == 0):
            return 0,0,None,None,None

        # size = max(8,int(self.scale_w*size))

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(color)
        painter.setPen(pen)
        painter.setBrush(color)
        font = QFont(self.font_name)
        font.setPixelSize(size)
        painter.setFont(font)
        fm = QFontMetrics(font)

        # w = fm.width(_str)
        # h = fm.height()
        # a = fm.ascent()
        # d = fm.descent()
        # l = fm.leading()
        lb = fm.leftBearing(_str[0])

        x_adj = x
        y_adj = y

        rect = fm.tightBoundingRect(_str)
        w = rect.topRight().x() - rect.topLeft().x()
        h = rect.bottomLeft().y() - rect.topLeft().y()

        if(orientation == self.NONE):
            x_adj = x
            y_adj = y
        elif(orientation == self.CENTERED):
            x_adj = x-w/2-lb/2
            y_adj = y+h/2
        elif(orientation == self.TOP_LEFT):
            x_adj = x
            y_adj = y+h
        elif(orientation == self.TOP_RIGHT):
            x_adj = x-w
            y_adj = y+h
        elif(orientation == self.BOTTOM_LEFT):
            x_adj = x
            y_adj = y
        elif(orientation == self.BOTTOM_RIGHT):
            x_adj = x-w
            y_adj = y
        elif(orientation == self.CENTERED_TOP):
            x_adj = x-w/2-lb/2
            y_adj = y+h
        elif(orientation == self.CENTERED_BOTTOM):
            x_adj = x-w/2-lb/2
            y_adj = y
        elif(orientation == self.CENTERED_LEFT):
            x_adj = x
            y_adj = y+h/2

        xdelta = x_adj-x
        ydelta = y_adj-y

        painter.drawText(int(x_adj), int(y_adj), _str)
        # painter.drawStaticText(QPoint(x,y),QStaticText(_str))
        # self.draw_circle(painter, int(x), int(y), 1, 1, self.color_none, Qt.blue)
        # self.draw_circle(painter, int(x_adj), int(y_adj), 1, 1, self.color_none, Qt.red)
        return w,h,fm,xdelta,ydelta


    def draw_weapon_selection(self, painter):
        y = self.bl_y + self.hud_y_offset
        x = self.bl_x

        ls = self.click_params["l"]["selection"]
        rs = self.click_params["r"]["selection"]

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(Qt.black)
        painter.setPen(pen)
        painter.setBrush(Qt.black)
        font = QFont(self.font_name)
        font.setPixelSize(16)
        fm = QFontMetrics(font)

        _str = str(ls) + " | "
        if(rs >= 0):
            _str += str(rs)
        else:
            _str += "-"

        y += fm.height()
        painter.setFont(font)
        painter.drawText(x, y, _str)

    def draw_player_hud(self, painter):
        self.draw_player_lives(painter)
        self.draw_game_stage(painter)
        self.draw_player_kills(painter)
        self.draw_time(painter)
        self.draw_player_power_ups(painter)

    def draw_player_power_ups(self, painter):
        vpad = 10
        hpad = 20
        r = 10
        size = 16
        gray = QColor(0x303030)

        x = self.tr_x
        y = self.tr_y


        perm_condition = True

        for _ in range(2):

            for i in range(len(self.power_params)):
                p = self.power_params[i]
                if(p["special"]): continue
                if(p["perm"] != perm_condition): continue

                # TODO: figure out how to draw power ups
                # pup = PowerUp(p, x, y, r, 0)

                _x = x+hpad
                _y = y+vpad

                if(p["active"]):
                    color1 = QColor(p["color"])
                    color2 = Qt.black
                else:
                    color1 = gray
                    color2 = gray

                _str = p["symbol"]
                w,h,fm,xd,yd = self.draw_text(painter, _x, _y, self.TOP_LEFT, color1, size, _str)
                y += h+fm.descent()+vpad
                _x += w

                _str = " : %s" % p["description"]
                w,h,fm,_,_ = self.draw_text(painter, _x+xd, _y+yd, self.NONE, color2, size, _str)
                _x += w

                if(not(p["perm"]) and p["active"]):
                    _str = ": %d" % int(p["countdown"]/1000)
                    w,h,fm,_,_ = self.draw_text(painter, _x+xd, _y+yd, self.NONE, color2, size, _str)

                    # max_width = self.br_x - x - pad*3
                    # width = max_width * p["countdown"] / p["total_duration"]
                    # rect = QRect(QPoint(int(x+pad*3), int(y-r/2)), QPoint(int(x+pad*3+width), int(y+r/2)))
                    # painter.drawRect(rect)


            perm_condition = not(perm_condition)


    def draw_player_lives(self, painter):
        if(self.player_lives <= 0):
            return

        radius = 10
        pad = 5
        y = self.tl_y - radius - self.hud_y_offset
        x = self.center_x - (self.player_lives) * (radius*2 + pad) / 2

        shape = self.calc_player_shape(x, y, radius, math.pi/2)
        for i in range(self.player_lives-1):
            self.draw_player_shape(painter, shape, 2)
            shape = self.translate_player_shape(shape, radius*2 + pad, 0)


    def draw_game_stage(self, painter):
        y = self.tl_y-self.hud_y_offset
        x = self.tl_x
        _str = "Stage: " + str(self.game_stage+1)
        self.draw_text(painter, x, y, self.BOTTOM_LEFT, Qt.black, 16, _str)


    def draw_player_kills(self, painter):
        y = self.tl_y-self.hud_y_offset
        x = self.tr_x
        x = self.arena_w/4+self.tl_x
        x = self.tl_x+100
        _str = "Kills: " + str(self.player_kills)
        self.draw_text(painter, x, y, self.BOTTOM_LEFT, Qt.black, 16, _str)



    def draw_time(self, painter):
        y = self.tl_y-self.hud_y_offset
        x = self.tr_x
        _str = str(int(self.game_time/1000))
        self.draw_text(painter, x, y, self.BOTTOM_RIGHT, Qt.black, 16, _str)

    def draw_player(self, painter):

        self.draw_player_shape(painter, self.player_shape, 2)

    def draw_debug_info(self, painter):

        if(not(self.debug)): return

        # # player angle line
        # self.draw_player_angle_line(painter, self.bullet_params[2]["spread"])
        # self.draw_player_angle_line(painter, 0)

        # # player collision
        # self.draw_circle(painter, self.player_x, self.player_y, self.player_radius, 1, Qt.blue, self.color_none)

        x = 10
        y = self.tl_y
        size = 14


        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "FPS: %.1f", self.fps_display)
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Angle: %.2f (%.2f)", self.player_angle, self.player_angle * 180 / math.pi)
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Mouse (win): %d, %d", self.mouse_x, self.mouse_y)
        y += h+fm.descent()

        adj_mouse_x, adj_mouse_y = self.adj_coords(self.mouse_x, self.mouse_y)
        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Mouse (adj): %d, %d", adj_mouse_x, adj_mouse_y)
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Fire Period: %d, %d", self.click_params["l"]["fire_period"], self.click_params["r"]["fire_period"])
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Fire Cooldown: %d, %d", self.click_params["l"]["cooldown"], self.click_params["r"]["cooldown"])
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Damage Counter: %d", self.damage_counter)
        y += h+fm.descent()


        y += h+fm.descent()
        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Bullets: %d", len(self.bullets))
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Enemies: %d", len(self.enemies))
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Explosions: %d", len(self.explosions))
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Power-ups: %d", len(self.power_ups))
        y += h+fm.descent()


        y += h+fm.descent()
        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Stage Counter: %d", self.game_stage_timer)
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Max Enemies: %d", self.get_game_stage_param(self.max_enemies))
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Spawn Time: %d", self.get_game_stage_param(self.enemy_spawn_time))
        y += h+fm.descent()

        w,h,fm,xd,yd = self.draw_text(painter, x, y, self.TOP_LEFT, Qt.black, size, "Power-up Prob: %d", self.get_game_stage_param(self.power_up_probs))
        y += h+fm.descent()

        # w,h,fm,xd,yd = self.draw_text(painter, self.bl_x, self.bl_y, self.CENTERED, Qt.black, 32, "DEBUG")



    def draw_player_angle_line(self, painter, spread=0):
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

        if(spread != 0):
            rad_spread = spread*math.pi/180

            _x2 = l*math.cos(self.player_angle+rad_spread/2) + adj_x
            _y2 = l*math.sin(self.player_angle+rad_spread/2) + adj_y
            x2, y2 = self.win_coords(_x2, _y2)
            painter.drawLine(int(x2), int(y2), int(x1), int(y1))

            _x2 = l*math.cos(self.player_angle-rad_spread/2) + adj_x
            _y2 = l*math.sin(self.player_angle-rad_spread/2) + adj_y
            x2, y2 = self.win_coords(_x2, _y2)
            painter.drawLine(int(x2), int(y2), int(x1), int(y1))

    def draw_pause(self, painter):
        if(self.paused):
            size = 24
            _str = "PAUSED"
            w,h,_ = self.get_text_wh(size, _str)
            x = self.center_x
            y = self.center_y - h - 20
            self.draw_text(painter, x, y, self.CENTERED, Qt.black, size, _str)


    def draw_game_over(self, painter):

        if(self.game_over):

            size = 40
            _str = "GAME OVER"
            x = self.center_x
            y = self.center_y - self.arena_h/4
            w,h,fm,xd,yd = self.draw_text(painter, x, y, self.CENTERED, Qt.red, size, _str)

            y += h/2 + fm.descent()
            self.draw_text(painter, x, y, self.CENTERED_TOP, Qt.black, 16, "(press r to restart)")


    def draw_mouse(self, painter):

        l = 3
        x1 = self.mouse_x-l
        x2 = self.mouse_x+l
        y1 = self.mouse_y
        y2 = self.mouse_y
        self.draw_line(painter, x1, y1, x2, y2, 1, Qt.black, self.color_none)

        x1 = self.mouse_x
        x2 = self.mouse_x
        y1 = self.mouse_y-l
        y2 = self.mouse_y+l
        self.draw_line(painter, x1, y1, x2, y2, 1, Qt.black, self.color_none)


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


    def set_fire_period(self):

        ls = self.click_params["l"]["selection"]
        rs = self.click_params["r"]["selection"]

        if(self.power_params[self.RAPID]["active"]): _key = "rapid_fire_period"
        else: _key = "fire_period"

        if(ls >= 0 and ls < len(self.bullet_params)):
            self.click_params["l"]["fire_period"] = self.bullet_params[ls][_key]
        if(rs >= 0 and rs < len(self.bullet_params)):
            self.click_params["r"]["fire_period"] = self.bullet_params[rs][_key]

    def will_intersect(self, x0, y0, s0, a0, r0, x1, y1, s1, a1, r1):
        ax0, ay0 = self.adj_coords(x0,y0)
        ax1, ay1 = self.adj_coords(x1,y1)
        # aox0, aoy0 = self.adj_coords(ox0,oy0)
        # aox1, aoy1 = self.adj_coords(ox1,oy1)

        n = -1 * (ax0 - ax1) / (s1*math.cos(a1))
        d = s0*math.cos(a0) / (s1*math.cos(a1)) - 1
        t = n/d

        if(t < 0):
            return False,None,None

        xtest0 = t*s0*math.cos(a0)+ax0
        xtest1 = t*s1*math.cos(a1)+ax1
        ytest0 = t*s0*math.sin(a0)+ay0
        ytest1 = t*s1*math.sin(a1)+ay1
        # print(t, ytest0, ytest1)

        if(abs(ytest0-ytest1) <= (r0+r1-0)):
            # printf("ax0: %d, ay0: %d, s0: %d, r0: %d")
            # print("BANG",t, ytest0, ytest1, r0, r1)
            # print(ax0, ay0, s0, a0, r0, ax1, ay1, s1, a1, r1)
            # print(t,xtest0, xtest1, ytest0, ytest1)
            # print(t)
            return True,xtest0,ytest0

        return False,None,None


    def handle_auto_aim(self):
        mind = 1000000
        idx = -1
        for i in range(len(self.enemies)):
            e = self.enemies[i]
            d = self.calc_magnitude(self.player_x, e.x, self.player_y, e.y)-e.r
            if(d < mind):
                mind = d
                idx = i
        if(idx != -1):
            # if(d > 500): continue
            e = self.enemies[idx]
            start_angle = self.calc_angle(e.x, self.player_x, e.y, self.player_y)
            # self.player_angle = start_angle

            ls = self.click_params["l"]["selection"]

            deg = start_angle*180/math.pi

            intersect = False
            for i in range(0,200):
                for j in [-1,1]:

                    deg_test = deg+i/10*j
                    rad = deg_test*math.pi/180

                    shape = self.calc_player_shape(self.player_x, self.player_y, self.player_radius, rad)

                    speed = e.speed
                    if(self.power_params[self.SLOW]["active"]):
                        speed *= self.slow_mult

                    intersect,x,y = self.will_intersect(
                                            shape[0][0], shape[0][1], self.bullet_params[0]["speed"], rad, self.bullet_params[0]["radius"],
                                            e.fx, e.fy, speed, e.angle, e.r
                                        )

                    if(intersect):
                        self.player_angle = rad
                        break
                if(intersect):
                    break

            if(intersect):
                self.click_params["l"]["held"] = True
            else:
                self.click_params["l"]["held"] = False

        else:
            self.click_params["l"]["held"] = False

    def player_timer(self):
        self.damage_counter += self.damage_counter_incr
        if(self.damage_counter >= self.damage_counter_max):
            self.damage_counter_incr *= -1
            self.damage_counter = self.damage_counter_max
        elif(self.damage_counter <= 0):
            self.damage_counter_incr = 0
            self.damage_counter = 0

        # check for expired power ups
        for i in range(len(self.power_params)):
            p = self.power_params[i]
            if(p["active"]):
                if(not(p["perm"])):
                    p["countdown"] -= self.timer_ms
                    if(p["countdown"] <= 0):
                        p["active"] = False
                        p["countdown"] = 0
                        p["total_duration"] = 0


    def update_player(self):

        if(self.auto_aim):
            self.handle_auto_aim()
        else:
            self.player_angle = self.calc_angle(self.mouse_x, self.player_x, self.mouse_y, self.player_y)

        self.player_shape = self.calc_player_shape(self.player_x, self.player_y, self.player_radius, self.player_angle)


    def get_cursor_pos(self):
        gpos = QCursor.pos()
        pos = self.mapFromGlobal(gpos)
        x = pos.x()
        y = pos.y()
        return x,y


    def click_timer(self):

        if(self.click_params["l"]["cooldown"] > 0):
            self.click_params["l"]["cooldown"] = max(self.click_params["l"]["cooldown"]-self.timer_ms,0)


        if(self.click_params["r"]["cooldown"] > 0):
            self.click_params["r"]["cooldown"] = max(self.click_params["r"]["cooldown"]-self.timer_ms,0)

        if(self.click_params["l"]["held"]):
            self.click(True, True)

        if(self.click_params["r"]["held"]):
            self.click(False, True)



    def set_click_selection(self, left, _type):
        if(left): _key = "l"
        else: _key = "r"
        self.click_params[_key]["selection"] = _type
        self.set_fire_period()

    def click(self, left, hold):

        if(left): _key = "l"
        else: _key = "r"

        _type = self.click_params[_key]["selection"]
        if(_type < 0 or _type >= len(self.bullet_params)): return

        self.click_params[_key]["cooldown"] -= self.timer_ms
        if(self.click_params[_key]["cooldown"] > 0): return
        self.click_params[_key]["cooldown"] = self.click_params[_key]["fire_period"]

        params = self.bullet_params[_type]
        self.spawn_bullet(params, _type)


    def mouseMoveEvent(self, event):


        x = event.x()
        y = event.y()

        if(x == self.mouse_x and y == self.mouse_y): return

        self.mouse_x = x
        self.mouse_y = y

        # print("move",x,y)
        if(self.auto_aim): return
        if(self.paused): return

        self.update_player()
        self.repaint()

    def mousePressEvent(self, event):
        if(self.paused): return
        if(self.auto_aim): return

        # QMouseEvent
        b = event.button()
        # print(b)

        if(b != Qt.RightButton and b != Qt.LeftButton):
            return

        left = (b == Qt.LeftButton)
        if(left): _key = "l"
        else: _key = "r"

        # can't click faster than fire period
        # self.click_params[_key]["cooldown"] = self.click_params[_key]["fire_period"]
        self.click_params[_key]["held"] = True
        self.click(left, False)

    def mouseReleaseEvent(self, event):
        if(self.auto_aim): return
        b = event.button()

        if(b != Qt.RightButton and b != Qt.LeftButton):
            return

        left = (b == Qt.LeftButton)
        if(left): _key = "l"
        else: _key = "r"
        self.click_params[_key]["held"] = False


    def eventFilter(self,source,event):

        t = datetime.now()

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
                        if(not(self.game_over)):
                            self.game_time += (t-self.t0).microseconds/1000
                        self.click_params["l"]["held"] = False
                        self.click_params["r"]["held"] = False
                    else:
                        self.t0 = t
                        self.update_player()
                        # self.repaint()


                if(key == Qt.Key_R):
                    if(self.game_over):
                        self.reload()
                        self.paused = False

                if(self.paused): return 0


                if(key == Qt.Key_Escape):
                    pass

                elif(key == Qt.Key_O):
                    self.player_lives += 1


                elif(key == Qt.Key_A):
                    self.auto_aim = not(self.auto_aim)
                    self.click_params["l"]["held"] = False

                if(key == Qt.Key_V):
                    idx = self.EXP
                    self.power_params[idx]["active"] = not(self.power_params[idx]["active"])
                    idx = self.PEN
                    self.power_params[idx]["active"] = not(self.power_params[idx]["active"])


                elif(key == Qt.Key_D):
                    self.debug = not(self.debug)

                elif(key == Qt.Key_X):
                    x,y = self.get_cursor_pos()
                    # self.spawn_explosion(x,y,100,1000,False)
                    # self.spawn_power_up(x,y,self.INV)
                    idx = self.rand_range(0,len(self.power_params)-1)
                    self.spawn_power_up(x,y, idx)

                elif(key == Qt.Key_E):
                    x,y = self.get_cursor_pos()
                    # self.spawn_enemy(x,y,choice([0,1]))
                    # self.spawn_enemy(x,y,1)
                    _type = 0
                    e = Enemy(self.enemy_params[_type], _type, x, y)
                    self.enemies.append(e)

                elif(key == Qt.Key_M):
                    self.show_mouse = not(self.show_mouse)

                elif(key >= Qt.Key_0 and key <= Qt.Key_9):
                    sel = key - Qt.Key_0
                    self.set_click_selection(False, sel)

                elif(key == Qt.Key_Minus):
                    self.set_click_selection(False, -1)

        return 0

    def spawn_rand_power_up(self, x, y):
        if(len(self.power_ups) >= self.max_power_ups):
            return
        p = self.get_game_stage_param(self.power_up_probs)
        r = self.rand_range(1,100)

        num_powerup_types = len(self.power_params)

        if(r <= p):
            ps = [] # probabilities
            p_sum = 0
            for i in range(num_powerup_types):
                p_sum += self.get_game_stage_param(self.power_params[i]["p"])
                ps.append(p_sum)

            r = self.rand_range(1,max(ps))
            for i in range(num_powerup_types):
                if(r <= ps[i]):
                    self.spawn_power_up(x, y, self.power_params[i]["idx"])
                    break


    def spawn_power_up(self, x, y, idx):
        params = self.power_params[idx]
        r = 10
        if(idx == self.LIFE):
            r = 10
        p = PowerUp(params, x, y, r, 5000)
        self.power_ups.append(p)

    def draw_power_ups(self, painter):
        for i in range(len(self.power_ups)):
            p = self.power_ups[i]
            p.draw(painter)

    def power_ups_update(self):
        for i in range(len(self.power_ups)):
            p = self.power_ups[i]
            p.update()

    def power_ups_delete(self):
        power_ups = self.power_ups.copy()
        self.power_ups = []
        for i in range(len(power_ups)):
            p = power_ups[i]
            if(not p.delete):
                self.power_ups.append(p)
        return len(self.power_ups)

    def power_ups_check_collision(self):
        for i in range(len(self.bullets)):
            b = self.bullets[i]
            for j in range(len(self.power_ups)):
                p = self.power_ups[j]
                if(p.delete): continue
                dist = self.calc_magnitude(p.x, b.x, p.y, b.y)
                if(dist < (p.r + b.r)):
                    p.on_bullet_collision()
                    b.on_enemy_collision() # and power ups
                    continue
        self.power_ups_delete()
        self.bullets_delete()

    def spawn_bullet(self, params, _type):

        x = self.player_shape[0][0]
        y = self.player_shape[0][1]

        num = params["num"]
        spread = params["spread"]

        # colors = []
        # colors1 = [0xff0000,0x00ff00,0x0000ff,0xffffff]
        # for i in range(100):
        #     colors.append(colors1[i%len(colors1)])

        if(num > 1 and spread != 0):
            incr = spread / (num-1)
            angle_adj = -1*incr*math.pi/180
            angle = self.player_angle + (spread/2*math.pi/180)
            for i in range(num):
                b = Bullet(params, _type, x, y, angle, self.power_params[self.EXP]["active"], self.power_params[self.PEN]["active"])
                self.bullets.append(b)
                angle += (angle_adj)
        else:
            b = Bullet(params, _type, x, y, self.player_angle, self.power_params[self.EXP]["active"], self.power_params[self.PEN]["active"])
            self.bullets.append(b)


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
                    e.on_bullet_collision(b)
                    b.on_enemy_collision()
                    if(not(self.game_over)):
                        self.player_kills += 1
                    continue
        self.enemies_delete()
        self.bullets_delete()

    def enemies_check_collision(self):
        for i in range(len(self.enemies)):
            e = self.enemies[i]
            dist = self.calc_magnitude(self.player_x, e.x, self.player_y, e.y)
            if(dist < (e.r + self.player_radius)):
                e.on_player_collision()
                if(self.power_params[self.INV]["active"]):
                    continue
                if(not(self.game_over)):
                    self.player_lives -= 1
                    self.damage_counter_incr = self.damage_counter_incr_value
                if(self.player_lives <= 0):
                    self.game_over = True
                continue
        self.bullets_delete()

    def explosions_check_collision(self):
        for i in range(len(self.explosions)):
            b = self.explosions[i]
            if(not(b.damaging)): continue
            for j in range(len(self.enemies)):
                e = self.enemies[j]
                if(e.delete): continue
                dist = self.calc_magnitude(b.x, e.x, b.y, e.y)
                if(dist < (e.r + b.r)):
                    e.delete = True
                    continue
        self.enemies_delete()

    # 0=top, 1=left, 2=bottom, 3=right
    def rand_border_coords(self, sides=[0,1,2,3], radius=0):
        side = choice(sides)

        if(side == 0):
            return (choice(range(self.tl_x, self.tr_x)),self.tl_y+radius)
        elif(side == 1):
            return (self.tl_x+radius, choice(range(self.tl_y,self.bl_y)))
        elif(side == 2):
            return (self.bl_x-radius, choice(range(self.tr_y,self.br_y)))
        elif(side == 3):
            return (choice(range(self.bl_x, self.br_x)),self.bl_y-radius)

    # TODO
    def rand_range(self, lower, upper):
        return choice(range(lower,upper+1))


    def spawn_enemy(self, _type):
        params = self.enemy_params[_type]
        e = Enemy(params, _type)
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

    def explosions_update(self):
        for i in range(len(self.explosions)):
            e = self.explosions[i]
            e.update()

    def explosions_delete(self):
        explosions = self.explosions.copy()
        self.explosions = []
        for i in range(len(explosions)):
            e = explosions[i]
            if(not e.delete):
                self.explosions.append(e)
        return len(self.explosions)

    def draw_explosions(self, painter):
        for i in range(len(self.explosions)):
            e = self.explosions[i]
            e.draw(painter)

    def spawn_explosion(self, x, y, max_r, delta_r, damaging, can_spawn_powerup):
        e = Explosion(x,y,max_r,delta_r,damaging,can_spawn_powerup)
        self.explosions.append(e)


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

    # TODO
    def draw_gradients(self, painter):

        alpha = int(self.damage_counter / self.damage_counter_max * 255)
        color = QColor(0xff, 0, 0)

        if(alpha == 0):
            return

        lst = [70, 50, 30, 10]
        if(self.player_lives >= len(lst)):
            w_add = 0
        else:
            w_add = lst[self.player_lives]

        width = int(50 + w_add)

        # left
        rect = QRect(0, 0, width, self.h)
        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        self.draw_gradient_rect(painter, rect, gradient, color, alpha)

        # right
        rect = QRect(self.w-width, 0, width, self.h)
        gradient = QLinearGradient(rect.topRight(), rect.topLeft())
        self.draw_gradient_rect(painter, rect, gradient, color, alpha)

        # top
        rect = QRect(0, 0, self.w, width)
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        self.draw_gradient_rect(painter, rect, gradient, color, alpha)

        # bottom
        rect = QRect(0, self.h-width, self.w, width)
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
        if(self.width() != 200 and self.height() != 100 and not(self.initialized)):
        # if(self.isMaximized() and not(self.initialized)):
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

    # el = []
    # el.append(Explosion(0,0,0,20,False))
    # e = el[0]
    # e.max_r = 1
    # print(e.max_r, el[0].max_r)

    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)
    gui = MainWindow()
    # gui.show()
    app.exec_()

