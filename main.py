import os

import arcade
from arcade import particles
from arcade.math import rand_in_circle
import arcade.future.background

# Constants
WINDOW_WIDTH = 2560
WINDOW_HEIGHT = 1440
WINDOW_TITLE = "Platformer"

TILE_SCALING = 1

PLAYER_MOVEMENT_SPEED = 2
GRAVITY = 1
PLAYER_JUMP_SPEED = 10

RIGHT_FACING = 1
LEFT_FACING = 0

ASSETS_DIR = "assets"


def make_trail(attached_sprite):
    e = particles.Emitter(
        center_xy=attached_sprite.position,
        emit_controller=particles.EmitInterval(0.01),
        particle_factory=lambda emitter: particles.FadeParticle(
            filename_or_texture=arcade.make_soft_square_texture(4, arcade.color.Color(46, 31, 38), outer_alpha=255),
            change_xy=rand_in_circle((0, 0.5), -0.5),
            scale=0.75,
            lifetime=0.2,
            end_alpha=255
        )
    )
    return e


class Character(arcade.Sprite):
    def __init__(self, name_folder):
        super().__init__()

        self.facing_direction = RIGHT_FACING
        self.current_texture = 0

        self.idle_textures = []
        for i in range(5):
            texture = arcade.load_texture(os.path.join(ASSETS_DIR, name_folder, f"idle_{i}.png"))
            self.idle_textures.append((texture, texture.flip_left_right()))

        self.walk_textures = []
        for i in range(8):
            texture = arcade.load_texture(os.path.join(ASSETS_DIR, name_folder, f"walk_{i}.png"))
            self.walk_textures.append((texture, texture.flip_left_right()))

        self.jump_textures = []
        for i in range(4):
            texture = arcade.load_texture(os.path.join(ASSETS_DIR, name_folder, f"jump_{i}.png"))
            self.jump_textures.append((texture, texture.flip_left_right()))

        self.fail_textures = []
        for i in range(4):
            texture = arcade.load_texture(os.path.join(ASSETS_DIR, name_folder, f"fail_{i}.png"))
            self.fail_textures.append((texture, texture.flip_left_right()))

        self.texture = self.idle_textures[0][1]


class PlayerCharacter(Character):
    def __init__(self):
        super().__init__("warrior")
        self.texture_change_time = 0
        self.texture_change_delay = 0.15

        self.climbing = False
        self.should_update_walk = 0

    def update_animation(self, delta_time):
        if self.change_x < 0 and self.facing_direction == RIGHT_FACING:
            self.facing_direction = LEFT_FACING
        elif self.change_x > 0 and self.facing_direction == LEFT_FACING:
            self.facing_direction = RIGHT_FACING

        if self.change_x == 0:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture > 4:
                    self.current_texture = 0
                self.texture = self.idle_textures[self.current_texture][self.facing_direction]
                return

        # Handle walking
        if self.change_x != 0:
            self.texture_change_time += delta_time
            if self.texture_change_time >= self.texture_change_delay:
                self.current_texture += 1
                self.texture_change_time = 0
                if self.current_texture > 6:
                    self.current_texture = 0
                self.texture = self.walk_textures[self.current_texture][self.facing_direction]
                self.should_update_walk = 0
                return

        if self.change_y > 0:
            self.texture_change_time += delta_time
            if self.texture_change_time >= 0.05:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture > 3:
                    self.current_texture = 0
                self.texture = self.jump_textures[self.current_texture][self.facing_direction]
                return

        if self.change_y < -2 * PLAYER_JUMP_SPEED:
            self.texture_change_time += delta_time
            if self.texture_change_time >= 0.05:
                self.texture_change_time = 0
                self.current_texture += 1
                if self.current_texture > 3:
                    self.current_texture = 0
                self.texture = self.fail_textures[self.current_texture][self.facing_direction]
                return

        self.should_update_walk += 1


