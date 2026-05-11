from ursina import *

class TextureScroller:
    def __init__(self, speed:Vec2=None):
        self.speed = speed or Vec2(.005,.005)

    def update(self):
        self.entity.texture_offset += self.speed * time.dt


if __name__ == '__main__':
    app = Ursina()
    p = Entity(model='quad', texture='brick')

    p.add_script(TextureScroller(speed=Vec2(1,1)))
    app.run()
