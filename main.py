from ursina import *
from ursina.shaders import lit_with_shadows_shader, matcap_shader, unlit_shader
from panda3d.core import TransparencyAttrib, GeomNode, LPoint3f
from PIL import Image
import random
import math
import os

app = Ursina()
window.title = "OFFROAD HORIZON 3D - ULTRA OPEN WORLD"
window.borderless = False

def rgba(r, g, b, a=255):
    return Vec4(r / 255.0, g / 255.0, b / 255.0, a / 255.0)

window.color = rgba(115, 168, 218)

# ==========================================
# 0. PROCEDURAL HIGH-RES TEXTURES (PIL)
# ==========================================
def create_terrain_detail_texture():
    img = Image.new('RGB', (256, 256))
    px = img.load()
    for y in range(256):
        for x in range(256):
            n = int(random.uniform(215, 255))
            if (x + y) % 6 == 0:
                n = int(n * 0.92)
            px[x, y] = (n, n, n)
    return Texture(img)

def create_soft_circle_texture(r_col, g_col, b_col, max_alpha):
    size = 128
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    px = img.load()
    cx, cy = size / 2.0, size / 2.0
    for y in range(size):
        for x in range(size):
            d = math.hypot((x - cx) / (size * 0.45), (y - cy) / (size * 0.45))
            if d < 1.0:
                alpha = int(((1.0 - d) ** 1.8) * max_alpha)
                px[x, y] = (r_col, g_col, b_col, alpha)
    return Texture(img)

def create_sky_gradient_texture():
    img = Image.new('RGB', (64, 256))
    px = img.load()
    for y in range(256):
        t = y / 255.0
        r = int(32 * (1 - t) + 195 * t)
        g = int(82 * (1 - t) + 220 * t)
        b = int(155 * (1 - t) + 245 * t)
        for x in range(64):
            px[x, y] = (r, g, b)
    return Texture(img)

detail_tex = create_terrain_detail_texture()
shadow_tex = create_soft_circle_texture(0, 0, 0, 215)
glow_tex = create_soft_circle_texture(0, 255, 255, 165)
procedural_sky_tex = create_sky_gradient_texture()

# ==========================================
# 1. LIGHTING, FOG & SKY DOME
# ==========================================
sun_light = DirectionalLight(y=35, z=20, shadows=False)
sun_light.look_at(Vec3(-1, -1.3, -1))
sun_light.color = rgba(255, 248, 235)

ambient_light = AmbientLight()
ambient_light.color = rgba(165, 175, 190)

try:
    scene.fog_color = rgba(165, 200, 230)
    scene.fog_density = 0.0016
except Exception:
    pass

sky_tex = None
for folder in ['textures', 'texture', '.']:
    if os.path.exists(folder):
        for fname in os.listdir(folder):
            if fname.lower().endswith(('.jpg', '.png', '.hdr', '.exr')):
                try:
                    loaded = load_texture(f'{folder}/{fname}')
                    if loaded:
                        sky_tex = loaded
                        break
                except Exception:
                    pass
    if sky_tex:
        break

sky_dome = Entity(
    model='sphere',
    scale=1150,
    texture=sky_tex if sky_tex else procedural_sky_tex,
    color=rgba(255, 255, 255),
    double_sided=True,
    unlit=True
)

sun_orb = Entity(model='sphere', scale=55, position=(280, 210, 360), color=rgba(255, 245, 180), unlit=True)

# ==========================================
# 2. DRAMATIC ROLLING HILLS, MOUNTAIN HIGHWAY & RAMPS
# ==========================================
MAP_SIZE = 640.0
GRID_RES = 84
CELL_SIZE = MAP_SIZE / GRID_RES
HALF_MAP = MAP_SIZE * 0.5

# Stunt Ramp definitions: (center_x, center_z, width, length, height, direction_z)
RAMP_LIST = [
    (0.0, 50.0, 11.0, 22.0, 5.2, 1),
    (31.0, 125.0, 11.0, 24.0, 5.8, 1),
    (-28.0, -90.0, 11.0, 22.0, 5.2, -1),
    (75.0, -30.0, 12.0, 24.0, 6.0, 1),
    (-75.0, 45.0, 12.0, 24.0, 6.0, 1),
]

def road_center_curve(z):
    return math.sin(z * 0.015) * 42.0

