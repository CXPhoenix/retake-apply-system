# 校園重補修課程登記 Web App AI 輔助程式設計規範

一款讓學生能使用校園 Google 帳號登入，並查詢與登記校方開設之重補修課程；同時也供課程管理者管理課程、學生修課資格與名單，以及系統管理者維護系統基本設定與權限的網路應用程式。本專案將採用 Reflex 框架、MongoDB 資料庫 (透過 Beanie ODM)、Docker 微服務架構進行開發，並整合 Google 身分驗證 (reflex-google-auth)。

## 專案需求規格

### 一、總體目標與核心價值

本「校園重補修課程登記 Web App」旨在提供一套現代化、高效率的解決方案，取代傳統或既有系統在重補修課程管理與學生選課流程上的不便。核心價值在於：
* **提升行政效率：** 自動化課程管理、學生名單處理及衝堂檢查等功能，減輕課程管理者負擔。
* **優化學生體驗：** 提供清晰、易用的線上選課介面，學生可透過校園 Google 帳號快速登入，即時查詢個人化課程資訊並完成登記。
* **強化系統整合：** 採用現代化的技術棧 (Reflex, MongoDB, Docker)，確保系統的穩定性、可擴展性及未來維護的便利性。
* **確保資料準確：** 透過系統化的資料管理與驗證機制，降低人為操作錯誤。

### 二、目標使用者與角色權限定義

#### 1. 角色定義
本系統主要包含以下三種使用者角色：

* **1.1. 學生 (Student):**
    * 定義：校內需要或可能需要參與重補修課程的在學學生。
    * 主要互動：查詢個人應修課程、瀏覽可選課程、進行線上選課登記。
* **1.2. 課程管理者 (CourseManager):**
    * 定義：校內負責規劃、開設、管理重補修課程的行政人員（例如：教學組、註冊組）。
    * 主要互動：設定與維護課程資訊、上傳與管理學生應重補修名單、管理學生選課結果、調整學年度設定。
* **1.3. 系統管理者 (SystemAdmin):**
    * 定義：負責系統整體運作、維護及使用者權限管理的技術人員。
    * 主要互動：管理使用者帳號角色、監控系統日誌、進行必要的系統配置。

#### 2. 各角色主要權限範圍 (初步規劃)

* **學生 (Student):**
    * 透過 Google OAuth (校園帳號) 登入系統。
    * 檢視個人化「應重補修科目列表」（包含成績）。
    * 瀏覽、查詢目前開放登記的重補修課程詳細資訊。
    * 執行線上課程登記，並接收衝堂檢查結果。
    * 檢視個人已登記課程清單。
* **課程管理者 (CourseManager):**
    * 透過 Google OAuth (職員帳號) 登入系統。
    * **課程管理：** 新增、修改、刪除、查詢重補修課程；批次上傳 (CSV) 開課資料。
    * **學生名單管理：** 新增、修改、刪除、查詢學生應重補修科目；批次上傳 (CSV) 學生應重補修名單（含成績）。
    * **學年度管理：** 設定與調整當前系統運作的學年度。
    * **報名管理：** 檢視所有學生的報名資料；下載報名資料 (例如 CSV 格式)。
    * **現場報名管理：** 能夠即時增加學生報名資料。
    * (TODO) 處理現場報名後產生繳費單相關資料。
* **系統管理者 (SystemAdmin):**
    * 透過 Google OAuth (特定職員帳號) 登入系統。
    * 管理使用者帳號的角色指派（學生、課程管理者、系統管理者）。
    * 查閱系統操作日誌與錯誤記錄。
    * (可能) 進行系統層級的基本組態設定。

### 三、核心功能詳述

#### 1. 使用者身份驗證與授權機制
* **登入方式：** 所有使用者均透過校園 Google Workspace 帳號，利用 `reflex-google-auth` 函式庫提供的 OAuth 2.0 機制進行登入。
* **學生登入憑證：** 學生首次登入後，系統應能關聯其 Google 帳號與校內學籍資料（例如透過學號+身分證字號進行唯一性識別，此部分需確認具體實施方式，或由管理者預先匯入學生 Google Email 對應學號資料）。
* **角色判斷與授權：** 系統需能根據登入使用者的 Google 帳號資訊（例如 Email 或預先設定的群組對應），判斷其角色（學生、課程管理者、系統管理者），並據此進行功能與頁面的存取控制。角色資訊應儲存於應用程式的 `AuthState` 或相關使用者模型中。

#### 2. 學生使用者介面與功能

* **2.1. 個人化重補修課程資訊顯示：**
    * 學生登入後，系統首頁或特定頁面應清晰展示該學生「被判定需要重補修」的所有科目及其相關成績（此列表由課程管理者預先上傳）。
* **2.2. 課程查詢與篩選：**
    * 提供介面供學生查詢當學年度所有已開設的重補修課程。
    * 應包含課程名稱、科目代碼、授課教師（若有）、上課時間（週次、星期、節次、上下午）、學分數、費用等資訊。
    * (可選) 提供篩選器，如依科目名稱、時段等進行篩選。
* **2.3. 課程登記流程：**
    * 學生選擇欲修課程後，點擊「登記」或類似按鈕。
    * 系統執行衝堂檢查。
    * 若無衝突，則記錄選課成功，並更新學生已選課程列表。
    * 若有衝突，則提示錯誤訊息，不予登記。
* **2.4. 衝堂 (課程衝突) 檢查機制：**
    * **定義一：時間重疊：** 不同課程之間，若課程表定的上課時間（需考慮日期、週次、星期、節次、上下午時段）有任何重疊，即視為衝堂。
    * **定義二：同課程不同時段：** 若同一門課程（以科目代碼及學年期識別）於多個不同時段重複開設，學生一旦成功選取其中一個時段的課程後，該課程的其他所有時段對此學生均視為衝堂。
    * **處理方式：** 學生嘗試登記第二門（或後續）會造成衝堂的課程時，系統應明確提示衝突原因，並阻止該次登記操作。第一次選課不受此限。

#### 3. 課程管理者介面與功能

