# test.py
import os
import random
import time
import copy 
import sys

# --- Matplotlib (条件导入和全局变量) ---
plt = None
np = None
font_manager = None # 用于字体管理
FIG = None 
AX = None  

# --- 游戏常量 ---
TRACK_LENGTH = 24 # 赛道总长度
DEFAULT_NUM_SELECTED_PLAYERS = 6 # 每局游戏中选择的玩家数量
NUM_ROWS = 2 # 主赛道在可视化时分为2行显示

# 玩家详细信息, 包括用于日志的名称 (log_name) 和可视化的颜色 (viz_color, 0-1范围)
PLAYER_DETAILS = {
    1: {"name": "洛可可", "log_name": "洛可可", "id_internal": 1, "color_code": "粉+黄", "viz_color": (255/255, 192/255, 203/255)},
    2: {"name": "布兰特", "log_name": "布兰特", "id_internal": 2, "color_code": "蓝", "viz_color": (0/255, 0/255, 255/255)},
    3: {"name": "坎特蕾拉", "log_name": "坎特蕾拉", "id_internal": 3, "color_code": "紫", "viz_color": (128/255, 0/255, 128/255)},
    4: {"name": "赞妮", "log_name": "赞妮", "id_internal": 4, "color_code": "红", "viz_color": (255/255, 0/255, 0/255)},
    5: {"name": "卡提西亚", "log_name": "卡提西亚", "id_internal": 5, "color_code": "绿", "viz_color": (0/255, 128/255, 0/255)},
    6: {"name": "菲比", "log_name": "菲比", "id_internal": 6, "color_code": "黄", "viz_color": (255/255, 255/255, 0/255)},
    7: {"name": "今汐", "log_name": "今汐", "id_internal": 7, "color_code": "白", "viz_color": (245/255, 245/255, 245/255)},
    8: {"name": "长离", "log_name": "长离", "id_internal": 8, "color_code": "淡红", "viz_color": (255/255, 153/255, 153/255)},
    9: {"name": "卡卡罗", "log_name": "卡卡罗", "id_internal": 9, "color_code": "灰", "viz_color": (128/255, 128/255, 128/255)},
    10: {"name": "守岸人", "log_name": "守岸人", "id_internal": 10, "color_code": "天蓝", "viz_color": (135/255, 206/255, 250/255)},
    11: {"name": "椿", "log_name": "椿", "id_internal": 11, "color_code": "红+白", "viz_color": (255/255, 100/255, 100/255)},
    12: {"name": "科莱塔", "log_name": "科莱塔", "id_internal": 12, "color_code": "蓝+红", "viz_color": (100/255, 100/255, 255/255)},
}
ALL_CHARACTER_IDS = list(PLAYER_DETAILS.keys()) # 所有可用角色的ID列表
DEFAULT_PLAYER_VIZ_COLOR = (0/255,0/255,0/255) # 默认可视化颜色：黑色

# 可视化常量
FRAMES_DIRECTORY_BASE = "game_simulation_frames_output" # 帧图像保存的基础目录名
CELL_WIDTH_VIZ = 1.0  # Matplotlib中每个格子的宽度单位
CELL_HEIGHT_VIZ = 1.5 # Matplotlib中每个格子的高度单位 (调整以适应内容)
PLAYER_RADIUS_VIZ = 0.3 # 玩家在图上显示的半径
STACK_OFFSET_Y_VIZ = PLAYER_RADIUS_VIZ * 0.3  # 堆叠玩家在Y轴上的视觉偏移量
ACTION_LOG_PANEL_WIDTH = 7.0 # 左侧行动日志面板的估计宽度
PRE_TRACK_CELL_AREA_WIDTH = 5.0 # 0号格之前的预备赛道区域的估计宽度

# --- 玩家类 Player Class ---
class Player:
    def __init__(self, player_id_arg):
        self.id = player_id_arg 
        details = PLAYER_DETAILS[self.id]
        self.name = details["name"] 
        self.log_name = details["log_name"] 
        self.viz_color = details.get("viz_color", DEFAULT_PLAYER_VIZ_COLOR)
        self.position = 0
        self.has_finished = False; self.rank = 0; self.finish_round = float('inf')
        # 技能状态
        self.cantarella_skill_used_game = False
        self.zanni_potential_next_turn_bonus = False
        self.katisia_skill_used_game = False
        self.katisia_bonus_active_for_game = False
        self.changli_wants_last_move_next_round = False 
        self.chun_moves_alone_this_turn = False       

    def __repr__(self): return f"玩家({self.id}-{self.name}, 位置:{self.position}, 完成:{self.has_finished})"
    def roll_dice(self): # 掷骰子
        if self.id == 4: return random.choice([1, 3]) # 赞妮
        if self.id == 10: return random.choice([2, 3]) # 守岸人
        return random.randint(1, 3)

# --- 全局游戏状态变量 Global Game State Variables ---
track = [[] for _ in range(TRACK_LENGTH)]
players = [] 
game_over = False
winners_podium = [] 
current_round = 0
current_round_player_actions_log = [] 
all_round_states = [] 
current_display_round_index = -1
SELECTED_PLAYERS_THIS_GAME = []
pre_track_stacks_map = {} 
current_start_method = "normal"

# --- 核心游戏逻辑函数 (此处省略了它们的完整主体，因为它们非常长，假设与您上传版本中的逻辑一致，但日志输出为中文) ---
# 您需要确保这些函数的主体是您之前版本中包含所有技能和规则的完整版本，并且所有
# 添加到 current_round_player_actions_log 的信息都已经是中文。

