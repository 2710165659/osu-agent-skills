from __future__ import annotations

PIXELS_PER_MS = 0.4  # 纵向时间轴像素密度
MAX_AREA_HEIGHT_0_TO_1_MIN = 4000  # [0, 1) 分钟最大区域高度
MAX_AREA_HEIGHT_1_TO_2_MIN = 5500  # [1, 2) 分钟最大区域高度
MAX_AREA_HEIGHT_2_TO_3_MIN = 7000  # [2, 3) 分钟最大区域高度
MAX_AREA_HEIGHT_3_TO_4_MIN = 8500  # [3, 4) 分钟最大区域高度
MAX_AREA_HEIGHT_4_TO_5_MIN = 10000  # [4, 5) 分钟最大区域高度
MAX_AREA_HEIGHT_5_TO_6_MIN = 11500  # [5, 6) 分钟最大区域高度
FIXED_COLUMN_COUNT_6_TO_10_MIN = 30  # [6, 10) 分钟固定列数
MAX_SUPPORTED_DURATION_MS = 10 * 60 * 1000  # 支持渲染的最大谱面时长
PAGE_MARGIN_X = 20  # 图片左右外边距
PAGE_MARGIN_Y = 20  # 图片上下外边距
LANE_WIDTH = 38  # 单个轨道宽度
LANE_GAP = 0  # 轨道之间间距
COLUMN_GAP = 100  # 列与列之间间距
NOTE_HEAD_HEIGHT = 15  # 长条头部高度
BOTTOM_PADDING_MS = 2000  # 谱面底部额外预留时间
TOP_BUFFER = NOTE_HEAD_HEIGHT  # 顶部额外缓冲高度
LEFT_PANEL_WIDTH = 12  # 轨道左侧区域宽度
NOTE_SIDE_PADDING = 2  # note 左右内边距
TIME_LABEL_FONT_SIZE = 20  # 时间标签字号
SV_TEXT_FONT_SIZE = 10  # SV 文字字号

LEFT_PANEL_BACKGROUND = (112, 112, 112, 255)  # 轨道左侧区域背景色
IMAGE_BACKGROUND = (0, 0, 0, 255)  # 整体背景色
LANE_BACKGROUND = (0, 0, 0, 255)  # 轨道背景色
RULER_TEXT = (232, 232, 232, 255)  # 时间文字颜色
MEASURE_LINE = (220, 220, 220, 96)  # 小节线颜色
BEAT_LINE = (200, 200, 200, 72)  # 拍线颜色
SUBDIVISION_LINE = (180, 180, 180, 48)  # 细分节拍线颜色
LANE_SEPARATOR = (32, 32, 32, 255)  # 轨道分隔线颜色
SV_TEXT_COLOR = (95, 221, 108, 255)  # SV 文字显示颜色