* **3.1. 開設課程管理：**
    * 提供表單介面，供管理者手動新增、修改、刪除單筆重補修課程。
    * **課程欄位應包含（但不限於）：** 學年度、科目代碼、科目名稱、學分數、每學分費用（例如 240 元）、上課時段（以 A/B 代號表示上下午）、上課日期/時間（以「週次+星期+節次」組合定義）、授課教師（可選）、人數上限（可選，初期可不考慮）。
    * **批次匯入：** 支援透過 CSV 檔案格式批次上傳多筆開課課程資料。系統需驗證 CSV 格式與欄位內容。
* **3.2. 學生應重補修名單管理：**
    * 提供表單介面，供管理者手動新增、修改、刪除學生應重補修的科目記錄。
    * **記錄欄位應包含（但不限於）：** 學年度、學號、學生姓名、科目代碼、科目名稱、不及格成績。
    * **批次匯入：** 支援透過 CSV 檔案格式批次上傳多筆學生應重補修名單。系統需驗證 CSV 格式與欄位內容。
* **3.3. 學年度設定與調整：**
    * 提供介面讓課程管理者可以獨立設定或調整目前系統運作的學年度（例如：「113學年度上學期」），選課、開課等操作均基於此設定。此調整不應需要系統管理者介入或重啟系統。
* **3.4. 學生報名資料檢視與下載：**
    * 提供介面讓課程管理者可以依條件（如學年度、課程、學生）查詢學生選課報名結果。
    * 支援將查詢結果下載為 CSV 檔案，其欄位格式應符合先前提供的「報名下載資料.csv」樣本。

#### 4. 系統管理者介面與功能

* **4.1. 使用者角色與權限指派 (初步概念)：**
    * 提供介面，列出已透過 Google 登入系統的使用者（可考慮顯示其 Email、姓名）。
    * 系統管理者可為這些使用者指派或修改其應用程式角色（學生、課程管理者、系統管理者）。
    * 此功能應與 `reflex-google-auth` 的 `AuthState` 及 `UserGroup` Enum 結合。
* **4.2. 系統運作日誌 (Log) 查閱介面：**
    * 提供一個網頁介面，讓系統管理者可以方便地查詢應用程式後端產生的重要運作日誌與錯誤記錄，無需直接存取伺服器檔案系統或終端機。
    * (可選) 提供日誌篩選功能（如依時間、日誌級別、關鍵字）。

#### 5. 待辦 (TODO) 功能規劃

* **5.1. 繳費單相關資料處理與介面：**
    * **初期目標：** LLM 僅需協助規劃與此功能相關的資料模型結構（例如：`Payment` 模型，記錄繳費狀態、金額、對應選課等）。
    * **遠期目標（本次 LLM 開發範圍之外，但需考慮擴充性）：**
        * 課程管理者能為已報名學生產生繳費通知資料（可能非直接列印三聯單，而是產生繳費資訊供校內出納組使用）。
        * 若學生報名多個科目，應能彙整於一張繳費通知上，計算總金額。
        * 課程管理者於特定時段（如現場報名）可透過系統輔助學生報名，並立即產生繳費資訊。

### 四、技術棧與架構規範

* **1. Web 應用程式框架：**
    * **Python Reflex：** 版本需與使用者提供的特定 Git Commit Hash (`v0.7.12`) 的 API 與功能相容。
* **2. 資料庫與 ODM (Object Document Mapper)：**
    * **資料庫：** MongoDB (版本應與 Beanie 和 Async Motor 相容的較新穩定版)。
    * **ODM：** Beanie，並搭配 `motor.motor_asyncio` 客戶端進行所有非同步資料庫操作。
* **3. 部署架構與環境：**
    * **容器化：** 採用 Docker 微服務架構。
    * **編排：** 使用 `docker-compose.yml` 檔案編排部署應用程式服務 (app)、MongoDB 資料庫服務 (mongodb)、以及資料庫管理工具 (如 mongo-express)。
    * **設定管理：** `config` 模組內的 `__init__.py` 使用 `pydantic-settings` 函式庫從環境變數讀取資料庫連線字串、Google OAuth 金鑰等敏感設定。
* **4. 程式碼設計原則遵循：**
    * 嚴格遵循 **SOLID** 設計原則，提升程式碼的可維護性、可擴展性與可測試性。
* **5. 專案模組化結構：**
    * 程式碼應組織在以下主要模組目錄中：
        * `config/`: 應用程式組態設定。
        * `model/`: Beanie 資料庫文件模型定義、資料庫初始化 (`init_beanie`) 設定。
        * `page/`: Reflex 的前端頁面 (UI元件) 及對應的後端狀態 (`rx.State`) 與事件處理邏輯。
        * `utils/`: 共用的輔助函式、工具程式（例如：CSV 處理、日期時間轉換、特定驗證邏輯等）。
        * `auth/`: (建議新增) 專門處理身份驗證與授權相關的邏輯，例如 `AuthState`、`UserGroup` Enum、`require_group` 裝飾器等。
* **6. 程式碼撰寫風格、品質與文件化要求：**
    * **風格指南：** 嚴格遵守 PEP 8 Python 風格指南。
    * **文件字串 (Docstrings)：** 所有公開的模組、類別、函式和方法均須撰寫 Google Style Docstrings。
    * **註解 (Comments)：**
        * 針對複雜的商業邏輯、演算法或非直觀的程式碼片段，需撰寫清晰的行內或區塊註解進行解釋。
        * 對於需要由開發者後續處理、或 LLM 未能完全實現的功能點，應明確標註 `TODO:`，並簡要說明待辦事項及原因。
    * **語言與標點：**
        * 所有 Docstrings 及註解（`TODO` 標註的說明文字亦同）均需使用「台灣慣用繁體中文用語及標點符號」書寫。
        * 若在註解或文件中提及程式設計的專有名詞（例如：`MongoDB`, `Beanie ODM`, `Reflex State`, `SOLID principles`, `OAuth 2.0`, `Docker Compose` 等），則該專有名詞應以其原文（通常為英文）呈現。

### 五、資料模型初步概念 (MongoDB Beanie Documents)

以下為本專案核心業務所需的 Beanie Document 模型初步設想，LLM 應基於此進行擴充與細化，並確保所有欄位均有 Pydantic 類型提示。