def compute_world_height(x, z):
    """Generates steep, unmistakable uphill/downhill slopes both on the highway and offroad."""
    rcx = road_center_curve(z)
    dist_road = abs(x - rcx)

    # Keep only a small 14m starting pad flat at (0,0) so hills start immediately!
    spawn_mask = min(max((math.hypot(x, z) - 12.0) / 16.0, 0.0), 1.0)

    # Highway elevation profile (smooth rollercoaster hills & valleys along Z)
    highway_hills = (math.sin(z * 0.032) * 9.5 + math.cos(z * 0.016) * 6.5) * spawn_mask

    # Offroad rugged hills, steep ridges, and outer mountains
    offroad_h1 = math.sin(x * 0.035) * math.cos(z * 0.035) * 16.0
    offroad_h2 = math.sin(x * 0.07 + 1.1) * math.sin(z * 0.065) * 6.5
    border_dist = max(0.0, (math.hypot(x, z) - 205.0) / 80.0)
    mountains = (border_dist ** 2) * 38.0

    # Blend smoothly from highway elevation to offroad mountains
    road_blend = min(max((dist_road - 7.5) / 18.0, 0.0), 1.0)
    base_h = highway_hills * (1.0 - road_blend) + (highway_hills * 0.5 + offroad_h1 + offroad_h2 + mountains) * road_blend * spawn_mask

    # Mold stunt ramps into the terrain
    for rx, rz, rw, rl, rh, rdir in RAMP_LIST:
        dx = abs(x - rx)
        dz = (z - rz) * rdir
        if dx < rw * 0.5 and -rl * 0.5 <= dz <= rl * 0.5:
            prog = (dz + rl * 0.5) / rl
            side_fade = min(1.0, (rw * 0.5 - dx) / 1.2)
            base_h += (prog ** 1.3) * rh * side_fade

    return base_h

height_grid = [[0.0 for _ in range(GRID_RES + 1)] for _ in range(GRID_RES + 1)]
for gz in range(GRID_RES + 1):
    z = -HALF_MAP + gz * CELL_SIZE
    for gx in range(GRID_RES + 1):
        x = -HALF_MAP + gx * CELL_SIZE
        height_grid[gz][gx] = compute_world_height(x, z)

def get_ground_height(x, z):
    gx_f = (x + HALF_MAP) / CELL_SIZE
    gz_f = (z + HALF_MAP) / CELL_SIZE
    gx = int(max(0, min(GRID_RES - 1, math.floor(gx_f))))
    gz = int(max(0, min(GRID_RES - 1, math.floor(gz_f))))
    tx, tz = gx_f - gx, gz_f - gz
    h0 = height_grid[gz][gx] * (1 - tx) + height_grid[gz][gx + 1] * tx
    h1 = height_grid[gz + 1][gx] * (1 - tx) + height_grid[gz + 1][gx + 1] * tx
    return h0 * (1 - tz) + h1 * tz

# Build Sun-Shaded 3D Terrain Mesh
verts, uvs, norms, cols, tris = [], [], [], [], []
sun_dir = Vec3(0.55, 0.72, 0.42).normalized()

for gz in range(GRID_RES + 1):
    z = -HALF_MAP + gz * CELL_SIZE
    for gx in range(GRID_RES + 1):
        x = -HALF_MAP + gx * CELL_SIZE
        y = height_grid[gz][gx]
        verts.append(Vec3(x, y, z))
        uvs.append(Vec2(gx * 0.75, gz * 0.75))

        hL = height_grid[gz][max(0, gx - 1)]
        hR = height_grid[gz][min(GRID_RES, gx + 1)]
        hD = height_grid[max(0, gz - 1)][gx]
        hU = height_grid[min(GRID_RES, gz + 1)][gx]
        normal = Vec3(hL - hR, 2.0 * CELL_SIZE, hD - hU).normalized()
        norms.append(normal)

        sun_dot = max(0.0, normal.x * sun_dir.x + normal.y * sun_dir.y + normal.z * sun_dir.z)
        shade = 0.45 + 0.62 * sun_dot
        slope = 1.0 - normal.y

        rcx = road_center_curve(z)
        dist_road = abs(x - rcx)
        on_ramp = any(abs(x - rx) < rw * 0.5 and abs(z - rz) < rl * 0.5 for rx, rz, rw, rl, _, _ in RAMP_LIST)

        if on_ramp:
            r, g, b = 225, 95, 30
        elif dist_road < 6.8:
            r, g, b = 46, 48, 54
        elif dist_road < 8.8:
            r, g, b = 140, 115, 85
        elif y < -5.5:
            r, g, b = 194, 168, 118
        elif y > 20.0 and slope < 0.35:
            r, g, b = 235, 242, 252
        elif slope > 0.22 or y > 13.5:
            r, g, b = 108, 102, 96
        else:
            alt_blend = min(1.0, max(0.0, (y + 4.0) / 18.0))
            r = int(52 * (1 - alt_blend) + 86 * alt_blend)
            g = int(106 * (1 - alt_blend) + 128 * alt_blend)
            b = int(42 * (1 - alt_blend) + 56 * alt_blend)

        cols.append(rgba(min(255, int(r * shade)), min(255, int(g * shade)), min(255, int(b * shade))))

for gz in range(GRID_RES):
    for gx in range(GRID_RES):
        i0 = gz * (GRID_RES + 1) + gx
        i1 = i0 + 1
        i2 = (gz + 1) * (GRID_RES + 1) + gx
        i3 = i2 + 1
        tris.extend([i0, i2, i1, i1, i2, i3])

terrain_mesh = Mesh(vertices=verts, triangles=tris, normals=norms, uvs=uvs, colors=cols, mode='triangle')
terrain_ent = Entity(model=terrain_mesh, texture=detail_tex, double_sided=True, unlit=True)

