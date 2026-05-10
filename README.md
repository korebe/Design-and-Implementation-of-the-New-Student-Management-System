# 新生管理系统设计与实现文档

## 1. 项目概述

本项目是一个基于 **Flask + SQLite + Tkinter + C** 的新生信息管理系统。系统采用 **BS 与 CS 混合架构**：  
- **Flask 后端** 提供 Web 管理界面和 RESTful JSON API，管理员可通过浏览器或桌面客户端访问。  
- **SQLite 双数据库** 将管理员账户与新生数据分离存储，确保数据安全。  
- **Tkinter 桌面客户端** 通过 HTTP 请求调用后端 API，实现新生信息的增删改查，并借助 C 语言动态库进行快速排序。  
- **C 语言算法库** 封装快速排序算法，由桌面客户端通过 `ctypes` 调用，提升大数据量下的排序性能。

系统适用于高校迎新场景，可高效管理新生基本信息，并支持管理员权限控制。
~~~~
---

## 2. 项目结构

```
新生管理系统/
├── app.py                  # Flask 主程序（后端 + API）
├── sort_algorithm.c        # C 语言排序算法源码
├── sort_algorithm.so       # 编译生成的动态链接库（Linux）
├── student_client.py       # Tkinter 桌面客户端
├── templates/
│   ├── base.html           # 后台管理页面公共模板
│   ├── login.html          # 管理员登录页面
│   ├── register.html       # 管理员注册页面
│   ├── dashboard.html      # 仪表盘页面
│   ├── students.html       # 新生列表页面（Web）
│   └── student_form.html   # 新生添加/编辑表单（Web）
└── instance/               # 自动生成的数据库文件夹
    ├── users.db            # 管理员账户数据库
    └── students.db         # 新生信息数据库
```

---

## 3. 环境依赖与运行方法

### 3.1 环境要求

- Python 3.8+
- GCC / MinGW（用于编译 C 库）
- 操作系统：Windows / Linux / macOS

### 3.2 安装依赖

进入项目目录，创建并激活虚拟环境（推荐），然后安装 Python 包：

```bash
python3 -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
pip install flask flask-sqlalchemy requests
```

### 3.3 编译 C 算法库

在项目根目录下执行：

```bash
gcc -shared -fPIC -o sort_algorithm.so sort_algorithm.c    # Linux/Mac
gcc -shared -o sort_algorithm.dll sort_algorithm.c         # Windows (MinGW)
```

### 3.4 启动系统

1. **启动 Flask 后端服务**  
   ```bash
   python app.py
   ```
   启动后控制台会显示：
   ```
   ✅ 数据库已就绪
   ✅ 已注册路由：/api/students
   🚀 服务启动: http://127.0.0.1:5000
   ```

2. **启动桌面客户端**（可选）  
   另开一个终端，同样进入项目目录：
   ```bash
   python student_client.py
   ```
   登录后即可使用桌面版功能。

3. **Web 端访问**  
   打开浏览器访问 `http://127.0.0.1:5000`，注册管理员账户后登录。

---

## 4. 功能模块

### 4.1 管理员账户管理（users.db）
- **注册**：管理员填写用户名、邮箱、密码，后端验证唯一性后存入 `users` 表，密码使用 `Werkzeug` 安全哈希。
- **登录 / 退出**：基于 Flask Session 实现，登录后所有敏感操作需登录验证。
- **权限控制**：通过装饰器 `@login_required` 保护所有管理路由和 API。

### 4.2 新生信息管理（students.db）
- **添加新生**：学号、姓名、性别、年龄、专业为必填项，电话和邮箱为选填。后端进行字段合法性验证及学号唯一性检查。
- **编辑新生**：除学号外其他字段可修改，保存前校验必填项。
- **删除新生**：支持单条删除，删除前弹窗确认。
- **列表展示**：按录入时间倒序排列，支持分页（Web 端每页10条，桌面端全量加载后本地排序）。
- **排序**：
  - Web 端暂未实现服务器端排序。
  - 桌面客户端调用 C 语言库，支持按年龄升序/降序、按学号升序三种排序模式。

