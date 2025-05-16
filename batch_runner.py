# batch_runner.py
import os
import csv
import time 

try:
    import test # 导入你的 test.py 文件
except ImportError:
    print("错误：无法导入 'test.py'。请确保该文件与 batch_runner.py 在同一目录下，或者在 PYTHONPATH 中。")
    exit()
except AttributeError as e:
    print(f"导入 'test.py' 时发生 AttributeError: {e}")
    print("这可能意味着 'test.py' 中的某些顶层定义缺失或名称不正确。")
    exit()

def batch_simulate_and_analyze(num_simulations=10000, visualize_run_idx=None, selected_ids_for_simulation=None):
    """
    执行批量游戏模拟，统计胜率，并选择性地保存一次模拟的可视化过程。
    现在使用选定的角色进行模拟。
    """
    if selected_ids_for_simulation is None or len(selected_ids_for_simulation) != test.DEFAULT_NUM_SELECTED_PLAYERS:
        # DEFAULT_NUM_SELECTED_PLAYERS 应该在 test.py 中定义
        num_expected = getattr(test, 'DEFAULT_NUM_SELECTED_PLAYERS', 6)
        print(f"错误: 需要提供 {num_expected} 个选定的角色ID。当前提供: {selected_ids_for_simulation}")
        return

    selected_player_names = [test.PLAYER_DETAILS[pid]["name"] for pid in selected_ids_for_simulation]
    print(f"\n开始进行 {num_simulations} 次模拟，使用选定角色: {', '.join(selected_player_names)} (IDs: {selected_ids_for_simulation})")
    batch_start_time = time.time()

    # 胜率统计将针对所有可能的角色，但只有选中的角色才会有非零的获胜次数
    win_counts = {player_id: 0 for player_id in test.PLAYER_DETAILS} # 统计所有12个角色

    base_visualization_dir = getattr(test, 'FRAMES_DIRECTORY_BASE', 'default_simulation_frames')
    visualization_run_output_dir = os.path.join(base_visualization_dir, "batch_visualized_run_selected_chars")

    for i in range(num_simulations):
        is_this_the_visual_run = (i == visualize_run_idx)
        current_sim_start_time = time.time()
        ranked_results = None

        if is_this_the_visual_run:
            print(f"\n--- [第 {i+1}/{num_simulations} 次模拟 (保存可视化帧至 '{os.path.abspath(visualization_run_output_dir)}') ({time.strftime('%Y-%m-%d %H:%M:%S')})] ---")
            if not os.path.exists(visualization_run_output_dir):
                os.makedirs(visualization_run_output_dir)
            
            # 调用 test.py 中的带可视化帧保存的模拟函数
            # **确保 test.py 中的这个函数签名已更新为接受 selected_ids_for_game**
            ranked_results = test.run_single_simulation_for_auto_frames(
                selected_ids_for_game=selected_ids_for_simulation, # <--- 传递选定的角色
                specific_frames_dir_param=visualization_run_output_dir,
                suppress_all_prints_param=False 
            )
            print(f"--- [第 {i+1}/{num_simulations} 次模拟 (可视化) 完成，用时: {time.time() - current_sim_start_time:.2f} 秒] ---")
        else:
            # 对于非可视化运行，调用纯逻辑模拟函数
            # **确保 test.py 中的这个函数签名已更新为接受 selected_ids_for_game**
            ranked_results = test.run_simulation_logic_only(
                selected_ids_for_game=selected_ids_for_simulation, # <--- 传递选定的角色
                suppress_all_prints=True 
            )

        if ranked_results:
            if ranked_results[0].rank == 1: 
                winner_id = ranked_results[0].id
                if winner_id in win_counts:
                    win_counts[winner_id] += 1
                else:
                    print(f"警告: 获胜者ID {winner_id} 在 PLAYER_DETAILS 中未定义。") 
        else:
            print(f"警告: 模拟 {i+1} 未返回有效结果。")

        if (i + 1) % (num_simulations // 20 if num_simulations >= 20 else 1) == 0 or i == num_simulations - 1:
            current_batch_time = time.time() - batch_start_time
            print(f"已完成 {i + 1}/{num_simulations} 次模拟... (总用时: {current_batch_time:.2f} 秒)")

    total_batch_time = time.time() - batch_start_time
    print(f"\n--- 所有 {num_simulations} 次模拟完成，总用时: {total_batch_time:.2f} 秒 ({total_batch_time/num_simulations if num_simulations > 0 else 0:.3f} 秒/次) ---")

    print("\n--- 玩家胜率统计 (基于所有12个角色池) ---")
    win_rates = {}
    table_data_for_csv = [["玩家ID", "玩家名称", "是否参与本次批量模拟", "获胜次数", f"总模拟次数 ({num_simulations})", "基于参与的胜率 (%)", "基于总池的胜率 (%)"]]

    for player_id_key in test.PLAYER_DETAILS: 
        p_name = test.PLAYER_DETAILS[player_id_key]["name"]
        is_selected_for_batch = "是" if player_id_key in selected_ids_for_simulation else "否"
        wins = win_counts.get(player_id_key, 0)
        
        # 胜率可以计算两种：一种是仅在参与者中的胜率，一种是相对于总模拟次数的胜率
        # 这里我们计算相对于总模拟次数的胜率，对于未参与者自然是0
        overall_win_rate = (wins / num_simulations) * 100 if num_simulations > 0 else 0
        
        # 如果需要计算“条件胜率”（即该角色被选中参与游戏时的胜率），则需要更复杂的统计
        # 目前的 win_counts 是基于总模拟次数的，所以对于未选中的角色，wins会是0。
        # 如果我们想展示的是“如果这个角色被选中了，它的胜率是多少”，那么 win_counts 应该只在它被选中的时候才可能增加。
        # 当前的逻辑是正确的：win_counts[selected_id] += 1. 所以未选中的角色wins为0.
        
        win_rates[player_id_key] = overall_win_rate
        print(f"{p_name} (ID: {player_id_key}): 获胜 {wins} 次, 总体胜率 {overall_win_rate:.2f}% (本次批量是否参与: {is_selected_for_batch})")
        table_data_for_csv.append([player_id_key, p_name, is_selected_for_batch, wins, num_simulations, 
                                   f"{overall_win_rate:.2f}", f"{overall_win_rate:.2f}"])


    csv_filename = "game_win_rate_report_selected_chars.csv"
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(table_data_for_csv)
        print(f"\n胜率报告已保存到: {os.path.abspath(csv_filename)}")
    except IOError as e:
        print(f"\n保存CSV文件 {csv_filename} 时出错: {e}")
    except Exception as e_general:
        print(f"\n保存CSV时发生一般错误: {e_general}")


if __name__ == "__main__":
    # 1. 首先，调用 test.py 中的函数进行角色选择
    print("启动角色选择流程...")
    # select_characters_cli() 是在 test.py 中定义的，它会与用户交互
    chosen_ids = test.select_characters_cli() 

    if chosen_ids and len(chosen_ids) == getattr(test, 'DEFAULT_NUM_SELECTED_PLAYERS', 6):
        # 2. 如果角色选择成功，则进行批量模拟
        SIM_COUNT = 50000  # 可以根据需要调整模拟次数，10000次会很慢
        VISUALIZE_INDEX = SIM_COUNT - 1 # 保存最后一次模拟的可视化过程
        # VISUALIZE_INDEX = None # 如果不想在批量运行中保存任何可视化

        batch_simulate_and_analyze(
            num_simulations=SIM_COUNT, 
            visualize_run_idx=VISUALIZE_INDEX,
            selected_ids_for_simulation=chosen_ids # <--- 传递选定的角色ID
        )
    else:
        num_expected = getattr(test, 'DEFAULT_NUM_SELECTED_PLAYERS', 6)
        print(f"角色选择未完成或选择数量不等于 {num_expected}。批量模拟已取消。")