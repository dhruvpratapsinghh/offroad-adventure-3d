# 🏎️ Offroad Horizon 3D - Open World Game

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Ursina Engine](https://img.shields.io/badge/Engine-Ursina-orange.svg)](https://www.ursinaengine.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An immersive **Open-World 3D Offroad Driving & Stunt Game** built completely from scratch in Python using the Ursina 3D Engine. Featuring real 4-wheel terrain slope alignment, dynamic day/sunset/night cycles, stunt ramps, nitro boosts, and live in-game car switching!

---

## 🎮 Game Controls

### 🚗 Driving & Navigation
| Key | Action | Description |
| :--- | :--- | :--- |
| **`W`** | **Accelerate** | Drive forward / climb hills |
| **`S`** | **Reverse / Brake** | Reverse gear / apply dynamic braking |
| **`A`** | **Steer Left** | Turn wheels left |
| **`D`** | **Steer Right** | Turn wheels right |
| **`Spacebar`** | **Handbrake Drift** | Initiate tire skids & accumulate drift points |

---

### 🚀 Stunts & Abilities
| Key | Action | Description |
| :--- | :--- | :--- |
| **`J`** | **Jump Jet** | Launch car into the air with vertical thrust |
| **`Left Shift`** | **Nitro Boost** | Engage twin afterburners, increase top speed & widen FOV |
| **`W` / `S` *(in Air)*** | **Air Pitch Control** | Tilt vehicle nose-up or nose-down during jumps |

---

### 🚘 Vehicle Garage & Visual Customization
| Key | Action | Description |
| :--- | :--- | :--- |
| **`1`** | **Mahindra Thar 4x4** | All-terrain crawler with balanced traction |
| **`2`** | **Tesla Cybertruck** | Heavy electric utility with rapid acceleration |
| **`3`** | **BMW M-Competition** | High-speed track & highway performance |
| **`4`** | **Bugatti Chiron** | Extreme hypercar speed |
| **`L`** | **Cycle Shaders** | Switch between *Default glTF*, *Lit*, *Matcap*, and *Unlit* |
| **`U`** | **Neon Underglow** | Toggle custom underglow lighting under the chassis |
| **`F`** | **Rotate Car 90°** | Adjust orientation if imported `.glb` faces sideways |
| **`[` / `]`** | **Height Offset** | Raise or lower the car body relative to the wheels |
| **`+` / `-`** | **Scale Car** | Enlarge or shrink the 3D car model |

---

### 🎥 Camera & Environment Controls
| Key | Action | Description |
| :--- | :--- | :--- |
| **`C`** | **Cycle Camera** | Toggle Close Chase, Far Action, and First-Person Hood Cam |
| **`T`** | **Time of Day** | Cycle through Sunny Day, Golden Sunset, and Midnight Neon |
| **`R`** | **Reset Car** | Respawn safely at the highway starting pad |
| **`ESC`** | **Exit Game** | Close application |

---

## ✨ Key Features
* **True 3D Procedural Open-World:** Smooth rolling hills, winding mountain highways, deep alpine lakes, and custom stunt ramps.
* **4-Wheel Slope Tilt Physics:** Car dynamically pitches nose-up on uphills and nose-down on downhills with real-time roll calculations.
* **Multi-Vehicle Garage:** Switch on-the-fly between 4 detailed 3D vehicles.
* **Dynamic Visual Effects:** Twin nitro flames, tire skid marks, dirt/mud particle bursts, soft ground shadows, and neon underglow.
* **Horizon-Stabilized Camera:** Prevents camera clipping below hills while accurately displaying vehicle pitch and roll angles.

---

## 🛠️ Project Structure
```text
car game/
│
├── main.py              # Main game engine script
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignore rules
├── README.md            # Project documentation & controls
├── LICENSE              # MIT License
│
├── models/              # Place your .glb car models here
│   ├── thar.glb
│   ├── cybertruck.glb
│   ├── bmw.glb
│   └── bugatti.glb
│
├── textures/            # Sky and ground textures
│   └── flamingo_pan_4k.exr (or sky.jpg)
│
└── sounds/              # Audio loops
    └── car_sound.wav