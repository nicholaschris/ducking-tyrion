import os       # for fixing templates directory
import webapp2  # for web handlers
import jinja2   # for templates
import logging

from google.appengine.ext import db # for database
from google.appengine.api import users # to enable users

'''
Main file for blog platform.
'''

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=True)

def blog_key(name='default'):
    return db.Key.from_path('blogs', name)

class BlogPost(db.Model):
    """Models an individual blog post."""
    title = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

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

class Home(Handler):

    def get(self):
        self.render('front.html')

class Blog(Handler):

    def get(self):
        posts = db.GqlQuery("SELECT * FROM BlogPost ORDER BY created DESC")
        self.render('front_page.html', articles = posts)

# Permalink page for rendering a single blog post
class Permalink(Handler):
    def get(self, post_id):
        post = BlogPost.get_by_id(int(post_id))
        self.render('post.html', articles = [post], post_id = post_id)

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


class PermalinkPage():
    pass

app = webapp2.WSGIApplication(
    [('/', Home),
     ('/blog', Blog),
     ('/blog/newpost', NewPost),
     ('/blog/(\d+)', Permalink)],
      debug=True)