* **1. `User` (使用者模型):**
    * `google_sub`: `str` (來自 Google ID Token 的 `sub`，唯一識別碼，建立索引)
    * `email`: `EmailStr` (Google Email，唯一識別碼，建立索引)
    * `fullname`: `Optional[str]` (使用者全名，來自 Google)
    * `picture`: `Optional[str]` (使用者頭像 URL，來自 Google)
    * `student_id`: `Optional[str]` (校內學號，若為學生，可建立索引)
    * `id_card_number_hash`: `Optional[str]` (校內身分證號碼的雜湊值，用於學生身份核對，不應明文儲存)
    * `groups`: `List[UserGroup]` (使用者所屬群組/角色，例如 `[UserGroup.STUDENT, UserGroup.AUTHENTICATED_USER]`)
    * `created_at`: `datetime` (帳號創建時間)
    * `last_login`: `Optional[datetime]` (最後登入時間)
    * `is_active`: `bool` (帳號是否啟用，預設為 True)
    * `Settings`: 內嵌類別，指定 `collection_name = "users"`

* **2. `Course` (重補修課程模型):**
    * `academic_year`: `str` (學年度，例如 "113-1" 代表113學年度上學期，建立索引)
    * `course_code`: `str` (科目代碼，同一學年度內應唯一，建立索引)
    * `course_name`: `str` (科目名稱)
    * `credits`: `float` (學分數)
    * `fee_per_credit`: `int` (每學分費用，例如 240)
    * `total_fee`: `Computed[int]` (總費用 = `credits` * `fee_per_credit`)
    * `time_slots`: `List[CourseTimeSlot]` (上課時間列表，允許一門課有多個不連續時段，或用於表示每週固定時間)
        * `CourseTimeSlot` (內嵌 Pydantic 模型):
            * `week_number`: `Optional[int]` (週次，若適用)
            * `day_of_week`: `int` (星期幾，1=週一, ..., 7=週日)
            * `period`: `str` (節次，例如 "1", "2", "A", "B"，需定義清楚對應時間)
            * `start_time`: `str` (格式 HH:MM)
            * `end_time`: `str` (格式 HH:MM)
            * `location`: `Optional[str]` (上課地點)
    * `instructor_name`: `Optional[str]` (授課教師姓名)
    * `max_students`: `Optional[int]` (人數上限，初期可忽略)
    * `is_open_for_registration`: `bool` (是否開放選課，預設 True)
    * `created_at`: `datetime`
    * `updated_at`: `Optional[datetime]`
    * `Settings`: 內嵌類別，指定 `collection_name = "courses"`

* **3. `Enrollment` (學生選課記錄模型):**
    * `user_id`: `Link[User]` (關聯到學生，Beanie Link)
    * `course_id`: `Link[Course]` (關聯到課程，Beanie Link)
    * `academic_year`: `str` (選課當下學年度，冗餘欄位，方便查詢)
    * `enrolled_at`: `datetime` (登記時間)
    * `status`: `str` (選課狀態，例如 "成功", "待處理", "已退選", "衝堂取消" - 可用 Enum)
    * `payment_status`: `Optional[str]` (繳費狀態，例如 "待繳費", "已繳費" - 可用 Enum，TODO 功能)
    * `Settings`: 內嵌類別，指定 `collection_name = "enrollments"`，並可考慮建立 `(user_id, course_id)` 的複合唯一索引。

* **4. `RequiredCourse` (學生應重補修科目模型):**
    * `user_id`: `Link[User]` (關聯到學生)
    * `academic_year_taken`: `str` (原始修課學年度)
    * `course_code`: `str` (應重補修的科目代碼)
    * `course_name`: `str` (應重補修的科目名稱)
    * `original_grade`: `str` (原始不及格成績，例如 "45", "F")
    * `is_remedied`: `bool` (是否已完成重補修，預設 False)
    * `uploaded_at`: `datetime` (此記錄上傳時間)
    * `Settings`: 內嵌類別，指定 `collection_name = "required_courses"`

* **5. (其他可能模型):**
    * `AcademicYearSetting`: 用於儲存當前系統運作的學年度設定。
    * `SystemLog`: 用於儲存系統操作日誌。
    * `Payment`: (TODO) 用於繳費相關記錄。

### 六、資料交換格式定義 (CSV 檔案)

LLM 應設計對應的 Pydantic 模型來驗證 CSV 匯入的資料。

* **1. 開課課程資料批次匯入格式 (範例欄位，需與 `Course` 模型對應)：**
    * `學年度` (例如: "113-1")
    * `科目代碼`
    * `科目名稱`
    * `學分數`
    * `每學分費用`
    * `上課時間_週次` (可為空)
    * `上課時間_星期` (1-7)
    * `上課時間_節次代號` (例如: "A", "B", "1", "2", 對應 `CourseTimeSlot`)
    * `上課時間_開始` (HH:MM)
    * `上課時間_結束` (HH:MM)
    * `授課教師` (可為空)
    * `上課地點` (可為空)
    * `人數上限` (可為空)
    * (LLM 應參考 `報名上傳下載資料樣本.xlsx - 開課資料上傳.csv` 檔案來確定確切欄位，並考慮如何處理一門課可能有多個時段的問題，可能需要多行表示或特定格式)

* **2. 學生應重補修名單批次匯入格式 (範例欄位，需與 `RequiredCourse` 及 `User` 模型關聯)：**
    * `學號`
    * `學生姓名`
    * `不及格科目之學年度` (例如: "112-2")
    * `不及格科目代碼`
    * `不及格科目名稱`
    * `不及格成績`
    * `學生GoogleEmail` (建議加入此欄位，以便系統關聯 `User` 模型)

* **3. 學生報名資料匯出格式 (範例欄位，從 `Enrollment`, `User`, `Course` 模型組合)：**
    * 應參考 `報名上傳下載資料樣本.xlsx - 報名下載資料.csv` 檔案的欄位結構。
    * 例如：`報名日期`, `學號`, `學生姓名`, `選課序號`, `科目代碼`, `科目名稱`, `學分數`, `費用` 等。

* **4. CSV 欄位名稱與資料庫內部欄位名稱轉換規則概述：**
    * **原則：** CSV 檔案使用中文欄位名稱（如使用者提供之樣本），方便人工閱讀與準備；資料庫內部（Beanie 模型）則使用英文小寫蛇形命名法 (snake_case) 作為欄位名稱。
    * **實作：** LLM 應在 CSV 匯入/匯出相關的 `utils` 函式或 `State` 方法中，實作明確的欄位名稱對應（mapping）與轉換邏輯。例如，CSV 的「學號」對應到 `User` 模型的 `student_id`。

