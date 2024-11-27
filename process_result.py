import os
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

# 指定文件夹路径
folder_path = "E:/devwildchat/data/result"

# 定义感兴趣的任务
categories_of_interest = [
    "dev knowledge qa", "code generation", "debugging", "program repair", "code translation",
    "code edit", "code summarization", "code understanding", "test generation", "others"
]

# 初始化存储
category_counts = Counter()
task_counts_in_dash1_files = Counter()
task_combinations = Counter()

# 遍历文件夹中的所有 Excel 文件
for file_name in os.listdir(folder_path):
    if file_name.endswith(".xlsx") and file_name != "~$updated_gpt-3.5-turbo-0301-English-3.xlsx":
        file_path = os.path.join(folder_path, file_name)

        # 读取文件内容
        df = pd.read_excel(file_path)

        # 过滤掉不感兴趣的任务
        df = df[df['category'].isin(categories_of_interest)]

        # 更新任务占比统计
        category_counts.update(df['category'].value_counts().to_dict())

        # 如果文件名以 -1 结尾，统计任务数量
        if file_name.endswith("-1.xlsx"):
            task_counts_in_dash1_files.update(df['category'].value_counts().to_dict())
        else:
            # 统计相同 conversation_id 的不同 session_id 中的任务组合
            grouped = df.groupby('conversation_id')['category'].unique()
            for tasks in grouped:
                cleaned_tasks = sorted(map(str, tasks))
                if len(cleaned_tasks) > 1:
                    task_combinations[tuple(cleaned_tasks)] += 1

# 转换为 DataFrame 以便于绘图
category_distribution = pd.DataFrame(category_counts.items(), columns=['Category', 'Count'])
task_counts_in_dash1 = pd.DataFrame(task_counts_in_dash1_files.items(), columns=['Category', 'Count'])
task_combination_distribution = pd.DataFrame(task_combinations.items(), columns=['Combination', 'Count'])
# 只绘制任务组合数量较多的部分（例如数量前10名）
task_combination_distribution = task_combination_distribution.sort_values(by='Count', ascending=False).head(10)

# 绘制各任务的数量条形图
plt.figure(figsize=(15, 10))
plt.bar(category_distribution['Category'], category_distribution['Count'])
plt.xticks(rotation=45)
plt.title("Category Counts")
plt.xlabel("Category")
plt.ylabel("Count")
plt.show()

# 去除 "others" 任务
category_distribution = category_distribution[category_distribution['Category'] != "others"]
# 计算任务占比
category_distribution['Percentage'] = (category_distribution['Count'] / category_distribution['Count'].sum()) * 100

# 绘制任务占比饼图
plt.figure(figsize=(8, 8))
plt.pie(category_distribution['Percentage'], labels=category_distribution['Category'], autopct="%.1f%%")
plt.title("Category Distribution")
plt.show()

# 绘制各任务的数量条形图
plt.figure(figsize=(15, 10))
plt.bar(category_distribution['Category'], category_distribution['Count'])
plt.xticks(rotation=45)
plt.title("Category Counts")
plt.xlabel("Category")
plt.ylabel("Count")
plt.show()

# 绘制文件名以 -1 结尾的任务数量条形图
plt.figure(figsize=(10, 8))
plt.bar(task_counts_in_dash1['Category'], task_counts_in_dash1['Count'])
plt.xticks(rotation=45)
plt.title("Task Counts in '-1' Files")
plt.xlabel("Category")
plt.ylabel("Count")
plt.show()

# 绘制任务组合数量条形图
plt.figure(figsize=(18, 8))
plt.barh(task_combination_distribution['Combination'].astype(str), task_combination_distribution['Count'])
plt.title("Task Combination Counts")
plt.xlabel("Count")
plt.ylabel("Combination")
plt.yticks(wrap=True)  # 设置字体大小
plt.tight_layout()  # 自动调整布局，防止标签溢出
plt.show()
