'''
Class for locations.
Province
City
Town
Municipality
'''

provinces = ["Western Cape",
             "Northern Cape",
             "Eastern Cape",
             "Free State",
             "Kwazulu-Natal",
             "North West Province",
             "Mpumalanga",
             "Limpopo",
             "Gauteng"]

municipalities = []

cities = []

towns = []

class Location():
    self.province = ""
    self.municipality = ""
    self.city = ""
    self.town = ""

class AllPost(db.model):

    name = db.StringProperty(required=True)
    profession = db.StringProperty(required=True)
    province = db.StringProperty(required=True)
    municipality = db.StringProperty(required=True)
    ip_address = db.StringProperty(required=True)
    email_address = db.StringProperty(required=True)
    phone_number = db.StringProperty(required=True) # Should be number?
    refas = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add = True)


class AllPost(Handler):

    def get(self):
        self.render('allsubmit.html')

    def post(self):
        name = self.request.get('name')
        profession = self.request.get('profession')
        province = self.request.get('province')
        municipality = self.request.get('municipality')
        ip_address = self.request.remote_addr
        email_address = "test@test.com"

        curr_post = RefaPost(name = name, 
                             profession = profession,
                             province = province,
                             municipality = municipality.
                             ip_address = ip_address,
                             email_address = email_address,
                             phone_number = phone_number,
                             refas = 0)
        curr_post.put()
        self.redirect('/thanks')

'''
Post has to have:
The email address of the person who posted it?
A comment section?
'''