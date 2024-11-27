import os
import json
import pandas as pd


def load_json_data_from_folder(folder_path):
    """从文件夹中加载所有 JSON 文件的数据"""
    json_data = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                json_data.extend(data)  # 合并所有文件中的数据
    return json_data


def update_excel_with_prompt(excel_file, json_data, output_file):
    """根据 JSON 数据更新 Excel 中的 prompt 信息"""

    # 读取现有的 Excel 文件
    df = pd.read_excel(excel_file, engine='openpyxl')

    # 创建一个字典以便快速查找 prompt
    prompt_dict = {
        (item["conversation_id"], item["session_id"]): item["category"]
        for item in json_data
    }

    # 在 DataFrame 中新增一列 'prompt'
    df['category'] = df.apply(lambda row: prompt_dict.get((row['conversation_id'], row['session_id']/2), None), axis=1)

    # 将更新后的 DataFrame 保存到新的 Excel 文件
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"Updated Excel file saved as {output_file}")


def process_files(json_folder, excel_folder, output_folder):
    """从 JSON 文件夹加载数据，并更新对应的 Excel 文件"""

    # 加载所有 JSON 数据
    json_data = load_json_data_from_folder(json_folder)

    # 遍历 Excel 文件夹中的每个文件
    for excel_filename in os.listdir(excel_folder):
        if excel_filename.endswith(".xlsx"):
            # 构造 Excel 文件的完整路径
            excel_file_path = os.path.join(excel_folder, excel_filename)

            # 确保有同名的 JSON 文件（无扩展名）
            json_file_name = excel_filename.replace(".xlsx", ".json")
            json_file_path = os.path.join(json_folder, json_file_name)

            # 如果有对应的 JSON 文件，则更新 Excel 文件
            if os.path.exists(json_file_path):
                output_file_path = os.path.join(output_folder, excel_filename)
                update_excel_with_prompt(excel_file_path, json_data, output_file_path)
            else:
                print(f"Warning: No corresponding JSON file for {excel_filename}. Skipping.")


# 示例：使用 JSON 文件夹和 Excel 文件夹更新 Excel 文件
if __name__ == "__main__":
    # JSON 数据所在的文件夹路径
    json_folder = "E:\devwildchat\data\gpt-4o-mini-result-3"  # 例如： "path/to/json_folder"

    # Excel 文件所在的文件夹路径
    excel_folder = "E:/devwildchat/data/final_output"  # 例如： "path/to/excel_folder"

    # 输出文件夹路径（保存更新后的 Excel 文件）
    output_folder = "E:/devwildchat/data/result-3"  # 例如： "path/to/updated_excel_folder"

    # 调用函数处理文件
    process_files(json_folder, excel_folder, output_folder)
