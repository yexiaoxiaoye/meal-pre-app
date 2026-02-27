# 如何把 Meal Prep 助手部署到 Streamlit 云端

Streamlit 官方提供 **Streamlit Community Cloud**，可免费把应用部署到公网。部署前需要先把代码放到 **GitHub** 仓库。

---

## 第一步：注册 / 登录 GitHub

1. 打开 [https://github.com](https://github.com)
2. 若没有账号，点击 **Sign up** 注册
3. 若已有账号，点击 **Sign in** 登录

---

## 第二步：在电脑上安装 Git（若尚未安装）

- Windows：从 [https://git-scm.com/download/win](https://git-scm.com/download/win) 下载并安装
- 安装后打开 **PowerShell** 或 **命令提示符**，执行 `git --version` 能显示版本号即表示安装成功

---

## 第三步：把项目上传到 GitHub

在 **PowerShell** 里依次执行（请把 `你的用户名` 换成你的 GitHub 用户名，`meal-pre-app` 可改成你想要的仓库名）：

```powershell
# 1. 进入项目目录
cd "c:\Users\95809\Desktop\meal pre"

# 2. 初始化 Git 仓库（若尚未初始化）
git init

# 3. 添加所有文件
git add .

# 4. 第一次提交
git commit -m "Initial commit: Meal Prep app"

# 5. 在 GitHub 网页上先新建一个空仓库（不要勾选 README），记下仓库地址，然后执行：
#    把下面的 你的用户名 和 meal-pre-app 换成你的仓库信息
git remote add origin https://github.com/你的用户名/meal-pre-app.git

# 6. 推送到 GitHub（主分支名一般为 main）
git branch -M main
git push -u origin main
```

**在 GitHub 网页上新建仓库：**

1. 登录 GitHub → 右上角 **+** → **New repository**
2. **Repository name** 填：`meal-pre-app`（或任意名称）
3. 选择 **Public**
4. **不要**勾选 “Add a README file”
5. 点击 **Create repository**
6. 页面会显示仓库地址，把上面命令里的 `https://github.com/你的用户名/meal-pre-app.git` 换成这个地址

---

## 第四步：部署到 Streamlit Community Cloud

1. 打开 **[https://share.streamlit.io](https://share.streamlit.io)**（或 [https://streamlit.io/cloud](https://streamlit.io/cloud)）
2. 点击 **Sign in with GitHub**，用 GitHub 账号授权登录
3. 登录后点击 **Create app** 或 **New app**
4. 填写部署信息：
   - **Repository**：选择你刚上传的仓库（如 `你的用户名/meal-pre-app`）
   - **Branch**：选 `main`
   - **Main file path**：填 `app.py`
5. 若页面有 **Advanced settings**，可展开：
   - **Python version**：选 3.9 或 3.10 即可
6. 点击 **Deploy** 或 **Deploy app**

等待几分钟，部署完成后会得到一个链接，例如：  
`https://你的应用名.streamlit.app`

---

## 第五步：使用与后续更新

- **访问应用**：在浏览器打开部署完成后显示的链接即可使用
- **更新应用**：在本地改好代码后，在项目目录执行：
  ```powershell
  git add .
  git commit -m "更新说明"
  git push
  ```
  Streamlit 会自动检测到推送并重新部署

---

## 重要说明：云端数据不会永久保存

- Streamlit 云端每次重启或重新部署时，**应用所在环境会被重置**，你在应用里添加的食材、配方、一周计划等会**丢失**。
- 因此更适合：
  - **本地使用**：在你自己电脑上 `streamlit run app.py`，数据会保存在本机 `data/` 目录
  - **云端演示 / 临时使用**：部署到 Streamlit 用于分享或演示，接受数据不持久

若希望云端也持久化数据，需要后续改造成使用数据库或云存储（如 Firebase、Supabase 等），这需要更多开发工作。

---

## 常见问题

**Q: 部署时报错 “ModuleNotFoundError”**  
A: 确保项目根目录有 `requirements.txt`，且包含 `streamlit` 和 `google-generativeai`。

**Q: 部署后打开是空白或报错**  
A: 检查 **Main file path** 是否填的是 `app.py`（不是 `src/app.py` 等）。

**Q: 需要填 API Key 或密码吗？**  
A: 部署时不必填 Gemini API Key；用户在打开你的应用后，在「AI 助手」页面自己输入 API Key 即可使用。

**Q: 如何让应用只有自己能访问？**  
A: 在 Streamlit Cloud 该应用的 **Settings** 里，可设置为仅自己或指定邮箱可访问（视当前 Streamlit 提供的选项而定）。

完成以上步骤后，你的 Meal Prep 应用就会在 Streamlit 上运行，并可通过链接分享给他人使用（记得提醒他们：云端数据不会永久保存）。
