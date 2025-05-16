# test.py
import os
import random
import time
import copy 
import sys

# --- Matplotlib (Conditional Import and Global Variables) ---
plt = None
np = None
# ----------------------------------------------------------------------
# 新增：尝试导入 matplotlib.font_manager 以便更灵活地处理字体
font_manager = None
# ----------------------------------------------------------------------
FIG = None 
AX = None  

# --- Game Constants ---
TRACK_LENGTH = 24
DEFAULT_NUM_SELECTED_PLAYERS = 6 
NUM_ROWS = 2 

PLAYER_DETAILS = {
    1: {"name": "洛可可", "id_internal": 1, "color_code": "粉+黄", "viz_color": (255/255, 192/255, 203/255)},
    2: {"name": "布兰特", "id_internal": 2, "color_code": "蓝", "viz_color": (0/255, 0/255, 255/255)},
    3: {"name": "坎特蕾拉", "id_internal": 3, "color_code": "紫", "viz_color": (128/255, 0/255, 128/255)},
    4: {"name": "赞妮", "id_internal": 4, "color_code": "红", "viz_color": (255/255, 0/255, 0/255)},
    5: {"name": "卡提西亚", "id_internal": 5, "color_code": "绿", "viz_color": (0/255, 128/255, 0/255)},
    6: {"name": "菲比", "id_internal": 6, "color_code": "黄", "viz_color": (255/255, 255/255, 0/255)},
    # New Characters
    7: {"name": "今汐", "id_internal": 7, "color_code": "白", "viz_color": (245/255, 245/255, 245/255)},
    8: {"name": "长离", "id_internal": 8, "color_code": "淡红", "viz_color": (255/255, 153/255, 153/255)},
    9: {"name": "卡卡罗", "id_internal": 9, "color_code": "灰", "viz_color": (128/255, 128/255, 128/255)},
    10: {"name": "守岸人", "id_internal": 10, "color_code": "天蓝", "viz_color": (135/255, 206/255, 250/255)},
    11: {"name": "椿", "id_internal": 11, "color_code": "红+白", "viz_color": (255/255, 100/255, 100/255)},
    12: {"name": "科莱塔", "id_internal": 12, "color_code": "蓝+红", "viz_color": (100/255, 100/255, 255/255)},
}
ALL_CHARACTER_IDS = list(PLAYER_DETAILS.keys())
DEFAULT_PLAYER_VIZ_COLOR = (0,0,0)

FRAMES_DIRECTORY_BASE = "game_simulation_frames_output"
CELL_WIDTH_VIZ = 1.0 
CELL_HEIGHT_VIZ = 2.0
PLAYER_RADIUS_VIZ = 0.3
STACK_OFFSET_Y_VIZ = PLAYER_RADIUS_VIZ * 0.3 
ACTION_LOG_PANEL_WIDTH = 6.0

# --- Player Class ---
class Player:
    def __init__(self, player_id_arg): # Changed parameter name to avoid conflict
        self.id = player_id_arg # Use the passed player_id_arg
        details = PLAYER_DETAILS[self.id]
        self.name = details["name"]
        self.color_str = details["color_code"]
        self.viz_color = details.get("viz_color", DEFAULT_PLAYER_VIZ_COLOR)
        self.position = 0
        self.has_finished = False
        self.rank = 0
        self.finish_round = float('inf')
        # Original skills
        self.cantarella_skill_used_game = False
        self.zanni_potential_next_turn_bonus = False
        self.katisia_skill_used_game = False
        self.katisia_bonus_active_for_game = False
        # New skills flags
        self.changli_wants_last_move_next_round = False # For 长离
        self.chun_moves_alone_this_turn = False       # For 椿

    def __repr__(self):
        return f"P({self.id}-{self.name},Pos:{self.position})"

    def roll_dice(self):
        if self.id == 4: return random.choice([1, 3]) # 赞妮
        if self.id == 10: return random.choice([2, 3]) # 守岸人
        return random.randint(1, 3)

# --- Global Game State Variables ---
track = [[] for _ in range(TRACK_LENGTH)]
players = [] # THIS WILL BE POPULATED BY initialize_game_state WITH SELECTED PLAYERS
game_over = False
winners_podium = [] 
current_round = 0
current_round_player_actions_log = [] 
all_round_states = [] 
current_display_round_index = -1
SELECTED_PLAYERS_THIS_GAME = [] # Stores the list of Player objects for the current game

# --- Core Game Logic Functions ---
def initialize_game_state_logic_only(selected_player_ids):
    global track, players, game_over, winners_podium, current_round, current_round_player_actions_log
    global all_round_states, current_display_round_index, SELECTED_PLAYERS_THIS_GAME

    track = [[] for _ in range(TRACK_LENGTH)]
    # Create Player objects ONLY for selected IDs
    players = [Player(pid) for pid in selected_player_ids]
    SELECTED_PLAYERS_THIS_GAME = list(players) # Keep a reference to current game's players

    game_over = False
    winners_podium = []
    current_round = 0
    current_round_player_actions_log = [f"游戏开始! 参赛选手: {[p.name for p in players]}"]
    all_round_states = []
    current_display_round_index = -1

    for player_obj in players: player_obj.position = 0
    track[0] = list(players) # Initial stack at cell 0, order determined in Round 1

def get_player_stack_info(player_obj_to_find, current_track_state_to_search):
    # (Keep the robust version from previous answer that searches by ID as fallback)
    for cell_idx, stack_in_cell in enumerate(current_track_state_to_search):
        if player_obj_to_find in stack_in_cell:
            try: return stack_in_cell, stack_in_cell.index(player_obj_to_find)
            except ValueError: pass 
    for cell_idx, stack_in_cell in enumerate(current_track_state_to_search):
        for p_idx_in_stack, p_in_stack in enumerate(stack_in_cell):
            if p_in_stack.id == player_obj_to_find.id: return stack_in_cell, p_idx_in_stack
    return None, -1

