from bson import ObjectId
from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/pics"

SECRET_KEY = 'AMUREVIEW'

client = MongoClient('mongodb+srv://sparta:test@cluster0.vql3p0m.mongodb.net/?retryWrites=true&w=majority')
db = client.dbsparta


# --------------------------------------- 보안 기능 시작 --------------------------------------------
@app.route('/')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        return render_template('index.html', user_info=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256').decode('utf-8')

        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,
        "password": password_hash,
        "profile_name": username_receive,
        "profile_pic": "",
        "profile_pic_real": "profile_pics/profile_placeholder.png",
        "profile_info": ""
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})
# --------------------------------------- 보안 기능 끝 --------------------------------------------
# --------------------------------------- 리뷰 기능 시작 --------------------------------------------
@app.route('/api/get_board', methods=['GET'])
def get_board():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        my_username = payload["id"]
        username_receive = request.args.get("username_give")
        if username_receive == "":
            boards = list(db.boards.find({}).sort("date", -1).limit(20))
        else:
            boards = list(db.boards.find({"username": username_receive}).sort("date", -1).limit(20))
        for board in boards:
            board['_id'] = str(board['_id'])
            board['profile_pic_real'] = db.users.find_one({'username': board['username']})['profile_pic_real']

            board["count_heart"] = db.likes.count_documents({"board_id": board["_id"], "type": "heart"})
            board["heart_by_me"] = bool(db.likes.find_one({"board_id": board["_id"], "type": "heart", "username": my_username}))

            board["count_star"] = db.likes.count_documents({"board_id": board["_id"], "type": "star"})
            board["star_by_me"] = bool(db.likes.find_one({"board_id": board["_id"], "type": "star", "username": my_username}))

            board["count_like"] = db.likes.count_documents({"board_id": board["_id"], "type": "like"})
            board["like_by_me"] = bool(db.likes.find_one({"board_id": board["_id"], "type": "like", "username": my_username}))

        return jsonify({"result": "success", "msg": "리뷰 목록을 가져왔습니다", "boards": boards})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/api/write/<username>', methods=['GET'])
def write_board(username):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])
        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('write.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/api/post_board', methods=['POST'])
def post_board():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        title_receive = request.form['title_give']
        content_receive = request.form['content_give']
        date_receive = request.form['date_give']
        doc = {
            'username': user_info['username'],
            'title': title_receive,
            'content': content_receive,
            'date': date_receive,
            'profile_name': user_info['profile_name'],
            'profile_pic_real': user_info['profile_pic_real']
        }
        db.boards.insert_one(doc)
        board = db.boards.find_one({'date': date_receive})
        board_id = str(board['_id'])
        if 'file_give' in request.files:
            file = request.files['file_give']
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"thumbnail_pics/{board_id}.{extension}"
            file.save('./static/pics/' + file_path)
            db.boards.update_one({'date': date_receive}, {'$set': {'thumbnail_pic': filename, 'thumbnail_pic_real': file_path}})
        return jsonify({"result": "success", 'msg': '리뷰 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/api/like', methods=['POST'])
def like_board():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        board_id_receive = request.form["board_id_give"]
        type_receive = request.form["type_give"]
        action_receive = request.form["action_give"]
        doc = {
            "board_id": board_id_receive,
            "username": user_info["username"],
            "type": type_receive
        }
        if action_receive == "like":
            db.likes.insert_one(doc)
        else:
            db.likes.delete_one(doc)
        count = db.likes.count_documents({"board_id": board_id_receive, "type": type_receive})
        return jsonify({"result": "success", 'msg': '좋아요가 업데이트되었습니다', "count": count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
# --------------------------------------- 리뷰 기능 끝 --------------------------------------------
# --------------------------------------- 상세 페이지 시작 --------------------------------------------
@app.route('/api/get_detail', methods=['GET'])
def detail_board():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        board_id_receive = request.args.get("board_id_give")
        board = db.boards.find_one({'_id': ObjectId(board_id_receive)})
        board['_id'] = str(board['_id'])
        return render_template('detail.html', board=board, user_info=user_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
# --------------------------------------- 상세 페이지 끝 ---------------------------------------------
# --------------------------------------- 프로필 시작 ---------------------------------------------
@app.route('/user/<username>')
def user(username):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])

        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]
        name_receive = request.form["name_give"]
        about_receive = request.form["about_give"]
        new_doc = {
            "profile_name": name_receive,
            "profile_info": about_receive
        }
        if 'file_give' in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            file.save("./static/pics/"+file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        db.users.update_one({'username': payload['id']}, {'$set':new_doc})
        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))
# --------------------------------------- 프로필 끝 ---------------------------------------------

if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)

