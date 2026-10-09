"""
Configuration and Game Balance Constants for Frontline: Steel Vanguard RTS
"""
import math

# Window and Display
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS_NORMAL = 60
FPS_BATTERY = 30
GAME_TITLE = "Frontline: Steel Vanguard RTS | Сталевий Рубіж"

# World Map
MAP_WIDTH = 2560
MAP_HEIGHT = 1920
TILE_SIZE = 32
GRID_COLS = MAP_WIDTH // TILE_SIZE   # 80
GRID_ROWS = MAP_HEIGHT // TILE_SIZE  # 60

# Minimap
MINIMAP_W = 220
MINIMAP_H = 165
MINIMAP_X = WINDOW_WIDTH - MINIMAP_W - 16
MINIMAP_Y = WINDOW_HEIGHT - MINIMAP_H - 16

# Fog of War grid cell size
FOW_CELL_SIZE = 32
FOW_COLS = MAP_WIDTH // FOW_CELL_SIZE
FOW_ROWS = MAP_HEIGHT // FOW_CELL_SIZE

FOW_UNEXPLORED = 0
FOW_EXPLORED = 1
FOW_VISIBLE = 2

# Factions
FACTION_PLAYER = "player"  # Сили Оборони (UA / Vanguard)
FACTION_ENEMY = "enemy"    # Супротивник (Invader / Legion)
FACTION_NEUTRAL = "neutral"

# Visual Colors (RGB)
COLOR_BG = (28, 32, 28)
COLOR_PLAYER = (33, 150, 243)       # Tactical Blue / Cyan
COLOR_PLAYER_GLOW = (0, 229, 255)
COLOR_ENEMY = (244, 67, 54)         # Hostile Crimson
COLOR_ENEMY_GLOW = (255, 23, 68)
COLOR_NEUTRAL = (255, 193, 7)       # Gold / Amber
COLOR_HEALTH_GREEN = (76, 175, 80)
COLOR_HEALTH_YELLOW = (255, 235, 59)
COLOR_HEALTH_RED = (244, 67, 54)
COLOR_SELECTION = (0, 255, 128)
COLOR_FOG_DARK = (12, 14, 16)
COLOR_FOG_EXPLORED = (30, 36, 32, 140)  # semi-transparent overlay
COLOR_UI_PANEL = (20, 24, 28, 230)
COLOR_UI_BORDER = (55, 71, 79)
COLOR_UI_TEXT = (236, 239, 241)
COLOR_UI_ACCENT = (255, 179, 0)
COLOR_TERRAIN_GRASS = (46, 56, 36)
COLOR_TERRAIN_DIRT = (78, 67, 51)
COLOR_TERRAIN_ROAD = (65, 68, 72)
COLOR_TERRAIN_WATER = (32, 60, 84)
COLOR_TERRAIN_FOREST = (28, 42, 24)

# Unit Balance Configurations
UNIT_CONFIGS = {
    "rifleman": {
        "name": "Піхотинець",
        "name_en": "Rifleman",
        "category": "infantry",
        "cost": 100,
        "build_time": 4.0,
        "hp": 110,
        "speed": 2.2,
        "range": 160,
        "damage": 15,
        "reload": 0.6,
        "vision": 280,
        "pop": 1,
        "can_capture": True,
        "splash": 0,
        "projectile_speed": 18,
        "weapon_type": "bullet",
        "description": "Швидкий стрілець. Ефективний проти піхоти, захоплює ресурсні вишки."
    },
    "rpg": {
        "name": "Штурмовик РПГ",
        "name_en": "RPG Shocktrooper",
        "category": "infantry",
        "cost": 175,
        "build_time": 6.0,
        "hp": 130,
        "speed": 1.9,
        "range": 220,
        "damage": 80,
        "reload": 2.0,
        "vision": 280,
        "pop": 1,
        "can_capture": True,
        "splash": 25,
        "projectile_speed": 12,
        "weapon_type": "rocket",
        "description": "Протитанковий боєць. Завдає нищівного урону бронетехніці та спорудам."
    },
    "ifv": {
        "name": "БМП «Буцефал»",
        "name_en": "IFV Striker",
        "category": "vehicle",
        "cost": 320,
        "build_time": 8.0,
        "hp": 380,
        "speed": 3.2,
        "range": 230,
        "damage": 22,
        "reload": 0.3,
        "vision": 320,
        "pop": 2,
        "can_capture": False,
        "splash": 0,
        "projectile_speed": 20,
        "weapon_type": "autocannon",
        "description": "Швидкісна бойова машина з 30-мм автоматичною гарматою."
    },
    "tank": {
        "name": "Танк Т-84 «Оплот»",
        "name_en": "Main Battle Tank",
        "category": "vehicle",
        "cost": 550,
        "build_time": 12.0,
        "hp": 850,
        "speed": 2.1,
        "range": 270,
        "damage": 130,
        "reload": 2.4,
        "vision": 320,
        "pop": 3,
        "can_capture": False,
        "splash": 45,
        "projectile_speed": 16,
        "weapon_type": "cannon",
        "description": "Важкий танк з потужною 125-мм гарматою та міцною бронею."
    },
    "artillery": {
        "name": "САУ «Богдана»",
        "name_en": "Self-Propelled Howitzer",
        "category": "vehicle",
        "cost": 620,
        "build_time": 15.0,
        "hp": 320,
        "speed": 1.5,
        "min_range": 150,
        "range": 560,
        "damage": 190,
        "reload": 4.2,
        "vision": 360,
        "pop": 3,
        "can_capture": False,
        "splash": 80,
        "projectile_speed": 9,
        "weapon_type": "artillery",
        "description": "Далекобійна гаубиця 155-мм. Знищує ворожі бази та скупчення на дистанції."
    },
    "fpv_drone": {
        "name": "Ударний FPV-дрон",
        "name_en": "Kamikaze FPV Drone",
        "category": "air",
        "cost": 180,
        "build_time": 5.0,
        "hp": 45,
        "speed": 5.2,
        "range": 32,
        "damage": 380,
        "reload": 0.0,
        "vision": 380,
        "pop": 1,
        "can_capture": False,
        "splash": 50,
        "projectile_speed": 0,
        "weapon_type": "suicide",
        "description": "Швидкісний дрон-камікадзе. Ігнорує перешкоди, вибухає при контакті з ціллю."
    },
    "aa_vehicle": {
        "name": "ЗРК «Гепард / Стріла»",
        "name_en": "Anti-Air Defense",
        "category": "vehicle",
        "cost": 380,
        "build_time": 9.0,
        "hp": 400,
        "speed": 2.6,
        "range": 300,
        "damage": 45,
        "reload": 0.65,
        "vision": 340,
        "pop": 2,
        "can_capture": False,
        "splash": 20,
        "projectile_speed": 22,
        "weapon_type": "flak",
        "description": "Зенітна установка. Збиває ворожі FPV-дрони та підтримує наземні війська."
    }
}