def initialize_game_state_logic_only(selected_player_ids, start_method="normal", first_race_ranks_data=None):
    global track, players, game_over, winners_podium, current_round, current_round_player_actions_log
    global all_round_states, current_display_round_index, SELECTED_PLAYERS_THIS_GAME
    global pre_track_stacks_map, current_start_method

    track = [[] for _ in range(TRACK_LENGTH)] 
    players = [Player(pid) for pid in selected_player_ids]
    SELECTED_PLAYERS_THIS_GAME = list(players)
    game_over = False; winners_podium = []; current_round = 0
    current_start_method = start_method 
    pre_track_stacks_map = {} 

    selected_names_for_log = [p.log_name for p in players]
    current_round_player_actions_log = [f"游戏开始! 模式: {start_method}. 参赛选手: {', '.join(selected_names_for_log)}"]
    all_round_states = []; current_display_round_index = -1

    for player_obj in players: player_obj.position = 0

    if start_method == "normal":
        track[0] = list(players) 
        current_round_player_actions_log.append("起点模式: 标准模式 (全部从0号格开始).")
    elif start_method == "ranked_start": # ... (处理排名起点的逻辑，日志为中文) ...
        current_round_player_actions_log.append("起点模式: 排名模式 (基于“上一局”排名).")
        if not first_race_ranks_data or len(first_race_ranks_data) == 0 :
            current_round_player_actions_log.append("警告: 排名起点模式需要排名数据，数据不足，自动切换为标准模式。")
            track[0] = list(players) 
            current_start_method = "normal_fallback_no_ranks"
        else:
            for i in range(TRACK_LENGTH): track[i] = []
            id_to_current_player_obj_map = {p.id: p for p in SELECTED_PLAYERS_THIS_GAME}
            ranked_participants = []
            for prev_rank_entry in first_race_ranks_data:
                if prev_rank_entry.id in id_to_current_player_obj_map:
                    current_player_obj_for_rank = id_to_current_player_obj_map[prev_rank_entry.id]
                    ranked_participants.append({'player': current_player_obj_for_rank, 'rank': prev_rank_entry.rank})
            ranked_participants.sort(key=lambda x: x['rank'])
            start_positions_config = { 
                1: (-1, []), 2: (-2, []), 3: (-2, []), 4: (-3, []), 5: (-3, []), 6: (-4, [])
            } # rank: (position, stack_list_ref)
            for entry in ranked_participants:
                p_obj = entry['player']; rank = entry['rank']
                if rank in start_positions_config:
                    pos, _ = start_positions_config[rank]; p_obj.position = pos
                    if pos not in pre_track_stacks_map: pre_track_stacks_map[pos] = []
                    if rank in [1, 2, 4, 6]: pre_track_stacks_map[pos].insert(0, p_obj) # 顶层
                    else: pre_track_stacks_map[pos].append(p_obj)    # 底层
            for pos_val, stack_val in pre_track_stacks_map.items():
                current_round_player_actions_log.append(f"  赛前位置 {pos_val}: {[p.log_name for p in stack_val]}")


def get_player_stack_info(player_obj_to_find, current_track_state, current_pre_track_map):
    if player_obj_to_find.position < 0:
        stack_in_pre_cell = current_pre_track_map.get(player_obj_to_find.position)
        if stack_in_pre_cell:
            try: return stack_in_pre_cell, stack_in_pre_cell.index(player_obj_to_find)
            except ValueError:
                for idx, p_in_stack in enumerate(stack_in_pre_cell):
                    if p_in_stack.id == player_obj_to_find.id: return stack_in_pre_cell, idx
        return None, -1
    else:
        if 0 <= player_obj_to_find.position < len(current_track_state):
             stack_in_cell = current_track_state[player_obj_to_find.position]
             try: return stack_in_cell, stack_in_cell.index(player_obj_to_find)
             except ValueError:
                 for idx, p_in_stack in enumerate(stack_in_cell):
                     if p_in_stack.id == player_obj_to_find.id: return stack_in_cell, idx
        return None, -1


def check_is_player_last(player_to_check, current_game_players_list, current_track_state_to_check, current_pre_track_map_to_check):
    if player_to_check.has_finished: return False
    min_pos_val = TRACK_LENGTH 
    active_player_positions = []
    for p_obj in current_game_players_list:
        if not p_obj.has_finished: active_player_positions.append(p_obj.position)
    if not active_player_positions: return False
    min_pos_val = min(active_player_positions) 
    return player_to_check.position == min_pos_val