## 程式設計實務 (CODING_PRACTICES)

### 支援等級指南 (Guidelines for SUPPORT_LEVEL)

#### 專家級支援 (SUPPORT_EXPERT)

* 傾向於優雅、易於維護的解決方案，而非冗餘的程式碼。假設使用者已理解語言特性和設計模式。
* 在建議的程式碼中，應強調潛在的效能影響和最佳化機會。
* 將解決方案置於更廣泛的架構背景下進行闡述，並在適當時提出設計替代方案。
* 註解應專注於解釋「為何如此」（why），而非「做了什麼」（what）—— 良好的函式與變數命名應確保程式碼的可讀性。
* 無需提示，即應主動處理邊緣案例、競爭條件 (race conditions) 和安全性考量。
* 進行除錯時，應提供針對性的診斷方法，而非漫無目的的嘗試。
* 建議全面的測試策略，而不僅僅是範例測試，應包含模擬 (mocking)、測試組織和覆蓋率等考量。

### 文件撰寫指南 (Guidelines for DOCUMENTATION)

#### 文件更新 (DOC_UPDATES)

* 保持 `README.md` 與新功能同步。
* 在 `CHANGELOG.md` 中維護變更日誌條目。
* 在 `PROJECT_STRUCTURE.md` 中維護整體專案架構。

### 架構設計指南 (Guidelines for ARCHITECTURE)

#### 乾淨架構 (CLEAN_ARCHITECTURE)

* 嚴格將程式碼分層：實體 (entities)、使用案例 (use cases)、介面 (interfaces) 和框架 (frameworks)。
* 確保依賴關係指向內層，內層對外層無感知。
* 實作領域實體 (domain entities)，用於封裝校園重補修課程登記 Web App 的核心業務規則（例如：使用者身份與權限驗證、課程資料管理、學生應重補修科目管理、學生選課流程及衝堂判斷邏輯、資料處理與轉換規則等），且不依賴於特定框架。
* 使用介面（端口，ports）和實作（適配器，adapters）來隔離外部依賴。
* 創建使用案例，用於協調針對特定業務操作的實體互動。
* 實作對應器 (mappers)，用於在不同層之間轉換資料，以維持關注點分離 (separation of concerns)。

## 網頁應用程式開發 (Web Application)

### Python 指南 (Guidelines for PYTHON)

#### Reflex 框架

* **狀態管理 (STATE_MANAGEMENT):** 在 `rx.State` 中使用具備類型提示的 `rx.Var` 來定義應用程式的 UI 相關狀態。
* **資料庫模型 (DATABASE_MODELS):**
    * 若使用 SQL 資料庫，建議使用 `rx.Model` (基於 SQLModel，整合 Pydantic 驗證) 來定義資料模型。
    * 若使用 MongoDB，應搭配 Beanie ODM。Beanie `Document` 模型本身已整合 Pydantic，用於資料驗證。
* **Beanie (MongoDB ODM) 整合:**
    * **生命週期管理 (LIFESPAN_MANAGEMENT):** `AsyncIOMotorClient` 的建立與關閉，以及 `beanie.init_beanie` 的呼叫，應透過定義一個 `asynccontextmanager` 並將其加入到 `rx.App` 實例的 `lifespan_tasks` 列表來進行管理。這確保資料庫連線在應用程式啟動時正確初始化，並在關閉時妥善釋放。 (詳細範例請參考「資料庫」->「NoSQL 指南」->「MongoDB」->「Beanie ODM 與 Async Motor 實踐指南」一節)。
    * **非同步操作 (ASYNC_OPERATIONS):** 所有在 `rx.State` 方法中與 Beanie 互動的資料庫操作，均須使用 `async/await` 語法。
* **業務邏輯封裝 (BUSINESS_LOGIC_ENCAPSULATION):** 將相關的業務邏輯和資料庫操作封裝在 `rx.State` 的方法中。透過繼承 `rx.State` 或組合子狀態 (substates) 的方式來組織和管理應用程式的服務及資源，以提升模組化、可測試性與資源管理效率。
* **非同步事件處理器 (ASYNC_EVENT_HANDLERS):** 對於涉及 I/O 的操作 (例如網路請求、檔案讀寫、資料庫查詢)，應優先使用 async 事件處理器 (event handlers) 以提升應用程式的反應速度和吞吐量，尤其是在處理例如處理學生大量同時查詢或提交選課、課程管理者批次上傳/下載大量資料（如 CSV 學生名單或課程資料）、以及執行複雜的衝堂檢查邏輯等高負載或需時較長的操作時。
* **背景任務 (BACKGROUND_TASKS):** 對於不需要立即阻塞使用者介面回應的非關鍵性操作 (例如寄送郵件、資料清理)，應利用 Reflex 提供的 `@rx.background` 裝飾器將其作為背景任務執行。
* **例外處理 (EXCEPTION_HANDLING):** 在事件處理器 (`event handlers`) 和後端邏輯中，應使用標準的 Python `try-except` 機制進行周全的例外處理。針對例如選課時發生衝堂、選到不存在或已額滿的課程、課程管理者上傳之 CSV 檔案格式錯誤或內容不合規、資料庫操作失敗、Google 登入驗證失敗、或使用者試圖存取未授權功能等特定錯誤情境，可考慮使用 `rx.window_alert`、`rx.toast` (例如整合 Radix Themes 的 Toast) 或自訂的 UI 組件向使用者提供清晰的錯誤反饋。
* **API 端點 (API_ENDPOINTS):** 主要透過將事件處理器 (event handlers) 綁定到 UI 組件的事件 (如 `on_click`, `on_submit`, `on_change` 等) 來驅動應用程式的邏輯和狀態更新。若需額外提供傳統的 HTTP API 端點 (例如供第三方服務呼叫)，可使用 `app.api_add_route()` 方法，並遵循 RESTful 原則設計路由及處理對應的 HTTP 方法。

#### 身分驗證與授權 (AUTHENTICATION_AUTHORIZATION)

##### 1. Google 身分驗證整合 (GOOGLE_AUTHENTICATION_INTEGRATION)

