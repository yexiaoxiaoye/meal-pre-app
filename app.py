# -*- coding: utf-8 -*-
"""
Meal Prep 智能助手 - 基于 Streamlit
功能：食材库、配方与逆向热量计算、一周计划、购物清单导出、Gemini AI 助手
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

import streamlit as st

# ---------- 路径与配置 ----------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INGREDIENTS_FILE = DATA_DIR / "ingredients.json"
RECIPES_FILE = DATA_DIR / "recipes.json"
WEEKLY_PLAN_FILE = DATA_DIR / "weekly_plan.json"
SHOPPING_LIST_DIR = DATA_DIR / "shopping_lists"

DATA_DIR.mkdir(exist_ok=True)
SHOPPING_LIST_DIR.mkdir(exist_ok=True)

# ---------- 数据持久化 ----------
def load_json(path: Path, default: Any):
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_ingredients():
    return load_json(INGREDIENTS_FILE, [])

def save_ingredients(data):
    save_json(INGREDIENTS_FILE, data)

def get_recipes():
    return load_json(RECIPES_FILE, [])

def save_recipes(data):
    save_json(RECIPES_FILE, data)

def get_weekly_plan():
    return load_json(WEEKLY_PLAN_FILE, {})

def save_weekly_plan(data):
    save_json(WEEKLY_PLAN_FILE, data)

# ---------- 营养与配方计算 ----------
def ingredient_by_id(ingredients_list, ing_id):
    for ing in ingredients_list:
        if ing.get("id") == ing_id:
            return ing
    return None

def recipe_nutrition(recipe, ingredients_list):
    """计算一道菜的总营养（按当前重量）。返回 dict: calories, protein, carbs, fat"""
    total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for item in recipe.get("ingredients", []):
        ing = ingredient_by_id(ingredients_list, item.get("ingredient_id"))
        if not ing:
            continue
        w = item.get("weight_grams", 0) / 100.0
        total["calories"] += ing.get("calories_per_100g", 0) * w
        total["protein"] += ing.get("protein_per_100g", 0) * w
        total["carbs"] += ing.get("carbs_per_100g", 0) * w
        total["fat"] += ing.get("fat_per_100g", 0) * w
    return total

def meal_total_nutrition(meal_recipes_with_weights, recipes_list, ingredients_list):
    """meal_recipes_with_weights: [ (recipe, scale), ... ] 或 [ {recipe_id, scale, ingredients_weights?}, ... ]"""
    total = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0}
    for rec_entry in meal_recipes_with_weights:
        if isinstance(rec_entry, dict):
            rec = next((r for r in recipes_list if r.get("id") == rec_entry.get("recipe_id")), None)
            scale = rec_entry.get("scale", 1.0)
        else:
            rec, scale = rec_entry
        if not rec:
            continue
        nut = recipe_nutrition(rec, ingredients_list)
        total["calories"] += nut["calories"] * scale
        total["protein"] += nut["protein"] * scale
        total["carbs"] += nut["carbs"] * scale
        total["fat"] += nut["fat"] * scale
    return total

def solve_meal_weights(meal_recipe_entries, recipes_list, ingredients_list, target_calories):
    """
    meal_recipe_entries: 当前一餐的配方列表，每项为 { recipe_id, scale 或 默认1 }
    根据目标热量反算每道菜的缩放比例，使总热量 = target_calories。
    返回：每道菜的 scale，以及每道菜各食材的克数（用于展示）。
    """
    if not meal_recipe_entries or target_calories <= 0:
        return [], []

    base_total = 0.0
    recipe_nuts = []
    for entry in meal_recipe_entries:
        rec = next((r for r in recipes_list if r.get("id") == entry.get("recipe_id")), None)
        if not rec:
            recipe_nuts.append(None)
            continue
        nut = recipe_nutrition(rec, ingredients_list)
        recipe_nuts.append(nut)
        base_total += nut["calories"]

    if base_total <= 0:
        return [1.0] * len(meal_recipe_entries), []

    scale = target_calories / base_total
    scales = [scale] * len(meal_recipe_entries)
    # 每道菜各食材的克数
    detailed_weights = []
    for i, entry in enumerate(meal_recipe_entries):
        rec = next((r for r in recipes_list if r.get("id") == entry.get("recipe_id")), None)
        if not rec:
            detailed_weights.append([])
            continue
        row = []
        for item in rec.get("ingredients", []):
            row.append({
                "ingredient_id": item["ingredient_id"],
                "weight_grams": round(item.get("weight_grams", 0) * scale, 1)
            })
        detailed_weights.append(row)
    return scales, detailed_weights

# ---------- 页面样式 ----------
def apply_custom_css():
    st.markdown("""
    <style>
    /* 主色调与卡片 */
    :root {
        --primary: #2e7d32;
        --primary-light: #4caf50;
        --surface: #fafafa;
        --card: #ffffff;
        --text: #1a1a1a;
        --text-muted: #666;
    }
    .stApp { background: linear-gradient(180deg, #f1f8e9 0%, #fff 30%); }
    div[data-testid="stAppViewContainer"] { background: transparent; }
    /* 指标卡片 */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #fff 0%, #f5f5f5 100%);
        padding: 1rem 1.25rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e8e8e8;
    }
    div[data-testid="stMetric"] label { color: #555 !important; font-weight: 500; }
    /* 标签样式 */
    .ingredient-tag {
        display: inline-block;
        background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
        color: white !important;
        padding: 0.35rem 0.75rem;
        border-radius: 20px;
        margin: 0.25rem;
        font-size: 0.9rem;
        cursor: pointer;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .ingredient-tag:hover { opacity: 0.9; transform: scale(1.02); }
    /* 区块标题 */
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2e7d32;
        margin: 1rem 0 0.5rem 0;
        padding-bottom: 0.3rem;
        border-bottom: 2px solid #c8e6c9;
    }
    /* 提示框 */
    .stAlert { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ---------- 初始化 session_state ----------
def init_session():
    if "ingredients" not in st.session_state:
        st.session_state.ingredients = get_ingredients()
    if "recipes" not in st.session_state:
        st.session_state.recipes = get_recipes()
    if "weekly_plan" not in st.session_state:
        st.session_state.weekly_plan = get_weekly_plan()
    if "gemini_messages" not in st.session_state:
        st.session_state.gemini_messages = []

# ---------- 食材库 Tab ----------
def render_ingredients_tab():
    st.subheader("🥗 食材库管理")
    st.caption("在这里添加、编辑或删除食材。每种食材会作为标签在配方中使用。")

    ingredients = st.session_state.ingredients

    with st.expander("➕ 添加新食材", expanded=False):
        with st.form("add_ingredient_form"):
            name = st.text_input("名称", placeholder="例如：鸡胸肉")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                cal = st.number_input("热量 (kcal/100g)", min_value=0, value=100, step=1)
            with c2:
                protein = st.number_input("蛋白质 (g/100g)", min_value=0.0, value=20.0, step=0.1)
            with c3:
                carbs = st.number_input("碳水 (g/100g)", min_value=0.0, value=0.0, step=0.1)
            with c4:
                fat = st.number_input("脂肪 (g/100g)", min_value=0.0, value=5.0, step=0.1)
            if st.form_submit_button("保存"):
                if name.strip():
                    new_id = "ing_" + str(uuid.uuid4())[:8]
                    ingredients.append({
                        "id": new_id,
                        "name": name.strip(),
                        "calories_per_100g": cal,
                        "protein_per_100g": protein,
                        "carbs_per_100g": carbs,
                        "fat_per_100g": fat,
                    })
                    save_ingredients(ingredients)
                    st.session_state.ingredients = ingredients
                    st.success("已添加食材")
                    st.rerun()
                else:
                    st.warning("请输入名称")

    st.markdown('<p class="section-title">当前食材（点击标签可复制名称）</p>', unsafe_allow_html=True)
    if not ingredients:
        st.info("暂无食材，请先添加。")
        return

    # 以标签形式展示，并支持编辑/删除
    for ing in ingredients:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f'<span class="ingredient-tag">{ing["name"]}</span> '
                f'· {ing["calories_per_100g"]} kcal · {ing["protein_per_100g"]}g 蛋白 · '
                f'{ing["carbs_per_100g"]}g 碳水 · {ing["fat_per_100g"]}g 脂肪',
                unsafe_allow_html=True
            )
        with col2:
            if st.button("删除", key=f"del_{ing['id']}", type="secondary"):
                ingredients = [i for i in ingredients if i["id"] != ing["id"]]
                # 更新引用该食材的配方（可选：移除或保留）
                save_ingredients(ingredients)
                st.session_state.ingredients = ingredients
                st.rerun()

    # 简单编辑：用 expander 编辑选中的食材
    st.markdown("---")
    ids = [i["name"] for i in ingredients]
    edit_choice = st.selectbox("选择要编辑的食材", options=ids, key="edit_ing_select")
    if edit_choice:
        ing = next((i for i in ingredients if i["name"] == edit_choice), None)
        if ing:
            with st.form("edit_ingredient_form"):
                new_name = st.text_input("名称", value=ing["name"])
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    new_cal = st.number_input("热量", min_value=0, value=ing["calories_per_100g"], step=1, key="ec")
                with c2:
                    new_protein = st.number_input("蛋白质", min_value=0.0, value=ing["protein_per_100g"], step=0.1, key="ep")
                with c3:
                    new_carbs = st.number_input("碳水", min_value=0.0, value=ing["carbs_per_100g"], step=0.1, key="ecarb")
                with c4:
                    new_fat = st.number_input("脂肪", min_value=0.0, value=ing["fat_per_100g"], step=0.1, key="ef")
                if st.form_submit_button("更新"):
                    ing["name"] = new_name.strip() or ing["name"]
                    ing["calories_per_100g"] = new_cal
                    ing["protein_per_100g"] = new_protein
                    ing["carbs_per_100g"] = new_carbs
                    ing["fat_per_100g"] = new_fat
                    save_ingredients(ingredients)
                    st.session_state.ingredients = ingredients
                    st.success("已更新")
                    st.rerun()

# ---------- 配方与一餐组合：烹饪区 + 逆向计算 ----------
def render_daily_plan_tab():
    st.subheader("📅 每日计划与智能配方")

    ingredients = st.session_state.ingredients
    recipes = st.session_state.recipes
    weekly_plan = st.session_state.weekly_plan

    # 一周 7 天 x 每天 2 顿
    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    meal_names = ["早餐/午餐", "晚餐"]

    # 侧边：选择某一天、某一顿
    st.sidebar.markdown("### 选择日期与餐次")
    day_idx = st.sidebar.selectbox("星期", range(7), format_func=lambda i: day_names[i], key="plan_day")
    meal_idx = st.sidebar.selectbox("餐次", range(2), format_func=lambda i: meal_names[i], key="plan_meal")
    day_key = f"day_{day_idx}"
    meal_key = f"meal_{meal_idx}"
    if day_key not in weekly_plan:
        weekly_plan[day_key] = {}
    if meal_key not in weekly_plan[day_key]:
        weekly_plan[day_key][meal_key] = {"target_calories": 500, "recipe_ids": []}

    plan = weekly_plan[day_key][meal_key]
    target_cal = plan.get("target_calories", 500)
    selected_recipe_ids = plan.get("recipe_ids", [])

    st.markdown(f"**{day_names[day_idx]} · {meal_names[meal_idx]}**")

    # 烹饪区：从配方库把“标签”（配方）选进这一餐
    st.markdown("#### 烹饪区：从下方选择要加入本餐的配方")
    recipe_options = {r["name"]: r["id"] for r in recipes}
    if not recipe_options:
        st.warning("请先在「配方管理」中创建配方，或使用下方快速添加。")
    else:
        chosen = st.multiselect(
            "选择本餐包含的菜（可多选）",
            options=list(recipe_options.keys()),
            default=[r["name"] for r in recipes if r["id"] in selected_recipe_ids],
            key="meal_recipes_select"
        )
        selected_recipe_ids = [recipe_options[n] for n in chosen]

    # 目标热量
    target_cal = st.number_input("本餐目标总热量 (kcal)", min_value=100, value=int(target_cal), step=50, key="target_cal_input")
    plan["target_calories"] = target_cal
    plan["recipe_ids"] = selected_recipe_ids

    # 逆向计算
    meal_entries = [{"recipe_id": rid, "scale": 1.0} for rid in selected_recipe_ids]
    if meal_entries and target_cal > 0:
        scales, detailed_weights = solve_meal_weights(meal_entries, recipes, ingredients, target_cal)
        total_nut = meal_total_nutrition(
            [{"recipe_id": e["recipe_id"], "scale": scales[i]} for i, e in enumerate(meal_entries)],
            recipes, ingredients
        )
        st.markdown("#### 营养汇总（按目标热量反算后）")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("热量 (kcal)", f"{total_nut['calories']:.0f}")
        m2.metric("蛋白质 (g)", f"{total_nut['protein']:.1f}")
        m3.metric("碳水 (g)", f"{total_nut['carbs']:.1f}")
        m4.metric("脂肪 (g)", f"{total_nut['fat']:.1f}")

        st.markdown("#### 各道菜所需食材克数")
        for i, rid in enumerate(selected_recipe_ids):
            rec = next((r for r in recipes if r["id"] == rid), None)
            if not rec:
                continue
            rec_nut = recipe_nutrition(rec, ingredients)
            with st.expander(f"🍽 {rec['name']}（约 {rec_nut['calories']*scales[i]:.0f} kcal）"):
                if i < len(detailed_weights):
                    for w in detailed_weights[i]:
                        ing = ingredient_by_id(ingredients, w["ingredient_id"])
                        name = ing["name"] if ing else w["ingredient_id"]
                        st.write(f"- **{name}**: {w['weight_grams']} g")

    if st.button("保存本餐到计划"):
        save_weekly_plan(weekly_plan)
        st.session_state.weekly_plan = weekly_plan
        st.success("已保存")

    # ---------- 配方管理（在同一 Tab 下用 expander 或子区）----------
    st.markdown("---")
    st.markdown("#### 配方管理：创建新菜（如西红柿炒蛋）")
    with st.expander("新建配方", expanded=False):
        with st.form("new_recipe_form"):
            rec_name = st.text_input("配方名称", placeholder="例如：西红柿炒蛋")
            category = st.selectbox("类别", ["vegetable", "meat", "staple"], format_func=lambda x: {"vegetable": "素菜", "meat": "肉类", "staple": "主食"}[x])
            st.caption("添加食材：选择食材并填写克数（生重）。")
            rec_ingredients = []
            if not ingredients:
                st.info("请先在食材库中添加食材。")
            else:
                ing_names = [i["name"] for i in ingredients]
                num_ings = st.number_input("本配方包含几种食材", min_value=1, max_value=20, value=2, key="num_ings")
                for k in range(int(num_ings)):
                    c1, c2 = st.columns(2)
                    with c1:
                        name = st.selectbox(f"食材 {k+1}", ing_names, key=f"rec_ing_name_{k}")
                    with c2:
                        grams = st.number_input(f"克数", min_value=1, value=100, key=f"rec_ing_g_{k}")
                    rec_ingredients.append({"ingredient_id": next(i["id"] for i in ingredients if i["name"] == name), "weight_grams": grams})
            if st.form_submit_button("创建配方"):
                if rec_name.strip() and (ingredients and rec_ingredients):
                    new_id = "rec_" + str(uuid.uuid4())[:8]
                    new_recipe = {
                        "id": new_id,
                        "name": rec_name.strip(),
                        "category": category,
                        "ingredients": rec_ingredients if ingredients else []
                    }
                    recipes.append(new_recipe)
                    save_recipes(recipes)
                    st.session_state.recipes = recipes
                    st.success("配方已创建")
                    st.rerun()

    # ---------- 一周购物清单 ----------
    st.markdown("---")
    st.markdown("#### 一周购物清单")
    if st.button("生成本周购物清单"):
        agg = {}  # ingredient_id -> total_grams
        for d in range(7):
            for m in range(2):
                key_d = f"day_{d}"
                key_m = f"meal_{m}"
                if key_d not in weekly_plan or key_m not in weekly_plan[key_d]:
                    continue
                plan_meal = weekly_plan[key_d][key_m]
                target = plan_meal.get("target_calories", 500)
                rids = plan_meal.get("recipe_ids", [])
                if not rids:
                    continue
                entries = [{"recipe_id": rid, "scale": 1.0} for rid in rids]
                scales, detailed_weights = solve_meal_weights(entries, recipes, ingredients, target)
                for i, rid in enumerate(rids):
                    if i >= len(detailed_weights):
                        continue
                    for w in detailed_weights[i]:
                        uid = w["ingredient_id"]
                        agg[uid] = agg.get(uid, 0) + w["weight_grams"]

        if not agg:
            st.warning("本周计划中还没有安排任何餐食，无法生成购物清单。")
        else:
            lines = []
            for ing_id, grams in sorted(agg.items()):
                ing = ingredient_by_id(ingredients, ing_id)
                name = ing["name"] if ing else ing_id
                lines.append(f"{name},{grams:.0f}")
            from datetime import datetime
            filename = f"shopping_list_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            filepath = SHOPPING_LIST_DIR / filename
            with open(filepath, "w", encoding="utf-8-sig") as f:
                f.write("食材,克数\n")
                f.write("\n".join(lines))
            st.success(f"已生成购物清单并保存到：{filepath}")
            st.download_button(
                "下载购物清单 CSV",
                data="食材,克数\n" + "\n".join(lines),
                file_name=filename,
                mime="text/csv",
                key="download_shopping"
            )

# ---------- Gemini AI 聊天 ----------
def call_gemini(api_key: str, user_message: str, history: list) -> str:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        chat = model.start_chat(history=[])
        for h in history:
            if h["role"] == "user":
                chat.send_message(h["content"])
            else:
                pass  # 用 send_message 后 response 会带历史
        response = chat.send_message(user_message)
        return response.text
    except Exception as e:
        return f"调用失败：{str(e)}"

def render_ai_tab():
    st.subheader("🤖 AI 助手（Gemini）")
    api_key = st.text_input("Gemini API Key", type="password", placeholder="在此输入你的 API Key", key="gemini_key")
    if not api_key:
        st.info("请输入 Gemini API Key 后即可提问，例如：「我剩下的食材还能做什么菜？」或「给我一个高蛋白的中餐菜谱建议」。")
        return

    # 聊天历史
    messages = st.session_state.gemini_messages
    for msg in messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("输入问题，例如：我剩下的食材还能做什么菜？")
    if prompt:
        messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                history_for_api = [{"role": m["role"], "content": m["content"]} for m in messages[:-1]]
                reply = call_gemini(api_key, prompt, history_for_api)
            st.markdown(reply)
        messages.append({"role": "assistant", "content": reply})
        st.session_state.gemini_messages = messages

    if messages and st.button("清空对话"):
        st.session_state.gemini_messages = []
        st.rerun()

# ---------- 主入口 ----------
def main():
    st.set_page_config(
        page_title="Meal Prep 智能助手",
        page_icon="🥗",
        layout="wide",
        initial_sidebar_state="auto"
    )
    apply_custom_css()
    init_session()

    st.title("🥗 Meal Prep 智能助手")
    st.caption("管理食材、搭配配方、按目标热量反算克数，并生成一周购物清单。")

    tab1, tab2, tab3 = st.tabs(["📅 每日计划", "🥬 食材库", "🤖 AI 助手"])
    with tab1:
        render_daily_plan_tab()
    with tab2:
        render_ingredients_tab()
    with tab3:
        render_ai_tab()

if __name__ == "__main__":
    main()