def execute_move_logic(current_player_obj, num_steps, move_description_prefix=""):
    global game_over, winners_podium, track, current_round_player_actions_log, pre_track_stacks_map
    player_log_name_val = PLAYER_DETAILS[current_player_obj.id]["log_name"]
    action_log_start_str = f"{move_description_prefix}{player_log_name_val}({current_player_obj.id})"
    if current_player_obj.has_finished: return False
    if num_steps <= 0:
        current_round_player_actions_log.append(f"{action_log_start_str} 无有效移动步数.")
        return False
    original_pos_val = current_player_obj.position
    is_from_pre_track = original_pos_val < 0
    current_stack_list, player_idx_val = get_player_stack_info(current_player_obj, track, pre_track_stacks_map)
    if current_stack_list is None:
        current_round_player_actions_log.append(f"{action_log_start_str} 错误: 玩家未在当前位置 {original_pos_val} 找到!")
        return False
    moving_seg_list = []; remaining_list = []
    if current_player_obj.id == 11 and current_player_obj.chun_moves_alone_this_turn:
        moving_seg_list = [current_player_obj]
        remaining_list = [p for p in current_stack_list if p.id != current_player_obj.id]
        current_round_player_actions_log.append(f"{player_log_name_val}(椿)技能: 单独移动!")
    else:
        moving_seg_list = current_stack_list[:player_idx_val + 1]
        remaining_list = current_stack_list[player_idx_val + 1:]
    action_log_start_str += f" 从{'赛前位置' if is_from_pre_track else '格子'}{original_pos_val}移动{num_steps}格"
    if is_from_pre_track:
        if remaining_list: pre_track_stacks_map[original_pos_val] = remaining_list
        elif original_pos_val in pre_track_stacks_map: del pre_track_stacks_map[original_pos_val]
    else: track[original_pos_val] = remaining_list
    new_logic_pos_val = original_pos_val + num_steps
    for p_in_moving_seg in moving_seg_list: p_in_moving_seg.position = new_logic_pos_val
    if new_logic_pos_val >= TRACK_LENGTH:
        action_log_start_str += f" -> 到达终点!"
        current_round_player_actions_log.append(action_log_start_str)
        for p_fin_obj in moving_seg_list:
            if not p_fin_obj.has_finished:
                p_fin_obj.has_finished = True; p_fin_obj.finish_round = current_round
                if p_fin_obj not in winners_podium: winners_podium.append(p_fin_obj)
        game_over = True; return True
    elif new_logic_pos_val >= 0: 
        final_cell_idx_main_track = new_logic_pos_val % TRACK_LENGTH
        action_log_suffix_str = f" -> 至赛道格 {final_cell_idx_main_track}."
        if current_player_obj.id == 3 and not current_player_obj.cantarella_skill_used_game:
            if track[final_cell_idx_main_track]: 
                action_log_suffix_str += " 坎特蕾拉发动技能!"
                current_player_obj.cantarella_skill_used_game = True
        track[final_cell_idx_main_track] = moving_seg_list + track[final_cell_idx_main_track] 
        for p_in_moving_seg in moving_seg_list: p_in_moving_seg.position = final_cell_idx_main_track
        current_round_player_actions_log.append(action_log_start_str + action_log_suffix_str)
        return False
    else: 
        action_log_start_str += f" -> 至赛前位置 {new_logic_pos_val}."
        current_round_player_actions_log.append(action_log_start_str)
        if new_logic_pos_val in pre_track_stacks_map:
            pre_track_stacks_map[new_logic_pos_val] = moving_seg_list + pre_track_stacks_map[new_logic_pos_val]
        else: pre_track_stacks_map[new_logic_pos_val] = moving_seg_list
        return False

def process_single_player_turn(player_obj, is_first, is_last):
    global game_over, current_round_player_actions_log, track, SELECTED_PLAYERS_THIS_GAME, pre_track_stacks_map
    if player_obj.has_finished: return
    player_log_name_val = PLAYER_DETAILS[player_obj.id]["log_name"]
    action_log_base = f"{player_log_name_val}({player_obj.id})"
    turn_skills_log = []; bonus_steps = 0; player_obj.chun_moves_alone_this_turn = False
    if player_obj.id == 7: 
        stack_j, idx_j = get_player_stack_info(player_obj, track, pre_track_stacks_map)
        if stack_j and idx_j > 0 and random.random() < 0.40:
            current_round_player_actions_log.append(f"{action_log_base} 今汐技能: 移至当前堆叠顶部!")
            target_stack = pre_track_stacks_map.get(player_obj.position) if player_obj.position < 0 else track[player_obj.position]
            if target_stack: target_stack.pop(idx_j); target_stack.insert(0, player_obj)
    if player_obj.id == 9 and check_is_player_last(player_obj, SELECTED_PLAYERS_THIS_GAME, track, pre_track_stacks_map):
        turn_skills_log.append("卡卡罗垫底奖"); bonus_steps += 3
    if player_obj.id == 4 and player_obj.zanni_potential_next_turn_bonus: 
        if random.random() < 0.40: turn_skills_log.append("赞妮叠后奖"); bonus_steps += 2
        player_obj.zanni_potential_next_turn_bonus = False
    if player_obj.id == 5 and player_obj.katisia_bonus_active_for_game: 
        if random.random() < 0.60: turn_skills_log.append("卡提西亚永久奖"); bonus_steps += 2
    dice = player_obj.roll_dice(); total_steps = dice + bonus_steps
    turn_skills_log.insert(0, f"掷{dice}") 
    if player_obj.id == 2 and is_first: total_steps += 2; turn_skills_log.append("布兰特首位奖")
    if player_obj.id == 6 and random.random() < 0.50: total_steps += 2; turn_skills_log.append("菲比50%奖")
    if player_obj.id == 11 and random.random() < 0.50:
        s_c, _ = get_player_stack_info(player_obj, track, pre_track_stacks_map)
        if s_c:
            others = len(s_c) - 1
            if others > 0: total_steps += others; turn_skills_log.append(f"椿同格+{others}")
            player_obj.chun_moves_alone_this_turn = True
    move_prefix = f"{action_log_base} ({', '.join(turn_skills_log)}): "
    if execute_move_logic(player_obj, total_steps, move_prefix): return
    if player_obj.has_finished: return
    if player_obj.id == 12 and random.random() < 0.28:
        current_round_player_actions_log.append(f"{action_log_base} 科莱塔技能: 再次以骰子步数({dice})前进!")
        chun_flag_orig = player_obj.chun_moves_alone_this_turn; player_obj.chun_moves_alone_this_turn = False 
        if execute_move_logic(player_obj, dice, f"{action_log_base} 科莱塔二次移动:"):
            player_obj.chun_moves_alone_this_turn = chun_flag_orig; return
        player_obj.chun_moves_alone_this_turn = chun_flag_orig
    if player_obj.has_finished: return
    post_move_logs = []
    if player_obj.id == 4: 
        s_z, _ = get_player_stack_info(player_obj, track, pre_track_stacks_map);
        if s_z and len(s_z) > 1: player_obj.zanni_potential_next_turn_bonus = True; post_move_logs.append("赞妮移动后堆叠")
        else: player_obj.zanni_potential_next_turn_bonus = False
    if player_obj.id == 5 and not player_obj.katisia_skill_used_game: 
        if check_is_player_last(player_obj, SELECTED_PLAYERS_THIS_GAME, track, pre_track_stacks_map):
            player_obj.katisia_skill_used_game = True; player_obj.katisia_bonus_active_for_game = True
            post_move_logs.append("卡提西亚最后激活永久奖")
    if player_obj.id == 8:
        s_cl, idx_cl = get_player_stack_info(player_obj, track, pre_track_stacks_map)
        if s_cl and idx_cl < len(s_cl) - 1: 
            player_obj.changli_wants_last_move_next_round = True; post_move_logs.append("长离脚下有人")
        else: player_obj.changli_wants_last_move_next_round = False
    if post_move_logs:
        current_round_player_actions_log.append(f"{action_log_base} 移动后触发: {', '.join(post_move_logs)}.")
    if player_obj.id == 1 and is_last and not player_obj.has_finished: 
        execute_move_logic(player_obj, 2, f"{player_log_name_val}({player_obj.id}) 洛可可末位奖:")

