# batch_runner.py
import os
import csv
import time 
import random # 用于为排名起点模式生成“虚拟”排名（如果用户不手动输入）

try:
    import test # 导入你的 test.py 文件
except ImportError:
    print("错误：无法导入 'test.py'。请确保该文件与 batch_runner.py 在同一目录下，或者在 PYTHONPATH 中。")
    exit()
except AttributeError as e:
    print(f"导入 'test.py' 时发生 AttributeError: {e}")
    print("这可能意味着 'test.py' 中的某些顶层定义缺失或名称不正确（比如 Player 类或 PLAYER_DETAILS）。")
    exit()

def get_manual_ranks_for_selected_players(selected_ids_for_ranking):
    """
    允许用户为选定的角色手动输入排名顺序。
    参数:
        selected_ids_for_ranking (list): 已选定的角色ID列表。
    返回:
        list: 按手动指定名次排序的Player对象列表 (包含rank属性)，如果输入无效或用户跳过则返回None。
    """
    print("\n--- 为“排名起点”模式手动设定固定排名 ---")
    print("请为以下已选角色指定名次顺序（第1名最先输入，以此类推）。")
    
    # 创建一个 id -> name 的映射方便显示
    id_to_name_map = {pid: test.PLAYER_DETAILS[pid]["name"] for pid in selected_ids_for_ranking}
    print(f"当前已选角色: {[(pid, name) for pid, name in id_to_name_map.items()]}")

    ranked_player_objects = []
    input_ids_ordered = []
    
    for i in range(len(selected_ids_for_ranking)):
        while True:
            try:
                prompt = f"请输入第 {i+1} 名的角色ID (从上述已选角色中选择): "
                chosen_id_for_rank = int(input(prompt))
                if chosen_id_for_rank not in selected_ids_for_ranking:
                    print(f"错误：ID {chosen_id_for_rank} 不是本次模拟选定的角色之一。请重新输入。")
                elif chosen_id_for_rank in input_ids_ordered:
                    print(f"错误：ID {chosen_id_for_rank} ({id_to_name_map[chosen_id_for_rank]}) 已被指定过名次。请为其他角色指定名次。")
                else:
                    input_ids_ordered.append(chosen_id_for_rank)
                    # 创建一个临时的Player对象或包含必要信息的字典来传递排名
                    # Player对象更符合 first_race_ranks_data 的预期结构
                    # 注意：这里我们只需要ID和rank属性用于初始化，不需要完整的游戏状态Player对象
                    temp_p = test.Player(chosen_id_for_rank) # 使用test.py中的Player类
                    temp_p.rank = i + 1 # 赋予手动指定的排名
                    ranked_player_objects.append(temp_p)
                    print(f"第 {i+1} 名已指定为: {id_to_name_map[chosen_id_for_rank]} (ID: {chosen_id_for_rank})")
                    break 
            except ValueError:
                print("无效输入，请输入数字ID。")
            except KeyError: # 万一PLAYER_DETAILS有问题
                print("错误：查找角色信息时出错。")
                return None # 表示获取失败

    if len(ranked_player_objects) == len(selected_ids_for_ranking):
        print(f"\n已手动设定固定排名: {[f'{p.rank}.{test.PLAYER_DETAILS[p.id]['log_name']}' for p in ranked_player_objects]}")
        return ranked_player_objects
    else:
        print("手动排名设置未完成。")
        return None


