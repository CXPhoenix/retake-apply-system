# 校園重補修課程登記 Web App (Retake Apply System)

一款讓學生能使用校園 Google 帳號登入，並查詢與登記校方開設之重補修課程；同時也供課程管理者管理課程、學生修課資格與名單，以及系統管理者維護系統基本設定與權限的網路應用程式。

## 專案核心價值

*   **提升行政效率：** 自動化課程管理、學生名單處理及衝堂檢查等功能，減輕課程管理者負擔。
*   **優化學生體驗：** 提供清晰、易用的線上選課介面，學生可透過校園 Google 帳號快速登入，即時查詢個人化課程資訊並完成登記。
*   **強化系統整合：** 採用現代化的技術棧，確保系統的穩定性、可擴展性及未來維護的便利性。
*   **確保資料準確：** 透過系統化的資料管理與驗證機制，降低人為操作錯誤。

## 技術架構 (Tech Stack)

*   **後端框架：** Python, [Reflex](https://reflex.dev/) (本專案基於 `reflex>=0.7.11`)
*   **資料庫：** [MongoDB](https://www.mongodb.com/)
*   **ODM (Object Document Mapper)：** [Beanie](https://beanie-odm.dev/) (本專案基於 `beanie>=1.29.0`)
*   **身份驗證：** Google OAuth 2.0 (透過 [reflex-google-auth](https://pypi.org/project/reflex-google-auth/) `>=0.1.1`)
*   **設定管理：** [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (本專案基於 `pydantic-settings>=2.9.1`)
*   **部署：** [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/)
*   **前端：** Reflex (Python 編譯為 React)
*   **樣式：** [Tailwind CSS](https://tailwindcss.com/) (透過 Reflex 整合)
*   **Python 版本：** `>=3.12.9`

## 專案結構 (Project Structure)

```
.
├── app/                      # Reflex 應用程式主要目錄
│   ├── retake_apply/         # 應用程式核心模組 (rxconfig.py 中的 app_name)
│   │   ├── __init__.py
│   │   ├── retake_apply.py   # Reflex App 實例與頁面定義
│   │   ├── assets/           # 靜態資源 (圖示等)
│   │   ├── components/       # (若有) 可重用的 UI 組件
│   │   ├── configs/          # 環境變數設定模型 (如 DbEnv)
│   │   ├── models/           # Beanie 資料庫文件模型 (User, Course, etc.)
│   │   ├── pages/            # Reflex UI 頁面元件與其後端邏輯
│   │   ├── states/           # Reflex 後端狀態管理 (如 AuthState, 各頁面 State)
│   │   └── utils/            # 共用輔助函式 (資料庫、生命週期、CSV等)
│   ├── requirements.txt    # Python 依賴 (通常由 pyproject.toml 生成或管理)
│   └── rxconfig.py         # Reflex 應用程式基本設定
├── .clinerules/              # AI 輔助程式設計規範
├── .gitignore
├── .python-version           # 指定 Python 版本 (供 pyenv 等工具使用)
├── app.env.example           # 應用程式環境變數範例
├── docker-compose.yaml       # Docker Compose 設定檔
├── Dockerfile.web            # 應用程式服務的 Dockerfile
├── LICENSE                   # 專案授權文件
├── me.env.example            # Mongo Express 環境變數範例
├── mongo.env.example         # MongoDB 環境變數範例
├── pyproject.toml            # Python 專案依賴與元數據 (PEP 517/518)
├── README.md                 # 本文件
└── token.env.example         # Cloudflare Tunnel Token 環境變數範例
```

## 功能特色 (Features)

### 使用者角色

1.  **學生 (Student):** 校內需要或可能需要參與重補修課程的在學學生。
2.  **課程管理者 (CourseManager):** 校內負責規劃、開設、管理重補修課程的行政人員。
3.  **系統管理者 (SystemAdmin):** 負責系統整體運作、維護及使用者權限管理的技術人員。

### 核心功能

*   **通用：**
    *   透過校園 Google Workspace 帳號登入系統。
*   **學生 (Student)：**
    *   檢視個人化「應重補修科目列表」。
    *   瀏覽、查詢目前開放登記的重補修課程。
    *   執行線上課程登記，系統自動進行衝堂檢查。
    *   檢視個人已登記課程清單。
*   **課程管理者 (CourseManager)：**
    *   **課程管理：** 新增、修改、刪除、查詢重補修課程；支援批次上傳 (CSV) 開課資料。
    *   **學生名單管理：** 新增、修改、刪除、查詢學生應重補修科目；支援批次上傳 (CSV) 學生應重補修名單。
    *   **學年度管理：** 設定與調整當前系統運作的學年度及學生登記起迄時間。
    *   **報名管理：** 檢視所有學生的報名資料；下載報名資料 (CSV 格式)。
    *   **(TODO)** 處理現場報名後產生繳費單相關資料。
*   **系統管理者 (SystemAdmin)：**
    *   管理使用者帳號的角色指派。
    *   查閱系統操作日誌與錯誤記錄。

## 環境設定與啟動 (Setup and Running the Project)

### 先決條件 (Prerequisites)

*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/) (通常隨 Docker Desktop 一併安裝)
*   Google OAuth 2.0 Client ID 與 Client Secret (需預先至 [Google Cloud Console](https://console.cloud.google.com/) 設定)

### 環境變數設定

在專案根目錄下，複製以下 `.example` 檔案並移除 `.example` 副檔名，然後填入對應的設定值：

1.  **`app.env`** (應用程式相關設定)
    ```env
    # Google OAuth 憑證
    GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
    # Google OAuth 重新導向 URI (需與 Google Cloud Console 設定一致)
    # 開發時若 Reflex 運行於 http://localhost:3000，則通常為：
    GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/google/callback
    # 若部署於其他網域，請相應修改。
    ```

2.  **`mongo.env`** (MongoDB 資料庫設定)
    ```env
    # MongoDB Root 使用者 (用於初始化)
    MONGO_INITDB_ROOT_USERNAME=mongoadmin
    MONGO_INITDB_ROOT_PASSWORD=your_strong_password_for_mongo_admin

    # 供應用程式連線 MongoDB 的使用者帳密 (將由初始化腳本創建)
    MONGODB_USERNAME=retake_user
    MONGODB_PASSWORD=your_strong_password_for_retake_user
    MONGODB_DB_NAME=retake_apply_db # 應用程式使用的資料庫名稱
    MONGODB_AUTHSOURCE=admin # 驗證資料庫 (通常是 admin)
    MONGODB_URL=mongo # Docker Compose 服務名稱
    MONGODB_PORT=27017
    ```
    *注意：`MONGODB_USERNAME` 和 `MONGODB_PASSWORD` 是應用程式實際用來連線資料庫的帳密。這些帳密會在 MongoDB 容器首次啟動時，透過 `MONGO_INITDB_ROOT_USERNAME` 和 `MONGO_INITDB_ROOT_PASSWORD` 的權限，在指定的 `MONGODB_DB_NAME` 中被創建（或確保其存在）。*

3.  **`me.env`** (Mongo Express 設定)
    ```env
    ME_CONFIG_MONGODB_ADMINUSERNAME=mongoadmin # 應與 mongo.env 中的 MONGO_INITDB_ROOT_USERNAME 相同
    ME_CONFIG_MONGODB_ADMINPASSWORD=your_strong_password_for_mongo_admin # 應與 mongo.env 中的 MONGO_INITDB_ROOT_PASSWORD 相同
    ME_CONFIG_MONGODB_SERVER=mongo # Docker Compose 中的 MongoDB 服務名稱
    # 若 MongoDB 有設定應用程式專用帳號，也可以讓 Mongo Express 使用該帳號登入特定資料庫
    # ME_CONFIG_MONGODB_URL=mongodb://retake_user:your_strong_password_for_retake_user@mongo:27017/retake_apply_db?authSource=retake_apply_db
    # ME_CONFIG_BASICAUTH_USERNAME= (可選，Mongo Express 登入帳號)
    # ME_CONFIG_BASICAUTH_PASSWORD= (可選，Mongo Express 登入密碼)
    ```

4.  **`token.env`** (若使用 Cloudflare Tunnel 服務)
    ```env
    TUNNEL_TOKEN=YOUR_CLOUDFLARE_TUNNEL_TOKEN
    ```
    *若不使用 Cloudflare Tunnel，可以忽略此檔案，或將 `docker-compose.yaml` 中的 `tunnel`服務註解掉。*

### 啟動指令

完成環境變數設定後，在專案根目錄執行以下指令：

```bash
docker-compose up --build
```

此指令會建置 Docker 映像檔並啟動所有定義在 `docker-compose.yaml` 中的服務。

### 存取應用程式

*   **Reflex Web App：** [http://localhost:3000](http://localhost:3000)
*   **Mongo Express (資料庫管理工具)：** [http://localhost:8081](http://localhost:8081)
*   **Cloudflare Tunnel：** 若已設定並啟動，請查閱 Cloudflare Dashboard 提供的公開 URL。

## 資料模型 (Data Models)

本專案使用 Beanie ODM 管理 MongoDB 資料庫文件。主要模型定義於 `app/retake_apply/models/` 目錄下：

*   **`User`**: 儲存使用者基本資訊 (來自 Google OAuth)、校內學號、身分證雜湊 (用於核對)、以及應用程式內的角色群組 (`UserGroup`)。
*   **`Course`**: 包含重補修課程的詳細資訊，如學年度、科目代碼/名稱、學分數、費用、上課時間 (`CourseTimeSlot` 內嵌模型)、授課教師、人數上限等。
*   **`Enrollment`**: 記錄學生選課的關聯，包含選課狀態 (`EnrollmentStatus`)、繳費狀態 (`PaymentStatus`) 及相關時間戳。
*   **`RequiredCourse`**: 記錄學生被判定需要重補修的科目及其原始成績。
*   **`AcademicYearSetting`**: 儲存系統當前運作的學年度設定，以及學生登記的起迄時間。
*   **`SystemLog`**: 用於記錄應用程式的重要操作日誌與錯誤資訊，包含日誌級別 (`LogLevel`)。
*   **`Payment`**: 記錄學生的繳費單資訊，包含應繳金額、實繳金額、繳費狀態 (`PaymentRecordStatus`)，並可關聯多筆選課記錄。

詳細欄位定義請參考各模型檔案內的 Pydantic 與 Beanie 宣告。

## API 端點

本專案主要透過 Reflex 的事件處理器 (event handlers) 與後端狀態 (states) 互動。`reflex-google-auth` 套件會自動處理 `/api/auth/google/callback` 等 Google OAuth 相關端點。
目前未額外定義供第三方呼叫的自訂 HTTP API 端點。

## 程式碼設計原則與風格

*   **SOLID 原則：** 致力於遵循 SOLID 設計原則以提升程式碼品質。
*   **PEP 8：** 嚴格遵守 PEP 8 Python 風格指南。
*   **文件字串 (Docstrings)：** 所有公開的模組、類別、函式和方法均撰寫 Google Style Docstrings。
*   **註解 (Comments)：**
    *   針對複雜邏輯或非直觀程式碼片段提供清晰註解。
    *   使用 `TODO:` 標註待辦事項。
*   **語言與標點：** 所有 Docstrings 及註解均使用「台灣慣用繁體中文用語及標點符號」。程式設計專有名詞以原文呈現。

詳細規範請參考 `.clinerules/CODEING_STYLE_RULE.md`。

## 授權 (License)

本專案採用 MIT 授權。詳情請見 [LICENSE](./LICENSE) 檔案。
