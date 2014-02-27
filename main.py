import os       # for fixing templates directory
import webapp2  # for web handlers
import jinja2   # for templates
import logging
import random
import string
import re
import json

from google.appengine.ext import db # for database
from google.appengine.api import users # to enable users

'''
Main file for blog publishing platform.

signup_url = url + "/signup"
login_url = url + "/login"
logout_url = url + "/logout"
post_url = url + "/newpost"
json_url = url + "/.json"
permalink_json_url = permalink_url + ".json

'''

SECRET = "imsosecret"

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

### Checking the form is entered correctly ###
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
MAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def valid_username(username):
    return USER_RE.match(username)

def valid_password(password):
    return PASS_RE.match(password)

def valid_verify(password, verify):
    return password == verify

def valid_email(email):
    return MAIL_RE.match(email)

def blog_key(name='default'):
    return db.Key.from_path('blogs', name)

### End ###

### Hashing the cookies ###
import hashlib
import hmac

def hash_str(s):
        # return hashlib.md5(s).hexdigest()
        return hmac.new(SECRET, s).hexdigest()

def make_secure_val(s):
        return "%s|%s" % (s, hash_str(s))

def check_secure_val(h):
        val = h.split('|')[0]
        if h == make_secure_val(val):
                return val

### End ###

### Hashing passwords ###
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt=make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s|%s' % (h, salt)

def valid_pw(name, pw, h):
    print "h is: ", h
    salt = h.split('|')[1]
    print "salt is: ", salt
    return h == make_pw_hash(name, pw, salt)

### End ###

### Database models ###
class BlogPost(db.Model):
    """Models an individual blog post."""
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

class User(db.Model):
    """Models an individual user."""
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    ip_address = db.StringProperty(required=True)
    email_address = db.StringProperty()

### END ###

### Handlers ###
class Handler(webapp2.RequestHandler):
    '''
    Make some helper classes.
    '''
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))
        ### Function to render json ###
    def render_json(self, d):
        json_txt = json.dumps(d)
        print d
        print json_txt
        self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
        self.response.out.write(json_txt)

### END ###


class Home(Handler):

    def get(self):
        cookie = self.request.cookies.get('user_id')
        print "Home", cookie
        if cookie:
            self.write("Welcome, " +cookie+"!")
        else:
            self.render('front.html')

class WelcomeHandler(Handler):

    def get(self):
        cookie = self.request.cookies.get('user_id')
        print "Welcome", cookie
        if cookie:
            self.write("Welcome," +cookie+"!")
        else:
            self.render('front.html')

class Blog(Handler):

    def get(self):
        posts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC")
        posts = list(posts)
        self.render('front_page.html', articles = posts)

# Permalink page for rendering a single blog post
class Permalink(Handler):

    def get(self, post_id):
        post = BlogPost.get_by_id(int(post_id))
        self.render('post.html', articles = [post], post_id = post_id)

class PermalinkJSON(Handler):

    def get(self, post_id):
        p = BlogPost.get_by_id(int(post_id))
        time_fmt = '%c'
        d = {'title': p.title,'content': p.content,'created': p.created.strftime(time_fmt)}
        self.render_json(d)

class BlogJSON(Handler):

    def get(self):
        posts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC")
        # posts = list(posts)
        print posts
        blog_json = []
        for p in posts:
            time_fmt = '%c'
            d = {'title': p.title,'content': p.content,'created': p.created.strftime(time_fmt)}
            blog_json.append(d)
            print d
        self.render_json(blog_json)

class NewPost(Handler):

    def get(self):
        self.render('submit_form.html')

    def post(self):
        title = self.request.get("subject")
        content = self.request.get("content")

        if title and content:
            post = BlogPost(title = title, content = content)
            key = post.put()
            self.redirect("/blog/%d" % key.id())
        else:
            error = "Oops. It seems as though there is an error. We need both a title and some content!" 
            self.render('submit_form.html', title, content, error)

class SignupPage(Handler):

    def write_form(self, value="", username="", password="", verify="", email=""):
        self.render('signup_form.html', value = value,
                                        username = username,
                                        password = password,
                                        verify = verify,
                                        email = email)

    def get(self):
        print "get signup"
        self.write_form("")

    def post(self):
        global user_username
        have_error = False

        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username,
                            email = email)
        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True
        if not valid_password(username):
            params['error_username'] = "That's not a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True
        if email != "":
            if not valid_email(email):
                params['error_username'] = "That's not a valid email."
                have_error = True

        if have_error:
            # self.write_form("Invalid", user_username, user_password, user_verify, user_email)
            print "ERROR", params
            self.render('signup_form.html', **params)
        else:
            hashed_password = make_pw_hash(username, password)
            print hashed_password
            ip_address = self.request.remote_addr
            account=User(name=username,password=hashed_password, ip_address=ip_address, email_address=email)
            account.put()
            self.response.headers.add_header('Set-Cookie','user_id=%s; Path=/'%str(username))
            self.redirect('/blog/welcome')

class LoginHandler(Handler):

    def get(self):
        # user = self.request.cookies.get('user_id')
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        query = db.GqlQuery('SELECT * FROM User WHERE name = :username', username=username)
        username_result = query.get()

        params = {}
        if username_result:
            pw = username_result.password
            b = valid_pw(username_result.name,password,pw)
            print username_result.name,password,pw
            if b:
                self.response.headers.add_header('Set-Cookie','user_id=%s; Path=/'%str(username))
                self.redirect('/blog/welcome')
            else:
                params['invalid_login'] = "This is an invalid login (pw)."
                self.render('login.html', **params)
                print "ERROR", pw
        else:
            params['invalid_login'] = "This is an invalid login."
            self.render('login.html', **params)
            print "ERROR", username

class LogoutHandler(Handler):

    def get(self):
        empty_string = ""
        self.response.headers.add_header('Set-Cookie', 'user_id=%s; Path=/' % empty_string)
        self.redirect('/blog/signup')

class TestPage(Handler):

    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        visits = self.request.cookies.get('visits', 0)
        #make sure visits is an int
        visit_cookie_str = self.request.cookies.get('visits')
        if visit_cookie_str:
            cookie_val = check_secure_val(visit_cookie_str)
            if cookie_val:
                visits = int(cookie_val)
        visits += 1
        new_cookie_val = make_secure_val(str(visits))
        self.response.headers.add_header('Set-Cookie', 'visits=%s; Path=/' % new_cookie_val)
        self.write("You've been here %s times!" % visits)

### END HANDLERS ###


app = webapp2.WSGIApplication(
    [('/', Home),
     ('/blog/welcome/?', WelcomeHandler),
     ('/blog/signup/?', SignupPage),
     ('/blog/login/?', LoginHandler),
     ('/blog/logout/?', LogoutHandler),
     ('/blog/?', Blog),
     ('/blog/newpost/?', NewPost),
     ('/blog/(\d+)/?', Permalink),
     ('/test/?', TestPage),
     ('/blog/.json', BlogJSON),
     ('/blog/(\d+).json', PermalinkJSON)],
      debug=True)