def check_is_player_last(player_to_check, current_game_players_list, current_track_state_to_check):
    # (Keep the robust version from previous answer)
    if player_to_check.has_finished: return False
    min_pos_val = TRACK_LENGTH 
    active_p_on_track = [p for p in current_game_players_list if not p.has_finished and p.position < TRACK_LENGTH]
    if not active_p_on_track: return False # No one to be last against, or player_to_check is only one
    
    # If player_to_check is the only one left on track, they are last.
    if len(active_p_on_track) == 1 and active_p_on_track[0].id == player_to_check.id:
        return True

    for p_obj in active_p_on_track: min_pos_val = min(min_pos_val, p_obj.position)
    if min_pos_val == TRACK_LENGTH: return False 
    return player_to_check.position == min_pos_val


def execute_move_logic(current_player_obj, num_steps, move_description_prefix=""):
    global game_over, winners_podium, track, current_round_player_actions_log

    action_log_start = f"{move_description_prefix}{current_player_obj.name}({current_player_obj.id})"

    if current_player_obj.has_finished: return False
    if num_steps <= 0:
        current_round_player_actions_log.append(f"{action_log_start} 无有效移动步数.")
        return False

    current_actual_stack_on_track, player_idx_in_actual_stack = get_player_stack_info(current_player_obj, track)
    if current_actual_stack_on_track is None:
        print(f"CRITICAL ERROR: Player {current_player_obj.name} (Pos: {current_player_obj.position}) not found on track for execute_move.")
        current_round_player_actions_log.append(f"{action_log_start} 错误: 核心逻辑未在赛道找到玩家!")
        return False
    
    original_pos_idx = current_player_obj.position
    # Verify stack consistency
    if track[original_pos_idx] != current_actual_stack_on_track:
        current_actual_stack_on_track = track[original_pos_idx]
        try: player_idx_in_actual_stack = current_actual_stack_on_track.index(current_player_obj)
        except ValueError: print(f"CRITICAL ERROR: {current_player_obj.name} not in its cell {original_pos_idx}. Stack: {track[original_pos_idx]}"); return False

    # --- 椿 (Chun) Skill: Moves Alone ---
    if current_player_obj.id == 11 and current_player_obj.chun_moves_alone_this_turn:
        moving_segment = [current_player_obj]
        # Create remaining_in_cell by removing only Chun
        remaining_in_cell = [p for p in current_actual_stack_on_track if p.id != current_player_obj.id]
        current_round_player_actions_log.append(f"{current_player_obj.name}(椿)技能: 单独移动!")
    else:
        moving_segment = current_actual_stack_on_track[:player_idx_in_actual_stack + 1]
        remaining_in_cell = current_actual_stack_on_track[player_idx_in_actual_stack + 1:]
    
    action_log_start += f" 从{original_pos_idx}移{num_steps}格"
    track[original_pos_idx] = remaining_in_cell
    new_logical_pos = original_pos_idx + num_steps

    for p_in_seg in moving_segment: p_in_seg.position = new_logical_pos

    if new_logical_pos >= TRACK_LENGTH:
        action_log_start += f" -> 到达终点!"
        current_round_player_actions_log.append(action_log_start)
        for p_fin in moving_segment:
            if not p_fin.has_finished:
                p_fin.has_finished = True; p_fin.finish_round = current_round
                if p_fin not in winners_podium: winners_podium.append(p_fin)
        game_over = True
        return True
    else:
        final_cell = new_logical_pos % TRACK_LENGTH
        action_log_start_suffix = f" -> 至{final_cell}."
        if current_player_obj.id == 3 and not current_player_obj.cantarella_skill_used_game:
            if track[final_cell]: 
                action_log_start_suffix += " 坎特蕾拉发动技能!"
                current_player_obj.cantarella_skill_used_game = True
        
        track[final_cell] = moving_segment + track[final_cell] 
        for p_in_seg in moving_segment: p_in_seg.position = final_cell
        current_round_player_actions_log.append(action_log_start + action_log_start_suffix)
        return False