water_plane = Entity(
    model='plane', scale=(MAP_SIZE, 1, MAP_SIZE), position=(0, -6.0, 0),
    texture=detail_tex, texture_scale=(35, 35), color=rgba(30, 130, 200, 185),
    double_sided=True, unlit=True
)

# Sloped Highway Center Dashes (aligned to road slope!)
for z_step in range(-270, 270, 10):
    rx = road_center_curve(z_step)
    next_rx = road_center_curve(z_step + 2.5)
    ry = get_ground_height(rx, z_step)
    next_ry = get_ground_height(next_rx, z_step + 2.5)
    yaw_angle = math.degrees(math.atan2(next_rx - rx, 2.5))
    pitch_angle = -math.degrees(math.atan2(next_ry - ry, 2.5))
    Entity(
        model='cube', scale=(0.35, 0.05, 4.2),
        position=(rx, ry + 0.08, z_step),
        rotation=(pitch_angle, yaw_angle, 0),
        color=rgba(250, 210, 35), unlit=True
    )

# ==========================================
# 3. TREES & ROCKS
# ==========================================
obstacles = []
for _ in range(110):
    tx, tz = random.uniform(-250, 250), random.uniform(-250, 250)
    if abs(tx - road_center_curve(tz)) < 15.0 or math.hypot(tx, tz) < 28.0:
        continue
    ty = get_ground_height(tx, tz)
    if ty < -5.0 or ty > 17.0:
        continue
    th = random.uniform(3.6, 5.4)
    Entity(model='cube', scale=(0.75, th, 0.75), position=(tx, ty + th * 0.5, tz), color=rgba(82, 52, 32), unlit=True)
    Entity(model='sphere', scale=(4.2, 3.4, 4.2), position=(tx, ty + th + 0.6, tz), color=rgba(36, 78, 34), unlit=True)
    Entity(model='sphere', scale=(3.3, 2.8, 3.3), position=(tx, ty + th + 2.2, tz), color=rgba(48, 98, 42), unlit=True)
    Entity(model='sphere', scale=(2.2, 2.0, 2.2), position=(tx, ty + th + 3.5, tz), color=rgba(64, 118, 52), unlit=True)
    obstacles.append(Vec3(tx, ty, tz))

for _ in range(45):
    bx, bz = random.uniform(-240, 240), random.uniform(-240, 240)
    if abs(bx - road_center_curve(bz)) < 14.0 or math.hypot(bx, bz) < 26.0:
        continue
    by = get_ground_height(bx, bz)
    if by < -5.0:
        continue
    bs = random.uniform(2.2, 4.8)
    Entity(
        model='sphere', scale=(bs, bs * 0.7, bs * 0.85),
        position=(bx, by + bs * 0.25, bz),
        rotation=(random.uniform(0, 45), random.uniform(0, 360), 0),
        texture=detail_tex, color=rgba(110, 108, 104), unlit=True
    )
    obstacles.append(Vec3(bx, by, bz))

# ==========================================
# 4. HIERARCHICAL CAR RIG & BULLETPROOF .GLB RESCUE LOADER
# ==========================================
# HIERARCHY:
# car (world position & horizontal heading ONLY -> keeps car.forward horizontal for camera!)
#  └── slope_pivot (tilts nose UP/DOWN and rolls sideways to match the hill!)
#       └── chassis (suspension bounce & steering body-roll)
#            └── wrapper (holds each rescued .glb car)

car = Entity(position=(0, get_ground_height(0, 0), 0))
slope_pivot = Entity(parent=car, position=(0, 0, 0))
chassis = Entity(parent=slope_pivot, position=(0, 0, 0))

car_shadow = Entity(model='quad', texture=shadow_tex, rotation_x=90, scale=(4.2, 6.4, 1), position=(0, 0.1, 0), double_sided=True, unlit=True)
underglow = Entity(model='quad', texture=glow_tex, rotation_x=90, scale=(3.6, 5.6, 1), position=(0, 0.12, 0), double_sided=True, unlit=True, enabled=True)

nitro_flames = [
    Entity(parent=chassis, model='sphere', scale=(0.35, 0.35, 2.2), position=(-0.65, 0.65, -2.7), color=rgba(0, 240, 255), unlit=True, enabled=False),
    Entity(parent=chassis, model='sphere', scale=(0.35, 0.35, 2.2), position=(0.65, 0.65, -2.7), color=rgba(0, 240, 255), unlit=True, enabled=False)
]

car_configs = [
    {"name": "MAHINDRA THAR 4x4", "key": "thar", "color": rgba(210, 45, 35), "max_dry": 36.0, "accel": 24.0, "jump": 17.0},
    {"name": "TESLA CYBERTRUCK", "key": "cyber", "color": rgba(185, 195, 205), "max_dry": 40.0, "accel": 28.0, "jump": 16.0},
    {"name": "BMW M-COMPETITION", "key": "bmw", "color": rgba(30, 95, 210), "max_dry": 46.0, "accel": 32.0, "jump": 15.0},
    {"name": "BUGATTI CHIRON", "key": "bugatti", "color": rgba(25, 140, 235), "max_dry": 54.0, "accel": 38.0, "jump": 15.0},
]

