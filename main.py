import pygame
import sys
import math
import random

# Initialize Framework
pygame.init()

# Display Config (16:9 Cinematic Ratio)
LARGURA_TELA, ALTURA_TELA = 1152, 648
LARGURA_MUNDO, ALTURA_MUNDO = 3000, 2000
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Echoes of Deep Water - Alpha Build")
relogio = pygame.time.Clock()

# --- SPRITE ENGINE & COLOR PALETTES ---
ABYSS_DEEP = (4, 10, 20)
WALL_COLOR = (18, 30, 49)
GLOW_GREEN = (0, 255, 140)
GLOW_BLUE = (0, 190, 255)
GLOW_RED = (255, 60, 60)
LIGHT_YELLOW = (255, 250, 210)

def gerar_sprite_jogador():
    """Generates an animated frame dictionary for the deep-sea diver."""
    frames = {'idle': [], 'swim': []}
    for i in range(4):
        # Frame Base Setup (32x32 Surface)
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        # Suit Body (Heavy Brass/Steel Diver Suit)
        pygame.draw.circle(surf, (40, 80, 110), (16, 16), 8)
        # Oxygen Tank Pack
        pygame.draw.rect(surf, (70, 110, 140), (4, 10, 6, 12), border_radius=2)
        # Glowing Visor (Changes shape slightly based on frame to simulate breathing)
        pulse = int(math.sin(i * 0.5) * 2)
        pygame.draw.circle(surf, GLOW_BLUE, (22, 14), 3 + (pulse // 2))
        # Flippers / Legs (Idle vs Swim Animation state)
        if i % 2 == 0:
            pygame.draw.line(surf, (30, 60, 80), (10, 22), (6, 26), 3)
            pygame.draw.line(surf, (30, 60, 80), (14, 22), (10, 28), 3)
        else:
            pygame.draw.line(surf, (30, 60, 80), (10, 22), (4, 24), 3)
            pygame.draw.line(surf, (30, 60, 80), (14, 22), (8, 25), 3)
        frames['swim'].append(surf)
        
        # Idle Frame variation
        surf_idle = surf.copy()
        frames['idle'].append(surf_idle)
    return frames

def gerar_sprite_monstro():
    """Generates a procedural sprite sheet for the bioluminescent predator."""
    frames = []
    for i in range(6):
        surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        # Central predatory eye/core
        pygame.draw.circle(surf, (220, 40, 40), (24, 24), 10)
        pygame.draw.circle(surf, (255, 140, 0), (24, 24), 5)
        # Organic sweeping tentacles shifting across animation index
        offset = math.sin(i * 1.0) * 6
        pygame.draw.line(surf, (150, 30, 30), (14, 24), (2, 20 + int(offset)), 4)
        pygame.draw.line(surf, (150, 30, 30), (14, 18), (4, 10 + int(offset)), 3)
        pygame.draw.line(surf, (150, 30, 30), (14, 30), (4, 34 + int(offset)), 3)
        frames.append(surf)
    return frames

# Cache Graphics to RAM
SPRITES_PLAYER = gerar_sprite_jogador()
SPRITES_MONSTER = gerar_sprite_monstro()

# --- GAME SYSTEM CLASSES ---

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.color = color
        self.vx = random.uniform(-1, 1)
        self.vy = random.uniform(-1, 1)
        self.life = 255
        self.size = random.randint(2, 4)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 4

    def draw(self, surf, cam_x, cam_y):
        if self.life > 0:
            p_surf = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, self.color + (self.life,), (self.size, self.size), self.size)
            surf.blit(p_surf, (self.x - cam_x - self.size, self.y - cam_y - self.size))

class Player:
    def __init__(self):
        self.x, self.y = LARGURA_MUNDO // 2, ALTURA_MUNDO // 2
        self.vx, self.vy = 0, 0
        self.angle = 0
        self.speed = 3.5
        self.oxygen = 100.0
        self.anim_frame = 0
        self.is_moving = False

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.vx, self.vy = 0, 0
        self.is_moving = False
        
        if keys[pygame.K_w] or keys[pygame.K_UP]: self.vy = -1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: self.vy = 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: self.vx = -1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: self.vx = 1
        
        if self.vx != 0 or self.vy != 0:
            self.is_moving = True
            # Compute rotational swimming angle based on movement vector
            self.angle = math.degrees(math.atan2(-self.vy, self.vx)) - 90

    def update(self, obstacles, particles):
        self.handle_input()
        
        # Normalize diagonals
        if self.vx != 0 and self.vy != 0:
            self.vx *= 0.7071
            self.vy *= 0.7071

        # Axis-separated collision validation
        old_x, old_y = self.x, self.y
        self.x += self.vx * self.speed
        p_rect = pygame.Rect(self.x - 12, self.y - 12, 24, 24)
        for obs in obstacles:
            if p_rect.colliderect(obs): self.x = old_x

        self.y += self.vy * self.speed
        p_rect = pygame.Rect(self.x - 12, self.y - 12, 24, 24)
        for obs in obstacles:
            if p_rect.colliderect(obs): self.y = old_y

        # Oxygen Mechanics
        if self.is_moving:
            self.oxygen -= 0.04
            if random.random() < 0.15: # Generate micro air bubbles trail
                particles.append(Particle(self.x, self.y, (200, 240, 255)))
        else:
            self.oxygen -= 0.02

        # Animation Ticking
        self.anim_frame = (self.anim_frame + 0.15) % 4

    def draw(self, surf, cam_x, cam_y):
        state = 'swim' if self.is_moving else 'idle'
        frame_surface = SPRITES_PLAYER[state][int(self.anim_frame)]
        rotated_surf = pygame.transform.rotate(frame_surface, self.angle)
        new_rect = rotated_surf.get_rect(center=(self.x - cam_x, self.y - cam_y))
        surf.blit(rotated_surf, new_rect.topleft)

class SonarPulse:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.radius = 0
        self.max_radius = 450
        self.active = True

    def update(self):
        self.radius += 6
        if self.radius > self.max_radius:
            self.active = False

    def draw(self, surf, cam_x, cam_y):
        if self.active:
            alpha = int(255 * (1 - self.radius / self.max_radius))
            pulse_surf = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
            pygame.draw.circle(pulse_surf, GLOW_GREEN + (alpha,), (int(self.x - cam_x), int(self.y - cam_y)), int(self.radius), 3)
            surf.blit(pulse_surf, (0,0))

class AbyssMonster:
    def __init__(self, obstacles):
        self.x, self.y = self.get_valid_pos(obstacles)
        self.state = "PATRULHA"
        self.anim_frame = random.randint(0, 5)
        self.speed = 1.2
        self.target_angle = 0
        self.angle = 0
        self.aggro_timer = 0

    def get_valid_pos(self, obstacles):
        while True:
            x = random.randint(200, LARGURA_MUNDO - 200)
            y = random.randint(200, ALTURA_MUNDO - 200)
            m_rect = pygame.Rect(x-20, y-20, 40, 40)
            if not any(m_rect.colliderect(obs) for obs in obstacles):
                return x, y

    def update(self, player, sonar, obstacles):
        self.anim_frame = (self.anim_frame + 0.1) % 6
        dist_player = math.hypot(player.x - self.x, player.y - self.y)

        # GDD AI System: Aggro triggered by structural Sonar pings
        if sonar and sonar.active:
            dist_sonar_wave = math.hypot(sonar.x - self.x, sonar.y - self.y)
            if abs(dist_sonar_wave - sonar.radius) < 40:
                self.state = "PERSEGUICAO"
                self.aggro_timer = 300  # Persistent alert phase frames

        if self.state == "PERSEGUICAO":
            self.target_angle = math.atan2(player.y - self.y, player.x - self.x)
            self.x += math.cos(self.target_angle) * (self.speed * 2.2)
            self.y += math.sin(self.target_angle) * (self.speed * 2.2)
            self.aggro_timer -= 1
            if self.aggro_timer <= 0 and dist_player > 300:
                self.state = "PATRULHA"
        else:
            # Casual drift
            if random.random() < 0.02:
                self.target_angle += random.uniform(-1, 1)
            self.x += math.cos(self.target_angle) * self.speed
            self.y += math.sin(self.target_angle) * self.speed

        self.angle = math.degrees(-self.target_angle) - 90

    def draw(self, surf, cam_x, cam_y, sonar):
        # Environmental Visibility Check: Only visible inside active sonar ripple or when hunting
        render_allowed = False
        if self.state == "PERSEGUICAO":
            render_allowed = True
        elif sonar and sonar.active:
            d = math.hypot(self.x - sonar.x, self.y - sonar.y)
            if d < sonar.radius:
                render_allowed = True

        if render_allowed:
            frame_surf = SPRITES_MONSTER[int(self.anim_frame)]
            rotated_surf = pygame.transform.rotate(frame_surf, self.angle)
            new_rect = rotated_surf.get_rect(center=(self.x - cam_x, self.y - cam_y))
            surf.blit(rotated_surf, new_rect.topleft)

class O2Pod:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.rect = pygame.Rect(x-16, y-16, 32, 32)
        self.active = True
        self.pulse = 0

    def draw(self, surf, cam_x, cam_y):
        if self.active:
            self.pulse = (self.pulse + 0.05) % (math.pi * 2)
            r_mod = int(math.sin(self.pulse) * 4)
            # Draw structural organic plant base
            pygame.draw.circle(surf, (20, 90, 60), (self.x - cam_x, self.y - cam_y), 14)
            # Glowing Core Bio-pod
            pygame.draw.circle(surf, GLOW_GREEN, (self.x - cam_x, self.y - cam_y), 8 + r_mod)
            pygame.draw.circle(surf, (255, 255, 255), (self.x - cam_x, self.y - cam_y), 3)

# --- MAP / INFRASTRUCTURE SETUP ---
def gerar_mapa_procedural():
    obstacles = []
    # Outer Map Boundaries
    obstacles.append(pygame.Rect(0, 0, LARGURA_MUNDO, 40))
    obstacles.append(pygame.Rect(0, ALTURA_MUNDO-40, LARGURA_MUNDO, 40))
    obstacles.append(pygame.Rect(0, 0, 40, ALTURA_MUNDO))

    obstacles.append(pygame.Rect(LARGURA_MUNDO - 40, 0, 40, ALTURA_MUNDO))
        
        # Internal Cave Columns/Ruins Blockers
    for _ in range(35):
            w = random.randint(120, 350)
            h = random.randint(120, 350)
            x = random.randint(200, LARGURA_MUNDO - 500)
            y = random.randint(200, ALTURA_MUNDO - 500)
            
            # Avoid blocking spawning grounds
            if not pygame.Rect(x, y, w, h).colliderect(pygame.Rect(LARGURA_MUNDO // 2 - 200, ALTURA_MUNDO // 2 - 200, 400, 400)):
                obstacles.append(pygame.Rect(x, y, w, h))
                
    return obstacles

# --- RUNTIME CORE ---
def executar_jogo():
    player = Player()
    obstacles = gerar_mapa_procedural()
    monsters = [AbyssMonster(obstacles) for _ in range(12)]
    
    # Generate O2 Nodes near valid floor structures
    pods = []
    for _ in range(10):
        while True:
            rx = random.randint(100, LARGURA_MUNDO - 100)
            ry = random.randint(100, ALTURA_MUNDO - 100)
            t_rect = pygame.Rect(rx - 16, ry - 16, 32, 32)
            if not any(t_rect.colliderect(o) for o in obstacles):
                pods.append(O2Pod(rx, ry))
                break
                
    sonares = []
    particles = []
    cam_shake = 0
    font_ui = pygame.font.SysFont("Consolas", 16, bold=True)
    font_huge = pygame.font.SysFont("Consolas", 42, bold=True)
    
    rodando = True
    while rodando:
        # Game State Mechanics Loop
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                sonares.append(SonarPulse(player.x, player.y))
                cam_shake = 16  # Induce camera shockwave vibration feedback
                
        # Systems Updates
        player.update(obstacles, particles)
        active_sonar = sonares[-1] if sonares else None
        
        for s in sonares[:]:
            s.update()
            if not s.active: 
                sonares.remove(s)
                
        for m in monsters:
            m.update(player, active_sonar, obstacles)
            # Attack vector evaluation
            if math.hypot(player.x - m.x, player.y - m.y) < 24:
                player.oxygen -= 0.6  # Threat contacts deplete current suit oxygen
                particles.append(Particle(player.x, player.y, GLOW_RED))
                
        for p in pods:
            if p.active and player.oxygen < 100:
                if math.hypot(player.x - p.x, player.y - p.y) < 32:
                    player.oxygen = min(100.0, player.oxygen + 35.0)
                    p.active = False  # Deactivated upon consumption
                    
        for pt in particles[:]:
            pt.update()
            if pt.life <= 0: 
                particles.remove(pt)
                
        # Smooth Tracking Camera Calculations
        cam_x = player.x - LARGURA_TELA // 2
        cam_y = player.y - ALTURA_TELA // 2
        cam_x = max(0, min(cam_x, LARGURA_MUNDO - LARGURA_TELA))
        cam_y = max(0, min(cam_y, ALTURA_MUNDO - ALTURA_TELA))
        
        # Apply procedural screenshake matrix
        if cam_shake > 0:
            cam_x += random.randint(-cam_shake, cam_shake)
            cam_y += random.randint(-cam_shake, cam_shake)
            cam_shake -= 1
            
        # --- GRAPHICS RENDERING PIPELINE ---
        tela.fill(ABYSS_DEEP)
        
        # Ambient Grid Backdrop
        grid_space = 64
        start_x = int(cam_x // grid_space) * grid_space
        start_y = int(cam_y // grid_space) * grid_space
        
        for gx in range(start_x, start_x + LARGURA_TELA + grid_space, grid_space):
            pygame.draw.line(tela, (8, 22, 40), (gx - cam_x, 0), (gx - cam_x, ALTURA_TELA))
        for gy in range(start_y, start_y + ALTURA_TELA + grid_space, grid_space):
            pygame.draw.line(tela, (8, 22, 40), (0, gy - cam_y), (LARGURA_TELA, gy - cam_y))
            
        # Render Game Entities
        for obs in obstacles:
            if obs.colliderect(pygame.Rect(cam_x, cam_y, LARGURA_TELA, ALTURA_TELA)):
                pygame.draw.rect(tela, WALL_COLOR, (obs.x - cam_x, obs.y - cam_y, obs.width, obs.height))
                pygame.draw.rect(tela, (30, 52, 82), (obs.x - cam_x, obs.y - cam_y, obs.width, obs.height), 2)
                
        for p in pods:
            p.draw(tela, cam_x, cam_y)
            
        for m in monsters:
            m.draw(tela, cam_x, cam_y, active_sonar)
            
        for pt in particles:
            pt.draw(tela, cam_x, cam_y)
            
        player.draw(tela, cam_x, cam_y)
        
        for s in sonares:
            s.draw(tela, cam_x, cam_y)
            
        # --- ADVANCED LIGHTING OVERLAY SYSTEM ---
        # Blits a dark mask over the screen, punctured by the diver's localized flashlight cone
        light_mask = pygame.Surface((LARGURA_TELA, ALTURA_TELA), pygame.SRCALPHA)
        light_mask.fill((2, 5, 12, 210))  # Depth darkness intensity
        
        # Punch light transparency ring at player screen vector
        p_screen_x, p_screen_y = player.x - cam_x, player.y - cam_y
        for r in range(160, 0, -20):  # Gradual fog fallout attenuation
            alpha = int(210 * (r / 160))
            pygame.draw.circle(light_mask, (0, 0, 0, 210 - alpha), (int(p_screen_x), int(p_screen_y)), r)
        tela.blit(light_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # --- HUD HEADS UP DISPLAY UI ---
        # Oxygen Status Core Panel
        o2_w = int(player.oxygen * 2.2)
        o2_color = GLOW_GREEN if player.oxygen > 35 else GLOW_RED
        pygame.draw.rect(tela, (20, 25, 35), (30, 30, 220, 24), border_radius=4)
        if player.oxygen > 0:
            pygame.draw.rect(tela, o2_color, (34, 34, o2_w - 8, 16), border_radius=2)
            
        txt_o2 = font_ui.render(f"EQUALIZADOR-O2: {max(0.0, int(player.oxygen))}%", True, (255, 255, 255))
        tela.blit(txt_o2, (34, 62))
        
        txt_controls = font_ui.render("[W,A,S,D] Mover Traje | [ESPAÇO] Emitir Pulso de Sonar", True, (100, 130, 160))
        tela.blit(txt_controls, (30, ALTURA_TELA - 40))
        
        # Failure State Context
        if player.oxygen <= 0:
            tela.fill((6, 2, 2))
            txt_fail = font_huge.render("CONTATO DE SINAL PERDIDO", True, GLOW_RED)
            txt_sub = font_ui.render("O oxigênio acabou. Kai desapareceu nos sistemas de cavernas abissais.", True, (180, 180, 180))
            tela.blit(txt_fail, (LARGURA_TELA // 2 - txt_fail.get_width() // 2, ALTURA_TELA // 2 - 40))
            tela.blit(txt_sub, (LARGURA_TELA // 2 - txt_sub.get_width() // 2, ALTURA_TELA // 2 + 20))
            pygame.display.flip()
            pygame.time.wait(4500)
            rodando = False
            
        pygame.display.flip()
        relogio.tick(60)
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    executar_jogo()