def process_single_player_turn(player_obj, is_first, is_last):
    global game_over, current_round_player_actions_log, track, players # players is now SELECTED_PLAYERS_THIS_GAME

    if player_obj.has_finished: return

    action_log_base_prefix = f"{player_obj.name}({player_obj.id})"
    current_turn_skill_log_parts = [] 
    bonus_from_skills_val = 0
    player_obj.chun_moves_alone_this_turn = False # Reset Chun's flag

    # --- 今汐 (Jin Xi) Skill: Move to top of stack ---
    if player_obj.id == 7: # 今汐
        current_stack_jinxi, idx_jinxi = get_player_stack_info(player_obj, track)
        if current_stack_jinxi and idx_jinxi > 0 : # If she's in a stack and not on top
            if random.random() < 0.40:
                current_round_player_actions_log.append(f"{action_log_base_prefix} 今汐技能: 移动到当前堆叠顶部!")
                current_stack_jinxi.pop(idx_jinxi)
                current_stack_jinxi.insert(0, player_obj)
                # No change in player_obj.position, just stack order in track[player_obj.position]

    # --- 卡卡罗 (Kakaluo) Skill: Last place bonus move ---
    if player_obj.id == 9: # 卡卡罗
        if check_is_player_last(player_obj, SELECTED_PLAYERS_THIS_GAME, track):
            current_turn_skill_log_parts.append("卡卡罗垫底奖"); bonus_from_skills_val += 3

    # --- Original Pre-roll skills ---
    if player_obj.id == 4 and player_obj.zanni_potential_next_turn_bonus: # Zanni
        if random.random() < 0.40: current_turn_skill_log_parts.append("赞妮叠后奖"); bonus_from_skills_val += 2
        player_obj.zanni_potential_next_turn_bonus = False
    if player_obj.id == 5 and player_obj.katisia_bonus_active_for_game: # Katisia
        if random.random() < 0.60: current_turn_skill_log_parts.append("卡提西亚永久奖"); bonus_from_skills_val += 2
            
    dice_val = player_obj.roll_dice()
    total_steps_val = dice_val + bonus_from_skills_val # Base steps for first part of move
    current_turn_skill_log_parts.insert(0, f"掷{dice_val}") 

    # --- Skills affecting total_steps (applied to first move segment) ---
    if player_obj.id == 2 and is_first: total_steps_val += 2; current_turn_skill_log_parts.append("布兰特首位奖")
    if player_obj.id == 6 and random.random() < 0.50: total_steps_val += 2; current_turn_skill_log_parts.append("菲比50%奖")
    
    # --- 椿 (Chun) Skill: +1 per other in cell, moves alone ---
    if player_obj.id == 11 and random.random() < 0.50:
        s_chun, _ = get_player_stack_info(player_obj, track)
        if s_chun:
            others_in_cell = len(s_chun) - 1
            if others_in_cell > 0:
                total_steps_val += others_in_cell
                current_turn_skill_log_parts.append(f"椿同格+{others_in_cell}")
            player_obj.chun_moves_alone_this_turn = True # Set flag for execute_move_logic

    move_desc_prefix_for_log = f"{action_log_base_prefix} ({', '.join(current_turn_skill_log_parts)}): "
    
    # --- Main Move Execution (Part 1 for Coletta, or full for others) ---
    if execute_move_logic(player_obj, total_steps_val, move_desc_prefix_for_log): return
    if player_obj.has_finished: return

    # --- 科莱塔 (Coletta) Skill: 28% chance for second move of dice_val steps ---
    if player_obj.id == 12 and random.random() < 0.28:
        current_round_player_actions_log.append(f"{action_log_base_prefix} 科莱塔技能: 再次以骰子步数({dice_val})前进!")
        # Second move does NOT re-trigger per-turn bonuses or Chun's "move alone" if it was set for the first part.
        # It also should not carry people if Chun's skill made her move alone initially.
        # For simplicity, assume Chun's 'move alone' doesn't apply to Coletta's second dash, or Coletta skill takes precedence.
        # Let's assume the second move is standard (carries stack if applicable, unless Chun skill is re-evaluated or persists).
        # To be safe, ensure Chun's flag is off for this second specific move if it's just dice steps.
        original_chun_flag = player_obj.chun_moves_alone_this_turn
        player_obj.chun_moves_alone_this_turn = False # Coletta's second dash is just dice steps
        if execute_move_logic(player_obj, dice_val, f"{action_log_base_prefix} 科莱塔二次移动:"):
            player_obj.chun_moves_alone_this_turn = original_chun_flag # Restore if needed, though turn ends
            return
        player_obj.chun_moves_alone_this_turn = original_chun_flag # Restore if not finished

    if player_obj.has_finished: return # Check again after potential Coletta second move

    # --- Post-move skills ---
    post_move_skill_log_entries = []
    if player_obj.id == 4: # Zanni
        s, _ = get_player_stack_info(player_obj, track)
        if s and len(s) > 1: player_obj.zanni_potential_next_turn_bonus = True; post_move_skill_log_entries.append("赞妮移动后堆叠")
        else: player_obj.zanni_potential_next_turn_bonus = False
    if player_obj.id == 5 and not player_obj.katisia_skill_used_game: # Katisia
        if check_is_player_last(player_obj, SELECTED_PLAYERS_THIS_GAME, track):
            player_obj.katisia_skill_used_game = True; player_obj.katisia_bonus_active_for_game = True
            post_move_skill_log_entries.append("卡提西亚最后激活永久奖")
    # 长离 (Chang Li) Skill: If people below, chance for last move next round
    if player_obj.id == 8:
        s_changli, idx_changli = get_player_stack_info(player_obj, track)
        if s_changli and idx_changli < len(s_changli) - 1: # If not bottom of stack
            player_obj.changli_wants_last_move_next_round = True # Set flag for next round's play_one_full_round
            post_move_skill_log_entries.append("长离脚下有人,下回合可能最后行动")
        else:
            player_obj.changli_wants_last_move_next_round = False


    if post_move_skill_log_entries:
        current_round_player_actions_log.append(f"{action_log_base_prefix} 移动后触发: {', '.join(post_move_skill_log_entries)}.")

    if player_obj.id == 1 and is_last and not player_obj.has_finished: # Rococo
        execute_move_logic(player_obj, 2, f"{player_obj.name}({player_obj.id}) 洛可可末位奖:")


def play_one_full_round():
    global current_round, game_over, current_round_player_actions_log, track, SELECTED_PLAYERS_THIS_GAME

    current_round += 1
    current_round_player_actions_log = [f"--- 回合 {current_round} ({time.strftime('%H:%M:%S')}) ---"]

    active_p_list_for_round = [p for p in SELECTED_PLAYERS_THIS_GAME if not p.has_finished]
    if not active_p_list_for_round:
        current_round_player_actions_log.append("没有可行动的玩家了。")
        game_over = True; return

    # --- 长离 (Chang Li) Skill: Affects move order ---
    eligible_for_last_move = []
    normal_move_order_pool = []
    for p in active_p_list_for_round:
        if p.id == 8 and p.changli_wants_last_move_next_round and random.random() < 0.65:
            eligible_for_last_move.append(p)
            current_round_player_actions_log.append(f"{p.name}(长离)技能触发! 本回合最后行动。")
        else:
            normal_move_order_pool.append(p)
        p.changli_wants_last_move_next_round = False # Reset flag for all

    random.shuffle(normal_move_order_pool)
    random.shuffle(eligible_for_last_move) # Shuffle those who want to be last among themselves
    round_move_order_list = normal_move_order_pool + eligible_for_last_move
    
    current_round_player_actions_log.append(f"本回合移动顺序: {[p.name for p in round_move_order_list]}")

    if current_round == 1:
        current_round_player_actions_log.append(f"注意: 回合1，起始点(格0)堆叠基于本轮实际移动顺序重置。")
        track[0] = list(round_move_order_list) 

    for i, player_to_act_this_turn in enumerate(round_move_order_list):
        if game_over: break
        process_single_player_turn(player_to_act_this_turn, i == 0, i == len(round_move_order_list) - 1)
    
