import os
import pandas as pd


def excel_to_json(excel_file, json_file):
    """将单个 Excel 文件转换为 JSON 格式并保存"""
    # 读取 Excel 文件
    df = pd.read_excel(excel_file)

    # 检查是否存在 'session_id' 列，并进行修改
    if 'session_id' in df.columns:
        df['session_id'] = (df['session_id'] / 2).astype(int)
        # print(f"已将 '{excel_file}' 中 'session_id' 列的数值除以 2。")
    else:
        print(f"'{excel_file}' 中没有 'session_id' 列，跳过修改。")

    # 将数据框 (DataFrame) 转换为 JSON 格式
    # 将数据框 (DataFrame) 转换为 JSON 格式，且所有记录都在一个 JSON 数组中
    df.to_json(json_file, orient='records', lines=False, force_ascii=False)
    print(f"数据已保存为 JSON 文件: {json_file}")


def convert_all_excel_in_folder(input_folder, output_folder):
    """将指定文件夹中的所有 Excel 文件转换为 JSON 格式并保存到另一个文件夹"""
    # 如果输出文件夹不存在，则创建该文件夹
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        if filename.endswith(".xlsx"):
            excel_file = os.path.join(input_folder, filename)
            # 输出文件的路径，将 Excel 扩展名替换为 .json
            json_file = os.path.join(output_folder, filename.replace(".xlsx", ".json"))

            # 调用转换函数
            excel_to_json(excel_file, json_file)


# 示例：将文件夹中的所有 Excel 文件转换为 JSON 文件，并保存在另一个文件夹
input_folder = "E:/devwildchat/data/final_output"  # 输入文件夹路径
output_folder = "E:\devwildchat\data\json_data"  # 输出文件夹路径

convert_all_excel_in_folder(input_folder, output_folder)