def batch_simulate_and_analyze(num_simulations=10000, 
                               visualize_run_idx=None, 
                               selected_ids_for_simulation=None,
                               start_method_for_batch="normal",       # 新增参数
                               ranks_for_batch_ranked_start=None): # 新增参数
    """
    执行批量游戏模拟，统计胜率，并选择性地保存一次模拟的可视化过程。
    使用选定的角色和起点模式进行模拟。
    """
    if selected_ids_for_simulation is None or len(selected_ids_for_simulation) != test.DEFAULT_NUM_SELECTED_PLAYERS:
        num_expected = getattr(test, 'DEFAULT_NUM_SELECTED_PLAYERS', 6)
        print(f"错误: 需要提供 {num_expected} 个选定的角色ID。当前提供: {selected_ids_for_simulation}")
        return

    selected_player_names_for_log = [test.PLAYER_DETAILS[pid]["log_name"] for pid in selected_ids_for_simulation]
    print(f"\n开始进行 {num_simulations} 次模拟...")
    print(f"使用角色: {', '.join(selected_player_names_for_log)} (IDs: {selected_ids_for_simulation})")
    print(f"起点模式: {'标准起点' if start_method_for_batch == 'normal' else '排名起点'}")
    if start_method_for_batch == "ranked_start":
        if ranks_for_batch_ranked_start:
            print(f"排名起点模式使用的固定排名: {[f'{p.rank}.{test.PLAYER_DETAILS[p.id]['log_name']}' for p in ranks_for_batch_ranked_start]}")
        else:
            print("警告: 选择了排名起点模式，但未提供排名数据，模拟可能按标准起点进行或在test.py中回退。")
    
    batch_start_time = time.time()
    # 胜率统计针对所有12个角色，即使它们没有全部参与（未参与的胜率为0）
    win_counts = {player_id: 0 for player_id in test.PLAYER_DETAILS} 

    base_visualization_dir = getattr(test, 'FRAMES_DIRECTORY_BASE', 'default_simulation_frames')
    # 为可视化运行创建一个能反映起点模式的子文件夹名
    viz_subfolder_name = f"batch_viz_{start_method_for_batch}_mode"
    visualization_run_output_dir = os.path.join(base_visualization_dir, viz_subfolder_name)

    for i in range(num_simulations):
        is_this_the_visual_run = (i == visualize_run_idx)
        ranked_results = None

        if is_this_the_visual_run:
            print(f"\n--- [第 {i+1}/{num_simulations} 次模拟 (保存可视化帧至 '{os.path.abspath(visualization_run_output_dir)}') ({time.strftime('%Y-%m-%d %H:%M:%S')})] ---")
            if not os.path.exists(visualization_run_output_dir):
                os.makedirs(visualization_run_output_dir)
            
            ranked_results = test.run_single_simulation_for_auto_frames(
                selected_ids_for_game=selected_ids_for_simulation,
                start_method_param=start_method_for_batch,               
                first_race_ranks_data_param=ranks_for_batch_ranked_start, 
                specific_frames_dir_param=visualization_run_output_dir,
                suppress_all_prints_param=False 
            )
            print(f"--- [第 {i+1}/{num_simulations} 次模拟 (可视化) 完成] ---")
        else:
            ranked_results = test.run_simulation_logic_only(
                selected_ids_for_game=selected_ids_for_simulation,
                start_method_param=start_method_for_batch,               
                first_race_ranks_data_param=ranks_for_batch_ranked_start, 
                suppress_all_prints=True 
            )

        if ranked_results and ranked_results[0].rank == 1:
            winner_id = ranked_results[0].id
            if winner_id in win_counts: win_counts[winner_id] += 1
        
        if (i + 1) % (num_simulations // 20 if num_simulations >= 20 else 1) == 0 or i == num_simulations - 1:
            current_batch_run_time = time.time() - batch_start_time
            print(f"已完成 {i + 1}/{num_simulations} 次模拟... (总用时: {current_batch_run_time:.2f} 秒)")

    total_batch_run_time = time.time() - batch_start_time
    avg_time_per_sim = total_batch_run_time / num_simulations if num_simulations > 0 else 0
    print(f"\n--- 所有 {num_simulations} 次模拟完成，总用时: {total_batch_run_time:.2f} 秒 ({avg_time_per_sim:.3f} 秒/次) ---")

    print("\n--- 玩家胜率统计 (基于所有角色池) ---")
    table_data_for_csv = [["玩家ID", "玩家名称", "是否参与本次批量模拟", "起点模式", "获胜次数", f"总模拟次数 ({num_simulations})", "胜率 (%)"]]
    for player_id_key_csv in test.PLAYER_DETAILS: 
        p_name_csv = test.PLAYER_DETAILS[player_id_key_csv]["name"]
        is_selected_csv = "是" if player_id_key_csv in selected_ids_for_simulation else "否"
        wins_csv = win_counts.get(player_id_key_csv, 0)
        rate_csv = (wins_csv / num_simulations) * 100 if num_simulations > 0 else 0
        print(f"{p_name_csv} (ID: {player_id_key_csv}): 获胜 {wins_csv} 次, 胜率 {rate_csv:.2f}% (参与:{is_selected_csv}, 起点模式:{start_method_for_batch})")
        table_data_for_csv.append([player_id_key_csv, p_name_csv, is_selected_csv, start_method_for_batch, wins_csv, num_simulations, f"{rate_csv:.2f}"])

    csv_filename = f"game_win_report_batch_{start_method_for_batch}.csv" #文件名包含起点模式
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csv_output_file:
            csv_writer_obj = csv.writer(csv_output_file)
            csv_writer_obj.writerows(table_data_for_csv)
        print(f"\n胜率报告已保存到: {os.path.abspath(csv_filename)}")
    except IOError as e_io: print(f"\n保存CSV文件 {csv_filename} 时出错: {e_io}")
    except Exception as e_gen_csv: print(f"\n保存CSV时发生一般错误: {e_gen_csv}")


if __name__ == "__main__":
    # 1. 从 test.py 调用函数进行角色选择
    print("启动角色选择流程 (定义在 test.py)...")
    chosen_player_ids = test.select_characters_cli() 

    num_expected = getattr(test, 'DEFAULT_NUM_SELECTED_PLAYERS', 6)
    if chosen_player_ids and len(chosen_player_ids) == num_expected:
        # 2. 从 test.py 调用函数进行起点模式选择
        chosen_start_method = test.select_start_method_cli() # 此函数现在只返回模式字符串
        
        fixed_ranks_for_batch = None # 用于存储手动设定的、用于本批次所有“排名起点”模拟的排名
        if chosen_start_method == "ranked_start":
            # 为“排名起点”模式获取一次固定的手动排名
            use_manual_ranks_choice = input("是否为本批次的“排名起点”模拟手动设定一个固定排名? (是[y]/否[n]，否将使用随机虚拟排名): ").lower()
            if use_manual_ranks_choice == 'y' or use_manual_ranks_choice == '是':
                fixed_ranks_for_batch = get_manual_ranks_for_selected_players(chosen_player_ids)
                if not fixed_ranks_for_batch:
                    print("手动设定固定排名失败，将对每次“排名起点”模拟使用随机虚拟排名。")
            else:
                print("将对每次“排名起点”模拟使用随机虚拟排名（在test.py内部生成）。")
            # 如果 fixed_ranks_for_batch 仍然是 None, test.py 中的 initialize_game_state_logic_only
            # 在 start_method="ranked_start" 且 first_race_ranks_data=None 时，应该有其自己的回退逻辑
            # (例如，内部生成随机排名或报错)。
            # 为了让批量测试中的“排名起点”有意义，最好是提供一个固定的“上一局”排名。
            # 如果用户选择不手动设定，我们可以为整个批次生成一次随机排名。
            if chosen_start_method == "ranked_start" and not fixed_ranks_for_batch: # 如果没手动设且是排名模式
                print("为本批次所有“排名起点”模拟生成一次固定的随机虚拟排名...")
                temp_players = [test.Player(pid) for pid in chosen_player_ids]
                random.shuffle(temp_players)
                fixed_ranks_for_batch = []
                for r_idx, p_obj in enumerate(temp_players):
                    p_obj.rank = r_idx + 1
                    fixed_ranks_for_batch.append(p_obj)
                print(f"本批次“排名起点”将使用此虚拟排名: {[f'{p.rank}.{test.PLAYER_DETAILS[p.id]['log_name']}' for p in fixed_ranks_for_batch]}")


        # 3. 进行批量模拟
        SIM_COUNT_TOTAL = 100000  # 测试时可适当减少次数
        VISUALIZE_RUN_AT_INDEX = SIM_COUNT_TOTAL - 1 
        # VISUALIZE_RUN_AT_INDEX = None 

        batch_simulate_and_analyze(
            num_simulations=SIM_COUNT_TOTAL, 
            visualize_run_idx=VISUALIZE_RUN_AT_INDEX,
            selected_ids_for_simulation=chosen_player_ids,
            start_method_for_batch=chosen_start_method,             # <--- 传递起点模式
            ranks_for_batch_ranked_start=fixed_ranks_for_batch    # <--- 传递排名数据
        )
    else:
        print(f"角色选择未完成或选择数量不等于 {num_expected}。批量模拟已取消。")