### 4.3 双数据库设计
- `users.db`：存储管理员账户，表 `users`。
- `students.db`：存储新生数据，表 `students`，通过 `__bind_key__` 绑定到独立数据库文件，隔离敏感数据。

---

## 5. 数据库设计

### 5.1 管理员表 (users)
| 字段名         | 类型        | 约束        | 说明           |
|---------------|-------------|-------------|----------------|
| id            | INTEGER     | PRIMARY KEY | 自增主键       |
| username      | VARCHAR(80) | UNIQUE, NOT NULL | 用户名       |
| email         | VARCHAR(120)| UNIQUE, NOT NULL | 邮箱         |
| password_hash | VARCHAR(256)| NOT NULL    | 密码哈希       |
| created_at    | DATETIME    |             | 创建时间       |

### 5.2 新生信息表 (students)
| 字段名      | 类型        | 约束        | 说明           |
|------------|-------------|-------------|----------------|
| id         | INTEGER     | PRIMARY KEY | 自增主键       |
| student_id | VARCHAR(20) | UNIQUE, NOT NULL | 学号         |
| name       | VARCHAR(50) | NOT NULL    | 姓名           |
| gender     | VARCHAR(10) | NOT NULL    | 性别           |
| age        | INTEGER     | NOT NULL    | 年龄           |
| major      | VARCHAR(100)| NOT NULL    | 专业           |
| phone      | VARCHAR(20) |             | 电话（可选）   |
| email      | VARCHAR(120)|             | 邮箱（可选）   |
| created_at | DATETIME    |             | 录入时间       |

---

## 6. 后端 API 接口说明

### 6.1 Web 页面路由（返回 HTML）

| 路径                      | 方法   | 说明                     |
|---------------------------|--------|--------------------------|
| `/`                       | GET    | 首页重定向               |
| `/login`                  | GET/POST | 登录页面               |
| `/register`               | GET/POST | 注册页面               |
| `/logout`                 | GET    | 退出登录                 |
| `/dashboard`              | GET    | 仪表盘（需登录）         |
| `/students`               | GET    | 新生列表（分页）         |
| `/students/new`           | GET    | 添加表单页               |
| `/students/add`           | POST   | 处理新增（网页表单）     |
| `/students/<id>/edit`     | GET/POST | 编辑页面及处理        |
| `/students/<id>/delete`   | POST   | 删除新生（网页）         |

### 6.2 JSON API（供桌面客户端调用）

| 路径                          | 方法   | 说明                     |
|-------------------------------|--------|--------------------------|
| `/api/students`               | GET    | 获取所有新生 JSON 列表   |
| `/api/students/add`           | POST   | 添加新生（接收表单数据） |
| `/api/students/<id>/edit`     | POST   | 编辑新生信息             |
| `/api/students/<id>/delete`   | POST   | 删除新生                 |

**添加接口示例**：
请求：`POST /api/students/add`  
Body（表单格式）：
```
student_id=2026001&name=张三&gender=男&age=19&major=计算机科学&phone=13800138000&email=zhangsan@example.com
```
成功响应（201）：
```json
{"success": true, "message": "新生 张三 添加成功"}
```
失败响应（400）：
```json
{"success": false, "errors": ["该学号已存在"]}
```

---

## 7. C 语言排序算法设计

### 7.1 数据结构

```c
typedef struct {
    int id;
    char student_id[20];
    char name[50];
    char gender[10];
    int age;
    char major[100];
    char phone[20];
    char email[120];
} Student;
```

### 7.2 排序函数

```c
void sort_students(Student *students, int count, int sort_mode);
```

- `sort_mode = 0`：按年龄升序（`qsort` + `compare_age_asc`）
- `sort_mode = 1`：按年龄降序（`qsort` + `compare_age_desc`）
- `sort_mode = 2`：按学号升序（`qsort` + `compare_id_asc`）

