import os
import logging
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users

class Group(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    center_lat = db.FloatProperty()
    center_lng = db.FloatProperty()
    marker_lat = db.FloatProperty()
    marker_lng = db.FloatProperty()
    zoom = db.IntegerProperty()
    place = db.StringProperty()
    people = db.StringProperty()
    contact =  db.StringProperty()
    moreinfo =  db.StringProperty()
    user = db.UserProperty()
    
class Pin(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    lat = db.FloatProperty()
    lng = db.FloatProperty()
    name = db.StringProperty()

def make_new_map(place_id,self):
      user = users.get_current_user()
      if user:    #send to add_place.html
          place= Group(key_name=place_id)
          place.place = place_id
          place.user = user
          place.put()
          key = db.Key.from_path("Group", place_id)
          path = os.path.join(os.path.dirname(__file__), 'add_place.html')
          template_values = dict(place=place.place, user=place.user) 
          self.response.out.write(template.render(path, template_values))
      else:     #send back to choose_place.html
          path = os.path.join(os.path.dirname(__file__), 'choose_place.html')
          template_values = dict()
          self.response.out.write(template.render(path, template_values))
                    
        
class MainPage(webapp.RequestHandler):
    def get(self):
        place_id = self.request.get("place", None)
        if place_id is None:
            ####'choose_place' on next line does not seem to matter
            path = os.path.join(os.path.dirname(__file__), 'choose_place.html')
            template_values = dict()
            self.response.out.write(template.render(path, template_values))
        else:
            ####go to map.html
            ####because choose_place.html has produced a desired place name
            key = db.Key.from_path("Group", place_id)
            place = Group.get(key)
            if place : 
                path = os.path.join(os.path.dirname(__file__), 'map.html')
                template_values = dict(place_id=place.key(), place=place.place, 
                                    people=place.people, center_lat=place.center_lat, 
                                    center_lng=place.center_lng, map_zoom=place.zoom,
                                    marker_lat=place.marker_lat, marker_lng=place.marker_lng, 
                                    contact=place.contact, moreinfo=place.moreinfo,
                                    user=place.user)
                self.response.out.write(template.render(path, template_values))
            #if place does not already exist
            else:
                db.run_in_transaction(make_new_map,place_id,self)

class Details(webapp.RequestHandler):
    def get(self):
        action = self.request.get("Action", "read")
        place_id = self.request.get("place")
        key = db.Key.from_path("Group", place_id)
        place = Group.get(key)
        
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
    #creates group 
    def get(self):
        place_id = self.request.get('place')
        key = db.Key.from_path("Group", place_id)
        group = Group.get(key)
        group.place = place_id
        group.center_lat = float(self.request.get('center_lat'))
        group.center_lng = float(self.request.get('center_lng'))
        group.zoom = int(self.request.get('zoom'))
        group.people = self.request.get('people')
        group.contact = self.request.get('contact')
        group.moreinfo = self.request.get('moreinfo')
        group.marker_lat = float(self.request.get('marker_lat'))
        group.marker_lng = float(self.request.get('marker_lng'))
        #this pin should NOT have a parent so it is not
        #included in the many ancestor pins
        pin = Pin()
        pin.name = place_id
        pin.lat = float(self.request.get('marker_lat'))
        pin.lng = float(self.request.get('marker_lng'))
        pin.put()
        group.put()
        self.redirect("/?place=%s" % place_id)
            
        
application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/details.txt', Details),
                                      ('/add_place', AddPlace)],
                                     debug=True)

                                     
                                     
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