def determine_final_ranking(): # Uses global SELECTED_PLAYERS_THIS_GAME, winners_podium, track
    # (Keep robust version from previous answers)
    current_assigned_rank = 1; final_ranks = []; p_ids_ranked = set()
    for p_win in winners_podium:
        if p_win.id not in p_ids_ranked:
            p_win.rank = current_assigned_rank; final_ranks.append(p_win)
            p_ids_ranked.add(p_win.id); current_assigned_rank += 1
    unfin_details = []
    for p_obj in SELECTED_PLAYERS_THIS_GAME: # Iterate over current game's players
        if p_obj.id not in p_ids_ranked:
            pos_s = p_obj.position if p_obj.position < TRACK_LENGTH else TRACK_LENGTH - 0.1
            stk, dep = get_player_stack_info(p_obj, track)
            dep_s = dep if stk else float('inf')
            unfin_details.append({'p': p_obj, 'pos': pos_s, 'dep': dep_s})
    unfin_details.sort(key=lambda x: (-x['pos'], x['dep'], x['p'].id))
    for entry in unfin_details:
        if entry['p'].id not in p_ids_ranked:
            entry['p'].rank = current_assigned_rank; final_ranks.append(entry['p'])
            p_ids_ranked.add(entry['p'].id); current_assigned_rank += 1
    return final_ranks

# --- Matplotlib Drawing Function (MODIFIED FOR FONT HANDLING) ---
def draw_matplotlib_board_state(current_ax_obj, current_fig_obj, round_num_to_display, current_track_to_draw, 
                                _current_players_list_ref, current_podium_to_draw,
                                list_of_actions_to_log, is_game_over_now):
    global plt, np, font_manager # Ensure font_manager is accessible if used

    if not current_ax_obj or not current_fig_obj or not plt or not np: return

    current_ax_obj.clear()
    cells_per_visual_row = TRACK_LENGTH // NUM_ROWS 
    action_log_panel_x_start = -ACTION_LOG_PANEL_WIDTH 
    track_drawing_actual_offset_x = 0.5 

    # ----------------------------------------------------------------------
    # 获取当前为中文设置的字体属性 (如果已通过 font_manager 设置)
    # 如果 zh_font_prop 是全局的或者可以通过其他方式获取，则使用它
    # global zh_font_prop # 如果 zh_font_prop 在别处定义为全局
    # font_properties_for_chinese = zh_font_prop if 'zh_font_prop' in globals() and zh_font_prop is not None else None
    # 为简化，我们将字体设置的rcParams['font.sans-serif']视为主要方式
    # ----------------------------------------------------------------------

    current_ax_obj.text(action_log_panel_x_start + 0.2, NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) - 0.1, 
                        f"回合 {round_num_to_display} 行动日志:", 
                        fontsize=8, weight='bold', ha='left', va='top', color='black') # fontproperties=font_properties_for_chinese)
    log_display_y_pos = NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) - 0.5
    if list_of_actions_to_log:
        max_log_entries_on_screen = 20
        displayed_logs = 0
        # 从列表末尾开始取（最新的日志），然后在屏幕上从上往下画
        logs_to_display_on_screen = list_of_actions_to_log[-max_log_entries_on_screen:]
        for idx, item_action_log in enumerate(logs_to_display_on_screen):
             current_ax_obj.text(action_log_panel_x_start + 0.2, 
                                 log_display_y_pos - (idx * 0.22), # 从上往下依次递减Y
                                 item_action_log, fontsize=7, ha='left', va='top', color=(0.1,0.1,0.1), 
                                 #family='monospace'
                                 ) # fontproperties=font_properties_for_chinese)
    else:
        current_ax_obj.text(action_log_panel_x_start + 0.2, log_display_y_pos, "等待行动...", 
                            fontsize=6, ha='left', va='top',color=(0.2,0.2,0.2)) # fontproperties=font_properties_for_chinese)
    
    # ... (赛道和玩家的绘制逻辑保持不变，它们使用的是数字或者从PLAYER_DETAILS获取的name[0]) ...
    # 例如，在绘制玩家ID或名字首字时：
    # player_display_name_char = player_obj_to_draw.name[0] ...
    # current_ax_obj.text(..., player_display_name_char, ..., fontproperties=font_properties_for_chinese_small) # 如果需要特定小号中文字体
    # 但通常全局设置的 plt.rcParams['font.sans-serif'] 会对所有文本生效。

    # (绘制赛道格子的代码，与你提供文件中的一致)
    for i in range(TRACK_LENGTH):
        viz_row = 0 if i < cells_per_visual_row else 1
        viz_col_logical = i % cells_per_visual_row
        viz_col_display = (cells_per_visual_row - 1 - viz_col_logical) if viz_row == 1 else viz_col_logical
        cell_x_coord = track_drawing_actual_offset_x + viz_col_display * (CELL_WIDTH_VIZ + 0.1)
        cell_y_coord = viz_row * (CELL_HEIGHT_VIZ + 0.5)
        cell_rect = plt.Rectangle((cell_x_coord, cell_y_coord), CELL_WIDTH_VIZ, CELL_HEIGHT_VIZ, fill=True, color=(0.88,0.88,0.88), ec=(0.4,0.4,0.4))
        current_ax_obj.add_patch(cell_rect)
        current_ax_obj.text(cell_x_coord + CELL_WIDTH_VIZ/2, cell_y_coord + CELL_HEIGHT_VIZ/2, str(i), ha='center', va='center', fontsize=7,color=(0.3,0.3,0.3))
        stack_to_draw_in_cell = current_track_to_draw[i]
        if stack_to_draw_in_cell:
            cell_center_x_for_player = cell_x_coord + CELL_WIDTH_VIZ/2
            cell_top_y_for_stacking_viz = cell_y_coord + CELL_HEIGHT_VIZ
            for stack_idx_from_top, player_obj_to_draw in enumerate(stack_to_draw_in_cell):
                player_center_y_for_draw = cell_top_y_for_stacking_viz - PLAYER_RADIUS_VIZ - (stack_idx_from_top * (PLAYER_RADIUS_VIZ*2 - STACK_OFFSET_Y_VIZ))
                player_draw_color = player_obj_to_draw.viz_color
                player_circle = plt.Circle((cell_center_x_for_player, player_center_y_for_draw), PLAYER_RADIUS_VIZ, color=player_draw_color, ec='black', lw=0.7)
                current_ax_obj.add_patch(player_circle)
                brightness = sum(player_draw_color[:3]) * 255 / 3 
                id_text_color = 'white' if brightness < 128 else 'black'
                player_display_name_char = player_obj_to_draw.name[0] if player_obj_to_draw.name else str(player_obj_to_draw.id)
                current_ax_obj.text(cell_center_x_for_player, player_center_y_for_draw, player_display_name_char,
                                    ha='center', va='center', fontsize=7, color=id_text_color, weight='bold')
    
    # (绘制排行榜的代码，与你提供文件中的一致)
    podium_area_x_start = track_drawing_actual_offset_x + cells_per_visual_row * (CELL_WIDTH_VIZ + 0.1) + 0.5
    current_ax_obj.text(podium_area_x_start, NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) - 0.1, "最终排名:", fontsize=9, weight='bold', color='black')
    for i, p_winner_obj_podium in enumerate(current_podium_to_draw):
        winner_draw_color = p_winner_obj_podium.viz_color
        current_ax_obj.text(podium_area_x_start, NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) - 0.5 - (i*0.35),
                            f"{p_winner_obj_podium.rank}. {p_winner_obj_podium.name} (R:{p_winner_obj_podium.finish_round})", 
                            fontsize=7, color=winner_draw_color) # Matplotlib text color is flexible
    
    # (设置标题和坐标轴限制的代码，与你提供文件中的一致)
    current_ax_obj.set_title(f"当前回合: {round_num_to_display}", fontsize=12)
    current_ax_obj.set_xlim(action_log_panel_x_start - 0.2, podium_area_x_start + 3.5) 
    current_ax_obj.set_ylim(-0.5, NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5) + 0.5)
    current_ax_obj.set_aspect('equal', adjustable='box')
    current_ax_obj.axis('off')
    if is_game_over_now:
        current_ax_obj.text( (podium_area_x_start + track_drawing_actual_offset_x - ACTION_LOG_PANEL_WIDTH) / 2 , 
                             (NUM_ROWS * (CELL_HEIGHT_VIZ + 0.5)) / 2,
                             "游戏结束!", ha='center', va='center', fontsize=28, color='darkred', weight='heavy',
                             bbox=dict(facecolor='gold', alpha=0.7, boxstyle='round,pad=0.6'))
    if current_fig_obj: current_fig_obj.canvas.draw_idle()


