from flask import Flask, render_template, jsonify,request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from functools import wraps
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24).hex()

basedir = os.path.abspath(os.path.dirname(__file__))
instance_path = os.path.join(basedir, "instance")
os.makedirs(instance_path, exist_ok=True)

# 双数据库绑定
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(instance_path, "users.db")
app.config["SQLALCHEMY_BINDS"] = {
    "students": "sqlite:///" + os.path.join(instance_path, "students.db")
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------- 模型 --------------------
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Student(db.Model):
    __bind_key__ = "students"
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    major = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

# -------------------- 登录装饰器 --------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("请先登录管理员账户", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# -------------------- 公共路由 --------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("用户名和密码不能为空", "error")
            return redirect(url_for("login"))

        user = User.query.filter_by(username=username).first()
        if not user:
            flash("管理员账户不存在", "error")
            return redirect(url_for("login"))
        if not user.check_password(password):
            flash("密码错误", "error")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session["username"] = user.username
        flash(f"欢迎，{user.username}！", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if len(username) < 3:
            errors.append("用户名至少3个字符")
        if "@" not in email or "." not in email:
            errors.append("邮箱格式不正确")
        if len(password) < 6:
            errors.append("密码至少6位")
        if password != confirm:
            errors.append("两次密码不一致")
        if User.query.filter_by(username=username).first():
            errors.append("用户名已被注册")
        if User.query.filter_by(email=email).first():
            errors.append("邮箱已被注册")

        if errors:
            for e in errors:
                flash(e, "error")
            return redirect(url_for("register"))

        new_admin = User(username=username, email=email)
        new_admin.set_password(password)
        db.session.add(new_admin)
        db.session.commit()

        flash("管理员账户注册成功，请登录", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("已安全退出", "success")
    return redirect(url_for("login"))

# -------------------- 后台管理页面 --------------------
@app.route("/dashboard")
@login_required
def dashboard():
    student_count = Student.query.count()
    return render_template("dashboard.html",
                           username=session.get("username"),
                           student_count=student_count)

@app.route("/students")
@login_required
def student_list():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    pagination = Student.query.order_by(Student.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    students = pagination.items
    return render_template("students.html", students=students, pagination=pagination)

# 添加新生 - 显示表单
@app.route("/students/new")
@login_required
def student_new_form():
    empty_form = {
        "student_id": "",
        "name": "",
        "gender": "",
        "age": "",
        "major": "",
        "phone": "",
        "email": ""
    }
    return render_template("student_form.html", form_data=empty_form, edit_mode=False)

# 添加新生 - 处理提交
@app.route("/students/add", methods=["POST"])
@login_required
def student_add():
    student_id = request.form.get("student_id", "").strip()
    name = request.form.get("name", "").strip()
    gender = request.form.get("gender", "").strip()
    age = request.form.get("age", type=int)
    major = request.form.get("major", "").strip()
    phone = request.form.get("phone", "").strip() or None
    email = request.form.get("email", "").strip().lower() or None

    errors = []
    if not student_id or not name or not gender or not major:
        errors.append("学号、姓名、性别、专业为必填项")
    if age is None or age <= 0 or age > 120:
        errors.append("请输入合法年龄")
    if Student.query.filter_by(student_id=student_id).first():
        errors.append("该学号已存在")

    if errors:
        for e in errors:
            flash(e, "error")
        form_data = {
            "student_id": student_id,
            "name": name,
            "gender": gender,
            "age": age or "",
            "major": major,
            "phone": phone or "",
            "email": email or ""
        }
        return render_template("student_form.html", form_data=form_data, edit_mode=False)

    new_student = Student(
        student_id=student_id, name=name, gender=gender,
        age=age, major=major, phone=phone, email=email
    )
    db.session.add(new_student)
    db.session.commit()

    flash(f"新生 {name} 添加成功", "success")
    return redirect(url_for("student_list"))

@app.route("/students/<int:student_id>/edit", methods=["GET", "POST"])
@login_required
def student_edit(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == "POST":
        student.name = request.form.get("name", "").strip()
        student.gender = request.form.get("gender", "").strip()
        student.age = request.form.get("age", type=int)
        student.major = request.form.get("major", "").strip()
        student.phone = request.form.get("phone", "").strip() or None
        student.email = request.form.get("email", "").strip().lower() or None

        errors = []
        if not student.name or not student.gender or not student.major:
            errors.append("姓名、性别、专业不能为空")
        if student.age is None or student.age <= 0:
            errors.append("年龄格式错误")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("student_form.html", form_data=student, edit_mode=True)

        db.session.commit()
        flash("新生信息更新成功", "success")
        return redirect(url_for("student_list"))

    return render_template("student_form.html", form_data=student, edit_mode=True)

@app.route("/students/<int:student_id>/delete", methods=["POST"])
@login_required
def student_delete(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash(f"已删除新生 {student.name}", "success")
    return redirect(url_for("student_list"))

@app.route("/api/students")
@login_required
def api_students():
    students = Student.query.order_by(Student.created_at.desc()).all()
    data = []
    for s in students:
        data.append({
            "id": s.id,
            "student_id": s.student_id,
            "name": s.name,
            "gender": s.gender,
            "age": s.age,
            "major": s.major,
            "phone": s.phone or "",
            "email": s.email or ""
        })
    return jsonify(data)

@app.route("/api/students/add", methods=["POST"])
@login_required
def api_student_add():
    student_id = request.form.get("student_id", "").strip()
    name = request.form.get("name", "").strip()
    gender = request.form.get("gender", "").strip()
    age = request.form.get("age", type=int)
    major = request.form.get("major", "").strip()
    phone = request.form.get("phone", "").strip() or None
    email = request.form.get("email", "").strip().lower() or None

    errors = []
    if not student_id or not name or not gender or not major:
        errors.append("学号、姓名、性别、专业为必填项")
    if age is None or age <= 0 or age > 120:
        errors.append("请输入合法年龄")
    if Student.query.filter_by(student_id=student_id).first():
        errors.append("该学号已存在")

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    new_student = Student(student_id=student_id, name=name, gender=gender,
                          age=age, major=major, phone=phone, email=email)
    db.session.add(new_student)
    db.session.commit()
    return jsonify({"success": True, "message": f"新生 {name} 添加成功"}), 201


@app.route("/api/students/<int:student_id>/edit", methods=["POST"])
@login_required
def api_student_edit(student_id):
    student = Student.query.get_or_404(student_id)
    student.name = request.form.get("name", "").strip()
    student.gender = request.form.get("gender", "").strip()
    student.age = request.form.get("age", type=int)
    student.major = request.form.get("major", "").strip()
    student.phone = request.form.get("phone", "").strip() or None
    student.email = request.form.get("email", "").strip().lower() or None

    errors = []
    if not student.name or not student.gender or not student.major:
        errors.append("姓名、性别、专业不能为空")
    if student.age is None or student.age <= 0:
        errors.append("年龄格式错误")

    if errors:
        return jsonify({"success": False, "errors": errors}), 400

    db.session.commit()
    return jsonify({"success": True, "message": "学生信息更新成功"})


@app.route("/api/students/<int:student_id>/delete", methods=["POST"])
@login_required
def api_student_delete(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({"success": True, "message": f"已删除 {student.name}"})

# -------------------- 启动 --------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ 管理员数据库 (users.db) 已就绪")
        print("✅ 新生数据库 (students.db) 已就绪")
    print("🚀 服务启动: http://127.0.0.1:5000")
    app.run(debug=True, host="127.0.0.1", port=5000)