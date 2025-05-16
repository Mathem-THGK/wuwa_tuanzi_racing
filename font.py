# matplotlib_chinese_test.py
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm # 用于更高级的字体管理（如此处用于指定文件路径）
import os # 用于检查字体文件是否存在

def setup_matplotlib_chinese_fonts_by_name():
    """
    尝试通过字体名称列表来设置 Matplotlib 支持中文。
    这是首选的尝试方法。
    """
    try:
        # 一个包含常见中文字体名称的列表。
        # Matplotlib会按顺序尝试使用列表中的字体。
        # 你可以根据你的操作系统调整这个列表，或者添加你知道已安装的字体。
        # Windows: 'SimHei', 'Microsoft YaHei', 'FangSong', 'KaiTi'
        # macOS: 'PingFang SC', 'STHeiti', 'Songti SC', 'Kaiti SC', 'Arial Unicode MS'
        # Linux: 'WenQuanYi Zen Hei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC'
        
        font_list = [
            'SimHei',           # 黑体 (Win/Linux常见)
            'Microsoft YaHei',  # 微软雅黑 (Win常见)
            'PingFang SC',      # 苹方-简 (macOS常见)
            'STHeiti',          # 华文黑体 (macOS常见)
            'WenQuanYi Zen Hei',# 文泉驿正黑 (Linux常见)
            'Noto Sans CJK SC', # Google Noto 思源黑体
            'sans-serif'        # 通用后备
        ]
        plt.rcParams['font.sans-serif'] = font_list
        plt.rcParams['axes.unicode_minus'] = False  # 正确显示负号

        # 可选: 打印Matplotlib实际选择的字体，以帮助调试
        # current_font_family = plt.rcParams['font.sans-serif']
        # print(f"Matplotlib 尝试使用的字体列表: {current_font_family}")
        # print(f"通常会选择列表中的第一个可用字体。")
        # if font_manager:
        #     try:
        #         prop = fm.FontProperties(family=current_font_family[0])
        #         print(f"Matplotlib 找到了名为 '{prop.get_name()}' 的字体作为首选。")
        #     except RuntimeError:
        #         print(f"警告: Matplotlib 可能未能找到列表中的首选字体 '{current_font_family[0]}'")
        print("已尝试通过名称设置中文字体。")
        return True
    except Exception as e:
        print(f"通过名称设置Matplotlib中文字体时发生错误: {e}")
        return False

def setup_matplotlib_chinese_fonts_by_path(font_file_path):
    """
    通过指定字体文件的绝对路径来设置 Matplotlib 支持中文。
    如果按名称设置不成功，这是一个更可靠的方法。
    """
    global font_manager # Ensure font_manager (fm) is accessible
    if not os.path.exists(font_file_path):
        print(f"错误：提供的字体文件路径不存在: '{font_file_path}'")
        return False
    try:
        # 创建一个 FontProperties 对象
        zh_font_prop = fm.FontProperties(fname=font_file_path)
        # 设置 Matplotlib 的默认字体系列为这个字体的名称
        # 这需要 Matplotlib 能够通过 get_name() 识别并后续使用它
        plt.rcParams['font.family'] = zh_font_prop.get_name()
        plt.rcParams['axes.unicode_minus'] = False
        print(f"已尝试通过路径 '{font_file_path}' 设置字体 '{zh_font_prop.get_name()}'。")
        return True
    except Exception as e:
        print(f"通过文件路径设置Matplotlib中文字体时发生错误: {e}")
        return False

def create_test_plot(title_prefix=""):
    """创建一个包含中文文本的简单图形用于测试。"""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ax.set_title(f"{title_prefix}中文标题测试 Chinese Title Test", fontsize=14)
    ax.set_xlabel("X轴标签 - 例如：玩家名称", fontsize=12)
    ax.set_ylabel("Y轴标签 - 例如：获胜次数", fontsize=12)
    
    ax.text(0.5, 0.6, "你好，世界！", 
            horizontalalignment='center', verticalalignment='center', 
            fontsize=18, color='blue')
    
    ax.text(0.5, 0.4, "Matplotlib 中文测试\n测试玩家：洛可可, 今汐", 
            horizontalalignment='center', verticalalignment='center', 
            fontsize=10, color='green')
            
    ax.plot([1, 2, 3, 4], [2, -1, 4, 3], marker='o', label="数据曲线")
    ax.legend(loc='upper right') # 图例也需要能显示中文
    
    plt.tight_layout() # 调整布局以防止标签重叠
    plt.show()

if __name__ == "__main__":
    print("--- 开始 Matplotlib 中文显示测试 ---")

    # --- 方法1：通过字体名称列表设置 (推荐首先尝试) ---
    print("\n尝试方法1：通过预定义字体名称列表设置...")
    if setup_matplotlib_chinese_fonts_by_name():
        create_test_plot("方法1: ")
    else:
        print("方法1：字体设置失败或部分失败。")

    print("\n------------------------------------------")
    
    # --- 方法2：通过指定字体文件路径设置 (如果方法1无效，请尝试此方法) ---
    # 1. 在你的操作系统中找到一个中文字体文件（通常是 .ttf, .ttc, 或 .otf 文件）。
    # 2. 将下面的 `your_actual_font_path` 变量替换为该文件的真实绝对路径。
    
    # 常见字体文件路径示例 (你需要取消注释并修改为你系统上的有效路径):
    # your_actual_font_path = 'C:/Windows/Fonts/simhei.ttf'      # Windows 黑体
    # your_actual_font_path = 'C:/Windows/Fonts/msyh.ttc'       # Windows 微软雅黑 (注意 .ttc 可能需要指定索引, 如 msyh.ttc:0)
    # your_actual_font_path = '/System/Library/Fonts/Supplemental/PingFang.ttc' # macOS 苹方 (也可能是 .ttc)
    # your_actual_font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc' # Linux 文泉驿正黑
    
    your_actual_font_path = "" # <--- *** 在这里填入你系统上的中文字体文件绝对路径 ***

    if your_actual_font_path and os.path.exists(your_actual_font_path):
        print(f"\n尝试方法2：通过字体文件路径 '{your_actual_font_path}' 设置...")
        # 在使用方法2前，最好重置一下 Matplotlib 的 rcParams，或者在一个新的Python会话中测试
        # plt.rcdefaults() # 重置 Matplotlib 到默认设置 (可选，但可能有助于隔离测试)
        # import matplotlib.font_manager as fm # 确保 fm 也重新导入或全局可用
        # globals()['font_manager'] = fm 
        
        if setup_matplotlib_chinese_fonts_by_path(your_actual_font_path):
            create_test_plot(f"方法2 ({os.path.basename(your_actual_font_path)}): ")
        else:
            print("方法2：字体文件路径设置失败或部分失败。")
    elif your_actual_font_path: # 路径填写了但不正确
         print(f"\n方法2：提供的字体文件路径 '{your_actual_font_path}' 未找到或无效，跳过测试。")
    else: # 用户未填写路径
        print("\n方法2：未指定字体文件路径，跳过此方法测试。")
        print("如果你想测试方法2，请编辑此脚本，在 'your_actual_font_path' 变量中填入一个有效的中文字体文件路径。")

    print("\n--- Matplotlib 中文显示测试结束 ---")