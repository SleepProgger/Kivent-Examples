from kivy.app import App
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window
from random import randint, choice
from math import radians, pi, sin, cos
import kivent_core
import kivent_cymunk
from kivent_core.gameworld import GameWorld, ObjectProperty
from kivent_core.managers.resource_managers import texture_manager
from kivent_core.systems.renderers import RotateRenderer
from kivent_core.systems.position_systems import PositionSystem2D
from kivent_core.systems.rotate_systems import RotateSystem2D
from kivy.properties import StringProperty, NumericProperty
from functools import partial


texture_manager.load_atlas('assets/background_objects.atlas')


class TestGame(Widget):
    def __init__(self, **kwargs):
        super(TestGame, self).__init__(**kwargs)
        self.gameworld.init_gameworld(
            ['cymunk_physics', 'rotate_color_renderer', 'rotate', 'color', 'position',
            'camera1'],
            callback=self.init_game)

    def init_game(self):
        self.setup_states()
        self.set_state()
        # set up click event
        self.ids.gameworld.bind(on_touch_down=self.on_mouse_click)
        # lol, we need this to stop clicks on our GUI to deselect the current asteroid 
        self._btn_pane = self.ids.gamescreenmanager.ids.main_screen.ids.bottom_pane

    def setup_states(self):
        self.gameworld.add_state(state_name='main', 
            systems_added=['rotate_color_renderer'],
            systems_removed=[], systems_paused=[],
            systems_unpaused=['rotate_color_renderer'],
            screenmanager_screen='main')

    def set_state(self):
        self.gameworld.state = 'main'
        

    def on_mouse_click(self, etype, event):
        # Check if we clicked the bottom pane.
        # A better way would be to make the "game viewport" smaller and
        # don't just overlay our GUI, but i failed to do this so far, so...
        if self._btn_pane.collide_point(*event.pos):
            return
        
        entities = self.gameworld.entities
        gameview = self.gameworld.system_manager['camera1']
                
        if not self.app.selected_id is None:
            ent = entities[self.app.selected_id]
            ent.color.r = 255   
                             
        # We need to handle scrolling offsets (TODO: zoom/scale)
        x, y = event.pos
        x = x - gameview.camera_pos[0]
        y = y - gameview.camera_pos[1]        
        physics = self.gameworld.system_manager['cymunk_physics']
        # if you want to select a region use physics.query_bb(...)
        hits = physics.query_segment((x,y), (x,y))
        if len(hits) > 0:            
            ent = entities[hits[0][0]]
            ent.color.r = 0
            self.app.selected_id = ent.entity_id
            gameview.entity_to_focus = ent.entity_id
            gameview.focus_entity = True
        else:
            self.app.selected = None            
            gameview.focus_entity = False

        
    def draw_some_stuff(self):
        gameview = self.gameworld.system_manager['camera1']
        x, y = int(-gameview.camera_pos[0]), int(-gameview.camera_pos[1])
        w, h =  int(gameview.size[0] + x), int(gameview.size[1] + y)
        create_asteroid = self.create_asteroid
        for i in range(100):
            pos = (randint(x, w), randint(y, h))
            ent_id = create_asteroid(pos)
        self.app.count += 100


    def create_asteroid(self, pos):
        x_vel = randint(-250, 250)
        y_vel = randint(-250, 250)
        angle = radians(randint(-360, 360))
        angular_velocity = radians(randint(-150, -150))
        shape_dict = {'inner_radius': 0, 'outer_radius': 22, 
            'mass': 50, 'offset': (0, 0)}
        col_shape = {'shape_type': 'circle', 'elasticity': .5, 
            'collision_type': 1, 'shape_info': shape_dict, 'friction': 1.0}
        col_shapes = [col_shape]
        physics_component = {'main_shape': 'circle', 
            'velocity': (x_vel, y_vel), 
            'position': pos, 'angle': angle, 
            'angular_velocity': angular_velocity, 
            'vel_limit': 500, 
            'ang_vel_limit': radians(200), 
            'mass': 50, 'col_shapes': col_shapes}
        create_component_dict = {'cymunk_physics': physics_component, 
            'rotate_color_renderer': {
                'texture': 'asteroid1',
                'size': (45, 45),
                'render': True
            },
            'color': (255,255,255,255),
            'position': pos, 'rotate': 0, }
        component_order = ['position', 'rotate', 'color', 'rotate_color_renderer', 
            'cymunk_physics',]
        return self.gameworld.init_entity(
            create_component_dict, component_order)

    def destroy_asteroid(self, ent_id):
        if ent_id is None: return #TODO: check if entity  is valid
        gameview = self.gameworld.system_manager['camera1']
        gameview.entity_to_focus = None        
        self.app.selected_id = None
        self.gameworld.remove_entity(ent_id)
        self.app.count -= 1

    def set_asteroid_velocity(self, ent_id, vx=0, vy=0):
        if ent_id is None: return #TODO: check if entity  is valid
        entities = self.gameworld.entities
        ent = entities[ent_id].cymunk_physics
        ent.body.velocity = (vx, vy)



class YourAppNameApp(App):
    count = NumericProperty(0)
    fps = NumericProperty(0)
    
    selected_id = None
    selected_coords = ObjectProperty(None, allownone=True)
    selected_velocity = ObjectProperty(None, allownone=True)    
    def __init__(self, **kwargs):
        App.__init__(self, **kwargs)
        Clock.schedule_once(self.update_stats, .5)
        
    def update_stats(self, dt):
        self.fps = int(Clock.get_fps())
        if self.selected_id is None:
            self.selected_coords = None
            self.selected_velocity = None
        else:
            ent = self.root.gameworld.entities[self.selected_id]
            physics = ent.cymunk_physics
            self.selected_coords = (int(ent.position.x), int(ent.position.y))
            self.selected_velocity = (physics.body.velocity.x, physics.body.velocity.y)                        
        Clock.schedule_once(self.update_stats, .5)
        
    


if __name__ == '__main__':
    YourAppNameApp().run()