class GameView(arcade.View):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class to set up the window
        super().__init__()

        self.max_stamina = 100
        self.current_stamina = self.max_stamina
        self.stamina_drain_rate = 20.0
        self.stamina_regen_rate = 10.0

        self.emitters = []
        self.trail = None

        # Track the current state of our input
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

        # Variable to hold our texture for our player
        self.player_texture = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Variable to hold our Tiled Map
        self.tile_map = None

        # Replacing all of our SpriteLists with a Scene variable
        self.scene = None

        # A variable to store our camera object
        self.camera = None

        # A variable to store our gui camera object
        self.gui_camera = None

        # Where is the right edge of the map?
        self.end_of_map = 0

        self.backgrounds = arcade.future.background.ParallaxGroup()
        bg_layer_size_px = (WINDOW_WIDTH, WINDOW_HEIGHT)

        self.backgrounds.add_from_file(
            os.path.join("resources", "GandalfHardcore FREE Platformer Assets", "GandalfHardcore Background layers",
                         "Normal BG", "GandalfHardcore Background layers_layer 5.png"),
            size=bg_layer_size_px,
            depth=10.0,
            scale=5
        )
        self.backgrounds.add_from_file(
            os.path.join("resources", "GandalfHardcore FREE Platformer Assets", "GandalfHardcore Background layers",
                         "Normal BG", "GandalfHardcore Background layers_layer 4.png"),
            size=bg_layer_size_px,
            depth=7.0,
            scale=5
        )
        self.backgrounds.add_from_file(
            os.path.join("resources", "GandalfHardcore FREE Platformer Assets", "GandalfHardcore Background layers",
                         "Normal BG", "GandalfHardcore Background layers_layer 3.png"),
            size=bg_layer_size_px,
            depth=5.0,
            scale=5
        )
        self.backgrounds.add_from_file(
            os.path.join("resources", "GandalfHardcore FREE Platformer Assets", "GandalfHardcore Background layers",
                         "Normal BG", "GandalfHardcore Background layers_layer 2.png"),
            size=bg_layer_size_px,
            depth=3.0,
            scale=5
        )

        self.backgrounds.add_from_file(
            os.path.join("resources", "GandalfHardcore FREE Platformer Assets", "GandalfHardcore Background layers",
                         "Normal BG",
                         "GandalfHardcore Background layers_layer 1.png"),
            size=bg_layer_size_px,
            depth=1.0,
            scale=5
        )

    def on_show_view(self):
        self.setup()

    def setup(self):
        """Set up the game here. Call this function to restart the game."""

        layer_options = {
            "Ground": {
                "use_spatial_hash": True
            }
        }

        self.tile_map = arcade.load_tilemap(
            os.path.join("resources", "FullMap.tmx"),
            scaling=TILE_SCALING,
            layer_options=layer_options
        )

        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        self.player_sprite = PlayerCharacter()
        self.player_sprite.scale = 1
        self.player_sprite.center_x = 128
        self.player_sprite.center_y = 128
        self.scene.add_sprite("Player", self.player_sprite)

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite,
            walls=self.scene["Ground"]
        )

        # Initialize our camera, setting a viewport the size of our window.
        self.camera = arcade.Camera2D()
        self.camera.width, self.camera.height = 224, 126

        # Initialize our gui camera, initial settings are the same as our world camera.
        self.gui_camera = arcade.Camera2D()

        # Calculate the right edge of the map in pixels
        self.end_of_map = (self.tile_map.width * self.tile_map.tile_width)
        self.end_of_map *= self.tile_map.scaling

        self.hp_bar = arcade.SpriteList()
        self.hp_bar.append(arcade.Sprite(
            os.path.join("resources", "GandalfHardcore Hp bar", "red bar.png"),
            scale=6, center_x=344, center_y=(WINDOW_HEIGHT - 294)
        ))
        self.hp_bar.append(arcade.Sprite(
            os.path.join("resources", "GandalfHardcore Hp bar", "yellow bar.png"),
            scale=6, center_x=640, center_y=(WINDOW_HEIGHT - 402)
        ))
        self.hp_bar.append(arcade.Sprite(
            os.path.join("resources", "GandalfHardcore Hp bar", "Blue bar.png"),
            scale=6, center_x=677, center_y=(WINDOW_HEIGHT - 450)
        ))
        self.hp_bar.append(arcade.Sprite(
            os.path.join("resources", "GandalfHardcore Hp bar", "Hp bar.png"),
            scale=6, center_x=500, center_y=(WINDOW_HEIGHT - 300)
        ))

    def on_draw(self):
        """Render the screen."""

        # The clear method should always be called at the start of on_draw.
        # It clears the whole screen to whatever the background color is
        # set to. This ensures that you have a clean slate for drawing each
        # frame of the game.
        self.clear()

        # Store a reference to the background layers as shorthand
        self.backgrounds.draw()

        # Activate our camera before drawing
        self.camera.use()

        # Draw our Scene
        self.scene.draw(pixelated=True)

        if self.physics_engine.can_jump(y_distance=3):
            for e in self.emitters:
                e.draw()

        # Activate our GUI camera
        self.gui_camera.use()
        self.hp_bar.draw(pixelated=True)

    def on_update(self, delta_time):
        """Movement and Game Logic"""

        # Move the player using our physics engine
        self.physics_engine.update()

        # Actually trigger animation updates. We've added the Background and Coins layer
        # here as well. Our Tiled map has some animated tiles built-in, check out the flags
        # and torches on the map.
        self.scene.update_animation(
            delta_time,
            [
                "Player",
                "Water",
                "BG"
            ]
        )

        is_moving = self.left_pressed or self.right_pressed
        on_ground = self.physics_engine.can_jump()

        if is_moving and on_ground:
            # Тратим стамину
            self.current_stamina -= self.stamina_drain_rate * delta_time
        else:
            if on_ground:
                self.current_stamina += self.stamina_regen_rate * delta_time

        # Ограничиваем значения, чтобы не ушли в минус или выше максимума
        if self.current_stamina < 0:
            self.current_stamina = 0
        elif self.current_stamina > self.max_stamina:
            self.current_stamina = self.max_stamina

        self.hp_bar.sprite_list[1].width = (self.current_stamina / self.max_stamina) * 192
        self.hp_bar.sprite_list[1].left = 544

        # Подкручиваем центр «следа» к игроку
        if self.trail:
            if self.player_sprite.facing_direction:
                self.trail.center_x = self.player_sprite.center_x - 9
            else:
                self.trail.center_x = self.player_sprite.center_x + 9
            self.trail.center_y = self.player_sprite.center_y - 32

        # Обновляем эмиттеры и чистим «умершие»
        emitters_copy = self.emitters.copy()  # Защищаемся от мутаций списка
        for e in emitters_copy:
            e.update(delta_time)
        for e in emitters_copy:
            if e.can_reap():  # Готов к уборке?
                self.emitters.remove(e)

        # Center our camera on the player
        if self.player_sprite.center_x >= 113:
            self.camera.position = self.player_sprite.position
        else:
            self.camera.position = 113, self.player_sprite.position[1]
        if self.player_sprite.center_y < -100:
            self.setup()

    def process_keychange(self):
        # Now we just handle our horizontal movement, very similar to how we
        # did before, but now just combined in our new function.
        if self.up_pressed and not self.down_pressed:
            if self.physics_engine.can_jump(y_distance=3):
                self.player_sprite.change_y = PLAYER_JUMP_SPEED

        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True

        if key == arcade.key.LEFT or key == arcade.key.A or key == arcade.key.RIGHT or key == arcade.key.D:
            if self.trail:
                self.emitters.remove(self.trail)
                self.trail = None
            else:
                self.trail = make_trail(self.player_sprite)
                self.emitters.append(self.trail)

        if key == arcade.key.ESCAPE:
            self.window.close()

        self.process_keychange()

    def on_key_release(self, key, modifiers):
        """Called whenever a key is released."""

        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False

        if key == arcade.key.LEFT or key == arcade.key.A or key == arcade.key.RIGHT or key == arcade.key.D:
            if self.trail:
                self.emitters.remove(self.trail)
                self.trail = None
            else:
                self.trail = make_trail(self.player_sprite)
                self.emitters.append(self.trail)

        self.process_keychange()


def main():
    """Main function"""
    window = arcade.Window(fullscreen=True)
    game = GameView()

    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()