算法基于 C 标准库的 `qsort` 实现，时间复杂度 O(n log n)，适合处理数千至数万条数据。

---

## 8. 桌面客户端架构

### 8.1 主要类与模块

- **StudentClient**  
  - 负责 UI 构建与事件绑定。  
  - 内部使用 `requests.Session` 保持 Cookie，实现持久登录。

- **CStudent (ctypes.Structure)**  
  - 与 C 结构体一一映射，用于排序时在 Python 与 C 之间传递数据。

- **动态库加载**  
  ```python
  clib = ctypes.CDLL('./sort_algorithm.so')
  clib.sort_students.argtypes = [POINTER(CStudent), c_int, c_int]
  ```

### 8.2 界面组成
- **登录 / 注册界面**：输入用户名密码，调用 `/login` 或 `/register`。
- **主界面**：
  - 菜单栏：刷新、添加、退出。
  - 工具栏：三个排序按钮（年龄↑、年龄↓、学号↑）。
  - Treeview 表格：展示所有学生信息。
  - 底部操作按钮：添加、编辑、删除。
- **弹出窗口**：
  - 添加/编辑窗口使用 `Toplevel` 实现，包含表单字段和提交按钮。

### 8.3 排序流程
1. 从服务器获取最新学生列表（JSON）。
2. 将 Python 字典列表转换为 C 结构体数组。
3. 调用 `clib.sort_students(c_array, n, mode)`。
4. 将排序后的 C 结构体数组解码回 Python 列表，刷新 Treeview 显示。

---

## 9. 安全策略

- 密码使用 `Werkzeug.security.generate_password_hash` 进行**加盐哈希**存储，不可逆。
- 所有敏感 API 和页面均通过 `@login_required` 检查 Session。
- Session 密钥由 `os.urandom(24)` 生成，每次启动随机变化。
- 表单输入在后端进行严格验证（长度、格式、唯一性），防止非法数据入库。

---

## 10. 测试与使用示例

### 10.1 Web 端流程
1. 访问 `http://127.0.0.1:5000` → 注册管理员 → 登录。
2. 进入仪表盘，点击“管理新生信息”。
3. 点击“添加新生”，填写表单提交。
4. 列表页可编辑、删除，支持分页浏览。

### 10.2 桌面端流程
1. 启动 Flask 服务，再启动 `student_client.py`。
2. 登录后自动加载学生列表。
3. 点击“➕ 添加”按钮，在弹出的窗口中输入新生信息并提交。
4. 选择某行后点击“编辑”或“删除”进行相应操作。
5. 点击年龄↑/↓或学号↑按钮，表格排序立即生效。

---

## 11. 常见问题

**Q：编译 C 库时报错找不到 `gcc`**  
A：Linux 执行 `sudo apt install build-essential`；Windows 安装 MinGW 并配置环境变量。

**Q：桌面客户端提示“无法连接到服务器”**  
A：请确保 Flask 已启动且地址为 `http://127.0.0.1:5000`，防火墙未拦截。

**Q：添加新生时提示“信息不合法”但网页端正常**  
A：请确认客户端代码中田野名映射（中文→英文）已正确设置，可参照第 7 节 API 要求。

**Q：浏览器访问 API 返回 404**  
A：检查 `app.py` 是否已包含 `/api/students` 路由，并确保 `jsonify` 已导入。

---

## 12. 项目总结

本项目实现了完整的新生信息管理功能，技术栈涵盖 Web 开发、桌面应用、数据库设计和 C 语言底层算法集成，具有以下特点：

- **双数据库隔离**，安全性高。
- **BS/CS 双端支持**，兼顾便捷与性能。
- **C 算法加速**，演示了 Python 调用 C 库的典型模式。
- **代码结构清晰**，易于扩展和维护。

可作为高校信息管理系统的原型或课程设计作品。