* **函式庫 (LIBRARY):** 應使用 `reflex-google-auth` 函式庫來整合 Google 身分驗證。
* **環境變數設定 (ENVIRONMENT_VARIABLES):**
    * `GOOGLE_CLIENT_ID`: (必要) 您的 Google OAuth 2.0 用戶端 ID。
    * `GOOGLE_CLIENT_SECRET`: (使用自訂登入按鈕或後端驗證授權碼時必要) 您的 Google OAuth 2.0 用戶端密鑰。
    * `GOOGLE_REDIRECT_URI`: (使用自訂登入按鈕或後端驗證授權碼時必要) 在 Google Cloud Console 中設定的已授權重新導向 URI。
    * 應在應用程式的設定檔 (如 `rxconfig.py` 使用 `os.environ.get`) 或部署環境中正確設定這些變數。
* **應用程式狀態整合 (`AuthState`):**
    * 建議創建一個繼承自 `reflex_google_auth.GoogleAuthState` 的基礎應用程式狀態類 (例如 `AuthState`)。
        ```python
        # 在 your_app/state.py 或 your_app/auth_state.py
        import reflex as rx
        from reflex_google_auth import GoogleAuthState
        from typing import List, Dict, Any
        
        # 假設 User 模型和 UserGroup Enum 已在 your_app.models 中定義
        # from your_app.models import User, UserGroup 

        # 為了範例清晰，UserGroup Enum 直接在此定義，實際專案應放在 models.py 或 enums.py
        from enum import Enum
        class UserGroup(str, Enum):
            ADMIN = "系統管理員"
            EDITOR = "編輯者"
            VIEWER = "檢視者"
            AUTHENTICATED_USER = "已驗證使用者"

        class AuthState(GoogleAuthState):
            # 使用 rx.Var 來儲存從資料庫同步的應用程式特定使用者群組，以實現反應式更新
            _app_user_groups_var: rx.Var[List[UserGroup]] = rx.Var([])

            @rx.event(transition=rx.Transition.PENDING) # 表示此事件處理期間可能處於等待狀態
            async def on_success(self, id_token: Dict[str, Any]):
                """
                在 Google 登入成功後觸發。
                處理 token 驗證、使用者資料庫同步及群組更新。
                """
                async with self: # 確保狀態更新的原子性與批次處理
                    await super().on_success(id_token) # 呼叫父類別的 on_success 處理 tokeninfo
                    
                    if self.token_is_valid:
                        user_email = self.tokeninfo.get("email")
                        google_sub = self.tokeninfo.get("sub") # Google User ID
                        user_name = self.tokeninfo.get("name")
                        
                        # --- 實際的資料庫操作 (應替換為真實的 Beanie 操作) ---
                        if google_sub:
                            # from your_app.models import User # 應在檔案頂部匯入
                            # existing_user = await User.find_one(User.google_sub == google_sub)
                            # simulated_groups_from_db = []
                            # if existing_user:
                            #     simulated_groups_from_db = existing_user.groups
                            #     # 可選擇更新使用者資訊，例如 fullname 或 last_login
                            #     # await existing_user.update(Set({User.fullname: user_name, User.last_login: datetime.utcnow()}))
                            #     print(f"使用者 {existing_user.fullname} (ID: {google_sub}) 已存在，群組: {simulated_groups_from_db}")
                            # else:
                            #     # 創建新使用者
                            #     default_groups = [UserGroup.VIEWER, UserGroup.AUTHENTICATED_USER]
                            #     new_user = User(
                            #         email=user_email,
                            #         fullname=user_name,
                            #         google_sub=google_sub,
                            #         groups=default_groups 
                            #     )
                            #     await new_user.insert()
                            #     simulated_groups_from_db = new_user.groups
                            #     print(f"新使用者 {user_name} (ID: {google_sub}) 已創建，群組: {simulated_groups_from_db}")
                            # self._app_user_groups_var = simulated_groups_from_db # 更新 rx.Var
                            
                            # --- 範例：基於 email 模擬群組指派 (僅為演示，實際應查資料庫) ---
                            if user_email and "admin" in user_email.lower():
                                self._app_user_groups_var = [UserGroup.ADMIN, UserGroup.AUTHENTICATED_USER]
                            elif user_email:
                                self._app_user_groups_var = [UserGroup.VIEWER, UserGroup.AUTHENTICATED_USER]
                            else:
                                self._app_user_groups_var = []
                            # --- 範例結束 ---
                            
                        else: # google_sub 不存在，理論上不應發生於成功登入
                            self._app_user_groups_var = []
                        
                        print(f"使用者 {user_name} ({user_email}) 登入成功。應用程式群組已設定。") # 應使用日誌系統
                    else:
                        self._app_user_groups_var = [] # Token 無效，清除群組

            @rx.cached_var
            def current_user_groups(self) -> List[UserGroup]:
                """獲取當前登入使用者的應用程式內部群組。"""
                if not self.token_is_valid:
                    return []
                return self._app_user_groups_var

        # 應用程式的主 State 應繼承 AuthState
        # class AppState(AuthState): # 假設這是您專案的主 State
        #     # ... 其他應用程式狀態 ...
        #     pass
        ```
    * 應用程式的主 `rx.State` (例如 `AppState`) 應繼承此 `AuthState`，以便在整個應用程式中存取驗證狀態和使用者資訊。
* **登入保護 (`require_google_login`):**
    * 使用 `reflex_google_auth.require_google_login` 裝飾器來保護需要登入才能存取的頁面或組件。
    * 此裝飾器會在使用者未登入時自動顯示 Google 登入按鈕。
        ```python
        # 在 your_app/pages/protected_page.py
        # import reflex as rx
        # from your_app.state import AuthState # 假設 AuthState 是您應用的主 State 或其基類
        # from reflex_google_auth import require_google_login

        # @rx.page(route="/protected_page")
        # @require_google_login
        # def protected_page() -> rx.Component:
        #     return rx.vstack(
        #         rx.text(f"歡迎, {AuthState.user_name}!"), # user_name 來自 GoogleAuthState
        #         rx.text("這是受保護的內容。"),
        #         rx.text("您的群組："),
        #         rx.foreach(
        #             AuthState.current_user_groups, # 使用更新後的 current_user_groups
        #             lambda group: rx.badge(group.value)
        #         )
        #     )
        ```