def build_custom_fallback_car(parent_ent, key, body_col):
    """Builds a sleek multi-part 3D car if a .glb file is missing or corrupted."""
    root = Entity(parent=parent_ent)
    # Main body & cabin
    Entity(parent=root, model='cube', scale=(2.3, 0.75, 4.8), position=(0, 0.65, 0), color=body_col, unlit=True)
    Entity(parent=root, model='cube', scale=(1.95, 0.65, 2.3), position=(0, 1.3, -0.2), color=rgba(30, 35, 45), unlit=True)
    # Headlights & Taillights
    for x_off in [-0.75, 0.75]:
        Entity(parent=root, model='cube', scale=(0.4, 0.2, 0.1), position=(x_off, 0.75, 2.41), color=rgba(255, 250, 190), unlit=True)
        Entity(parent=root, model='cube', scale=(0.4, 0.2, 0.1), position=(x_off, 0.75, -2.41), color=rgba(255, 30, 30), unlit=True)
    # 4 Wheels
    for wx in [-1.2, 1.2]:
        for wz in [-1.55, 1.55]:
            Entity(parent=root, model='sphere', scale=(0.55, 0.85, 0.85), position=(wx, 0.42, wz), color=rgba(20, 22, 25), unlit=True)
            Entity(parent=root, model='sphere', scale=(0.58, 0.5, 0.5), position=(wx, 0.42, wz), color=rgba(200, 205, 215), unlit=True)
    return root

def find_matching_glb_file(keyword):
    """Finds any matching model file in models/ regardless of capitalization or double extension."""
    search_dirs = ['models', '.']
    for d in search_dirs:
        if os.path.exists(d) and os.path.isdir(d):
            for fname in os.listdir(d):
                low = fname.lower()
                if keyword in low and any(ext in low for ext in ['.glb', '.gltf', '.obj', '.bam']):
                    return f'{d}/{fname}' if d != '.' else fname
    return f'models/{keyword}.glb'