def play_one_full_round(): 
    global current_round, game_over, current_round_player_actions_log, track, SELECTED_PLAYERS_THIS_GAME, current_start_method, pre_track_stacks_map
    current_round += 1
    current_round_player_actions_log = [f"--- 回合 {current_round} ({time.strftime('%H:%M:%S')}) (模式: {current_start_method}) ---"]
    active_p_list = [p for p in SELECTED_PLAYERS_THIS_GAME if not p.has_finished]
    if not active_p_list:
        current_round_player_actions_log.append("没有可行动的玩家。"); game_over = True; return
    eligible_last = []; normal_pool = []
    for p_order in active_p_list:
        if p_order.id == 8 and p_order.changli_wants_last_move_next_round and random.random() < 0.65:
            eligible_last.append(p_order)
            current_round_player_actions_log.append(f"{PLAYER_DETAILS[p_order.id]['log_name']}(长离)技能: 本回合最后行动。")
        else: normal_pool.append(p_order)
        p_order.changli_wants_last_move_next_round = False 
    random.shuffle(normal_pool); random.shuffle(eligible_last)
    round_order = normal_pool + eligible_last
    round_order_names_log = [PLAYER_DETAILS[p.id]["log_name"] for p in round_order]
    current_round_player_actions_log.append(f"本回合行动顺序: {', '.join(round_order_names_log)}")
    if current_round == 1 and current_start_method == "normal":
        current_round_player_actions_log.append(f"提示: 回合1 (标准起点)，0号格初始堆叠已按本轮行动顺序重置。")
        track[0] = list(round_order) 
    for i, player_act in enumerate(round_order):
        if game_over: break
        process_single_player_turn(player_act, i == 0, i == len(round_order) - 1)

def determine_final_ranking(): 
    current_assigned_rank = 1; final_ranks = []; p_ids_ranked = set()
    for p_win in winners_podium:
        if p_win.id not in p_ids_ranked:
            p_win.rank = current_assigned_rank; final_ranks.append(p_win); p_ids_ranked.add(p_win.id); current_assigned_rank += 1
    unfin_details = []
    for p_obj in SELECTED_PLAYERS_THIS_GAME:
        if p_obj.id not in p_ids_ranked:
            pos_s = p_obj.position if p_obj.position < TRACK_LENGTH else TRACK_LENGTH - 0.1
            stk, dep = get_player_stack_info(p_obj, track, pre_track_stacks_map) # Pass pre_track_map
            dep_s = dep if stk else float('inf')
            unfin_details.append({'p': p_obj, 'pos': pos_s, 'dep': dep_s})
    unfin_details.sort(key=lambda x: (-x['pos'], x['dep'], x['p'].id))
    for entry in unfin_details:
        if entry['p'].id not in p_ids_ranked:
            entry['p'].rank = current_assigned_rank; final_ranks.append(entry['p']); p_ids_ranked.add(entry['p'].id); current_assigned_rank += 1
    return final_ranks

