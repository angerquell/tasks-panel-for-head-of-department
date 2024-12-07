from app import db, login
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, DateTime, Enum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from functools import wraps
from flask import abort
from flask_login import current_user

class Role(enum.Enum):
    HoD = 'Руководитель отдела'
    Developer = 'Разработчик'
    Tester = 'Тестировщик ПО'


class DifficultyTask(enum.Enum):
    EASY = "Простая"
    MEDIUM = "Средняя"
    HARD = "Сложная"

COEFFICIENT_DIFF = {
    "EASY" : 1,
    "MEDIUM" : 2,
    "HARD" : 3 

}
class TaskType(enum.Enum):
    SOFTWARE_DEVELOPMENT = "Разработка ПО"
    SOFTWARE_DESIGN = "Проектирование ПО"
    BUG_FIXING = "Исправление ошибок"
    MANUAL_TESTING = "Ручное тестирование"
    AUTOMATED_TESTING = "Автоматизированное тестирование"
    PERFORMANCE_TESTING = "Тестирование производительности"


ROLE_TASK_TYPES = {
    Role.Developer: [
        TaskType.SOFTWARE_DEVELOPMENT,
        TaskType.SOFTWARE_DESIGN,
        TaskType.BUG_FIXING
    ],
    Role.Tester: [
        TaskType.MANUAL_TESTING,
        TaskType.AUTOMATED_TESTING,
        TaskType.PERFORMANCE_TESTING
    ],
}


class User(UserMixin, db.Model):
    username: Mapped[str] = mapped_column(String(256), unique=True, index=True)
    id: Mapped[int] = mapped_column(primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)
    tasks = relationship("Tasks", backref="user", lazy="joined")

    def __repr__(self):
        return self.id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Tasks(db.Model):
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(256))
    type: Mapped[TaskType] = mapped_column(Enum(TaskType),nullable= False)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), index=True)
    difficulty: Mapped[DifficultyTask] = mapped_column(Enum(DifficultyTask), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)  
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)       
    coefficient: Mapped[int] = mapped_column(Integer, nullable=False) 

    def calculation_coefficient(self, start_date, end_date, dificulty):
        day = None
        if (end_date-start_date).days == 0:
            day = 1 
        else:
            day = (end_date-start_date).days
        self.coefficient = round(dificulty / day, 2) 

    def s_time(self, t):
        return t.strftime("%d.%m.%Y")

def check_role(roles: list):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not  in roles:
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator