import webapp2
import cgi
import string

form = """<!DOCTYPE html>

<html>
  <head>
    <title>Unit 2 Rot 13</title>
  </head>

  <body>
    <h2>Enter some text to ROT13:</h2>
    <form method="post">
      <textarea name="text"
                style="height: 100px; width: 400px;">%(value)s</textarea>
      <br>
      <input type="submit">
    </form>
  </body>

</html>
"""

lc = string.ascii_lowercase
uc = string.ascii_uppercase

def convert_string(s):

    converted = list(s)
    for i, letter in enumerate(s):
        if letter in lc:
            ind = lc.find(letter)
            converted[i] = lc[ind-13]
        if letter in uc:
            ind = uc.find(letter)
            converted[i] = uc[ind-13]
    converted =  ''.join(converted)
    return html_escape(converted)

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