# Building Balance Configurations
BUILDING_CONFIGS = {
    "hq": {
        "name": "Командний пункт",
        "name_en": "Headquarters",
        "cost": 0,
        "build_time": 0.0,
        "hp": 2800,
        "size": (96, 96),
        "vision": 420,
        "passive_income": 12,
        "pop_cap": 20,
        "description": "Серце бази. Дає радарний огляд, ресурси та керує військами."
    },
    "barracks": {
        "name": "Казарми піхоти",
        "name_en": "Barracks",
        "cost": 280,
        "build_time": 8.0,
        "hp": 1300,
        "size": (80, 80),
        "vision": 280,
        "passive_income": 0,
        "produces": ["rifleman", "rpg"],
        "description": "Тренувальний центр для підготовки стрільців та штурмовиків РПГ."
    },
    "war_factory": {
        "name": "Завод бронетехніки",
        "name_en": "War Factory",
        "cost": 500,
        "build_time": 14.0,
        "hp": 1900,
        "size": (96, 96),
        "vision": 300,
        "passive_income": 0,
        "produces": ["ifv", "tank", "artillery", "aa_vehicle"],
        "description": "Виробництво важкої та легкої бронетехніки: БМП, Танки, САУ, ЗРК."
    },
    "drone_bay": {
        "name": "Станція БПЛА",
        "name_en": "Drone Bay",
        "cost": 360,
        "build_time": 10.0,
        "hp": 1100,
        "size": (80, 80),
        "vision": 320,
        "passive_income": 0,
        "produces": ["fpv_drone"],
        "description": "Пункт пілотів та майстерня збирання ударних FPV-дронів камікадзе."
    },
    "supply_depot": {
        "name": "Склад постачання",
        "name_en": "Supply Depot",
        "cost": 220,
        "build_time": 7.0,
        "hp": 950,
        "size": (64, 64),
        "vision": 240,
        "passive_income": 8,
        "pop_bonus": 15,
        "description": "Збільшує ліміт армії (+15 юнітів) та постачає припаси."
    },
    "bunker": {
        "name": "Кулеметний ДОТ",
        "name_en": "MG Bunker",
        "cost": 240,
        "build_time": 8.0,
        "hp": 950,
        "size": (64, 64),
        "vision": 280,
        "damage": 18,
        "range": 220,
        "reload": 0.35,
        "splash": 0,
        "description": "Укріплена вогнева точка для відбиття атак ворожої піхоти."
    },
    "missile_turret": {
        "name": "Ракетний бастіон",
        "name_en": "Missile Turret",
        "cost": 360,
        "build_time": 10.0,
        "hp": 1150,
        "size": (64, 64),
        "vision": 320,
        "damage": 95,
        "range": 280,
        "reload": 1.8,
        "splash": 35,
        "description": "Потужна стаціонарна турель проти ворожої бронетехніки та авіації."
    },
    "resource_derrick": {
        "name": "Нафтова вишка / Склад",
        "name_en": "Supply Derrick",
        "cost": 0,
        "build_time": 0,
        "hp": 2200,
        "size": (64, 64),
        "vision": 220,
        "passive_income": 20,
        "is_capturable": True,
        "description": "Стратегічне джерело палива та ресурсів. Захоплюється піхотою (+20 кожні 3 сек)."
    }
}