# --- Matplotlib 绘图函数 ---
def draw_matplotlib_board_state(current_ax_obj, current_fig_obj, round_num_to_display, 
                                current_track_to_draw, current_pre_track_map_to_draw, 
                                current_players_list_ref, current_podium_to_draw,
                                list_of_actions_to_log, is_game_over_now):
    global plt, np 
    if not current_ax_obj or not current_fig_obj or not plt or not np: return
    current_ax_obj.clear()
    cells_per_visual_row = TRACK_LENGTH // NUM_ROWS 
    action_log_panel_x_start = -ACTION_LOG_PANEL_WIDTH 
    num_pre_track_display_cells = 4 
    pre_track_cells_start_x = action_log_panel_x_start - PRE_TRACK_CELL_AREA_WIDTH - 0.5 
    track_drawing_actual_offset_x = 0.5 
    current_ax_obj.text(action_log_panel_x_start + 0.2, NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) - 0.1, 
                        f"回合 {round_num_to_display} 行动日志:", fontsize=8, weight='bold', ha='left', va='top', color='black')
    log_display_y_pos = NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) - 0.5
    if list_of_actions_to_log:
        max_log_entries = 20; displayed_logs_count = 0
        logs_to_show_on_screen = list_of_actions_to_log[-max_log_entries:]
        for idx, item_log_text in enumerate(logs_to_show_on_screen):
             current_ax_obj.text(action_log_panel_x_start + 0.2, log_display_y_pos - (idx * 0.22), item_log_text, 
                                 fontsize=5.5, ha='left', va='top', color=(0.1,0.1,0.1)) # 移除了 family='monospace'
    else:
        current_ax_obj.text(action_log_panel_x_start + 0.2, log_display_y_pos, "等待行动...", fontsize=6, ha='left', va='top',color=(0.2,0.2,0.2))
    for i in range(num_pre_track_display_cells): # 绘制赛前格子
        neg_pos_val_draw = -(i + 1); display_col_offset_draw = num_pre_track_display_cells -1 - i 
        pre_cell_x_draw = pre_track_cells_start_x + display_col_offset_draw * (CELL_WIDTH_VIZ + 0.1)
        pre_cell_y_draw = (NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5)) / 2 - CELL_HEIGHT_VIZ / 2 
        rect_draw = plt.Rectangle((pre_cell_x_draw, pre_cell_y_draw), CELL_WIDTH_VIZ, CELL_HEIGHT_VIZ, fill=True, color=(0.95, 0.95, 0.75), ec='black', ls=':')
        current_ax_obj.add_patch(rect_draw)
        current_ax_obj.text(pre_cell_x_draw + CELL_WIDTH_VIZ/2, pre_cell_y_draw + CELL_HEIGHT_VIZ/2, str(neg_pos_val_draw), ha='center', va='center', fontsize=7)
        stack_in_pre_cell_draw = current_pre_track_map_to_draw.get(neg_pos_val_draw, [])
        if stack_in_pre_cell_draw:
            pre_cell_center_x_draw = pre_cell_x_draw + CELL_WIDTH_VIZ / 2; pre_cell_top_y_draw = pre_cell_y_draw + CELL_HEIGHT_VIZ
            for stack_idx_draw, p_obj_draw in enumerate(stack_in_pre_cell_draw):
                p_center_y_draw = pre_cell_top_y_draw - PLAYER_RADIUS_VIZ - (stack_idx_draw * (PLAYER_RADIUS_VIZ*2 - STACK_OFFSET_Y_VIZ))
                norm_color_draw = p_obj_draw.viz_color 
                circle_draw = plt.Circle((pre_cell_center_x_draw, p_center_y_draw), PLAYER_RADIUS_VIZ, color=norm_color_draw, ec='black', lw=0.7)
                current_ax_obj.add_patch(circle_draw)
                player_char_draw = p_obj_draw.name[0] if p_obj_draw.name else str(p_obj_draw.id)
                brightness_draw = sum(norm_color_draw[:3]) * 255 / 3 
                txt_color_draw = 'white' if brightness_draw < 128 else 'black'
                current_ax_obj.text(pre_cell_center_x_draw, p_center_y_draw, player_char_draw, ha='center', va='center', fontsize=7, color=txt_color_draw, weight='bold')
    for i_track in range(TRACK_LENGTH): # 绘制主赛道
        viz_row_track = 0 if i_track < cells_per_visual_row else 1; viz_col_logical_track = i_track % cells_per_visual_row
        viz_col_display_track = (cells_per_visual_row - 1 - viz_col_logical_track) if viz_row_track == 1 else viz_col_logical_track
        cell_x_coord_track = track_drawing_actual_offset_x + viz_col_display_track * (CELL_WIDTH_VIZ + 0.1)
        cell_y_coord_track = viz_row_track * (CELL_HEIGHT_VIZ + 0.5)
        cell_rect_track = plt.Rectangle((cell_x_coord_track, cell_y_coord_track), CELL_WIDTH_VIZ, CELL_HEIGHT_VIZ, fill=True, color=(0.88,0.88,0.88), ec=(0.4,0.4,0.4))
        current_ax_obj.add_patch(cell_rect_track)
        current_ax_obj.text(cell_x_coord_track + CELL_WIDTH_VIZ/2, cell_y_coord_track + CELL_HEIGHT_VIZ/2, str(i_track), ha='center', va='center', fontsize=7,color=(0.3,0.3,0.3))
        stack_to_draw_in_cell_main = current_track_to_draw[i_track]
        if stack_to_draw_in_cell_main:
            cell_center_x_main = cell_x_coord_track + CELL_WIDTH_VIZ/2; cell_top_y_main = cell_y_coord_track + CELL_HEIGHT_VIZ
            for stack_idx_main, p_obj_main in enumerate(stack_to_draw_in_cell_main):
                p_center_y_main = cell_top_y_main - PLAYER_RADIUS_VIZ - (stack_idx_main * (PLAYER_RADIUS_VIZ*2 - STACK_OFFSET_Y_VIZ))
                color_main = p_obj_main.viz_color; circle_main = plt.Circle((cell_center_x_main, p_center_y_main), PLAYER_RADIUS_VIZ, color=color_main, ec='black', lw=0.7)
                current_ax_obj.add_patch(circle_main)
                bright_main = sum(color_main[:3]) * 255 / 3; txt_color_main = 'white' if bright_main < 128 else 'black'
                char_main = p_obj_main.name[0] if p_obj_main.name else str(p_obj_main.id)
                current_ax_obj.text(cell_center_x_main, p_center_y_main, char_main, ha='center', va='center', fontsize=7, color=txt_color_main, weight='bold')
    podium_x_start_val = track_drawing_actual_offset_x + cells_per_visual_row * (CELL_WIDTH_VIZ + 0.1) + 0.5 # 排行榜绘制
    current_ax_obj.text(podium_x_start_val, NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) - 0.1, "最终排名:", fontsize=9, weight='bold', color='black')
    for i_podium, p_winner_podium in enumerate(current_podium_to_draw):
        color_winner = p_winner_podium.viz_color
        current_ax_obj.text(podium_x_start_val, NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) - 0.5 - (i_podium*0.35),
                            f"{p_winner_podium.rank}. {p_winner_podium.name} (第{p_winner_podium.finish_round}回合)", 
                            fontsize=7, color=color_winner)
    current_ax_obj.set_title(f"当前回合: {round_num_to_display}", fontsize=12) # 图表标题
    current_ax_obj.set_xlim(pre_track_cells_start_x - 0.2, podium_x_start_val + 3.5) 
    current_ax_obj.set_ylim(-0.5, NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) + 0.5)
    current_ax_obj.set_aspect('equal', adjustable='box'); current_ax_obj.axis('off')
    if is_game_over_now:
        current_ax_obj.text( (podium_x_start_val + pre_track_cells_start_x) / 2 , 
                             (NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5)) / 2,
                             "游戏结束!", ha='center', va='center', fontsize=28, color='darkred', weight='heavy',
                             bbox=dict(facecolor='gold', alpha=0.7, boxstyle='round,pad=0.6'))
    if current_fig_obj: current_fig_obj.canvas.draw_idle()