def run_single_simulation_for_auto_frames(selected_ids_for_game, specific_frames_dir_param, suppress_all_prints_param=False):
    """
    运行一次游戏模拟，并为可视化运行保存Matplotlib帧图像。
    参数:
        selected_ids_for_game (list): 本次模拟要使用的玩家ID列表。
        specific_frames_dir_param (str): 用于保存该次运行帧图像的特定目录路径。
        suppress_all_prints_param (bool): 是否抑制控制台打印（除了错误和关键的可视化信息）。
    返回:
        list: 按最终排名排序的玩家对象列表。
    """
    # 引用在 test.py 中定义的全局变量
    global game_over, current_round, FIG, AX, plt, np 
    global current_round_player_actions_log, track, SELECTED_PLAYERS_THIS_GAME, winners_podium

    # 步骤1: 使用选定的角色ID重置核心游戏逻辑状态
    initialize_game_state_logic_only(selected_ids_for_game) 
    
    # 步骤2: 为本次可视化运行尝试初始化Matplotlib
    # initialize_matplotlib_for_auto_frames 是在 test.py 中定义的辅助函数
    # 它会设置全局的 FIG, AX, plt, np, 并创建目录
    can_visualize_this_run = initialize_matplotlib_for_auto_frames(specific_frames_dir_param)

    if can_visualize_this_run:
        # draw_matplotlib_board_state 是在 test.py 中的主要绘图函数
        # 它使用全局的 AX, FIG, current_round, track, SELECTED_PLAYERS_THIS_GAME (即这里的 players), 等.
        # 绘制初始状态 (回合0)
        draw_matplotlib_board_state(AX, FIG, 0, track, SELECTED_PLAYERS_THIS_GAME, winners_podium, 
                                    current_round_player_actions_log, False) 
        try:
            FIG.savefig(os.path.join(specific_frames_dir_param, f"round_{0:03d}_initial.png"), dpi=150)
        except Exception as e:
            print(f"保存初始帧时出错: {e}")
    elif not suppress_all_prints_param: # 如果可视化设置失败，但我们没有被要求完全静默
        print(f"警告: Matplotlib初始化失败，运行 '{specific_frames_dir_param}' 的可视化将不产生图片。")

    max_simulation_rounds = 200 # 防止无限循环的安全上限
    while not game_over and current_round < max_simulation_rounds:
        play_one_full_round() # 这个函数负责一回合的完整逻辑并更新全局状态

        if can_visualize_this_run: # 只有在Matplotlib成功初始化时才绘图和保存
            draw_matplotlib_board_state(AX, FIG, current_round, track, SELECTED_PLAYERS_THIS_GAME, winners_podium, 
                                        current_round_player_actions_log, game_over)
            try:
                FIG.savefig(os.path.join(specific_frames_dir_param, f"round_{current_round:03d}_end.png"), dpi=150)
            except Exception as e:
                print(f"保存回合 {current_round} 帧时出错: {e}")

        # 为非可视化（或可视化失败）的运行提供一些控制台进度反馈（如果不抑制打印）
        if not suppress_all_prints_param and not can_visualize_this_run:
            if current_round % 20 == 0: 
                print(f"  (模拟中回合(无图): {current_round})")
            
    final_player_rankings = determine_final_ranking() # 这个函数操作全局状态并返回排名列表

    if can_visualize_this_run: # 如果可视化成功初始化
        # 绘制并保存最终的 "游戏结束" 画面
        draw_matplotlib_board_state(AX, FIG, current_round, track, SELECTED_PLAYERS_THIS_GAME, final_player_rankings, 
                                    current_round_player_actions_log, True) # is_game_over_now = True
        try:
            FIG.savefig(os.path.join(specific_frames_dir_param, f"game_over_final_{current_round:03d}.png"), dpi=150)
        except Exception as e:
            print(f"保存最终 '游戏结束' 图片时出错: {e}")
        
        if plt and FIG: # 清理Matplotlib资源
            plt.close(FIG)
            # 重置Matplotlib相关的全局变量，以便下次（如果需要）可以重新初始化
            FIG, AX, plt, np = None, None, None, None 
    
    return final_player_rankings


    # --- Functions for Auto Frame Saving & Interactive Mode ---
