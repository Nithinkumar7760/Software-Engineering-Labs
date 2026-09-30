import math
import random
import pygame
from game.text_box import TextBox
 
class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.words = ["PYTHON", "PYGAME", "PLANET", "ROCKET", "GALAXY", "STREAM", "PUZZLE", "ALGORITHM"]
        self.secret_word = ""
        self.scrambled_word = ""

        self.score = 0
        self.feedback_msg = "Unscramble the letters above!"
        self.feedback_color = (210, 215, 225)

        self.input_box = TextBox(width // 2 - 130, 210, 160, 46)
        self.submit_btn = pygame.Rect(width // 2 + 45, 210, 95, 46)
        self.hint_btn = pygame.Rect(width // 2 + 150, 210, 95, 46)
        self.hint_penalty = 1
        self.hints_used = 0

        self.round_seconds = 20
        self.round_start_ms = 0
        self.time_left = self.round_seconds

        self.tile_size = 44
        self.tile_gap = 8
        self.row_y = {"pool": 98, "rack": 152}
        self.tiles = {"pool": [], "rack": []}
        self.drag = None

        self.font_title = pygame.font.SysFont(None, 40)
        self.font_word = pygame.font.SysFont(None, 52)
        self.font_msg = pygame.font.SysFont(None, 26)
        self.font_btn = pygame.font.SysFont(None, 24)
        self.font_tile = pygame.font.SysFont(None, 36)

        self.next_round()

    def scramble_string(self, word):
        letters = list(word)
        while True:
            random.shuffle(letters)
            shuffled = "".join(letters)
            if shuffled != word or len(word) <= 1:
                return shuffled

    def next_round(self):
        self.secret_word = random.choice(self.words)
        self.scrambled_word = self.scramble_string(self.secret_word)
        self.hints_used = 0
        self.round_start_ms = pygame.time.get_ticks()
        self.time_left = self.round_seconds
        self.reset_tiles()
        self.input_box.clear()

    def submit_guess(self):
        guess = self.input_box.text.strip().upper()
        if not guess:
            self.feedback_msg = "Type a word before submitting!"
            self.feedback_color = (240, 170, 50)
            return

        is_correct = (guess == self.secret_word)

        if is_correct:
            self.score += 1
            self.feedback_msg = f"CORRECT! '{self.secret_word}' is right."
            self.feedback_color = (80, 230, 110)
            self.next_round()
        else:
            self.feedback_msg = "WRONG GUESS! Try again."
            self.feedback_color = (240, 80, 80)
            self.input_box.clear()
            self.reset_tiles()

    def use_hint(self):
        if self.hints_used >= len(self.secret_word):
            self.feedback_msg = "The whole word is already revealed!"
            self.feedback_color = (240, 170, 50)
            return

        self.hints_used += 1
        self.score = max(0, self.score - self.hint_penalty)
        self.feedback_msg = f"Hint used! -{self.hint_penalty} point"
        self.feedback_color = (240, 170, 50)

    def time_up(self):
        self.feedback_msg = f"TIME'S UP! The word was '{self.secret_word}'."
        self.feedback_color = (240, 80, 80)
        self.next_round()

    def reset_tiles(self):
        count = len(self.scrambled_word)
        self.tiles = {"pool": list(self.scrambled_word), "rack": [None] * count}
        self.drag = None

    def slot_rect(self, row, index):
        count = len(self.scrambled_word)
        total = count * self.tile_size + (count - 1) * self.tile_gap
        x = self.width // 2 - total // 2 + index * (self.tile_size + self.tile_gap)
        return pygame.Rect(x, self.row_y[row], self.tile_size, self.tile_size)

    def slot_at(self, pos, pad=0):
        for row in ("pool", "rack"):
            for i in range(len(self.tiles[row])):
                if self.slot_rect(row, i).inflate(pad, pad).collidepoint(pos):
                    return row, i
        return None

    def sync_input(self):
        # The rack's letters, left to right, become the text that SUBMIT checks.
        self.input_box.text = "".join(letter for letter in self.tiles["rack"] if letter)

    def handle_tile_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.drag:
            hit = self.slot_at(event.pos)
            if hit and self.tiles[hit[0]][hit[1]]:
                row, i = hit
                rect = self.slot_rect(row, i)
                self.drag = {
                    "letter": self.tiles[row][i],
                    "origin": hit,
                    "offset": (event.pos[0] - rect.x, event.pos[1] - rect.y),
                    "pos": event.pos,
                }
                self.tiles[row][i] = None
                self.sync_input()
        elif event.type == pygame.MOUSEMOTION and self.drag:
            self.drag["pos"] = event.pos
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag:
            row, i = self.drag["origin"]
            target_row, target_i = self.slot_at(event.pos, self.tile_gap) or (row, i)
            # Whatever tile sat in the target slot swaps into the slot we picked up from.
            self.tiles[row][i] = self.tiles[target_row][target_i]
            self.tiles[target_row][target_i] = self.drag["letter"]
            self.drag = None
            self.sync_input()

    def handle_event(self, event):
        self.input_box.handle_event(event)
        self.handle_tile_event(event)

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self.submit_guess()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.submit_btn.collidepoint(event.pos):
                self.submit_guess()
            elif self.hint_btn.collidepoint(event.pos):
                self.use_hint()

    def update(self):
        elapsed = (pygame.time.get_ticks() - self.round_start_ms) / 1000
        self.time_left = max(0, self.round_seconds - elapsed)
        if self.time_left <= 0:
            self.time_up()

    def render(self, screen):
        screen.fill((26, 30, 38))

        title_surf = self.font_title.render("Word Scramble Arena", True, (245, 245, 245))
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 25))

        score_surf = self.font_msg.render(f"Score: {self.score}", True, (255, 220, 80))
        screen.blit(score_surf, (self.width // 2 - score_surf.get_width() // 2, 70))

        self.render_tiles(screen)

        self.input_box.render(screen)

        pygame.draw.rect(screen, (50, 150, 85), self.submit_btn, border_radius=6)
        pygame.draw.rect(screen, (220, 220, 220), self.submit_btn, width=2, border_radius=6)
        btn_text = self.font_btn.render("SUBMIT", True, (255, 255, 255))
        screen.blit(btn_text, (self.submit_btn.centerx - btn_text.get_width() // 2, self.submit_btn.centery - btn_text.get_height() // 2))

        pygame.draw.rect(screen, (200, 140, 40), self.hint_btn, border_radius=6)
        pygame.draw.rect(screen, (220, 220, 220), self.hint_btn, width=2, border_radius=6)
        hint_text = self.font_btn.render("HINT", True, (255, 255, 255))
        screen.blit(hint_text, (self.hint_btn.centerx - hint_text.get_width() // 2, self.hint_btn.centery - hint_text.get_height() // 2))

        feedback_surf = self.font_msg.render(self.feedback_msg, True, self.feedback_color)
        screen.blit(feedback_surf, (self.width // 2 - feedback_surf.get_width() // 2, 285))

        if self.hints_used > 0:
            pattern = "  ".join(
                letter if i < self.hints_used else "_"
                for i, letter in enumerate(self.secret_word)
            )
            hint_surf = self.font_word.render(pattern, True, (255, 200, 90))
            screen.blit(hint_surf, (self.width // 2 - hint_surf.get_width() // 2, 335))

        seconds = math.ceil(self.time_left)
        if self.time_left > self.round_seconds * 0.5:
            bar_color = (80, 230, 110)
        elif self.time_left > self.round_seconds * 0.25:
            bar_color = (240, 170, 50)
        else:
            bar_color = (240, 80, 80)

        timer_surf = self.font_msg.render(f"Time left: {seconds}s", True, bar_color)
        screen.blit(timer_surf, (self.width // 2 - timer_surf.get_width() // 2, 405))

        bar_bg = pygame.Rect(self.width // 2 - 150, 435, 300, 18)
        bar_fill = pygame.Rect(bar_bg.x, bar_bg.y, int(bar_bg.width * self.time_left / self.round_seconds), bar_bg.height)
        pygame.draw.rect(screen, (55, 60, 72), bar_bg, border_radius=6)
        if bar_fill.width > 0:
            pygame.draw.rect(screen, bar_color, bar_fill, border_radius=6)
        pygame.draw.rect(screen, (220, 220, 220), bar_bg, width=2, border_radius=6)

        self.render_drag(screen)

    def draw_tile(self, screen, rect, letter, lifted=False):
        fill = (70, 130, 200) if lifted else (45, 95, 150)
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, (100, 200, 255), rect, width=2, border_radius=8)
        letter_surf = self.font_tile.render(letter, True, (255, 255, 255))
        screen.blit(letter_surf, (rect.centerx - letter_surf.get_width() // 2, rect.centery - letter_surf.get_height() // 2))

    def render_tiles(self, screen):
        for row in ("pool", "rack"):
            for i, letter in enumerate(self.tiles[row]):
                rect = self.slot_rect(row, i)
                if letter:
                    self.draw_tile(screen, rect, letter)
                else:
                    pygame.draw.rect(screen, (38, 43, 54), rect, border_radius=8)
                    pygame.draw.rect(screen, (70, 76, 90), rect, width=2, border_radius=8)

    def render_drag(self, screen):
        if self.drag:
            x = self.drag["pos"][0] - self.drag["offset"][0]
            y = self.drag["pos"][1] - self.drag["offset"][1]
            self.draw_tile(screen, pygame.Rect(x, y, self.tile_size, self.tile_size), self.drag["letter"], lifted=True)
