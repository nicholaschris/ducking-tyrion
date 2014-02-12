import webapp2
import cgi
import string


def html_escape(s):
    return cgi.escape(s, quote=True)


class MainPage(webapp2.RequestHandler):

    def write_form(self, value=""):
        self.response.write(form % {"value" : value})

    def get(self):
        # self.response.headers['Content-Type'] = 'text/plain'
        # self.response.write(form)
        conv = ""
        self.write_form()

    def post(self):
        # self.redirect('unit2/rot13')
        text = self.request.get("text")
        print text
        conv = convert_string(text)
        print conv
        self.write_form(conv)

class TestHandler(webapp2.RequestHandler):
    def get(self):
        # q = self.request.get('q')
        # self.response.out.write(q)
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write(self.request)


application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/testform', TestHandler),
], debug=True)