# --- Matplotlib 初始化及运行器函数 ---
def _setup_matplotlib_fonts(): # (与上一版我提供的 test.py 中此函数的逻辑一致)
    global plt, font_manager
    if not plt or not font_manager: return
    try:
        common_chinese_fonts = ['SimHei','Microsoft YaHei','PingFang SC','WenQuanYi Zen Hei','Noto Sans CJK SC','sans-serif']
        plt.rcParams['font.sans-serif'] = common_chinese_fonts
        plt.rcParams['axes.unicode_minus'] = False
    except Exception as e: print(f"中文字体设置错误: {e}")



def run_single_simulation_for_auto_frames(selected_ids_for_game, start_method_param, first_race_ranks_data_param, specific_frames_dir_param, suppress_all_prints_param=False):
    global game_over, current_round, FIG, AX, plt, np, current_round_player_actions_log, track, SELECTED_PLAYERS_THIS_GAME, winners_podium, pre_track_stacks_map
    initialize_game_state_logic_only(selected_ids_for_game, start_method_param, first_race_ranks_data_param) 
    can_visualize = initialize_matplotlib_for_mode(is_interactive_mode=False) 
    if can_visualize and not os.path.exists(specific_frames_dir_param): os.makedirs(specific_frames_dir_param)
    if can_visualize:
        draw_matplotlib_board_state(AX, FIG, 0, track, pre_track_stacks_map, SELECTED_PLAYERS_THIS_GAME, winners_podium, current_round_player_actions_log, False) 
        FIG.savefig(os.path.join(specific_frames_dir_param, f"round_{0:03d}_initial.png"), dpi=150)
    elif not suppress_all_prints_param: print(f"警告: 可视化初始化失败，运行于 '{specific_frames_dir_param}' 的帧保存将不执行。")
    max_r = 200
    while not game_over and current_round < max_r:
        play_one_full_round() 
        if can_visualize:
            draw_matplotlib_board_state(AX, FIG, current_round, track, pre_track_stacks_map, SELECTED_PLAYERS_THIS_GAME, winners_podium, current_round_player_actions_log, game_over)
            FIG.savefig(os.path.join(specific_frames_dir_param, f"round_{current_round:03d}_end.png"), dpi=150)
    final_player_rankings = determine_final_ranking()
    if can_visualize:
        draw_matplotlib_board_state(AX, FIG, current_round, track, pre_track_stacks_map, SELECTED_PLAYERS_THIS_GAME, final_player_rankings, current_round_player_actions_log, True)
        FIG.savefig(os.path.join(specific_frames_dir_param, f"game_over_final_{current_round:03d}.png"), dpi=150)
        if plt and FIG: plt.close(FIG); FIG, AX, plt, np, font_manager = None, None, None, None, None
    return final_player_rankings



# 在 test.py 中
def initialize_matplotlib_for_mode(is_interactive_mode): # <--- 修改参数名称
    global FIG, AX, plt, np, font_manager
    try:
        # 仅在需要时导入，并赋值给全局变量
        # (确保这些导入和赋值逻辑与你文件中的一致)
        if plt is None: import matplotlib.pyplot as plt_module; globals()['plt'] = plt_module
        if np is None: import numpy as np_module; globals()['np'] = np_module
        if font_manager is None: import matplotlib.font_manager as fm_module; globals()['font_manager'] = fm_module
        
        _setup_matplotlib_fonts() # 调用字体设置

        if FIG: # 如果已存在图形对象，先关闭它
            plt.close(FIG)
            FIG, AX = None, None # 清理旧对象
            
        # 为行动日志和可能的赛前格子调整图形尺寸
        figsize_setting = (22 if is_interactive_mode else 19, 7) # <--- 使用新的参数名 is_interactive_mode
        FIG, AX = plt.subplots(figsize=figsize_setting) 
        # print(f"[调试] Matplotlib已为 {'交互' if is_interactive_mode else '自动帧'} 模式初始化。")
        return True
    except ImportError:
        print("错误: Matplotlib或Numpy未安装，无法进行可视化。")
        return False
    except Exception as e: 
        print(f"Matplotlib 初始化错误 ({'交互' if is_interactive_mode else '自动'}模式): {e}")
        return False

