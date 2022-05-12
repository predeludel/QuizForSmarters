from flask import render_template, request
from flask_login import LoginManager, login_required, logout_user, current_user, login_user
import datetime
from model import *

login_manager = LoginManager(app)
login_manager.login_view = '/login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    user = db.session.query(User).filter(User.username == current_user.username).first()
    user.is_active = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return show_login_form()


@app.route('/')
def index():
    return show_main()


@app.route('/main')
@login_required
def show_main(message=None):
    return render_template('main.html', user=current_user, message=message)


@app.route('/registration')
def show_registration():
    return render_template('registration.html')


@app.route('/register', methods=["POST"])
def registration():
    username = request.form.get("username")
    password = request.form.get("password")
    password2 = request.form.get("password2")
    if password != password2:
        return show_registration()
    user = db.session.query(User).filter(User.username == username).first()
    if user is None:
        user = User(username=username)
        user.set_password(password)
        login_user(user, remember=True)
        user.is_active = True
        db.session.add(user)
        db.session.commit()
        return show_main()
    else:
        return show_registration()


@login_required
def play():
    users = db.session.query(User).filter(User.is_active == True).all()
    game = db.session.query(Game).filter(Game.is_active == True).first()
    judge = db.session.query(User).filter(User.id == game.judge_id).first()
    set_obj = db.session.query(Set).filter(Set.id == game.set_id).first()
    questions = db.session.query(Question).filter(Question.set == set_obj).all()
    if game.current_question_id is None:
        game.current_question_id = questions[0].id
        db.session.add(game)
        db.session.commit()
    question = None
    for i in questions:
        if i.id == game.current_question_id:
            question = i
            break

    if game.last_answer is None:
        flag = True
    else:
        flag = False
    return render_template('play.html', players_list=users, judge=judge, question=question, flag=flag, game=game,
                           set_obj=set_obj)


@app.route('/send_answer')
@login_required
def get_answer():
    game = db.session.query(Game).filter(Game.is_active == True).first()
    game.last_answer = request.args.get("answer")
    db.session.add(game)
    db.session.commit()
    return play()


@app.route('/check_answer_<flag>')
@login_required
def check_answer(flag):
    game = db.session.query(Game).filter(Game.is_active == True).first()
    set_obj = db.session.query(Set).filter(Set.id == game.set_id).first()
    questions = db.session.query(Question).filter(Question.set == set_obj).all()
    if flag == "true":
        game.result += 1
    game.last_answer = None

    for i in range(len(questions)):
        if questions[i].id == game.current_question_id:
            if i != len(questions) - 1:
                game.current_question_id = questions[i + 1].id
                db.session.add(game)
                db.session.commit()
                return show_judge()
            else:
                game.is_active = False
                game.datetime = datetime.datetime.now()
                db.session.add(game)
                db.session.commit()
                return show_main(f"Игра закончена ваш результат: {game.result}")


@app.route('/table')
@login_required
def show_table():
    game_list = db.session.query(Game).filter(Game.is_active == False).all()
    game_list = sorted(game_list, key=lambda x: x.result, reverse=True)
    return render_template('lider_board.html', game_list=game_list)


@app.route('/game')
@login_required
def show_game():
    game = db.session.query(Game).filter(Game.is_active == True).first()
    if current_user.is_judge is True:
        if game is None:
            return show_game_config_page()
        else:
            return show_judge()
    else:
        if game is None:
            return show_main(message="Нет активных игр")
        else:
            return play()


def show_game_config_page():
    set_list = db.session.query(Set).all()
    return render_template('game_config.html', set_list=set_list)


@app.route('/create')
@login_required
def game_create():
    if current_user.is_judge is True:
        set_id = request.args.get("set_id")
        set_obj = db.session.query(Set).filter(Set.id == set_id).first()
        game = Game(set_id=set_id, judge_id=current_user.id, result=0, is_active=True, set_name=set_obj.name)
        db.session.add(game)
        db.session.commit()
        return show_game()
    else:
        return show_main("Только судьи могут создавать сессию")


@app.route('/judge')
@login_required
def show_judge():
    users = db.session.query(User).filter(User.is_active == True).all()
    game = db.session.query(Game).filter(Game.is_active == True).first()
    judge = db.session.query(User).filter(User.id == game.judge_id).first()
    set_obj = db.session.query(Set).filter(Set.id == game.set_id).first()
    questions = db.session.query(Question).filter(Question.set == set_obj).all()
    question = None
    for i in questions:
        if i.id == game.current_question_id:
            question = i
            break
    flag = "enabled"
    if game.last_answer is None:
        flag = "disabled"

    return render_template('judge.html', flag=flag, players_list=users, judge=judge, question=question,
                           last_answer=game.last_answer, set_name=set_obj.name, game=game)


@app.route('/designer')
@login_required
def show_designer():
    set_list = db.session.query(Set).all()
    return render_template('designer.html', set_list=set_list)


@app.route('/set/add', methods=['POST'])
def set_add():
    name = request.form.get("name")
    set_obj = Set(name=name)
    db.session.add(set_obj)
    db.session.commit()
    return show_designer()


@app.route('/set/<set_id>/delete', methods=['POST'])
def set_delete(set_id):
    set_obj = db.session.query(Set).filter(Set.id == set_id).first()
    db.session.delete(set_obj)
    db.session.commit()
    return show_designer()


@app.route('/set/<set_id>/question/<question_id>/delete', methods=['POST'])
def question_delete(set_id, question_id):
    question_obj = db.session.query(Question).filter(Question.id == question_id).first()
    db.session.delete(question_obj)
    db.session.commit()
    return set_edit(set_id)


@app.route('/set/<set_id>/edit')
def set_edit(set_id):
    set_obj = db.session.query(Set).filter(Set.id == set_id).first()
    questions_list = db.session.query(Question).filter(Question.set_id == set_id).all()
    return render_template('set_edit.html', set_obj=set_obj, questions_list=questions_list)


@app.route('/set/<set_id>/question/add', methods=['POST'])
def question_add(set_id):
    name = request.form.get("name")
    answer = request.form.get("answer")
    question = Question(name=name, answer=answer,
                        set=db.session.query(Set).filter(Set.id == set_id).first())
    db.session.add(question)
    db.session.commit()
    return set_edit(set_id)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.session.query(User).filter(User.username == username).first()
        if user is None:
            return show_login_form()
        else:
            if user.check_password(password):
                login_user(user, remember=True)
                user.is_active = True
                db.session.add(user)
                db.session.commit()
                return show_main()
            else:
                return show_login_form()

    else:
        return show_login_form()


def show_login_form():
    return render_template('login.html')


if __name__ == '__main__':
    db.create_all()
    app.run()
