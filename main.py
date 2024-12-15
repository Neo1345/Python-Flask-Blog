from flask import Flask,render_template,request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
import json ,os,math
from flask_mail import Mail,Message
from datetime import datetime
from werkzeug.utils import secure_filename

# from requests import request



class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

class Contact(db.Model):
    sno: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=False,nullable=False)
    phone: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str] = mapped_column(unique=True)
    mes: Mapped[str] = mapped_column(unique=True)

class Posts(db.Model):
    sno: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(unique=False,nullable=False)
    post: Mapped[str] = mapped_column(unique=False)
    date: Mapped[str] = mapped_column(unique=False)
    slug: Mapped[str] = mapped_column(unique=False)
    img_file: Mapped[str] = mapped_column(unique=False)

app = Flask(__name__)
app.secret_key = 'super-secret-key'


local_server = True
with open('config.json','r') as c:
    params = json.load(c)['params']

app.config['UPLOAD_FOLDER'] = params['file_location']

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT= '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME= params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)
mail = Mail(app)
mail.init_app(app)

if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
# db = SQLAlchemy(app)
db.init_app(app)


# class Contact(db.Model):
#     sno =  db.Column(db.Integer,primary_key= True)
#     name=  db.Column(db.String(),unique= False,nullable = False)
#     phone= db.Column(db.String(),unique= False,nullable = False)
#     email= db.Column(db.String(),unique= False,nullable = False)
#     mes=   db.Column(db.String(),unique= False,nullable = False)


@app.route("/")
def home():
    posts = Posts.query.filter_by().all()
    # posts = db.session.execute(db.select(Posts)).all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))

    page = request.args.get('page')

    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    # posts = db.session.execute(db.select(Posts)).scalars()
    posts = posts[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    if (page == 1):
        prev = '#'
        next = "/?page="+str(page + 1)
    elif (page == last):
        prev = "/?page="+str(page - 1)
        next = '#'
    else:
        prev = "/?page="+str(page - 1)
        next = "/?page="+str(page + 1)


    # posts = db.session.execute(db.select(Posts).limit(params['no_of_posts'])).scalars()
    # posts = Posts.query.filter_by().all()
    # posts = db.session.execute(db.select(Posts))
    # posts = posts[0:3]
    return render_template('index.html',params= params,posts=posts
                           ,prev=prev,next= next
                           )

@app.route("/about")
def about():
    return render_template('about.html',params= params)

@app.route("/dashboard",methods = ['GET','POST'])
def dashboard():

    if ('user' in session and session['user'] == params['admin_user']):
        posts = db.session.execute(db.select(Posts)).scalars()
        return render_template('dashboard.html',params= params,posts=posts)
    
    if(request.method == 'POST'):
        username = request.form.get('uname')
        password = request.form.get('pass')
        if (username == params['admin_user'] and password == params['password']):
            #set the session variable
            session['user'] = username
            posts = db.session.execute(db.select(Posts)).scalars()
            return render_template('dashboard.html',params= params,posts=posts)

        
    return render_template('login.html',params= params)


@app.route("/edit/<string:sno>",methods = ['GET','POST'])
def edit(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            box_title = request.form.get('title')
            postsdetails = request.form.get('postsdetails')
            box_slug = request.form.get('slug')
            box_imgfile = request.form.get('imgfile')

            if sno == '0':
                post = Posts(title = box_title,post=postsdetails,date=datetime.today().strftime('%Y-%m-%d'),slug=box_slug,img_file=box_imgfile)
                db.session.add(post)
                db.session.commit()
            

            else:
                post =  db.session.execute(db.select(Posts).where(Posts.sno ==sno )).scalar()
                post.title = box_title
                post.postdetails = postsdetails
                post.slug= box_slug
                post.imgfile = box_imgfile
                db.session.commit()
                return redirect('/edit/'+sno)
        post =  db.session.execute(db.select(Posts).where(Posts.sno ==sno )).scalar()
        return render_template('edit.html',params=params,post=post)


@app.route("/post/<string:post_slug>",methods = ['GET']) 
def post_route(post_slug):

    post = db.session.execute(db.select(Posts).where(Posts.slug ==post_slug )).scalar()
    # print({{post.title}})
    return render_template('post.html',params= params,post=post)

@app.route("/uploader",methods = ['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if(request.method == 'POST'):
            f= request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],secure_filename(f.filename) ))
            return "uploaded successfully"

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>",methods = ['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post =  db.session.execute(db.select(Posts).where(Posts.sno ==sno )).scalar()
        db.session.delete(post)
        db.session.commit()
        return redirect('/dashboard')


@app.route("/contact",methods = ['GET','POST'])
def contact():

    if(request.method == 'POST'):
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        mes = request.form.get('mes')

        entry = Contact(name = name,phone=phone,email= email,mes=mes)
        db.session.add(entry)
        db.session.commit()
        msg = Message(
        subject="Hello",
        sender=email,
        recipients=[params['gmail-user']],
        
        )
        msg.body = mes  + '\n' + phone
        # msg.html = "<b>testing</b>"
        # mail.send_message('new message from'+name,sender=email,recipients=params['gmail-user'],
        #                  body=mes  + '\n' + phone 
        #                   )
        mail.send(msg)

    return render_template('contact.html',params= params)

app.run(debug=True)