* **首次登入與使用者資料同步 (FIRST_LOGIN_USER_SYNC):**
    * 在 `AuthState` 的 `on_success` 事件處理器中，當使用者首次透過 Google 登入時，應檢查應用程式資料庫中是否已存在該使用者 (可使用 `tokeninfo['sub']` 作為唯一識別碼)。
    * 若使用者不存在，應在資料庫中創建新的使用者記錄，儲存必要的 Google 使用者資訊 (如 `sub`, `email`, `name`, `picture`)，並可指派預設的使用者群組 (例如 `[UserGroup.VIEWER, UserGroup.AUTHENTICATED_USER]`)。
    * 若使用者已存在，可更新其資訊 (如最後登入時間、姓名等) 並重新載入其群組資訊至 `_app_user_groups_var`。
    * `User` 模型 (例如在 MongoDB 中使用 Beanie) 應包含儲存 `google_sub` (唯一) 和 `groups` (群組列表) 的欄位。

##### 2. 角色型存取控制 (RBAC - ROLE_BASED_ACCESS_CONTROL)

* **群組定義 (`UserGroup` Enum):**
    * 使用 `enum.Enum` 定義應用程式中的所有使用者群組 (Roles)。應將此 Enum 定義在可共享的模組中 (例如 `your_app/models.py` 或 `your_app/enums.py`)。
        ```python
        # 在 your_app/enums.py (或 your_app/models.py)
        from enum import Enum

        class UserGroup(str, Enum):
            ADMIN = "系統管理員"
            EDITOR = "編輯者"
            VIEWER = "檢視者"
            AUTHENTICATED_USER = "已驗證使用者" # 代表任何已登入的使用者
            # ... 可依需求新增其他群組
        ```
* **使用者模型中的群組儲存 (USER_MODEL_GROUPS):**
    * 在應用程式的 `User` 資料庫模型中，應有一個欄位 (例如 `groups: List[UserGroup]`) 來儲存該使用者所屬的所有群組。 (參考「資料庫」->「MongoDB」->「模型定義」中的 `User` 模型範例)
* **群組授權裝飾器 (`require_group`):**
    * **單一職責原則:** 應創建一個獨立的裝飾器 (例如 `require_group`) 來處理基於群組的授權，與 `require_google_login` (負責登入驗證) 分開。
    * `require_group` 裝飾器應在 `require_google_login` *之後* 套用，以確保在檢查群組前使用者已經登入。
    * 此裝飾器接收一個允許的群組列表 (`allowed_groups: List[UserGroup]`) 作為參數。
    * 它會檢查當前登入使用者的群組 (從 `AuthState.current_user_groups` 獲取) 是否至少有一個存在於 `allowed_groups` 中。
    * 若使用者不具備所需群組，則應顯示未授權的訊息或導向至特定頁面。

    * **`require_group` 裝飾器範例概念:**
        ```python
        # 在 your_app/decorators.py 或 your_app/auth_utils.py
        import reflex as rx
        import functools
        from typing import List, Callable, TypeVar
        # from your_app.state import AuthState # 假設 AuthState 是應用程式的 State (例如 AppState)
        # from your_app.enums import UserGroup # 假設 UserGroup Enum

        ComponentCallable = Callable[[], rx.Component]
        F = TypeVar('F', bound=ComponentCallable)

        def default_unauthorized_view_factory(
            required_groups: List[UserGroup],
            current_user_groups_var: rx.Var[List[UserGroup]] # 傳入 rx.Var 以便反應式顯示
        ) -> rx.Component:
            """產生一個預設的未授權檢視元件。"""
            return rx.vstack(
                rx.heading("⛔ 存取權限不足", size="7", color_scheme="red"),
                rx.text("抱歉，您沒有足夠的權限來存取此頁面或功能。"),
                rx.text("所需群組：", font_weight="bold"),
                rx.hstack(
                    *[rx.badge(group.value, color_scheme="amber") for group in required_groups],
                    spacing="2"
                ),
                rx.text("您目前的群組：", font_weight="bold", margin_top="0.5em"),
                rx.cond(
                    rx.length(current_user_groups_var) > 0,
                    rx.hstack(
                        rx.foreach(
                            current_user_groups_var,
                            lambda group_item: rx.badge(group_item.value, color_scheme="grass")
                        ),
                        spacing="2"
                    ),
                    rx.text("(無群組或未載入)", color_scheme="gray")
                ),
                rx.link("返回首頁", href="/", margin_top="1.5em", color_scheme="blue"),
                align="center",
                spacing="3",
                padding="2em",
                border="1px solid var(--gray-a6)", # 使用 Radix Theme token
                border_radius="var(--radius-3)",
                box_shadow="var(--shadow-3)",
                max_width="500px",
                margin="2em auto",
            )

        def require_group(
            allowed_groups: List[UserGroup],
            # 假設 AuthState 是您應用程式的主狀態類別或其基底，且已混入 GoogleAuthState
            # 例如: from your_app.state import AppState as CurrentAuthState 
            # unauthorized_view_func 的簽名也需要符合
            unauthorized_view_func: Callable[[List[UserGroup], rx.Var[List[UserGroup]]], rx.Component] | None = None
        ) -> Callable[[F], F]:
            """
            一個裝飾器，用於限制只有特定群組的使用者才能存取某個頁面或組件。
            應在 @require_google_login 之後使用。
            """
            actual_unauthorized_view_factory = unauthorized_view_func or default_unauthorized_view_factory

            def decorator(func_to_protect: F) -> F:
                @functools.wraps(func_to_protect)
                def wrapper(*args, **kwargs) -> rx.Component:
                    # 這裡的 AuthState 應指向應用程式實際使用的 AuthState 類別
                    # 為了簡化，我們假設它就是 AuthState，但實際專案中可能是 AppState
                    # from your_app.state import AuthState as AppSpecificAuthState

                    # 創建一個內部組件狀態來封裝權限檢查邏輯，使其反應式
                    class PermissionCheckState(AuthState): # 應繼承自應用程式的 AuthState
                        @rx.var
                        def has_permission(self) -> bool:
                            if not self.token_is_valid:
                                return False
                            # self.current_user_groups 來自繼承的 AuthState
                            return any(group in self.current_user_groups for group in allowed_groups)

                    return rx.cond(
                        AuthState.is_hydrated, # 確保 GoogleAuthState 已完成客戶端水合
                        rx.cond(
                            PermissionCheckState.has_permission, # 使用內部狀態的權限檢查
                            func_to_protect(*args, **kwargs), # 如果有權限，渲染原始組件
                            # 將 AuthState.current_user_groups 傳遞給未授權視圖
                            actual_unauthorized_view_factory(allowed_groups, AuthState.current_user_groups) 
                        ),
                        rx.center(rx.spinner(size="3"), padding_y="5em") # 水合或檢查時的佔位符 (Radix Spinner size "3" is medium)
                    )
                return wrapper # type: ignore
            return decorator # type: ignore
        ```
        **使用範例：**
        ```python
        # from your_app.state import AppState # 假設 AppState 繼承了 AuthState
        # from your_app.enums import UserGroup
        # from your_app.decorators import require_group 
        # from reflex_google_auth import require_google_login

        # @rx.page(route="/admin_only")
        # @require_google_login # 1. 確保已登入
        # @require_group(allowed_groups=[UserGroup.ADMIN]) # 2. 檢查是否為管理員
        # def admin_only_page() -> rx.Component:
        #     return rx.vstack(
        #         rx.heading(f"管理員專區 - 歡迎 {AppState.user_name}"), # 使用 AppState
        #         # ... 管理員內容 ...
        #     )
        ```
