from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import SubmitField, PasswordField, SelectField, StringField, TextAreaField, DateTimeField
from wtforms.validators import DataRequired, ValidationError
import sqlalchemy 
from app import db
from app.models import User, Role, DifficultyTask, ROLE_TASK_TYPES

class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField('Войти')


class RegisterForm(FlaskForm):
    username = StringField("Логин", validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    role = SelectField('Роль', choices= [(i.name, i.value) for i in Role], validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')
    

    def validate_username(self, username):
        user = db.session.scalar(sqlalchemy.select(User).where(
            User.username == username.data
        ))
        if user is not  None:
            raise ValidationError("Логин уже занят. Введите новый логин")
        

class AddTask(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    description = TextAreaField('Описание задачи', validators=[DataRequired()])
    difficulty = SelectField('Сложность задачи',choices= [(i.name, i.value) for i in DifficultyTask], validators=[DataRequired()])
    start_time = DateTimeField(
        'Начало', 
        format='%Y-%m-%d',  
        validators=[DataRequired()],
        render_kw={"type": "date"}  
    )
    end_time = DateTimeField(
        'Конец', 
        format='%Y-%m-%d',  
        validators=[DataRequired()],
        render_kw={"type": "date"}  
    )

    task_type = SelectField('Тип задачи', choices= [])
    submit = SubmitField('Создать задачу')