def _setup_matplotlib_fonts():
    """尝试设置Matplotlib以正确显示中文字符。"""
    global plt, font_manager # 确保可以访问到已导入的模块

    if not plt or not font_manager:
        print("警告: Matplotlib 或 font_manager 未在 _setup_matplotlib_fonts 中正确初始化。")
        return

    try:
        # 尝试的常见中文字体列表 (Windows, macOS, Linux)
        # 你可以根据你的操作系统和已安装字体调整这个列表的顺序或内容
        # 确保列表中的至少一个字体是你系统上实际安装的
        common_chinese_fonts = [
            'SimHei',             # 黑体 (Windows上常见且通常有效)
            'Microsoft YaHei',    # 微软雅黑 (Windows)
            'PingFang SC',        # 苹方-简 (macOS)
            'STHeiti',            # 华文黑体 (macOS)
            'WenQuanYi Zen Hei',  # 文泉驿正黑 (Linux)
            'Noto Sans CJK SC',   # Google Noto 思源宋体/黑体
            'Arial Unicode MS'    # 一个比较全的Unicode字体，但不一定美观
        ]
        
        # 方式一：通过rcParams设置sans-serif字体族
        # Matplotlib 会按顺序尝试列表中的字体，直到找到一个可用的
        plt.rcParams['font.sans-serif'] = common_chinese_fonts + plt.rcParams['font.sans-serif']
        # plt.rcParams['font.family'] = 'sans-serif' # 有时也需要明确指定使用sans-serif族
        plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

        # ------------------ 调试信息：检查实际使用的字体 ------------------
        # 你可以取消下面几行的注释来帮助调试，看看Matplotlib最终选用了哪个字体
        # current_font_family_list = plt.rcParams['font.sans-serif']
        # print(f"[调试] Matplotlib 将尝试的字体列表: {current_font_family_list}")
        # try:
        #     # 尝试获取列表中的第一个字体（Matplotlib的优先选择）
        #     font_prop = font_manager.FontProperties(family=current_font_family_list[0])
        #     actual_font_name = font_prop.get_name()
        #     print(f"[调试] Matplotlib 实际解析到的首选字体可能是: '{actual_font_name}'")
        #     if not any(common_name.lower() in actual_font_name.lower() for common_name in common_chinese_fonts):
        #         print(f"[调试] 警告: Matplotlib选择的字体 '{actual_font_name}' 可能不是我们期望的中文字体。")
        # except RuntimeError: # 如果连第一个字体都找不到或无法解析
        #     print(f"[调试] 警告: Matplotlib无法解析首选字体 '{current_font_family_list[0]}'")
        # print("已尝试通过名称列表设置中文字体。")
        # ---------------------------------------------------------------

    except Exception as e:
        print(f"设置Matplotlib中文字体时发生错误: {e}")
        print("请尝试以下操作：")
        print("1. 确保你的系统中安装了至少一种上述列表中的中文字体。")
        print("2. 尝试直接在代码中指定字体文件的绝对路径（见下一种方法）。")
        print("3. 如果问题依旧，尝试清除Matplotlib的字体缓存。")

def initialize_matplotlib_for_auto_frames(specific_dir_for_frames):
    global FIG, AX, plt, np, font_manager # font_manager 需要在这里声明为全局以便 _setup_matplotlib_fonts 能访问
    try:
        import matplotlib.pyplot as plt_module
        import numpy as np_module
        import matplotlib.font_manager as fm_module # 确保导入
        globals()['plt'] = plt_module
        globals()['np'] = np_module
        globals()['font_manager'] = fm_module # 赋值给全局变量

        _setup_matplotlib_fonts() # <--- 调用字体设置

        if FIG: plt.close(FIG) 
        FIG, AX = plt.subplots(figsize=(19, 7)) # 调整figsize以适应左侧信息面板
        if not os.path.exists(specific_dir_for_frames): os.makedirs(specific_dir_for_frames)
        return True
    except ImportError:
        print("错误: Matplotlib或Numpy未安装，无法进行可视化帧保存。")
        return False
    except Exception as e: 
        print(f"Matplotlib (auto_frames) 初始化失败: {e}")
        return False

def run_interactive_visualization(selected_ids_for_game):
    global FIG, AX, plt, np, current_display_round_index, font_manager # font_manager 需要在这里声明为全局
    
    if not pre_calculate_all_round_states_for_interactive_view(selected_ids_for_game):
        print("未能预计算回合状态。"); return
    try: 
        import matplotlib.pyplot as plt_module
        import numpy as np_module
        import matplotlib.font_manager as fm_module # 确保导入
        globals()['plt'] = plt_module; globals()['np'] = np_module
        globals()['font_manager'] = fm_module # 赋值给全局变量
        
        _setup_matplotlib_fonts() # <--- 调用字体设置

        if FIG: plt.close(FIG) 
        FIG, AX = plt.subplots(figsize=(19, 7)) 
    except ImportError:
        print("错误: Matplotlib或Numpy未安装，无法进行交互式可视化。")
        return
    except Exception as e: 
        print(f"Matplotlib (interactive) 初始化错误: {e}"); return

    # ... (run_interactive_visualization 函数的其余部分，与你提供的文件一致) ...
    FIG.canvas.mpl_connect('key_press_event', on_key_press_interactive)
    current_display_round_index = 0 
    if all_round_states:
        state_to_display_initially = all_round_states[current_display_round_index]
        draw_matplotlib_board_state(AX, FIG, state_to_display_initially['round_num'], 
                                    state_to_display_initially['track'], state_to_display_initially['players_in_game'],
                                    state_to_display_initially['winners_podium'], 
                                    state_to_display_initially['player_actions_log'], 
                                    state_to_display_initially['is_game_over_at_this_point'])
        print("交互式查看器已启动。使用左右箭头键翻页，Home键到首页，End键到底页。关闭窗口结束。")
        plt.show() 
    else: print("没有可供显示的回合数据。")
    FIG, AX, plt, np, font_manager = None, None, None, None, None


def pre_calculate_all_round_states_for_interactive_view(selected_ids_for_game):
    # (Keep version from previous, ensure it calls initialize_game_state_logic_only(selected_ids_for_game))
    # And ensure deepcopy logic for players in track/podium is robust.
    global all_round_states, game_over, current_round, current_round_player_actions_log, track, SELECTED_PLAYERS_THIS_GAME, winners_podium
    
    initialize_game_state_logic_only(selected_ids_for_game)
    all_round_states = []
    all_round_states.append({
        'round_num': 0, 'track': copy.deepcopy(track), 
        'players_in_game': copy.deepcopy(SELECTED_PLAYERS_THIS_GAME), # Store the actual player objects used
        'winners_podium': copy.deepcopy(winners_podium),
        'player_actions_log': list(current_round_player_actions_log),
        'is_game_over_at_this_point': False
    })
    # ... (rest of pre-calculation loop, same as your last full test.py, using deepcopy correctly) ...
    max_interactive_sim_rounds = 200
    while not game_over and current_round < max_interactive_sim_rounds:
        play_one_full_round() 
        copied_player_list_state = [copy.deepcopy(p) for p in SELECTED_PLAYERS_THIS_GAME]
        player_id_to_copied_player_map = {p_orig.id: p_copy for p_orig, p_copy in zip(SELECTED_PLAYERS_THIS_GAME, copied_player_list_state)}
        copied_track_for_state = []
        for original_cell_stack in track:
            copied_cell_stack_list = [player_id_to_copied_player_map[p.id] for p in original_cell_stack if p.id in player_id_to_copied_player_map]
            copied_track_for_state.append(copied_cell_stack_list)
        copied_podium_for_state = [player_id_to_copied_player_map[p.id] for p in winners_podium if p.id in player_id_to_copied_player_map]
        
        # For interactive mode, we need the final ranking in each state if game is over
        final_ranks_for_this_state = []
        if game_over:
            # To get ranks for this *specific copied state*, we'd ideally run determine_final_ranking
            # on the copied_player_list_state, copied_track_for_state, copied_podium_for_state.
            # For now, let's assume determine_final_ranking on global state before copy is enough for podium.
            # Or pass the copied lists to determine_final_ranking if it's adapted.
            # Simpler: just copy the globally determined podium which has ranks.
            for p_ranked_global in winners_podium: # Assuming this podium is ranked
                if p_ranked_global.id in player_id_to_copied_player_map:
                     # find corresponding copied player and update its rank
                    player_id_to_copied_player_map[p_ranked_global.id].rank = p_ranked_global.rank
            # This part is tricky; `determine_final_ranking` modifies global `players` list's ranks.
            # A cleaner way is for determine_final_ranking to take players_list, podium, track as params and return ranked list of COPIES.
            # For now, the podium copy will have whatever ranks were set globally.

        all_round_states.append({
            'round_num': current_round, 'track': copied_track_for_state, 
            'players_in_game': copied_player_list_state, 
            'winners_podium': copied_podium_for_state, # This reflects ranked players if game ended
            'player_actions_log': list(current_round_player_actions_log), 
            'is_game_over_at_this_point': game_over
        })
        if game_over: break
    return bool(all_round_states)

