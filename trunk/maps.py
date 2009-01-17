import os
import logging
from datetime import datetime
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db

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
    activity =  db.StringProperty(default='live')
    user = db.UserProperty()
    
class Pin(db.Model):
    date = db.DateTimeProperty(auto_now_add=True)
    lat = db.FloatProperty()
    lng = db.FloatProperty()
    name = db.StringProperty()
    cornerColor	 = db.StringProperty(default='ffffff')
    height = db.IntegerProperty(default=32)
    label = db.StringProperty(default='')
    labelColor = db.StringProperty(default='000000')
    labelSize = db.IntegerProperty(default=2)
    primaryColor = db.StringProperty(default='ff0000')
    shadowColor = db.StringProperty(default='000000')
    shape = db.StringProperty(default='circle')
    strokeColor = db.StringProperty(default='000000')
    width = db.IntegerProperty(default=32)

        
class MainPage(webapp.RequestHandler):
    def get(self):
        place_id = self.request.get("place", None)
        if place_id is None:
            ####'choose_place' on next line does not seem to matter
            path = os.path.join(os.path.dirname(__file__), 'choose_place.html')
            if users.get_current_user():
              url = users.create_logout_url(self.request.uri)
              url_linktext = 'Signout'
              url_linktextmore = ' if you wish. You will be returned to this page after you signout.'
            else:
              url = users.create_login_url(self.request.uri)
              url_linktext = 'Signin'
              url_linktextmore = ' if you will be creating a map for your group. You will be returned to this page after you signin.'

            template_values = {
              'url': url,
              'url_linktext': url_linktext,
              'url_linktextmore': url_linktextmore,
              }
            self.response.out.write(template.render(path, template_values))
        else:
            ####determine if place exists already
            ####because choose_place.html has produced a desired place name
            ####or because user has supplied a place name with ?...
            key = db.Key.from_path("Group", place_id)
            place = Group.get(key)
            if place : 
                user = users.get_current_user()
                template_values = dict(place_id=place.key(), place=place.place, 
                         people=place.people, center_lat=place.center_lat, 
                         center_lng=place.center_lng, map_zoom=place.zoom,
                         marker_lat=place.marker_lat, marker_lng=place.marker_lng, 
                         contact=place.contact, moreinfo=place.moreinfo,
                         activity=place.activity, user=place.user)
                logging.info("place.place %s " % place.place)
                if user and user == place.user: #send user to add_place.html
                    path = os.path.join(os.path.dirname(__file__), 'add_place.html')
                else:                           #send to map.html
                    path = os.path.join(os.path.dirname(__file__), 'map.html')
                self.response.out.write(template.render(path, template_values))
            #if place does not already exist
            else:
                make_new_map(place_id,self)

class OwnerMap(webapp.RequestHandler):
    def get(self):
        place_id = self.request.get("place", None)
        logging.info("OwnerMap %s " % place_id)
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
                user = users.get_current_user()
                logging.info("OwnerMap user %s " % user)
                logging.info("OwnerMap place.user %s " % place.user)
                if user and user == place.user: #send user to mapowner.html
                    template_values = dict(place_id=place.key(), place=place.place, 
                         people=place.people, center_lat=place.center_lat, 
                         center_lng=place.center_lng, map_zoom=place.zoom,
                         marker_lat=place.marker_lat, marker_lng=place.marker_lng, 
                         contact=place.contact, moreinfo=place.moreinfo,
                         activity=place.activity, user=place.user)
                    path = os.path.join(os.path.dirname(__file__), 'mapowner.html')
                else:                           #send to choose_place.html
                    template_values = dict()
                    path = os.path.join(os.path.dirname(__file__), 'choose_place')
                self.response.out.write(template.render(path, template_values))

class Details(webapp.RequestHandler):
    def get(self):
        action = self.request.get("Action", "read")
        place_id = self.request.get("place")
        key = db.Key.from_path("Group", place_id)
        place = Group.get(key)
        
        if action == "read":
            pins = db.GqlQuery("SELECT * FROM Pin where ancestor is :group LIMIT 100", group=place)
            cnt = 1
            pinage = 0
            time = datetime.now()
            ord = time.toordinal()
            for pin in pins:
                pintime= pin.date
                pinord = pintime.toordinal()
                pinage = ord - pinord
                sPinage = "%s" % pinage
                self.response.out.write("\t".join( (str(pin.key()),
                  pin.date.strftime('%a %m %d %Y %H%M'), str(pin.lat),
                  str(pin.lng), pin.name, str(pin.primaryColor), pin.label, sPinage) ) )
                logging.info("Activity time %s " % pinage)
                cnt += 1
                self.response.out.write("\n")
        elif action == "add":
            pin = Pin(parent=place)
            pin.name = self.request.get('details')
            pin.lat = float(self.request.get('lat'))
            pin.lng = float(self.request.get('lng'))
            pin.primaryColor = self.request.get('primaryColor')
            pin.label = self.request.get('label')
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
        group.activity = self.request.get('activity')
        group.moreinfo = self.request.get('moreinfo')
        group.marker_lat = float(self.request.get('marker_lat'))
        group.marker_lng = float(self.request.get('marker_lng'))
        #this pin should NOT have a parent so it is not
        #included in the many ancestor pins
        key = db.Key.from_path("Pin", place_id)
        pin = Pin.get(key)
        pin.name = place_id
        pin.lat = float(self.request.get('marker_lat'))
        pin.lng = float(self.request.get('marker_lng'))
        pin.put()
        group.put()
        self.redirect("/?place=%s" % place_id)
            
        
                                     
                                     
def make_new_map(place_id,self):
      user = users.get_current_user()
      logging.info("Make_new User %s " % user)
      if user:    #send to add_place.html
          logging.info("Make_new User if %s " % user)
          place= Group(key_name=place_id)
          place.place = place_id
          place.user = user
          place.people = ""
          place.center_lat = float(-999)
          place.center_lng = float(-999)
          place.zoom = int(-999)
          place.marker_lat = float(-999)
          place.marker_lng = float(-999)
          place.contact = ""
          place.activity = ""
          place.moreinfo = ""
          place.put()
          pin = Pin(key_name=place_id)
          pin.name = place_id
          pin.put()
          path = os.path.join(os.path.dirname(__file__), 'add_place.html')
          template_values = dict(place=place.place, user=place.user) 
          template_values = dict(place_id=place.key(), place=place.place, 
                   people=place.people, center_lat=place.center_lat, 
                   center_lng=place.center_lng, map_zoom=place.zoom,
                   marker_lat=place.marker_lat, marker_lng=place.marker_lng, 
                   contact=place.contact, moreinfo=place.moreinfo,
                   activity=place.activity, user=place.user)
          self.response.out.write(template.render(path, template_values))
      else:     #send back to choose_place.html
          logging.info("User else %s " % user)
          greeting = ("<a href=\"%s\">Sign in or register</a>." %
                  users.create_login_url("/"))
          self.response.out.write("<html><body>%s</body></html>" % greeting)          
application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/details.txt', Details),
                                      ('/add_place', AddPlace),
                                      ('/mapowner', OwnerMap)],
                                     debug=True)

                    
def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