* **未授權處理 (UNAUTHORIZED_HANDLING):**
    * 當 `require_group` 檢查失敗時，應向使用者提供清晰的反饋。
    * 可以顯示一個標準的「未授權」組件（如 `default_unauthorized_view_factory` 所示），或導向到一個特定的未授權頁面。
    * 未授權組件應說明使用者為何無法存取，以及可能需要的權限。
* **群組管理 (GROUP_MANAGEMENT_INTERFACE):**
    * 雖然不直接是程式設計規範的一部分，但一個完整的 RBAC 系統通常需要一個管理介面，讓具備相應權限的使用者 (例如系統管理員) 能夠管理使用者及其所屬的群組。規範中可提及此需求。

##### 3. 安全性考量 (SECURITY_CONSIDERATIONS)

* **敏感資訊保護:** `GOOGLE_CLIENT_SECRET` 應被視為機密資訊，妥善保管，切勿直接寫在前端程式碼或版本控制系統中。應使用環境變數或安全的密鑰管理服務。
* **重新導向 URI 驗證:** 確保在 Google Cloud Console 中設定的「已授權 JavaScript 來源」和「已授權的重新導向 URI」是準確且限制性的，以防止釣魚攻擊和 token 洩漏。
* **ID Token 驗證:** `reflex-google-auth` 函式庫負責處理 Google ID Token 的驗證。確保使用的是最新版本的函式庫。
* **CSRF 與 XSS 防護:** Reflex 框架通常會提供 CSRF 保護機制。開發時應注意避免 XSS 漏洞，例如不要直接將未經處理的使用者輸入渲染為 HTML。

## 資料庫 (DATABASE)

### NoSQL 指南 (Guidelines for NOSQL)

#### MongoDB

##### Beanie ODM 與 Async Motor 實踐指南 (BEANIE_MOTOR_GUIDE)

* **初始化與生命週期管理 (INITIALIZATION_LIFESPAN_MANAGEMENT):**
    * Beanie 的初始化以及 `AsyncIOMotorClient` 的連線管理，應透過定義一個非同步上下文管理器 (`@asynccontextmanager`) 並將其加入 Reflex 應用程式的 `lifespan_tasks` 清單來實現。這種方式可以更優雅地管理資源的設定與清理。
    * `asynccontextmanager` 應包含 `AsyncIOMotorClient` 實例的建立、`beanie.init_beanie` 的呼叫，以及在 `finally` 區塊中關閉 `AsyncIOMotorClient` 實例。
    * 範例 (通常在專案的 `rxconfig.py` 或主應用程式設定檔 `your_app/your_app.py` 中):
        ```python
        # your_app/your_app.py (或 rxconfig.py)
        import reflex as rx
        import motor.motor_asyncio
        from beanie import init_beanie
        from contextlib import asynccontextmanager
        from typing import AsyncIterator
        # from your_app.state import AppState # 假設 AppState 是您的主狀態

        # 假設您的 Beanie Document 模型定義在 your_app.models 模組
        # 例如: from your_app.models import User, Product 

        _motor_client: motor.motor_asyncio.AsyncIOMotorClient | None = None

        @asynccontextmanager
        async def mongodb_lifespan_manager(app: rx.App) -> AsyncIterator[None]:
            """管理 MongoDB 連線和 Beanie 初始化的非同步上下文管理器。"""
            global _motor_client
            # 建議從 rx.Config 或環境變數讀取設定
            # config = rx.get_config()
            # db_connection_string = config.db_url # 假設您在 rx.Config 中定義了 db_url
            db_connection_string = "mongodb://localhost:27017" # 範例連接字串
            db_name = "mydatabase" # 您的資料庫名稱

            print(f"Lifespan: 正在連線至 MongoDB ({db_name})...")
            _motor_client = motor.motor_asyncio.AsyncIOMotorClient(db_connection_string)
            
            try:
                await init_beanie(
                    database=_motor_client[db_name],
                    document_models=[
                        "your_app.models.User",  # 包含身分驗證相關欄位的 User 模型
                        "your_app.models.Product", # 範例 Product 模型
                        # 列出所有其他的 Beanie Document 模型路徑
                    ]
                )
                print(f"Lifespan: 已連線至 MongoDB ({db_name}) 並初始化 Beanie。")
                yield # 應用程式運行階段
            finally:
                if _motor_client:
                    _motor_client.close()
                    print("Lifespan: 已關閉 MongoDB 連線。")
                _motor_client = None
        
        # 在定義 App 實例時加入 lifespan_tasks
        # app = rx.App(
        #     state=AppState, 
        #     lifespan_tasks=[mongodb_lifespan_manager],
        #     # ... 其他 App 設定
        # )
        ```
    * **重要提示**:
        * 使用 `@asynccontextmanager` 可以確保資源（如資料庫連線）在應用程式啟動時被正確設定，並在應用程式結束時（即使發生錯誤）被妥善清理。
        * `yield` 語句之前的部分會在應用程式啟動時執行，之後的部分 (通常在 `finally` 區塊中) 會在應用程式關閉時執行。
        * 在 `init_beanie` 的 `document_models` 參數中，使用模型的完整字串路徑 (例如 `"your_app.models.User"`) 是推薦的做法，以避免循環匯入問題。