def load_and_rescue_glb(cfg):
    """Loads .glb, removes giant background floors, fixes invisible alpha/materials, and centers accurately."""
    wrapper = Entity(parent=chassis, enabled=False)
    orient_node = Entity(parent=wrapper, position=(0, 0, 0))
    matched_path = find_matching_glb_file(cfg["key"])
    model_ent = None

    for candidate in [matched_path, f'models/{cfg["key"]}.glb', f'{cfg["key"]}.glb']:
        try:
            model_ent = Entity(parent=orient_node, model=candidate)
            if model_ent and model_ent.model:
                break
        except Exception as e:
            print(f"Load attempt for {candidate}:", e)

    loaded_ok = False
    if model_ent and model_ent.model:
        try:
            raw_np = model_ent.model
            # 1. Inspect all child GeomNodes & remove accidental giant studio floors/sky domes inside the .glb
            geom_nodes = raw_np.findAllMatches('**/+GeomNode')
            node_spans = []
            for gn in geom_nodes:
                b1, b2 = LPoint3f(), LPoint3f()
                if gn.calcTightBounds(b1, b2):
                    span_xz = max(b2.x - b1.x, b2.z - b1.z)
                    span_y = b2.y - b1.y
                    if span_xz > 0.0001:
                        node_spans.append((gn, span_xz, span_y))

            if len(node_spans) > 2:
                spans_sorted = sorted([s[1] for s in node_spans])
                median_span = spans_sorted[len(spans_sorted) // 2]
                for gn, sxz, sy in node_spans:
                    # If a single mesh is > 4.5x larger than the car parts and flat like a floor, hide it!
                    if sxz > median_span * 4.5 and sy < sxz * 0.25:
                        gn.hide()

            # 2. Fix invisible alpha/transmission and transfer material base colors so nothing renders invisible
            raw_np.setTransparency(TransparencyAttrib.M_none)
            raw_np.setTwoSided(True)
            for gn in geom_nodes:
                gn.setTransparency(TransparencyAttrib.M_none)
                gn.setTwoSided(True)
                mat = gn.getMaterial()
                if mat and mat.hasBaseColor():
                    bc = mat.getBaseColor()
                    # Ensure opaque alpha and visible brightness
                    r_v = max(0.08, min(1.0, bc.x))
                    g_v = max(0.08, min(1.0, bc.y))
                    b_v = max(0.08, min(1.0, bc.z))
                    if not gn.hasTexture():
                        gn.setColor(Vec4(r_v, g_v, b_v, 1.0))

            # 3. Measure exact UN-SCALED tight bounds first
            b_min, b_max = raw_np.getTightBounds()
            if b_min is not None and b_max is not None:
                size = b_max - b_min
                max_dim = max(size.x, size.y, size.z)
                if max_dim > 0.0001 and max_dim < 1e6:
                    scale_factor = 5.2 / max_dim
                    center = (b_min + b_max) * 0.5

                    # Scale and offset by (center * scale_factor) so the car is 100% pinned at (0, 0, 0)!
                    model_ent.scale = scale_factor
                    model_ent.position = Vec3(
                        -center.x * scale_factor,
                        -b_min.y * scale_factor,
                        -center.z * scale_factor
                    )

                    # Rotate the outer orient_node if the car was modeled along the X-axis instead of Z-axis
                    if size.x > size.z * 1.15:
                        orient_node.rotation_y = 90

                    loaded_ok = True
                    cfg["status"] = f"GLB LOADED ({os.path.basename(matched_path)})"
        except Exception as e:
            print(f"GLB rescue warning for {cfg['name']}:", e)

    if not loaded_ok:
        if model_ent:
            destroy(model_ent)
        build_custom_fallback_car(orient_node, cfg["key"], cfg["color"])
        cfg["status"] = "3D FALLBACK (CHECK .GLB FILE)"

    return wrapper

loaded_car_entities = []
for cfg in car_configs:
    loaded_car_entities.append(load_and_rescue_glb(cfg))

current_car_idx = 0
loaded_car_entities[0].enabled = True

current_shader_idx = 0
shaders_list = [
    ("DEFAULT GLB", None),
    ("UNLIT BRIGHT", unlit_shader),
    ("LIT SHADER", lit_with_shadows_shader),
    ("GLOSSY MATCAP", matcap_shader)
]

# ==========================================
# 5. SOUND LOADER
# ==========================================
engine_sound = None
if os.path.exists('sounds'):
    for f in os.listdir('sounds'):
        if f.lower().endswith(('.wav', '.ogg', '.mp3')):
            try:
                engine_sound = Audio(f'sounds/{f}', loop=True, autoplay=True, volume=0.45)
                break
            except Exception:
                pass

# ==========================================
# 6. CHECKPOINTS & 3D GPS COMPASS
# ==========================================
cp_start_x = road_center_curve(75)
checkpoint_node = Entity(position=(cp_start_x, get_ground_height(cp_start_x, 75), 75))
Entity(parent=checkpoint_node, model='cube', scale=(0.9, 11, 0.9), position=(-6.5, 5.5, 0), color=rgba(255, 55, 30), unlit=True)
Entity(parent=checkpoint_node, model='cube', scale=(0.9, 11, 0.9), position=(6.5, 5.5, 0), color=rgba(255, 55, 30), unlit=True)
Entity(parent=checkpoint_node, model='cube', scale=(14.0, 1.8, 0.8), position=(0, 10.5, 0), color=rgba(255, 215, 0), unlit=True)
cp_orb = Entity(parent=checkpoint_node, model='sphere', scale=(2.8, 4.2, 2.8), position=(0, 4.2, 0), color=rgba(0, 255, 220), unlit=True)

gps_arrow = Entity(position=(0, 5, 0))
Entity(parent=gps_arrow, model='cube', scale=(0.35, 0.35, 1.6), position=(0, 0, 0), color=rgba(50, 255, 100), unlit=True)
Entity(parent=gps_arrow, model='sphere', scale=(0.85, 0.45, 1.1), position=(0, 0, 0.85), color=rgba(50, 255, 100), unlit=True)

# ==========================================
# 7. TELEMETRY HUD & GAME VARIABLES
# ==========================================
speed = 0.0
vy = 0.0
gravity = -38.0
is_grounded = True
steer_angle = 0.0
nitro_amount = 100.0
score = 0
drift_score = 0
cam_mode = 0
time_of_day = 0
particle_timer = 0.0
particles = []
skid_marks = []

camera.position = (0, 6, -14)
camera.fov = 78

Entity(parent=camera.ui, model='quad', scale=(0.56, 0.27), position=(-0.59, 0.35), color=rgba(10, 14, 22, 200))
ui_car = Text(text=f'1: {car_configs[0]["name"]}', position=(-0.85, 0.46), scale=1.0, color=rgba(0, 235, 255))
ui_speed = Text(text='0 KM/H  [GEAR 1]', position=(-0.85, 0.41), scale=1.4, color=rgba(255, 255, 255))
ui_slope = Text(text='SLOPE TILT: 0° LEVEL | ROLL: 0°', position=(-0.85, 0.35), scale=0.95, color=rgba(120, 255, 140))
ui_nitro = Text(text='NITRO [SHIFT]: 100%', position=(-0.85, 0.30), scale=0.95, color=rgba(255, 165, 0))
ui_score = Text(text='CHECKPOINTS: 0 | DRIFT: 0', position=(-0.85, 0.25), scale=0.95, color=rgba(255, 230, 50))

Entity(parent=camera.ui, model='quad', scale=(1.76, 0.08), position=(0, -0.45), color=rgba(10, 14, 22, 200))
Text(
    text='WASD: Drive (W/S in Air: Tilt) | J: Jump | SHIFT: Nitro | SPACE: Drift | 1-4: Cars | L: Shader | F: Rotate Car | [/]: Height | +/-: Scale',
    position=(-0.86, -0.44),
    scale=0.71,
    color=rgba(255, 255, 255)
)

def switch_car(idx):
    global current_car_idx
    for ent in loaded_car_entities:
        ent.enabled = False
    current_car_idx = idx
    loaded_car_entities[idx].enabled = True
    ui_car.text = f'{idx + 1}: {car_configs[idx]["name"]}'

def spawn_dust(pos, count=8, col=rgba(195, 175, 140)):
    for _ in range(count):
        p = Entity(
            model='sphere', scale=random.uniform(0.35, 0.75),
            position=pos + Vec3(random.uniform(-1.4, 1.4), 0.25, random.uniform(-1.4, 1.4)),
            color=col, unlit=True
        )
        particles.append([p, 0.5])

# ==========================================
# 8. MAIN PHYSICS & 4-WHEEL SLOPE TILT LOOP
# ==========================================
def update():
    global speed, vy, is_grounded, steer_angle, nitro_amount, score, drift_score, particle_timer
    dt = min(time.dt, 0.05)

    cfg = car_configs[current_car_idx]
    max_speed = cfg["max_dry"]
    accel = cfg["accel"]

    # 1. Sample 4-Wheel Ground Heights (Front-Left, Front-Right, Rear-Left, Rear-Right)
    # Because `car` only rotates around Y, `car.forward` and `car.right` are always purely horizontal!
    fwd = car.forward
    rgt = car.right
    fl_pos = car.position + fwd * 2.2 - rgt * 1.2
    fr_pos = car.position + fwd * 2.2 + rgt * 1.2
    rl_pos = car.position - fwd * 2.2 - rgt * 1.2
    rr_pos = car.position - fwd * 2.2 + rgt * 1.2

    h_fl = get_ground_height(fl_pos.x, fl_pos.z)
    h_fr = get_ground_height(fr_pos.x, fr_pos.z)
    h_rl = get_ground_height(rl_pos.x, rl_pos.z)
    h_rr = get_ground_height(rr_pos.x, rr_pos.z)

    h_front = (h_fl + h_fr) * 0.5
    h_back = (h_rl + h_rr) * 0.5
    h_left = (h_fl + h_rl) * 0.5
    h_right = (h_fr + h_rr) * 0.5
    avg_wheel_y = (h_fl + h_fr + h_rl + h_rr) * 0.25

    in_water = avg_wheel_y < -5.6
    if in_water:
        max_speed *= 0.65

    # 2. Exact Terrain Slope Angle Calculation (Degrees)
    # Uphill: h_front > h_back -> negative rotation_x pitches nose UP in Ursina
    slope_deg = math.degrees(math.atan2(h_front - h_back, 4.4))
    roll_deg = math.degrees(math.atan2(h_right - h_left, 2.4))

    # 3. Nitro Boost (Hold Left Shift)
    boosting = held_keys['left shift'] or held_keys['shift']
    if boosting and nitro_amount > 1.0 and held_keys['w']:
        nitro_amount = max(0.0, nitro_amount - 30.0 * dt)
        max_speed *= 1.55
        accel *= 1.85
        camera.fov = lerp(camera.fov, 96, dt * 6)
        for nf in nitro_flames:
            nf.enabled = True
            nf.scale_z = random.uniform(1.6, 3.0)
    else:
        nitro_amount = min(100.0, nitro_amount + 14.0 * dt)
        camera.fov = lerp(camera.fov, 78, dt * 5)
        for nf in nitro_flames:
            nf.enabled = False

    ui_nitro.text = f'NITRO [SHIFT]: {int(nitro_amount)}%'

    # 4. Throttle, Reverse, Gravity Slope Pull & Drift
    if held_keys['w']:
        speed += accel * dt
    elif held_keys['s']:
        speed -= accel * 0.85 * dt
    else:
        speed *= (1.0 - 1.1 * dt)

    # Natural hill gravity pull (speeds up slightly going downhill, works harder going uphill)
    if is_grounded:
        speed -= math.sin(math.radians(slope_deg)) * 9.5 * dt

    drifting = held_keys['space'] and abs(speed) > 8.0 and is_grounded
    if held_keys['space'] and not drifting:
        speed *= (1.0 - 4.5 * dt)
    elif drifting:
        speed *= (1.0 - 0.55 * dt)
        drift_score += int(abs(speed) * dt * 6)

    speed = max(-16.0, min(max_speed, speed))

    # 5. Steering
    target_steer = (held_keys['d'] - held_keys['a']) * (40.0 if drifting else 27.0)
    steer_angle = lerp(steer_angle, target_steer, dt * 10)
    if abs(speed) > 0.35:
        car.rotation_y += (steer_angle / 27.0) * 76.0 * dt * (1 if speed > 0 else -1)

    # 6. Horizontal Movement & Obstacle Check
    prev_ground_y = avg_wheel_y
    next_pos = car.position + car.forward * speed * dt

    if any(distance_xz(next_pos, obs) < 2.2 and abs(car.y - obs.y) < 5.0 for obs in obstacles):
        speed = -speed * 0.45
        spawn_dust(car.position, count=8, col=rgba(110, 80, 50))
    else:
        car.x = max(-HALF_MAP + 18, min(HALF_MAP - 18, next_pos.x))
        car.z = max(-HALF_MAP + 18, min(HALF_MAP - 18, next_pos.z))

    # 7. Vertical Physics, Crest Launch & Jump
    new_ground_y = get_ground_height(car.x, car.z)
    ground_climb_rate = (new_ground_y - prev_ground_y) / max(dt, 0.001)

    if is_grounded:
        # Launch airborne if flying over a steep ramp or hill crest!
        if ground_climb_rate > 5.0 and abs(speed) > 17.0:
            vy = ground_climb_rate * 1.15
            is_grounded = False
        else:
            car.y = avg_wheel_y
            vy = 0.0
    else:
        car.y += vy * dt
        vy += gravity * dt
        if car.y <= avg_wheel_y:
            if vy < -9.0:
                spawn_dust(car.position, count=12)
            car.y = avg_wheel_y
            vy = 0.0
            is_grounded = True

    # 8. Apply Real 3D Hill Tilt to `slope_pivot` (While `car` stays horizontal for the camera!)
    if is_grounded:
        target_pitch = -slope_deg
        target_roll = -roll_deg
        slope_pivot.rotation_x = lerp(slope_pivot.rotation_x, target_pitch, dt * 16)
        slope_pivot.rotation_z = lerp(slope_pivot.rotation_z, target_roll, dt * 16)

        if abs(slope_deg) > 2.0:
            dir_str = "UPHILL" if slope_deg > 0 else "DOWNHILL"
            ui_slope.text = f'SLOPE TILT: {slope_deg:+.1f}° ({dir_str}) | ROLL: {roll_deg:+.1f}°'
            ui_slope.color = rgba(255, 210, 60)
        else:
            ui_slope.text = f'SLOPE TILT: {slope_deg:+.1f}° (LEVEL) | ROLL: {roll_deg:+.1f}°'
            ui_slope.color = rgba(120, 255, 140)
    else:
        # Mid-air stunt pitch control + natural jump arc tilt
        air_control = (held_keys['s'] - held_keys['w']) * 22.0
        air_pitch = -vy * 1.5 + air_control
        slope_pivot.rotation_x = lerp(slope_pivot.rotation_x, air_pitch, dt * 7)
        slope_pivot.rotation_z = lerp(slope_pivot.rotation_z, 0.0, dt * 5)
        ui_slope.text = f'AIRBORNE! +{int(max(0, car.y - avg_wheel_y))}M  (PITCH: {-slope_pivot.rotation_x:+.0f}°)'
        ui_slope.color = rgba(0, 240, 255)

    # Chassis Suspension Body Roll & Drift Yaw
    steer_roll = -(steer_angle / 27.0) * min(abs(speed) * 0.3, 6.5)
    chassis.rotation_z = lerp(chassis.rotation_z, steer_roll, dt * 8)
    chassis.rotation_y = lerp(chassis.rotation_y, steer_angle * 0.42 if drifting else 0.0, dt * 8)

    # Align Soft Shadow & Underglow with the terrain slope underneath the car!
    car_shadow.position = Vec3(car.x, avg_wheel_y + 0.10, car.z)
    car_shadow.rotation = Vec3(90 - slope_deg, car.rotation_y, -roll_deg)
    underglow.position = Vec3(car.x, avg_wheel_y + 0.13, car.z)
    underglow.rotation = Vec3(90 - slope_deg, car.rotation_y, -roll_deg)

    # 9. Engine Sound Pitch
    if engine_sound:
        try:
            engine_sound.pitch = 0.72 + (abs(speed) / 42.0) * 1.3
        except Exception:
            pass

    # 10. Tire Dust & Skid Marks
    particle_timer += dt
    if abs(speed) > 6.0 and is_grounded and particle_timer > 0.045:
        particle_timer = 0.0
        p_col = rgba(120, 225, 255) if in_water else (rgba(210, 210, 215) if drifting else rgba(175, 150, 115))
        for side in [-1.1, 1.1]:
            p_pos = car.position - car.forward * 2.2 + car.right * side + Vec3(0, 0.25, 0)
            p = Entity(model='sphere', scale=random.uniform(0.3, 0.65), position=p_pos, color=p_col, unlit=True)
            particles.append([p, 0.42])
            if drifting:
                skid = Entity(
                    model='quad', scale=(0.35, 0.95, 1),
                    position=(p_pos.x, avg_wheel_y + 0.08, p_pos.z),
                    rotation=(90 - slope_deg, car.rotation_y, -roll_deg),
                    color=rgba(15, 15, 18, 175), double_sided=True, unlit=True
                )
                skid_marks.append([skid, 5.0])

    for item in particles[:]:
        item[1] -= dt
        item[0].y += dt * 1.8
        item[0].scale *= (1.0 + dt * 1.8)
        if item[1] <= 0:
            destroy(item[0])
            particles.remove(item)

    for sk in skid_marks[:]:
        sk[1] -= dt
        if sk[1] <= 0:
            destroy(sk[0])
            skid_marks.remove(sk)

    # 11. Checkpoint & GPS Compass
    cp_orb.rotation_y += 120 * dt
    gps_arrow.position = car.position + Vec3(0, 4.4, 0)
    gps_arrow.look_at(Vec3(checkpoint_node.x, gps_arrow.y, checkpoint_node.z))

    if distance_xz(car.position, checkpoint_node.position) < 8.5:
        score += 1
        spawn_dust(checkpoint_node.position, count=14, col=rgba(255, 230, 0))
        while True:
            nx, nz = random.uniform(-210, 210), random.uniform(-210, 210)
            ny = get_ground_height(nx, nz)
            if math.hypot(nx - car.x, nz - car.z) > 65 and -4.0 < ny < 16.0:
                checkpoint_node.position = (nx, ny, nz)
                checkpoint_node.rotation_y = random.uniform(0, 360)
                break

    # 12. Horizon-Stabilized Camera (Lets you clearly see the car tilt up and down on hills!)
    if cam_mode == 0:
        cam_dist = 13.5 if boosting else 11.5
        desired_pos = car.position - car.forward * cam_dist + Vec3(0, 4.5, 0)
        min_cam_y = get_ground_height(desired_pos.x, desired_pos.z) + 2.2
        desired_pos.y = max(desired_pos.y, min_cam_y)
        camera.position = lerp(camera.position, desired_pos, dt * 8)
        camera.look_at(car.position + car.forward * 2.5 + Vec3(0, 1.3, 0))
    elif cam_mode == 1:
        desired_pos = car.position - car.forward * 18.0 + Vec3(0, 8.0, 0)
        desired_pos.y = max(desired_pos.y, get_ground_height(desired_pos.x, desired_pos.z) + 2.5)
        camera.position = lerp(camera.position, desired_pos, dt * 6)
        camera.look_at(car.position + car.forward * 2.0 + Vec3(0, 1.5, 0))
    else:
        # First-person hood cam (tilts with the car's hood on hills!)
        camera.position = car.position + Vec3(0, 2.3, 0) + slope_pivot.forward * 0.6
        camera.look_at(car.position + Vec3(0, 1.8, 0) + slope_pivot.forward * 25.0)

    kmh = int(abs(speed) * 3.8)
    gear = min(6, max(1, int(kmh / 32) + 1))
    ui_speed.text = f'{kmh} KM/H  [GEAR {gear}]'
    ui_score.text = f'CHECKPOINTS: {score} | DRIFT PTS: {drift_score}'


def input(key):
    global cam_mode, speed, vy, is_grounded, current_shader_idx, time_of_day
    active_wrapper = loaded_car_entities[current_car_idx]

    if key == 'escape':
        application.quit()
    elif key == 'j':
        if is_grounded:
            vy = car_configs[current_car_idx]["jump"]
            is_grounded = False
            spawn_dust(car.position, count=10, col=rgba(255, 255, 255))
    elif key in ['1', '2', '3', '4']:
        switch_car(int(key) - 1)
    elif key == 'l':
        current_shader_idx = (current_shader_idx + 1) % len(shaders_list)
        s_name, s_obj = shaders_list[current_shader_idx]
        for wrapper in loaded_car_entities:
            for orient_child in wrapper.children:
                for model_child in orient_child.children:
                    model_child.shader = s_obj
        ui_car.text = f'{current_car_idx + 1}: {car_configs[current_car_idx]["name"]} [{s_name}]'
    elif key == 'f':
        # Rotate the inner orient_node 90 degrees around (0,0,0) so the car never shifts off-center!
        if active_wrapper.children:
            active_wrapper.children[0].rotation_y += 90
    elif key == ']':
        active_wrapper.y += 0.15
    elif key == '[':
        active_wrapper.y -= 0.15
    elif key in ('+', '='):
        active_wrapper.scale *= 1.12
    elif key in ('-', '_'):
        active_wrapper.scale *= 0.88
    elif key == 'u':
        underglow.enabled = not underglow.enabled
    elif key == 't':
        time_of_day = (time_of_day + 1) % 3
        if time_of_day == 0:
            sky_dome.color = rgba(255, 255, 255)
            ambient_light.color = rgba(165, 175, 190)
        elif time_of_day == 1:
            sky_dome.color = rgba(245, 155, 110)
            ambient_light.color = rgba(155, 115, 95)
        else:
            sky_dome.color = rgba(25, 35, 65)
            ambient_light.color = rgba(75, 85, 115)
    elif key == 'c':
        cam_mode = (cam_mode + 1) % 3
    elif key == 'r':
        car.position = (0, get_ground_height(0, 0) + 1.0, 0)
        car.rotation = (0, 0, 0)
        slope_pivot.rotation = (0, 0, 0)
        speed, vy = 0.0, 0.0


app.run()