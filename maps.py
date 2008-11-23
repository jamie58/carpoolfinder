import os
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

class Group(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    center_lat = db.FloatProperty()
    center_lng = db.FloatProperty()
    zoom = db.IntegerProperty()
    place = db.StringProperty()
    people = db.StringProperty()
    contact =  db.StringProperty()
    moreinfo =  db.StringProperty()
    
class Pin(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    lat = db.FloatProperty()
    lng = db.FloatProperty()
    name = db.StringProperty()

        
class MainPage(webapp.RequestHandler):
    def get(self):
        place_id = self.request.get("place", None)
        if place_id is None:
            #group = Group()
            #group.center_lat=33.80777
            #group.center_lng=-84.30542
            #group.zoom=11
            #group.people="seniors"
            #group.place="DTC"
            #group.contact="schott DOT bee are eye eh en AT gee em ae eye el DOT com"
            #id=group.put()
            #self.response.out.write("Group added " + str(id))
            #return
            path = os.path.join(os.path.dirname(__file__), 'choose_place.html')
            template_values = dict()
            self.response.out.write(template.render(path, template_values))
        else:
            path = os.path.join(os.path.dirname(__file__), 'map.html')
            place = Group.get(place_id)
            template_values = dict(place_id=place.key(), place=place.place, 
                                   people=place.people, center_lat=place.center_lat, 
                                   center_lng=place.center_lng, map_zoom=place.zoom,
                                   contact=place.contact, moreinfo=place.moreinfo)
            self.response.out.write(template.render(path, template_values))

class Details(webapp.RequestHandler):
    def get(self):
        action = self.request.get("Action", "read")
        place_id = self.request.get("place")
        place = Group.get(place_id)
        
        if action == "read":
            pins = db.GqlQuery("SELECT * FROM Pin where ancestor is :group LIMIT 100", group=place)
            cnt = 1
            for pin in pins:
                self.response.out.write("\t".join( (str(pin.key()), pin.date.strftime('%a %m %d %Y %H%M'), str(pin.lat), str(pin.lng), pin.name) ) )
                cnt += 1
                self.response.out.write("\n")
        elif action == "add":
            pin = Pin(parent=place)
            pin.name = self.request.get('details')
            pin.lat = float(self.request.get('lat'))
            pin.lng = float(self.request.get('lng'))
            new_id = pin.put()
            self.response.out.write(new_id)
        elif action == "del":
            pin = Pin.get(self.request.get('ID'))
            db.delete(pin)
            self.response.out.write("pin deleted")
            
class AddPlace(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'add_place.html')
        template_values = dict()
        self.response.out.write(template.render(path, template_values))
    
    def post(self):
        group = Group()
        group.center_lat = float(self.request.get('center_lat')) # 33.80777
        group.center_lng = float(self.request.get('center_lng')) # -84.30542
        group.zoom = int(self.request.get('zoom')) # 11
        group.people = self.request.get('people') #"seniors"
        group.place = self.request.get('place') #"DTC"
        group.contact = self.request.get('contact') # "schott DOT bee are eye eh en AT gee em ae eye el DOT com"
        group.moreinfo = self.request.get('moreinfo') #""
        pin = Pin()
        pin.lat = float(self.request.get('marker_lat')) # 33.80777
        pin.lng = float(self.request.get('marker_lng')) # -84.30542
        id=group.put()
        self.redirect("/?place=%s" % id)
            
        # http://maps.google.com/maps?f=q&hl=en&geocode=&q=10+10th+street+30309&sll=34.00219,-84.476173&sspn=0.01263,0.017188&ie=UTF8&z=17&g=10+10th+street+30309&iwloc=addr

        
        
application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/details.txt', Details),
                                      ('/add_place', AddPlace)],
                                     debug=True)

                                     
                                     
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
