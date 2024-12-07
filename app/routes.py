from flask import render_template, flash, redirect, request
import sqlalchemy as sa
from flask_login import login_user, current_user, login_required, logout_user
from app.forms import LoginForm, RegisterForm, AddTask
from app.models import User, Role, check_role, ROLE_TASK_TYPES, Tasks, COEFFICIENT_DIFF
from app import app, db
from datetime import datetime
from sqlalchemy.orm import joinedload

@app.route('/')
@app.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect('/admin_tasks' if current_user.role == Role.HoD else '/all_tasks')
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect('/admin_tasks' if current_user.role == Role.HoD else '/all_tasks')
    
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User(username=form.username.data, role=Role[form.role.data])
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Пользователь успешно зарегистрирован!')
        return redirect('/login')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/admin_tasks' if current_user.role == Role.HoD else '/all_tasks')
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect('/admin_tasks' if current_user.role == Role.HoD else '/all_tasks')
        flash('Введен неверный логин или пароль')
    return render_template('login.html', form=form)

@app.route('/all_tasks', methods=['GET', 'POST'])
@login_required
@check_role([Role.Developer, Role.Tester])
def all_tasks():
    form = AddTask()
    tasks = db.session.execute(sa.select(Tasks).where(Tasks.user_id == current_user.id)).scalars().all()
    form.task_type.choices = [(i.name, i.value) for i in ROLE_TASK_TYPES.get(current_user.role, [])]

    if form.validate_on_submit():
        task = Tasks(
            title=form.title.data,
            description=form.description.data,
            type=form.task_type.data,
            difficulty=form.difficulty.data,
            start_date=form.start_time.data,
            end_date=form.end_time.data,
            user_id=current_user.id
        )
        task.calculation_coefficient(
            end_date=form.end_time.data,
            start_date=form.start_time.data,
            dificulty=COEFFICIENT_DIFF.get(form.difficulty.data)
        )
        db.session.add(task)
        db.session.commit()
        return redirect('/all_tasks')
    return render_template('all_task.html', tasks=tasks, form=form)

@app.route('/admin_tasks')
@login_required
@check_role([Role.HoD])
def admin_tasks():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = db.session.query(Tasks)
    if start_date:
        query = query.filter(Tasks.start_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Tasks.end_date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    tasks = query.all()
    return render_template('admin_tasks.html', tasks=tasks)

def calculate_users_with_coefficients(start_date=None, end_date=None):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = db.session.query(User).filter(User.role.in_([Role.Developer, Role.Tester]))
    users_with_coefs = []
    for user in query.options(joinedload(User.tasks)).all():
        filtered_tasks = [
            task for task in user.tasks
            if (not start_date or task.start_date >= datetime.strptime(start_date, '%Y-%m-%d')) and 
               (not end_date or task.end_date <= datetime.strptime(end_date, '%Y-%m-%d'))
        ]
        if filtered_tasks:
            coef = sum(task.coefficient for task in filtered_tasks) / len(filtered_tasks)
            users_with_coefs.append({
                "username": user.username,
                "role": user.role,
                "id": user.id,
                "tasks": filtered_tasks,
                "coef": round(coef, 2),
                "count": len(filtered_tasks)
            })
    return users_with_coefs

@app.route('/сoefficient_users')
@login_required
@check_role([Role.HoD])
def coeff_users():
    users = calculate_users_with_coefficients()
    return render_template('temp.html', users=users)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/rating_users')
@login_required
@check_role([Role.Developer, Role.Tester])
def rating_users():
    users = calculate_users_with_coefficients()
    users.sort(key=lambda x: x['coef'], reverse=True)
    return render_template('rating_users.html', users=users)
