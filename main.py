import os       # for fixing templates directory
import webapp2  # for web handlers
import jinja2   # for templates
import logging
import random
import string
import re
import json
import time

from google.appengine.ext import db # for database
from google.appengine.api import users # to enable users
from google.appengine.api import memcache #import memcache to lower hits on database

'''
Main file for blog publishing platform.

signup_url = url + "/signup"
login_url = url + "/login"
logout_url = url + "/logout"
post_url = url + "/newpost"
json_url = url + "/.json"
permalink_json_url = permalink_url + ".json
Cache the front page and permalink page

'''

SECRET = "imsosecret"

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

### memcache function ###

def top_blog(update = False):
    logging.error(update)
    key = 'top'
    posts = memcache.get(key)
    logging.error(posts) #posts is an empty 
    if posts is None or update:
        logging.error("DB QUERY")
        posts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC LIMIT 10")
        posts = list(posts)
        memcache.set(key, posts)
        logging.error("Set key and posts")
        # logging.error((key, posts))
        memcache.set('top_posts_qt', time.time())
    return posts 



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

    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

    def as_dict(self):
        time_fmt = '%c'
        d = {'title': self.title,
             'content': self.content,
             'created': self.created.strftime(time_fmt),
             'last_modified': self.last_modified.strftime(time_fmt)}
        return d

class User(db.Model):
    """Models an individual user."""
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    ip_address = db.StringProperty(required=True)
    email_address = db.StringProperty()
    
    #Stuff below added from hw5
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('name =', name).get()
        return u

    @classmethod
    def register(cls, name, pw, email = None):
        pw_hash = make_pw_hash(name, pw)
        return User(parent = users_key(),
                    name = name,
                    pw_hash = pw_hash,
                    email = email)

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u

class AllPost(db.Model):

    name = db.StringProperty(required=True)
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    location = db.StringProperty(required=True)
    # province = db.StringProperty(required=True)
    # municipality = db.StringProperty(required=True)
    ip_address = db.StringProperty(required=True)
    email_address = db.StringProperty(required=True)
    phone_number = db.StringProperty(required=True) # Should be number?
    votes = db.IntegerProperty(required=True)
    comments = db.StringListProperty()
    created = db.DateTimeProperty(auto_now_add = True)
### END ###

### Handlers ###
class Handler(webapp2.RequestHandler):
    '''
    Make some helper classes.
    '''
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self, template, **params):
        params['user'] = self.user # added from hw5
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
    
    # Stuff below was added from hw5
    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'
### END ###


class Home(Handler):

    def get(self):
        cookie = self.request.cookies.get('user_id')
        print "Home", cookie
        if cookie:
            self.write("Welcome, " +cookie+"! <a href='/blog'>Continue</a>")
        else:
            self.render('front.html')

class WelcomeHandler(Handler):

    def get(self):
        cookie = self.request.cookies.get('user_id')
        print "Welcome", cookie
        if cookie:
            self.write("Welcome," +cookie+"!"+" <a href='/blog'>Continue</a>")
        else:
            self.render('front.html')

class Blog(Handler):

    def get(self):
        cookie = self.request.cookies.get('user_id')
        posts = top_blog()
        logging.error('Blog')
        logging.error(posts)
        qt = memcache.get('top_posts_qt')
        logging.error(qt)
        if qt:
            qt = time.time() - qt
        logging.error((time.time(), qt))
        self.render('front_page.html', articles = posts, qt = qt, cookie=cookie)

# Permalink page for rendering a single blog post
def post_cache(blog_id, update= False):
    permacache = blog_id   #cache key based on blog_id
    posts = memcache.get(permacache)
    logging.error('post_cache: ', posts)
    pkey=permacache
    post_time_key ='plkey'
    times = memcache.get(post_time_key)
    if posts is None or update==True:
       logging.error("post_cache: DB QUERY")
       posts = BlogPost.get_by_id(int(blog_id))
       # posts = list(posts) #can't put in list coz its not iterable for 1 item
       memcache.set(pkey, posts)
       memcache.set(str(post_time_key), (time.time()))
    age = time.time() - memcache.get(post_time_key)
    timecache ="%f" % age
    return posts, timecache

def permalink_cache(post_id, update=False):
    post_id = post_id
    # post = memcache.get(post_id)
    # key = 'post'
    # times = memcache.get(key)
    # post = BlogPost.get_by_id(int(post_id))
    # post = memcache.get(key)
    # logging.error(post)
    # if post is None or update:
    #     logging.error("DB QUERY")
    #     post = BlogPost.get_by_id(int(post_id))
    #     memcache.set(key, post)
    #     memcache.set('post_qt', time.time())
    # age = time.time() - memcache.get(key)
    # timecache ="%f" % age
    # return post

class Permalink(Handler):
    def get(self, blog_id):
        posts, timecache= post_cache(blog_id)
        timecache = "Queried " + timecache.split('.')[0] +" seconds ago"
        if not posts:
           self.render("404.html")
        self.render("post.html", articles=[posts], age=timecache)

