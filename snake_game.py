"""
Snake Game with MySQL Leaderboard - Windows Version
Complete working game with wall collision, user registration, and score tracking
"""

import pygame
import random
import mysql.connector
from mysql.connector import Error
import datetime
from config import DB_CONFIG

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Connect to MySQL database on Windows"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                print("✅ Connected to MySQL database")
        except Error as e:
            print(f"❌ Database connection failed: {e}")
            print("Tip: Make sure MySQL is running and check config.py settings")
    
    def register_user(self, username):
        """Register a new user or get existing user ID"""
        try:
            # Ensure connection exists
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return None
            
            cursor = self.connection.cursor()
            
            # Try to insert new user
            insert_query = "INSERT IGNORE INTO users (username) VALUES (%s)"
            cursor.execute(insert_query, (username,))
            self.connection.commit()
            
            # Get user ID
            select_query = "SELECT id FROM users WHERE username = %s"
            cursor.execute(select_query, (username,))
            result = cursor.fetchone()
            
            cursor.close()
            return result[0] if result else None
            
        except Error as e:
            print(f"❌ Error registering user: {e}")
            return None
    
    def save_score(self, user_id, score, level):
        """Save score to database"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return False
            
            cursor = self.connection.cursor()
            query = "INSERT INTO scores (user_id, score, level) VALUES (%s, %s, %s)"
            cursor.execute(query, (user_id, score, level))
            self.connection.commit()
            cursor.close()
            print("✅ Score saved to database!")
            return True
        except Error as e:
            print(f"❌ Error saving score: {e}")
            return False
    
    def get_leaderboard(self, limit=10):
        """Get top scores with usernames"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                if not self.connection:
                    return []
            
            cursor = self.connection.cursor()
            query = """
                SELECT u.username, s.score, s.level, s.game_date 
                FROM scores s 
                JOIN users u ON s.user_id = u.id 
                ORDER BY s.score DESC 
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except Error as e:
            print(f"❌ Error fetching leaderboard: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

class SnakeGame:
    def __init__(self):
        pygame.init()
        
        # Game constants optimized for Windows display
        self.WIDTH, self.HEIGHT = 800, 600
        self.GRID_SIZE = 20
        self.GRID_WIDTH = self.WIDTH // self.GRID_SIZE
        self.GRID_HEIGHT = self.HEIGHT // self.GRID_SIZE
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (50, 205, 50)  # Lime green
        self.RED = (220, 20, 60)    # Crimson red
        self.BLUE = (30, 144, 255)  # Dodger blue
        self.GRAY = (60, 60, 60)
        self.WALL_COLOR = (178, 34, 34)  # Firebrick red for walls
        
        # Game variables
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Snake Game - Windows MySQL Edition")
        
        # Load fonts for Windows
        try:
            self.font = pygame.font.SysFont('Segoe UI', 24)
            self.title_font = pygame.font.SysFont('Segoe UI', 48, bold=True)
        except:
            self.font = pygame.font.SysFont('Arial', 24)
            self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        
        # Database
        self.db = DatabaseManager()
        self.username = ""
        self.user_id = None
        self.score = 0
        self.level = 1
        self.speed = 10
        
        # Game states
        self.game_state = "LOGIN"  # LOGIN, PLAYING, GAME_OVER, LEADERBOARD
        self.input_text = ""
        
        self.reset_game()
    
    def reset_game(self):
        """Reset game to initial state"""
        self.snake = [(self.GRID_WIDTH // 2, self.GRID_HEIGHT // 2)]
        self.direction = (1, 0)
        self.food = self.generate_food()
        self.score = 0
        self.level = 1
        self.speed = 10
    
    def generate_food(self):
        """Generate food at random position not on snake"""
        while True:
            food = (random.randint(0, self.GRID_WIDTH - 1), 
                    random.randint(0, self.GRID_HEIGHT - 1))
            if food not in self.snake:
                return food
    
    def draw_grid(self):
        """Draw grid background"""
        for x in range(0, self.WIDTH, self.GRID_SIZE):
            pygame.draw.line(self.screen, self.GRAY, (x, 0), (x, self.HEIGHT), 1)
        for y in range(0, self.HEIGHT, self.GRID_SIZE):
            pygame.draw.line(self.screen, self.GRAY, (0, y), (self.WIDTH, y), 1)
    
    def draw_snake(self):
        """Draw snake on screen with gradient effect"""
        for i, segment in enumerate(self.snake):
            # Gradient from bright head to darker tail
            if i == 0:  # Head
                color = self.GREEN
                border_color = (0, 150, 0)
            else:
                # Calculate gradient based on position
                gradient = max(0.3, 1.0 - (i / len(self.snake) * 0.7))
                color = (
                    int(self.GREEN[0] * gradient),
                    int(self.GREEN[1] * gradient),
                    int(self.GREEN[2] * gradient)
                )
                border_color = (0, 100, 0)
            
            rect = pygame.Rect(segment[0] * self.GRID_SIZE, 
                              segment[1] * self.GRID_SIZE, 
                              self.GRID_SIZE, self.GRID_SIZE)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, border_color, rect, 1)
    
    def draw_food(self):
        """Draw food on screen with shine effect"""
        rect = pygame.Rect(self.food[0] * self.GRID_SIZE, 
                          self.food[1] * self.GRID_SIZE, 
                          self.GRID_SIZE, self.GRID_SIZE)
        
        # Main food color
        pygame.draw.rect(self.screen, self.RED, rect)
        
        # Shine effect
        shine_rect = pygame.Rect(
            rect.x + self.GRID_SIZE//4,
            rect.y + self.GRID_SIZE//4,
            self.GRID_SIZE//3,
            self.GRID_SIZE//3
        )
        pygame.draw.ellipse(self.screen, (255, 200, 200), shine_rect)
    
    def update_snake(self):
        """Update snake position - DIES WHEN TOUCHING WALLS"""
        # Calculate new head position
        head_x, head_y = self.snake[0]
        dir_x, dir_y = self.direction
        new_head = (head_x + dir_x, head_y + dir_y)  # No wrap-around
        
        # Check collision with walls (dies on wall contact)
        if (new_head[0] < 0 or new_head[0] >= self.GRID_WIDTH or 
            new_head[1] < 0 or new_head[1] >= self.GRID_HEIGHT):
            return False  # Game over - hit wall
        
        # Check collision with self
        if new_head in self.snake:
            return False  # Game over - hit self
        
        # Move snake
        self.snake.insert(0, new_head)
        
        # Check if food is eaten
        if new_head == self.food:
            self.score += 10
            self.food = self.generate_food()
            
            # Level up every 50 points
            if self.score % 50 == 0:
                self.level += 1
                self.speed += 2
        else:
            # Remove tail if no food eaten
            self.snake.pop()
        
        return True  # Game continues
    
    def draw_login_screen(self):
        """Draw login/register screen"""
        self.screen.fill(self.BLACK)
        
        # Title with shadow effect
        title = self.title_font.render("SNAKE GAME", True, (200, 255, 200))
        title_shadow = self.title_font.render("SNAKE GAME", True, (0, 100, 0))
        self.screen.blit(title_shadow, (self.WIDTH//2 - title.get_width()//2 + 3, 53))
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 50))
        
        subtitle = self.font.render("Windows MySQL Edition", True, self.BLUE)
        self.screen.blit(subtitle, (self.WIDTH//2 - subtitle.get_width()//2, 110))
        
        # Instructions
        instruction = self.font.render("Enter your username and press ENTER:", True, self.WHITE)
        self.screen.blit(instruction, (self.WIDTH//2 - instruction.get_width()//2, 200))
        
        # Input box with Windows-style look
        input_rect = pygame.Rect(self.WIDTH//2 - 150, 250, 300, 40)
        pygame.draw.rect(self.screen, (240, 240, 240), input_rect)
        pygame.draw.rect(self.screen, self.BLUE, input_rect, 3)
        
        # Input text
        if self.input_text:
            text_surface = self.font.render(self.input_text, True, self.BLACK)
        else:
            text_surface = self.font.render("Type username here...", True, (180, 180, 180))
        self.screen.blit(text_surface, (input_rect.x + 10, input_rect.y + 8))
        
        # Info text
        info = self.font.render("(Creates/loads your player profile in MySQL)", True, (180, 180, 255))
        self.screen.blit(info, (self.WIDTH//2 - info.get_width()//2, 320))
        
        # Database status
        status_color = (0, 200, 0) if self.db.connection and self.db.connection.is_connected() else (255, 100, 100)
        status_text = "MySQL: CONNECTED" if self.db.connection and self.db.connection.is_connected() else "MySQL: DISCONNECTED"
        status = self.font.render(status_text, True, status_color)
        self.screen.blit(status, (self.WIDTH//2 - status.get_width()//2, 380))
    
    def draw_game_over_screen(self):
        """Draw game over screen"""
        self.screen.fill((20, 20, 20))
        
        # Game Over text
        game_over = self.title_font.render("GAME OVER", True, self.RED)
        self.screen.blit(game_over, (self.WIDTH//2 - game_over.get_width()//2, 100))
        
        # Score box
        score_box = pygame.Rect(self.WIDTH//2 - 200, 180, 400, 200)
        pygame.draw.rect(self.screen, (40, 40, 40), score_box)
        pygame.draw.rect(self.screen, self.BLUE, score_box, 3)
        
        # Score details
        score_text = self.font.render(f"Final Score: {self.score}", True, self.WHITE)
        level_text = self.font.render(f"Level Reached: {self.level}", True, self.WHITE)
        player_text = self.font.render(f"Player: {self.username}", True, self.BLUE)
        
        self.screen.blit(score_text, (self.WIDTH//2 - score_text.get_width()//2, 220))
        self.screen.blit(level_text, (self.WIDTH//2 - level_text.get_width()//2, 260))
        self.screen.blit(player_text, (self.WIDTH//2 - player_text.get_width()//2, 300))
        
        # Instructions
        instructions = [
            ("Press SPACE to play again", self.GREEN),
            ("Press L to view leaderboard", (255, 215, 0)),  # Gold
            ("Press ESC to quit", (255, 100, 100))
        ]
        
        for i, (text, color) in enumerate(instructions):
            rendered = self.font.render(text, True, color)
            self.screen.blit(rendered, (self.WIDTH//2 - rendered.get_width()//2, 380 + i * 40))
    
    def draw_leaderboard(self):
        """Draw leaderboard screen"""
        self.screen.fill(self.BLACK)
        
        # Title
        title = self.title_font.render("LEADERBOARD", True, self.GREEN)
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 30))
        
        # Get leaderboard data
        leaderboard = self.db.get_leaderboard(10)
        
        # Table background
        table_rect = pygame.Rect(50, 100, 700, 400)
        pygame.draw.rect(self.screen, (30, 30, 30), table_rect)
        pygame.draw.rect(self.screen, self.BLUE, table_rect, 2)
        
        # Column headers
        headers = ["Rank", "Player", "Score", "Level", "Date"]
        x_positions = [70, 170, 370, 470, 570]
        
        for i, header in enumerate(headers):
            header_text = self.font.render(header, True, self.BLUE)
            self.screen.blit(header_text, (x_positions[i], 110))
        
        # Draw scores
        if not leaderboard:
            no_data = self.font.render("No scores yet! Be the first to play!", True, self.WHITE)
            self.screen.blit(no_data, (self.WIDTH//2 - no_data.get_width()//2, 200))
        else:
            for i, (username, score, level, date) in enumerate(leaderboard):
                y = 150 + i * 35
                
                # Highlight current player
                if username == self.username:
                    row_rect = pygame.Rect(50, y - 5, 700, 35)
                    pygame.draw.rect(self.screen, (30, 60, 30), row_rect)
                
                color = self.GREEN if username == self.username else self.WHITE
                
                rank = self.font.render(f"{i+1}.", True, color)
                name = self.font.render(username[:15], True, color)
                score_text = self.font.render(str(score), True, color)
                level_text = self.font.render(str(level), True, color)
                
                # Format date
                if isinstance(date, datetime.datetime):
                    date_str = date.strftime("%m/%d/%Y")
                else:
                    date_str = str(date)
                date_text = self.font.render(date_str[:10], True, color)
                
                self.screen.blit(rank, (x_positions[0], y))
                self.screen.blit(name, (x_positions[1], y))
                self.screen.blit(score_text, (x_positions[2], y))
                self.screen.blit(level_text, (x_positions[3], y))
                self.screen.blit(date_text, (x_positions[4], y))
        
        # Instructions
        instructions = self.font.render("Press SPACE to play or ESC to return to menu", True, self.WHITE)
        self.screen.blit(instructions, (self.WIDTH//2 - instructions.get_width()//2, 530))
    
    def draw_game(self):
        """Draw main game screen with wall collision"""
        self.screen.fill(self.BLACK)
        self.draw_grid()
        self.draw_snake()
        self.draw_food()
        
        # Draw deadly walls
        wall_thickness = 4
        pygame.draw.rect(self.screen, self.WALL_COLOR, (0, 0, self.WIDTH, self.HEIGHT), wall_thickness)
        
        # Game info panel
        info_panel = pygame.Rect(10, 10, 200, 100)
        pygame.draw.rect(self.screen, (30, 30, 30, 200), info_panel)
        pygame.draw.rect(self.screen, self.BLUE, info_panel, 2)
        
        # Score and level display
        score_text = self.font.render(f"Score: {self.score}", True, self.WHITE)
        level_text = self.font.render(f"Level: {self.level}", True, self.WHITE)
        player_text = self.font.render(f"Player: {self.username}", True, self.BLUE)
        speed_text = self.font.render(f"Speed: {self.speed}", True, (255, 200, 100))
        
        self.screen.blit(score_text, (20, 20))
        self.screen.blit(level_text, (20, 50))
        self.screen.blit(player_text, (20, 80))
        self.screen.blit(speed_text, (20, 110))
        
        # Wall warning
        wall_warning = self.font.render("WALLS ARE DEADLY!", True, self.WALL_COLOR)
        self.screen.blit(wall_warning, (self.WIDTH - wall_warning.get_width() - 20, 20))
        
        # Controls reminder
        controls = self.font.render("Arrow Keys: Move | ESC: Menu", True, self.GRAY)
        self.screen.blit(controls, (self.WIDTH//2 - controls.get_width()//2, self.HEIGHT - 30))
    
    def handle_login_input(self, event):
        """Handle input during login screen"""
        if event.key == pygame.K_RETURN:
            if self.input_text.strip():
                self.username = self.input_text.strip()
                print(f"🔑 Registering user: {self.username}")
                self.user_id = self.db.register_user(self.username)
                if self.user_id:
                    print(f"✅ User registered with ID: {self.user_id}")
                    self.game_state = "PLAYING"
                    self.reset_game()
                else:
                    print("❌ Failed to register user")
        elif event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
        elif event.unicode.isprintable() and len(self.input_text) < 20:
            self.input_text += event.unicode
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    # Handle login screen
                    if self.game_state == "LOGIN":
                        self.handle_login_input(event)
                    
                    # Handle game over screen
                    elif self.game_state == "GAME_OVER":
                        if event.key == pygame.K_SPACE:
                            self.game_state = "PLAYING"
                            self.reset_game()
                        elif event.key == pygame.K_l:
                            self.game_state = "LEADERBOARD"
                        elif event.key == pygame.K_ESCAPE:
                            self.game_state = "LOGIN"
                            self.input_text = ""
                    
                    # Handle leaderboard screen
                    elif self.game_state == "LEADERBOARD":
                        if event.key == pygame.K_SPACE:
                            self.game_state = "PLAYING"
                            self.reset_game()
                        elif event.key == pygame.K_ESCAPE:
                            self.game_state = "GAME_OVER"
                    
                    # Handle game controls
                    elif self.game_state == "PLAYING":
                        if event.key == pygame.K_UP and self.direction != (0, 1):
                            self.direction = (0, -1)
                        elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                            self.direction = (0, 1)
                        elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                            self.direction = (-1, 0)
                        elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                            self.direction = (1, 0)
                        elif event.key == pygame.K_ESCAPE:
                            self.game_state = "GAME_OVER"
            
            # Update game state if playing
            if self.game_state == "PLAYING":
                if not self.update_snake():
                    # Game over - save score
                    print(f"💀 Game Over! Score: {self.score}, Level: {self.level}")
                    if self.user_id:
                        saved = self.db.save_score(self.user_id, self.score, self.level)
                        if saved:
                            print("✅ Score saved to MySQL database")
                    self.game_state = "GAME_OVER"
            
            # Draw current screen
            if self.game_state == "LOGIN":
                self.draw_login_screen()
            elif self.game_state == "PLAYING":
                self.draw_game()
            elif self.game_state == "GAME_OVER":
                self.draw_game_over_screen()
            elif self.game_state == "LEADERBOARD":
                self.draw_leaderboard()
            
            pygame.display.flip()
            
            # Control game speed
            self.clock.tick(self.speed if self.game_state == "PLAYING" else 60)
        
        # Cleanup
        self.db.close()
        pygame.quit()

if __name__ == "__main__":
    print("="*60)
    print("SNAKE GAME - WINDOWS MYSQL EDITION")
    print("="*60)
    
    print("\n🎮 Starting game...")
    print("📊 MySQL Configuration:")
    print(f"   Host: {DB_CONFIG['host']}")
    print(f"   User: {DB_CONFIG['user']}")
    print(f"   Database: {DB_CONFIG['database']}")
    print(f"   Password: {'[SET]' if DB_CONFIG['password'] else '[NOT SET - Using empty password]'}")
    
    print("\n⚠️  IMPORTANT WINDOWS SETUP:")
    print("1. Make sure MySQL is installed and running")
    print("2. Update config.py with your MySQL password if needed")
    print("3. Run 'python database_setup.py' first to create database")
    
    print("\n🎯 Game Features:")
    print("   • Snake dies when touching walls")
    print("   • MySQL score tracking")
    print("   • User registration system")
    print("   • Leaderboard with top 10 scores")
    print("   • Level progression system")
    
    print("\n" + "="*60)
    
    try:
        game = SnakeGame()
        game.run()
    except Exception as e:
        print(f"\n❌ Error starting game: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Install requirements: pip install -r requirements.txt")
        print("2. Check MySQL is running in Windows Services")
        print("3. Run database setup: python database_setup.py")
        print("4. Update config.py with correct MySQL credentials")
        input("\nPress Enter to exit...")
