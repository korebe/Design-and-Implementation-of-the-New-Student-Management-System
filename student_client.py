import tkinter as tk
from tkinter import ttk, messagebox
import requests
import ctypes
import os

# ---------- 加载 C 排序库 ----------
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sort_algorithm.so')
try:
    clib = ctypes.CDLL(lib_path)
except OSError:
    lib_path = lib_path.replace('.so', '.dll')
    clib = ctypes.CDLL(lib_path)

class CStudent(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("student_id", ctypes.c_char * 20),
        ("name", ctypes.c_char * 50),
        ("gender", ctypes.c_char * 10),
        ("age", ctypes.c_int),
        ("major", ctypes.c_char * 100),
        ("phone", ctypes.c_char * 20),
        ("email", ctypes.c_char * 120),
    ]

clib.sort_students.argtypes = [ctypes.POINTER(CStudent), ctypes.c_int, ctypes.c_int]

BASE_URL = "http://127.0.0.1:5000"

class StudentClient:
    def __init__(self, root):
        self.root = root
        self.root.title("新生管理系统 - 桌面客户端")
        self.root.geometry("1000x650")
        self.session = requests.Session()
        self.current_students = []
        self.show_login()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # ---------- 登录界面 ----------
    def show_login(self):
        self.clear_screen()
        frame = tk.Frame(self.root, padx=40, pady=40)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(frame, text="管理员登录", font=("Arial", 18, "bold")).grid(row=0, columnspan=2, pady=10)
        tk.Label(frame, text="用户名").grid(row=1, column=0, sticky="e", pady=5)
        self.entry_user = tk.Entry(frame)
        self.entry_user.grid(row=1, column=1, pady=5)
        tk.Label(frame, text="密码").grid(row=2, column=0, sticky="e", pady=5)
        self.entry_pass = tk.Entry(frame, show="*")
        self.entry_pass.grid(row=2, column=1, pady=5)

        tk.Button(frame, text="登录", command=self.login, width=20).grid(row=3, columnspan=2, pady=15)
        tk.Button(frame, text="注册管理员", command=self.show_register).grid(row=4, columnspan=2)

    def login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return
        try:
            resp = self.session.post(f"{BASE_URL}/login", data={"username": username, "password": password})
            if "欢迎" in resp.text:
                self.username = username
                self.show_main()
            else:
                messagebox.showerror("登录失败", "用户名或密码错误")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("连接错误", "请先启动 Flask 服务器")

    # ---------- 注册界面 ----------
    def show_register(self):
        self.clear_screen()
        frame = tk.Frame(self.root, padx=40, pady=40)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(frame, text="注册管理员", font=("Arial", 18, "bold")).grid(row=0, columnspan=2, pady=10)
        labels = ["用户名", "邮箱", "密码", "确认密码"]
        self.entries = {}
        for i, label in enumerate(labels):
            tk.Label(frame, text=label).grid(row=i+1, column=0, sticky="e", pady=5)
            show = "*" if "密码" in label else None
            ent = tk.Entry(frame, show=show)
            ent.grid(row=i+1, column=1, pady=5)
            self.entries[label] = ent

        tk.Button(frame, text="注册", command=self.register, width=20).grid(row=5, columnspan=2, pady=15)
        tk.Button(frame, text="返回登录", command=self.show_login).grid(row=6, columnspan=2)

    def register(self):
        data = {
            "username": self.entries["用户名"].get().strip(),
            "email": self.entries["邮箱"].get().strip(),
            "password": self.entries["密码"].get(),
            "confirm_password": self.entries["确认密码"].get()
        }
        resp = self.session.post(f"{BASE_URL}/register", data=data)
        if "注册成功" in resp.text:
            messagebox.showinfo("成功", "注册成功，请登录")
            self.show_login()
        else:
            messagebox.showerror("注册失败", "请检查输入")

    # ---------- 主界面 ----------
    def show_main(self):
        self.clear_screen()

        # 菜单栏
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        menubar.add_command(label="刷新列表", command=self.refresh_students)
        menubar.add_command(label="添加新生", command=self.add_student_window)
        menubar.add_command(label="退出登录", command=self.logout)

        # 排序工具栏
        toolbar = tk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(toolbar, text="排序方式(C算法)：").pack(side=tk.LEFT, padx=5)
        tk.Button(toolbar, text="年龄↑", command=lambda: self.sort_students(0)).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="年龄↓", command=lambda: self.sort_students(1)).pack(side=tk.LEFT, padx=3)
        tk.Button(toolbar, text="学号↑", command=lambda: self.sort_students(2)).pack(side=tk.LEFT, padx=3)

        # 表格
        columns = ("id", "学号", "姓名", "性别", "年龄", "专业", "电话", "邮箱")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=20)
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=40, stretch=False)
        for col in columns[1:]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 操作按钮（主界面底部）
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="➕ 添加", command=self.add_student_window).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✏️ 编辑", command=self.edit_student_window).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ 删除", command=self.delete_student).pack(side=tk.LEFT, padx=5)

        self.refresh_students()

    # ---------- 数据获取 ----------
    def refresh_students(self):
        try:
            resp = self.session.get(f"{BASE_URL}/api/students")
            if resp.status_code == 200:
                self.current_students = resp.json()
                self._display_students()
            else:
                messagebox.showerror("错误", "获取数据失败，请重新登录")
        except Exception as e:
            messagebox.showerror("网络错误", str(e))

    def _display_students(self):
        self.tree.delete(*self.tree.get_children())
        for stu in self.current_students:
            self.tree.insert("", tk.END, values=(
                stu["id"], stu["student_id"], stu["name"], stu["gender"],
                stu["age"], stu["major"], stu.get("phone", ""), stu.get("email", "")
            ))

    # ---------- C 排序 ----------
    def sort_students(self, mode):
        if not self.current_students:
            return
        n = len(self.current_students)
        c_array = (CStudent * n)()
        for i, s in enumerate(self.current_students):
            c_stu = CStudent()
            c_stu.id = s["id"]
            c_stu.student_id = s["student_id"].encode()
            c_stu.name = s["name"].encode()
            c_stu.gender = s["gender"].encode()
            c_stu.age = s["age"]
            c_stu.major = s["major"].encode()
            c_stu.phone = s.get("phone", "").encode()
            c_stu.email = s.get("email", "").encode()
            c_array[i] = c_stu
        clib.sort_students(c_array, n, mode)
        sorted_list = []
        for i in range(n):
            sorted_list.append({
                "id": c_array[i].id,
                "student_id": c_array[i].student_id.decode(),
                "name": c_array[i].name.decode(),
                "gender": c_array[i].gender.decode(),
                "age": c_array[i].age,
                "major": c_array[i].major.decode(),
                "phone": c_array[i].phone.decode(),
                "email": c_array[i].email.decode()
            })
        self.current_students = sorted_list
        self._display_students()

    # ---------- 添加新生窗口 ----------
    def add_student_window(self):
        win = tk.Toplevel(self.root)
        win.title("添加新生")
        win.geometry("400x400")
        win.grab_set()  # 强制停留在此窗口

        fields = ["学号", "姓名", "性别", "年龄", "专业", "电话", "邮箱"]
        entries = {}
        for i, field in enumerate(fields):
            tk.Label(win, text=field).grid(row=i, column=0, sticky="e", padx=10, pady=5)
            ent = tk.Entry(win)
            ent.grid(row=i, column=1, padx=10, pady=5)
            entries[field] = ent
            
        def submit():
            # 中文字段名 → 后端英文字段名映射
            field_map = {
                "学号": "student_id",
                "姓名": "name",
                "性别": "gender",
                "年龄": "age",
                "专业": "major",
                "电话": "phone",
                "邮箱": "email"
            }
            data = {}
            for field in fields:
                eng_key = field_map.get(field)
                if eng_key:
                    data[eng_key] = entries[field].get().strip()

            try:
                resp = self.session.post(f"{BASE_URL}/api/students/add", data=data)
                if resp.status_code == 201:
                    result = resp.json()
                    messagebox.showinfo("成功", result["message"])
                    win.destroy()
                    self.refresh_students()
                else:
                    result = resp.json()
                    msg = "\n".join(result.get("errors", ["添加失败"]))
                    messagebox.showerror("失败", msg)
            except Exception as e:
                messagebox.showerror("错误", str(e))

        tk.Button(win, text="提交", command=submit).grid(row=len(fields), columnspan=2, pady=20)

    # ---------- 编辑窗口 ----------
    def edit_student_window(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一名学生")
            return
        values = self.tree.item(selected[0])["values"]
        stu_id = values[0]
        stu = next((s for s in self.current_students if s["id"] == stu_id), None)
        if not stu:
            messagebox.showerror("错误", "找不到该学生数据")
            return

        win = tk.Toplevel(self.root)
        win.title("编辑新生")
        win.geometry("400x400")
        win.grab_set()

        fields = ["学号", "姓名", "性别", "年龄", "专业", "电话", "邮箱"]
        entries = {}
        key_map = {"学号": "student_id", "姓名": "name", "性别": "gender",
                   "年龄": "age", "专业": "major", "电话": "phone", "邮箱": "email"}
        for i, field in enumerate(fields):
            tk.Label(win, text=field).grid(row=i, column=0, sticky="e", padx=10, pady=5)
            ent = tk.Entry(win)
            ent.grid(row=i, column=1, padx=10, pady=5)
            val = stu.get(key_map[field], "")
            ent.insert(0, str(val))
            if field == "学号":
                ent.config(state="readonly")
            entries[field] = ent

        def submit():
            data = {
                "name": entries["姓名"].get().strip(),
                "gender": entries["性别"].get().strip(),
                "age": entries["年龄"].get().strip(),
                "major": entries["专业"].get().strip(),
                "phone": entries["电话"].get().strip(),
                "email": entries["邮箱"].get().strip()
            }
            try:
                resp = self.session.post(f"{BASE_URL}/api/students/{stu_id}/edit", data=data)
                if resp.status_code == 200:
                    result = resp.json()
                    messagebox.showinfo("成功", result["message"])
                    win.destroy()
                    self.refresh_students()
                else:
                    result = resp.json()
                    msg = "\n".join(result.get("errors", ["更新失败"]))
                    messagebox.showerror("失败", msg)
            except Exception as e:
                messagebox.showerror("错误", str(e))

        tk.Button(win, text="保存", command=submit).grid(row=len(fields), columnspan=2, pady=20)

    # ---------- 删除 ----------
    def delete_student(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择一名学生")
            return
        values = self.tree.item(selected[0])["values"]
        stu_id = values[0]
        name = values[2]
        if messagebox.askyesno("确认删除", f"确定要删除 {name} 吗？"):
            try:
                resp = self.session.post(f"{BASE_URL}/api/students/{stu_id}/delete")
                result = resp.json()
                if result["success"]:
                    messagebox.showinfo("成功", result["message"])
                    self.refresh_students()
                else:
                    messagebox.showerror("失败", result.get("message", "删除失败"))
            except Exception as e:
                messagebox.showerror("错误", str(e))

    def logout(self):
        self.session.get(f"{BASE_URL}/logout")
        self.show_login()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudentClient(root)
    root.mainloop()