def pre_calculate_all_round_states_for_interactive_view(selected_ids_for_game, start_method_param, first_race_ranks_data_param):
    global all_round_states, game_over, current_round, current_round_player_actions_log, track, SELECTED_PLAYERS_THIS_GAME, winners_podium, pre_track_stacks_map
    initialize_game_state_logic_only(selected_ids_for_game, start_method_param, first_race_ranks_data_param)
    all_round_states = []
    all_round_states.append({
        'round_num': 0, 'track': copy.deepcopy(track), 'pre_track_map': copy.deepcopy(pre_track_stacks_map),
        'players_in_game': copy.deepcopy(SELECTED_PLAYERS_THIS_GAME), 'winners_podium': copy.deepcopy(winners_podium),
        'player_actions_log': list(current_round_player_actions_log), 'is_game_over_at_this_point': False
    })
    max_interactive_rounds = 200
    while not game_over and current_round < max_interactive_rounds:
        play_one_full_round() 
        copied_players = [copy.deepcopy(p) for p in SELECTED_PLAYERS_THIS_GAME]
        id_map = {p.id: cp for p, cp in zip(SELECTED_PLAYERS_THIS_GAME, copied_players)}
        copied_track = [[id_map[p.id] for p in cell if p.id in id_map] for cell in track]
        copied_pre_track = {pos: [id_map[p.id] for p in stack if p.id in id_map] for pos, stack in pre_track_stacks_map.items()}
        copied_podium = [id_map[p.id] for p in winners_podium if p.id in id_map]
        if game_over: # 确保最终排名信息被复制到状态中
            final_ranks_for_state = determine_final_ranking() # 这会更新全局 SELECTED_PLAYERS_THIS_GAME 中的 rank
            for p_global in SELECTED_PLAYERS_THIS_GAME: # 将全局的rank更新到当前状态的复制对象中
                if p_global.id in id_map:
                    id_map[p_global.id].rank = p_global.rank
                    id_map[p_global.id].finish_round = p_global.finish_round
            # 重建 podium 以确保包含的是带有正确 rank 的复制对象
            copied_podium = [p_copy for p_copy in copied_players if p_copy.has_finished]
            copied_podium.sort(key=lambda x: (x.finish_round, x.rank if x.rank > 0 else float('inf')))


        all_round_states.append({
            'round_num': current_round, 'track': copied_track, 'pre_track_map': copied_pre_track,
            'players_in_game': copied_players, 'winners_podium': copied_podium,
            'player_actions_log': list(current_round_player_actions_log), 'is_game_over_at_this_point': game_over
        })
        if game_over: break
    print(f"交互模式: 预计算完成，总共 {len(all_round_states) -1 } 个有效回合。")
    return bool(all_round_states)

def on_key_press_interactive(event): # (与上一版我提供的 test.py 中此函数的逻辑一致)
    global current_display_round_index, all_round_states, FIG, AX 
    if not all_round_states or not FIG or not event.key: return
    if event.key == 'right': current_display_round_index = min(len(all_round_states) - 1, current_display_round_index + 1)
    elif event.key == 'left': current_display_round_index = max(0, current_display_round_index - 1)
    elif event.key == 'home': current_display_round_index = 0
    elif event.key == 'end': current_display_round_index = len(all_round_states) -1
    else: return 
    s = all_round_states[current_display_round_index]
    draw_matplotlib_board_state(AX, FIG, s['round_num'], s['track'], s['pre_track_map'], s['players_in_game'], 
                                s['winners_podium'], s['player_actions_log'], s['is_game_over_at_this_point'])

def run_interactive_visualization(selected_ids_for_game, start_method_param, first_race_ranks_data_param):

    global FIG, AX, plt, np, current_display_round_index, font_manager 
    if not pre_calculate_all_round_states_for_interactive_view(selected_ids_for_game, start_method_param, first_race_ranks_data_param):
        print("未能预计算回合状态。"); return
    if not initialize_matplotlib_for_mode(is_interactive_mode=True):
        print("Matplotlib (interactive) 初始化错误，无法启动查看器。"); return
    FIG.canvas.mpl_connect('key_press_event', on_key_press_interactive)
    current_display_round_index = 0 
    if all_round_states:
        s_init = all_round_states[0] 
        draw_matplotlib_board_state(AX, FIG, s_init['round_num'], s_init['track'], s_init['pre_track_map'], s_init['players_in_game'], 
                                    s_init['winners_podium'], s_init['player_actions_log'], s_init['is_game_over_at_this_point'])
        print("交互式查看器已启动。使用左右箭头键翻页，Home/End 跳转。关闭窗口结束。")
        plt.show() 
    else: print("没有可供显示的回合数据。")
    FIG, AX, plt, np, font_manager = None, None, None, None, None

def run_simulation_logic_only(selected_ids_for_game, start_method_param="normal", first_race_ranks_data_param=None, suppress_all_prints=True):
    global game_over, current_round 
    initialize_game_state_logic_only(selected_ids_for_game, start_method_param, first_race_ranks_data_param) 
    max_sim_rounds = 200 
    while not game_over and current_round < max_sim_rounds:
        play_one_full_round() 
        if not suppress_all_prints and current_round > 0 and current_round % 50 == 0: sys.stdout.write('.'); sys.stdout.flush()
    if not suppress_all_prints and current_round > 0 and (current_round % 50 != 0 or game_over): sys.stdout.write('\n')
    return determine_final_ranking()