def on_key_press_interactive(event):
    # (Keep version from previous full test.py)
    global current_display_round_index, all_round_states, FIG, AX 
    if not all_round_states or not FIG or not event.key: return
    if event.key == 'right': current_display_round_index = min(len(all_round_states) - 1, current_display_round_index + 1)
    elif event.key == 'left': current_display_round_index = max(0, current_display_round_index - 1)
    elif event.key == 'home': current_display_round_index = 0
    elif event.key == 'end': current_display_round_index = len(all_round_states) -1
    else: return 
    state_to_display = all_round_states[current_display_round_index]
    draw_matplotlib_board_state(AX, FIG, state_to_display['round_num'], state_to_display['track'],
                                state_to_display['players_in_game'], state_to_display['winners_podium'],
                                state_to_display['player_actions_log'], state_to_display['is_game_over_at_this_point'])


def run_interactive_visualization(selected_ids_for_game):
    # (Keep version from previous, ensure it calls pre_calculate_all_round_states_for_interactive_view(selected_ids_for_game))
    global FIG, AX, plt, np, current_display_round_index 
    if not pre_calculate_all_round_states_for_interactive_view(selected_ids_for_game):
        print("未能预计算回合状态。"); return
    try: 
        import matplotlib.pyplot as plt_module; import numpy as np_module
        globals()['plt'] = plt_module; globals()['np'] = np_module
        plt.rcParams['font.sans-serif'] = ['SimHei']; plt.rcParams['axes.unicode_minus'] = False
        if FIG: plt.close(FIG) 
        FIG, AX = plt.subplots(figsize=(19, 7)) 
    except Exception as e: print(f"Matplotlib (interactive) 初始化错误: {e}"); return
    FIG.canvas.mpl_connect('key_press_event', on_key_press_interactive)
    current_display_round_index = 0 
    if all_round_states:
        state_to_display_initially = all_round_states[current_display_round_index]
        draw_matplotlib_board_state(AX, FIG, state_to_display_initially['round_num'], 
                                    state_to_display_initially['track'], state_to_display_initially['players_in_game'],
                                    state_to_display_initially['winners_podium'], 
                                    state_to_display_initially['player_actions_log'], 
                                    state_to_display_initially['is_game_over_at_this_point'])
        print("交互式查看器已启动。使用左右箭头键翻页，Home键到首页，End键到底页。关闭窗口结束。")
        plt.show() 
    else: print("没有可供显示的回合数据。")
    FIG, AX, plt, np = None, None, None, None


def run_simulation_logic_only(selected_ids_for_game, suppress_all_prints=True):
    """
    运行一次纯游戏逻辑模拟，不涉及任何Matplotlib绘图。
    设计用于快速批量运行。
    参数:
        selected_ids_for_game (list): 本次模拟要使用的玩家ID列表。
        suppress_all_prints (bool): 是否抑制除错误外的所有控制台打印。
    返回:
        list: 按最终排名排序的玩家对象列表。
    """
    global game_over, current_round # 引用 test.py 中的全局游戏状态变量
    
    # 使用选定的角色ID初始化游戏状态
    # initialize_game_state_logic_only 函数现在需要接受 selected_ids_for_game
    initialize_game_state_logic_only(selected_ids_for_game) 

    max_sim_rounds = 200 # 防止无限循环的安全上限
    while not game_over and current_round < max_sim_rounds:
        play_one_full_round() # 这个函数负责一回合的完整逻辑并更新全局状态
        
        # 为长时间的批量运行提供最少的进度反馈（如果未抑制打印）
        if not suppress_all_prints:
            if current_round % 50 == 0: 
                sys.stdout.write('.') # 打印一个点
                sys.stdout.flush()    # 立即刷新输出
    
    # 确保在循环结束后换行（如果打印了进度点）
    if not suppress_all_prints and current_round > 0 and (current_round % 50 != 0 or game_over):
        sys.stdout.write('\n')
        
    return determine_final_ranking()


# --- Character Selection UI (Command Line) ---
def select_characters_cli():
    """Allows user to select 6 characters from the available list via command line."""
    print("\n--- 角色选择 ---")
    print("可用角色:")
    for char_id, details in PLAYER_DETAILS.items():
        print(f"  ID: {char_id} - {details['name']}")
    
    selected_ids = []
    while len(selected_ids) < DEFAULT_NUM_SELECTED_PLAYERS:
        try:
            prompt = f"请选择第 {len(selected_ids) + 1}/{DEFAULT_NUM_SELECTED_PLAYERS} 位角色 (输入ID): "
            choice = int(input(prompt))
            if choice not in PLAYER_DETAILS:
                print(f"无效的ID: {choice}。请输入列表中的ID。")
            elif choice in selected_ids:
                print(f"角色ID {choice} ({PLAYER_DETAILS[choice]['name']}) 已被选择，请选择其他角色。")
            else:
                selected_ids.append(choice)
                print(f"已选择: {PLAYER_DETAILS[choice]['name']}")
        except ValueError:
            print("无效输入，请输入数字ID。")
            
    print("\n你选择的参赛角色ID为:", selected_ids)
    return selected_ids

# 在 test.py 的末尾
# 在 test.py 的末尾

if __name__ == "__main__":
    print("--- [test.py] 启动 ---")
    
    # 首先调用角色选择函数
    selected_character_ids = select_characters_cli() 
    
    # DEFAULT_NUM_SELECTED_PLAYERS 应该是在 test.py 的常量部分定义的
    num_expected_players = DEFAULT_NUM_SELECTED_PLAYERS # <--- 修改在这里

    if selected_character_ids and len(selected_character_ids) == num_expected_players:
        # PLAYER_DETAILS 也是在 test.py 中定义的全局常量
        print(f"\n将使用选择的角色运行交互式可视化: {[PLAYER_DETAILS[pid]['name'] for pid in selected_character_ids]}")
        # 使用选定的角色ID启动交互式可视化
        run_interactive_visualization(selected_character_ids) 
    else:
        print(f"角色选择未完成或选择数量不等于 {num_expected_players}。交互式可视化已取消。")

    print("\n--- [test.py] 运行结束 ---")