class Permalink_old(Handler):

    def get(self, post_id):
        # post = BlogPost.get_by_id(int(post_id))
        post = permalink_cache(post_id)
        qt_post = memcache.get('posts_qt')
        if qt_post:
            qt_post = time.time() - qt_post
        logging.error(time.time(), qt_post)
        self.render('post.html', articles = [post], post_id = post_id, qt = qt_post)

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
            print key.id()
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
            time.sleep(0.5)
            update = top_blog(update=True)
            logging.error('Posting')
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

        query = db.GqlQuery('SELECT * FROM User WHERE name = :username', username=username)
        username_result = query.get()
        # print "_______HELLO___________"
        if username_result:
            logging.error((username_result.name, username))

        

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

        if username_result:
            if username_result.name == username:
                params['error_username'] = "That username has been taken."
                print "ERROR", params
                have_error = True
                # self.render('signup_form.html', **params)

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
                logging.error("Set Cookie")
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

### flush the cache ###
class RemoveCache(Handler):

    def get(self):
        logging.error("HELLO")
        memcache.flush_all()
        self.redirect("/blog")

class AllSubmit(Handler):

    def get(self):
        self.render('allsubmit.html')

    def post(self):
        name = self.request.get('name')
        title = self.request.get('title')
        content = self.request.get('content')
        # province = self.request.get('province')
        # municipality = self.request.get('municipality')
        location = self.request.get('location')
        ip_address = self.request.remote_addr
        email_address = "test@test.com"
        phone_number = self.request.get('contact_number')

        curr_post = AllPost(name = name,
                             title = title,
                             location = location,
                             content = content,
                             # profession = profession,
                             # province = province,
                             # municipality = municipality.
                             ip_address = ip_address,
                             email_address = email_address,
                             phone_number = phone_number,
                             votes = 0)
        curr_post.put()
        time.sleep(0.5)
        update = recent_posts(update=True)
        self.redirect('/thanks')

class Thanks(Handler):
    def get(self):
        self.render('thanks.html')

def recent_posts(update = False):
    logging.error("RECENT_POSTS CALLED")
    key = 'recent'
    posts = memcache.get(key)
    if posts is None or update:
        logging.error("DB QUERY")
        posts = db.GqlQuery("SELECT * FROM AllPost ORDER BY created DESC LIMIT 10")
        posts = list(posts)
        memcache.set(key, posts)
        memcache.set('recent_posts_qt', time.time())
    return posts


class Latest(Handler):

    def get(self):
        cookie = ""
        # cookie = self.request.cookies.get('user_id')
        posts = recent_posts() #
        qt = memcache.get('recent_posts_qt')
        if qt:
            qt = time.time() - qt
        self.render('latest.html', articles = posts, qt = qt, cookie=cookie)

    def post(self):
        post_id = int(self.request.get("id"))
        q = AllPost.get_by_id(post_id)
        q.votes += 1
        q.put()
        time.sleep(0.5)
        update = recent_posts(update=True)
        posts = db.GqlQuery("SELECT * FROM AllPost ORDER BY created DESC LIMIT 10")
        posts = list(posts)
        # self.render('latest.html', articles=posts)
        self.redirect('/latest')

class Filter(Handler):

    def get(self):
        self.render('filter_form.html')

    def post(self):
        t = self.request.get('title')
        l = self.request.get('location')
        q = db.GqlQuery("SELECT * FROM AllPost WHERE location = :1 AND title = :2", l ,t)
        logging.error("Hit THE DATASTORE!!!")


        # q.all().filter('location = ', l).filter('title = ', t)
        posts = list(q)
        self.render('latest.html', articles=posts, filtered=(t,l))

class Post(Handler):
    def get(self, post_id):
        post = AllPost.get_by_id(int(post_id))
        self.render('post.html', articles = [post])

    def post(self, post_id):
        # q = AllPost.get_by_id(post_id)
        post_id = int(self.request.get("id"))
        comment = self.request.get('comment')
        q = AllPost.get_by_id(post_id)
        # logging.error(post_id)
        # logging.error(comment)
        q.comments.append(comment)
        q.put()
        time.sleep(0.5)
        update = recent_posts(update=True)
        posts = db.GqlQuery("SELECT * FROM AllPost ORDER BY created DESC LIMIT 10")
        posts = list(posts)
        self.redirect('post.html', articles=[q])


class VoteUser(db.Model):
    """Models an individual user."""
    name = db.StringProperty(required=True)
    votes = db.IntegerProperty()

class VoteMaker(Handler):
    def get(self):
        self.render('vote-form.html')

    def post(self):
        name = self.request.get("name")
        vote = 0
        new_vote_user = VoteUser(name=name, votes=vote)
        new_vote_user.put()
        self.redirect('/thanks')

class Vote(Handler):
    def get(self):
        q = db.GqlQuery("SELECT * FROM VoteUser ORDER BY name DESC LIMIT 10")
        logging.error(q)
        votes = list(q)
        logging.error(votes)
        self.render('vote.html', votes=votes)

    def post(self):
        post_id = int(self.request.get("id"))
        # votes = int(self.request.get("votes"))
        data = self.request.get("data")
        q = VoteUser.get_by_id(post_id)
        logging.error(q)
        q.votes += 1
        q.put()
        self.redirect('/vote')

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
     ('/blog/(\d+).json', PermalinkJSON),
     ('/blog/flush/?', RemoveCache),
     ('/submit/?', AllSubmit),
     ('/thanks/?', Thanks),
     ('/latest/?', Latest),
     ('/filter/?', Filter),
     ('/post/(\d+)/?', Post),
     ('/votemake/?', VoteMaker),
     ('/vote/?', Vote)],
      debug=True)
