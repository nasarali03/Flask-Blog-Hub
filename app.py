from flask import Flask, render_template, request, session, redirect, url_for
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail,Message
import json
import os
import math

app = Flask(__name__)
local_server = True
with open("templates/config.json", "r") as c:
    params = json.load(c)["params"]


app.config["SECRET_KEY"]="thisismysecretekey123"
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USE_TLS'] = False  
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME']=params["gmail-user"]
app.config['MAIL_PASSWORD']=params['gmail-password']
app.config['UPLOAD_FOLDER']=params['upload_location']
mail=Mail(app)

app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    # srno ,name, email, phone_num, message, date'
    srno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(13), nullable=False)
    message = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(20), nullable=False)


class Posts(db.Model):
    # srno ,name, email, phone_num, message, date'
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    img_file = db.Column(db.String(12), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    tagline = db.Column(db.String, nullable=False)


@app.route("/")
def index():
    posts = Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params["num_of_posts"]))
    # [0 : params["num_of_posts"]]

    page=request.args.get("page")
    if not str(page).isnumeric():
        page=1

    page = int(page)
    posts = posts[(page-1)*int(params['num_of_posts']):(page-1)*int(params['num_of_posts'])+ int(params['num_of_posts'])]

    
    if page==1:
        prev="#"
        next="/?page="+str(page+1)
    elif page==last:
        prev="/?page="+str(page-1)
        next="#"
    else:
        prev="/?page="+str(page-1)
        next="/?page="+str(page+1)


    # posts = Posts.query.filter_by().all()[0 : params["num_of_posts"]] 
    return render_template("index.html", params=params, posts=posts,prev=prev,next=next)


@app.route("/about")
def about():
    return render_template("about.html", params=params)


@app.route("/dashboard", methods=["POST", "GET"])
def dashboard():
    if "user" in session and session["user"] == params["admin_user"]:
        posts = Posts.query.all()
        return render_template("dashboard.html", params=params, posts=posts)

    if request.method == "POST":
        username = request.form.get("uname")
        userpass = request.form.get("pass")
        if username == params["admin_user"] and userpass == params["admin_password"]:
            session["user"] = username
            posts = Posts.query.all()
            return render_template("dashboard.html", params=params, posts=posts)

    return render_template("signin.html", params=params)

@app.route("/edit/<string:sno>", methods=["GET", "POST"])
def edit(sno):
    if "user" in session and session["user"] == params["admin_user"]:
        if request.method=="POST":
            box_title=request.form.get("title")
            tline=request.form.get("tline")
            slug=request.form.get("slug")
            content=request.form.get("content")
            img_file=request.form.get("img_file")

            if sno=='0':
                post=Posts(title=box_title,slug=slug,content=content,img_file=img_file,date=datetime.now(),tagline=tline)
                db.session.add(post)
                db.session.commit()
            else:
                post=Posts.query.filter_by(sno=sno).first()
                post.title=box_title
                post.slug=slug
                post.content=content
                post.img_file=img_file
                post.date=datetime.now()
                post.tagline=tline
                db.session.commit()
                return redirect("/edit  /"+sno)
        post=Posts.query.filter_by(sno=sno).first()
        return render_template("edit.html",params=params,post=post)

@app.route("/uploader", methods=["GET", "POST"])
def uploader():
    if "user" in session and session["user"] == params["admin_user"]:
        if request.method=="POST":
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename)))
            return "Uploaded Successfully"
        
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")



@app.route("/delete/<string:sno>", methods=["GET", "POST"])
def delete(sno):
    if "user" in session and session["user"] == params["admin_user"]:
        post=Posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect("/dashboard")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        msg = request.form.get("message")
        # user = Contacts(
        #     name=name, phone_num=phone, message=msg, date=datetime.now(), email=email
        # )
        # db.session.add(user)
        # db.session.commit()
        msg_title=f"New Message from {name}"
        
        message=Message(msg_title,recipients=["nasarali1805@gmail.com"])
        message.sender=email
        data={
            'app_name':"Blog Hub",
            'title':msg_title,
            'message':msg,
            'phone':phone,
            'name':name,
            'email':email
            
        }
        message.html=render_template("email.html",data=data)
        try:
            mail.send(message)
            return render_template("contact.html",params=params)
        except Exception as e:
            print(e)
            return "Email was not send.."
    return render_template("contact.html", params=params)


@app.route("/post")
@app.route("/post/<string:post_slug>", methods=["GET"])
def post_route(post_slug):
    post_det = Posts.query.filter_by(slug=post_slug).first()
    print(post_det)

    return render_template("post.html", params=params, post=post_det)


if __name__ == "__main__":
    app.run(debug=True, port=5003)
