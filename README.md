# Meal Prep 智能助手

基于 Streamlit 的备餐助手：食材库、配方与逆向热量计算、一周计划、购物清单导出、Gemini AI 聊天。

## 运行方式

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 启动应用：
   ```bash
   streamlit run app.py
   ```

3. 在浏览器中打开显示的地址（通常为 http://localhost:8501）。

## 功能说明

- **每日计划**：选择星期与餐次，从配方库选择本餐包含的菜，输入目标热量，自动反算各食材克数并保存；可一键生成本周购物清单并导出 CSV。
- **食材库**：添加/编辑/删除食材（名称、每 100g 热量/蛋白质/碳水/脂肪），以标签形式展示。
- **AI 助手**：在界面输入 Gemini API Key 后，可提问如「我剩下的食材还能做什么菜？」「给我一个高蛋白的中餐菜谱建议」。

## 数据存储

- 数据保存在项目下的 `data/` 目录：`ingredients.json`、`recipes.json`、`weekly_plan.json`。
- 购物清单导出在 `data/shopping_lists/` 下，并支持页面内下载 CSV。

## Gemini API Key

从 [Google AI Studio](https://aistudio.google.com/apikey) 获取 API Key，在应用内「AI 助手」标签页输入即可使用。
