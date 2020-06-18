# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python37_app]
from flask import Flask, render_template,request,Response,abort,session
from flask_login import login_user,logout_user,login_required,UserMixin,LoginManager
from collections import defaultdict
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from markupsafe import escape
import hashlib
import pdb

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)

login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = "IUr239_&kjasdf3498ui"
cred = credentials.Certificate('env/python-test-273813-firebase-adminsdk-szfvp-75719f2548.json')
db_app = firebase_admin.initialize_app(cred)

class User(UserMixin):
    def __init__(self, id, name, password):
        self.id = id
        self.name = name
        self.password = password

users = {
    1: User(1,"user01", "password"),
    2: User(2, "user02", "password")
}

nested_dict = lambda: defaultdict(nested_dict)
user_check = nested_dict()
for i in users.values():
    user_check[i.name]["password"] = i.password
    user_check[i.name]["id"] = i.id

@login_manager.user_loader
def load_user(user_id):
    return users.get(int(user_id))

# ログインしないと表示されないパス
@app.route('/protected/')
@login_required
def protected():
    db = firestore.client()
    ref = db.collection(u'running_record').stream()
    #myData={}
    for data in ref:
        myData = data.to_dict()
#        myData = data.to_dict()
    message = "This is lisst page"
#    pdb.set_trace()
    return render_template('list.html', message=message, dict=myData,authorized="1")
    #    return 'Hello World!'

# ログインパス
@app.route('/login/', methods=["GET", "POST"])

def login():
    if(request.method == "POST"):
        # ユーザーチェック
        #print(request.form)
        if(request.form["username"] in user_check and request.form["password"] == user_check[request.form["username"]]["password"]):
            # ユーザーが存在した場合はログイン
            login_user(users.get(user_check[request.form["username"]]["id"]))
            session["username"] = request.form["username"]
            #pdb.set_trace()
            message = "Login Success"
            authflag=1
            return render_template("top.html", message=message, authorized=authflag ,name=session["username"])
        else:
            return render_template("login.html", message="Authorization is falied")
    else:
        return render_template("login.html")

# ログアウトパス
@app.route('/logout/')
def logout():
    logout_user()
    session.clear()
    return render_template("top.html")

@app.route('/', methods=["GET", "POST"])
def index():
    if 'username' in session:
        usname = escape(session['username'])
        authflag=1
    else:
        usname = ""
        authflag=0
    db = firestore.client()
    ref = db.collection(u'user_data').stream()
    myData=[]
    for data in ref:
        keys = data.to_dict()
        for key in keys:
            myData.append(keys[key])
    return render_template('top.html', name=usname, dict=myData, authorized=authflag)

@app.route('/record/', methods=["GET","POST"])
@login_required
def record():
    authflag='1'
    if(request.method=="GET"):
        return render_template('input.html', name=session["username"],authorized=authflag)
    else:
        running_date = request.form["running_date"]
        running_distance = request.form["running_distance"]
        running_time = request.form["running_time"]
        running_memo = request.form["running_memo"]

        cred = credentials.Certificate('env/python-test-273813-firebase-adminsdk-szfvp-75719f2548.json')
        app = firebase_admin.initialize_app(cred)

        db = firestore.client()
        ref = db.collection(u'running_record')
        dataset = {
            'running_date': running_date,
            'running_distance': float(running_distance),
            'running_time': running_time,
            'running_memo': running_memo
            }
        docs = ref.add(dataset)
        messages = "Record successfully. Let's run next day"
        return render_template('input.html', name=session["username"], authorized=authflag, messages=messages)

@app.route('/create_account/', methods=['GET','POST'])
def create_account():
    if(request.method == "GET"):
        return render_template('createaccount.html')
    else:
        account = request.form["login_account"]
        displayname = request.form["display_name"]
        if(request.form["password"] != request.form["confirm_password"]):
            messages = "パスワードが一致しません"
            return render_template('createaccount.html', messages=messages)
        else:
            #ログインアカウントの重複チェック
            #whereで同一ログイン名のデータを抽出し、辞書型変数にlogin_nameのキーが有るか（あれば重複あり）と判断
            db = firestore.client()
            ref = db.collection(u'user_data').where(u'login_name',u'==',account).stream()
            myData={}
            for data in ref:
                myData=data.to_dict()
            if(u'login_name' in myData):
                return render_template('createaccount.html',messages="ログインIDが重複しています。")
            else:
                passwd = request.form["password"]
                m = hashlib.sha256(passwd.encode('utf-8')).hexdigest()
                dataset={
                'login_name': account,
                'display_name': request.form['display_name'],
                'password': m
                }
                db.collection(u'user_data').add(dataset)
                return render_template('login.html', messages="Please login new account.")
#            myData=[]
#            for data in ref:
#                keys = data.to_dict()
#                for key in keys:
#                    myData.append(keys[key])

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