* **模型定義 (MODEL_DEFINITION):**
    * 所有 MongoDB 的文件模型均須繼承 `beanie.Document`。
    * 利用 Pydantic 的特性進行嚴謹的類型提示 (type hints) 與資料驗證 (validation)。
    * 應在模型內部使用 `Settings` 內部類別來配置集合名稱 (collection name) 或其他 Beanie 特定設定。
    * **User 模型範例 (整合身分驗證需求):**
        ```python
        # your_app/models.py
        from typing import Optional, List
        from pydantic import BaseModel, EmailStr, Field
        from beanie import Document, Indexed
        from enum import Enum # 用於 UserGroup
        import datetime # 用於 last_login

        # 從 your_app.enums 匯入 (如果 UserGroup 在那裡定義)
        # from .enums import UserGroup 
        # 為了範例獨立性，再次定義 UserGroup
        class UserGroup(str, Enum):
            ADMIN = "系統管理員"
            EDITOR = "編輯者"
            VIEWER = "檢視者"
            AUTHENTICATED_USER = "已驗證使用者"

        class Address(BaseModel):
            street: str
            city: str
            zip_code: str

        class User(Document):
            fullname: Optional[str] = None
            email: Indexed(EmailStr, unique=True) # Google Email
            google_sub: Indexed(str, unique=True, sparse=True) # Google User ID
            age: Optional[int] = Field(None, gt=0)
            addresses: List[Address] = Field(default_factory=list)
            groups: List[UserGroup] = Field(default_factory=lambda: [UserGroup.VIEWER, UserGroup.AUTHENTICATED_USER])
            created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
            last_login: Optional[datetime.datetime] = None

            class Settings:
                name = "users" # 明確指定集合名稱
        ```

* **非同步操作 (ASYNC_OPERATIONS):**
    * 所有使用 Beanie 進行的資料庫互動都必須採用 `async/await` 語法。

* **查詢與檢索 (QUERYING_RETRIEVAL):**
    * 優先使用 Beanie 提供的查詢 API。
    * 善用 Beanie 內建的查詢運算子。
    * 使用 `.project()` 方法來指定查詢時僅返回需要的欄位。

* **資料建立與更新 (DATA_CREATION_UPDATE):**
    * 使用 `.insert()`, `.replace()`, `.save()`, `.update()` 等方法。
    * **使用者創建/更新範例 (在 `AuthState.on_success` 中):**
        ```python
        # # (部分程式碼，展示如何在 AuthState 的 on_success 中創建/更新 User)
        # from your_app.models import User, UserGroup 
        # from beanie.operators import Set # 用於更新
        # import datetime
        # # ...
        # async def on_success(self, id_token: dict):
        #     await super().on_success(id_token)
        #     if self.token_is_valid:
        #         user_email = self.tokeninfo.get("email")
        #         google_sub = self.tokeninfo.get("sub")
        #         user_name = self.tokeninfo.get("name")
        #
        #         current_groups = []
        #         if google_sub: 
        #             existing_user = await User.find_one(User.google_sub == google_sub)
        #             if not existing_user:
        #                 default_groups = [UserGroup.VIEWER, UserGroup.AUTHENTICATED_USER]
        #                 new_user = User(
        #                     fullname=user_name,
        #                     email=user_email,
        #                     google_sub=google_sub,
        #                     groups=default_groups,
        #                     last_login=datetime.datetime.utcnow()
        #                 )
        #                 await new_user.insert()
        #                 current_groups = new_user.groups
        #                 print(f"新使用者 {user_name} 已創建。")
        #             else:
        #                 # 更新現有使用者資訊
        #                 await existing_user.update(
        #                     Set({User.fullname: user_name, User.last_login: datetime.datetime.utcnow()})
        #                 )
        #                 current_groups = existing_user.groups
        #                 print(f"使用者 {existing_user.fullname} 已存在，資訊已更新。")
        #             self._app_user_groups_var = current_groups # 更新 rx.Var
        # # ...
        ```

* **資料刪除 (DATA_DELETION):**
    * 使用 `.delete()` 方法。

* **聚合框架 (AGGREGATION_FRAMEWORK):**
    * 使用 `.aggregate()` 方法執行 MongoDB 的聚合管道操作。

* **索引管理 (INDEXING):**
    * 透過在 `beanie.Document` 模型的欄位上使用 `Indexed()` 來聲明索引。
    * `User` 模型中的 `email` 和 `google_sub` 欄位應建立唯一索引。

* **結構驗證 (SCHEMA_VALIDATION):**
    * Beanie 強制使用 Pydantic 模型，確保資料寫入前的驗證。

* **關聯與嵌入 (RELATIONSHIPS_EMBEDDING):**
    * 根據資料存取模式合理選擇使用嵌入式文件或引用。
    * **Beanie `Link` 與 `BackLink` 範例:**
        ```python
        # from typing import List 
        # from beanie import Document, Link, BackLink, Indexed
        # from pydantic import Field
        # from your_app.models import User # 假設 User 已定義

        # class Post(Document):
        #     title: Indexed(str)
        #     content: str
        #     author: Link[User] 

        #     class Settings:
        #         name = "posts"

        # # 在 User 模型中 (your_app/models.py)
        # # class User(Document):
        # #     ... (其他欄位) ...
        # #     # 若要從 User 反查其所有 Post (一對多關係)
        # #     # Beanie 的 BackLink 通常用於 Document 實例上，而非直接定義為模型欄位進行查詢
        # #     # 查詢 User 的 Post 通常是: posts = await Post.find(Post.author.id_ == user_instance.id).to_list()
        # #     # BackLink 更適用於在載入一個 Document 時自動預取相關聯的 Document。
        # #     # 例如，如果 Post 有一個 category: Link[Category]，則 Category 可以有
        # #     # posts: List[BackLink[Post]] = Field(original_field="category")
        # #     # 以便在載入 Category 時，可以 .fetch_link(Category.posts)
        #
        # # 查詢 Post 並取得作者資訊
        # # post_with_author = await Post.find_one(Post.title == "My First Post", fetch_links=True)
        # # if post_with_author and post_with_author.author: # author 此時會是 User 物件
        # #     print(f"文章 '{post_with_author.title}' 的作者是 {post_with_author.author.fullname}")
        ```

* **效能考量 (PERFORMANCE_CONSIDERATIONS):**
    * 正確使用索引和投影，考慮批次操作。