# --- 命令行交互函数 (中文提示) ---
def select_characters_cli(): 
    print("\n--- 角色选择 ---"); print("可用角色:")
    for char_id, details in PLAYER_DETAILS.items(): print(f"  ID: {char_id} - {details['name']}")
    selected_ids = []; num_to_select = DEFAULT_NUM_SELECTED_PLAYERS
    print(f"请选择 {num_to_select} 位角色。")
    while len(selected_ids) < num_to_select:
        try:
            prompt = f"请选择第 {len(selected_ids) + 1}/{num_to_select} 位角色 (输入ID): "
            choice = int(input(prompt))
            if choice not in PLAYER_DETAILS: print(f"无效的ID: {choice}。")
            elif choice in selected_ids: print(f"角色ID {choice} ({PLAYER_DETAILS[choice]['name']}) 已被选择。")
            else: selected_ids.append(choice); print(f"已选择: {PLAYER_DETAILS[choice]['name']}")
        except ValueError: print("无效输入，请输入数字ID。")
    print("\n你选择的参赛角色ID为:", selected_ids); return selected_ids

def select_start_method_cli(): 
    print("\n--- 请选择起点方式 ---")
    print("1. 标准起点 (所有选定玩家从0号格开始)")
    print("2. 排名起点 (根据虚拟“上一局”随机排名决定分散起点)")
    while True:
        choice = input("请输入选项 (1 或 2): ")
        if choice == '1': return "normal"
        if choice == '2': print("已选排名起点。将使用基于当前选手的虚拟随机排名。"); return "ranked_start"
        print("无效选项，请重新输入。")

# --- 主程序入口 ---
# 在 test.py 文件末尾

if __name__ == "__main__":
    print("--- [测试脚本 test.py] 交互模式启动 ---")
    
    selected_character_ids_main = select_characters_cli() 
    expected_player_count_main = DEFAULT_NUM_SELECTED_PLAYERS

    if selected_character_ids_main and len(selected_character_ids_main) == expected_player_count_main:
        start_method_selected_main = select_start_method_cli() # 用户选择起点模式
        
        mock_ranking_data_main = None # 用于排名起点的排名数据

        if start_method_selected_main == "ranked_start":
            print("\n--- 设置“排名起点”模式的排名 ---")
            manual_rank_choice = input("是否要手动指定上一局排名? (是[y]/否[n]，默认为否，将使用虚拟随机排名): ").lower()
            
            if manual_rank_choice == 'y' or manual_rank_choice == '是':
                print("请输入当前已选角色的排名顺序 (按名次输入ID，用空格分隔)。")
                print(f"当前已选角色: {[f'{pid}:{PLAYER_DETAILS[pid]['name']}' for pid in selected_character_ids_main]}")
                
                manual_ranks_ok = False
                while not manual_ranks_ok:
                    try:
                        rank_input_str = input(f"请输入 {len(selected_character_ids_main)} 个已选角色的ID作为排名顺序 (例如: 7 8 9 10 11 12): ")
                        ranked_ids_input = [int(pid_str) for pid_str in rank_input_str.split()]
                        
                        if len(ranked_ids_input) != len(selected_character_ids_main):
                            print(f"错误：需要输入 {len(selected_character_ids_main)} 个ID。")
                        elif not all(pid in selected_character_ids_main for pid in ranked_ids_input):
                            print("错误：输入的ID中包含未被选定的角色。")
                        elif len(set(ranked_ids_input)) != len(ranked_ids_input):
                            print("错误：输入的ID中有重复。")
                        else:
                            mock_ranking_data_main = []
                            for rank_idx, player_id_ranked in enumerate(ranked_ids_input):
                                # 创建一个临时的Player对象或包含必要信息的字典来传递排名
                                # Player对象更符合 first_race_ranks_data 的预期结构
                                temp_p = Player(player_id_ranked) 
                                temp_p.rank = rank_idx + 1 # 赋予手动指定的排名
                                mock_ranking_data_main.append(temp_p)
                            manual_ranks_ok = True
                            print(f"已手动设置排名: {[f'{p.rank}.{p.log_name}' for p in mock_ranking_data_main]}")
                    except ValueError:
                        print("无效输入，请输入数字ID并用空格分隔。")
            
            if not mock_ranking_data_main: # 如果用户选择否，或手动输入失败，则使用虚拟随机排名
                print("将使用基于当前选手的虚拟随机排名...")
                temp_players_for_mock_rank_main = [Player(pid) for pid in selected_character_ids_main]
                random.shuffle(temp_players_for_mock_rank_main) 
                mock_ranking_data_main = []
                for r_idx, p_obj_mock_main in enumerate(temp_players_for_mock_rank_main):
                    p_obj_mock_main.rank = r_idx + 1 
                    mock_ranking_data_main.append(p_obj_mock_main) 
                print(f"用于本次模拟的虚拟排名: {[f'{p.rank}.{p.log_name}' for p in mock_ranking_data_main]}")

        print(f"\n将使用选定角色及 '{start_method_selected_main}' 起点模式运行交互式可视化...")
        # run_interactive_visualization 函数需要能接收 start_method 和 mock_ranking_data
        run_interactive_visualization(selected_character_ids_main, start_method_selected_main, mock_ranking_data_main)
    
    else:
        print(f"角色选择未完成或选择数量不等于 {expected_player_count_main}。程序已取消。")

    print("\n--- [测试脚本 test.py] 运行结束 ---")