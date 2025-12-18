import pygame
import random
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import sys

# Database configuration - UPDATE THESE WITH YOUR DATABASE CREDENTIALS
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',  # Change to your MySQL username
    'password': '',  # Change to your MySQL password
    'database': 'snake_game_db'
}

class DatabaseHandler:
    def __init__(self):
        self.connection = None
        self.connect()
        self.create_database()
        self.create_table()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            print("Connected to MySQL database")
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            self.connection = None
    
    def create_database(self):
        """Create database if it doesn't exist"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
            cursor.close()
        except Error as e:
            print(f"Error creating database: {e}")
    
    def create_table(self):
        """Create scores table if it doesn't exist"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS high_scores (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    player_name VARCHAR(50) NOT NULL,
                    score INT NOT NULL,
                    level INT NOT NULL,
                    game_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.connection.commit()
            cursor.close()
        except Error as e:
            print(f"Error creating table: {e}")
    
    def save_score(self, player_name, score, level):
        """Save score to database"""
        if not self.connection:
            return False
        
        try:
            cursor = self.connection.cursor()
            query = "INSERT INTO high_scores (player_name, score, level) VALUES (%s, %s, %s)"
            cursor.execute(query, (player_name, score, level))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            print(f"Error saving score: {e}")
            return False
    
    def get_high_scores(self, limit=10):
        """Retrieve top high scores"""
        if not self.connection:
            return []
        
        try:
            cursor = self.connection.cursor()
            query = """
                SELECT player_name, score, level, game_date 
                FROM high_scores 
                ORDER BY score DESC 
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            scores = cursor.fetchall()
            cursor.close()
            return scores
        except Error as e:
            print(f"Error fetching scores: {e}")
            return []
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Database connection closed")

class SnakeGame:
    def __init__(self):
        pygame.init()
        
        # Game constants
        self.WIDTH, self.HEIGHT = 800, 600
        self.GRID_SIZE = 20
        self.GRID_WIDTH = self.WIDTH // self.GRID_SIZE
        self.GRID_HEIGHT = self.HEIGHT // self.GRID_SIZE
        
        # Colors
        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)
        self.GREEN = (0, 255, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 120, 255)
        self.DARK_GREEN = (0, 180, 0)
        self.GRAY = (40, 40, 40)
        
        # Game variables
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Snake Game with MySQL")
        
        # Fonts
        self.font = pygame.font.SysFont('Arial', 25)
        self.big_font = pygame.font.SysFont('Arial', 50)
        
        # Database
        self.db = DatabaseHandler()
        
        # Game state
        self.reset_game()
        
    def reset_game(self):
        """Reset game to initial state"""
        self.snake = [(self.GRID_WIDTH // 2, self.GRID_HEIGHT // 2)]
        self.direction = (1, 0)
        self.food = self.generate_food()
        self.score = 0
        self.level = 1
        self.speed = 10
        self.game_over = False
        self.paused = False
        self.player_name = ""
        self.input_active = False
        self.show_high_scores = False
        
    def generate_food(self):
        """Generate food at random position"""
        while True:
            food = (random.randint(0, self.GRID_WIDTH - 1), 
                   random.randint(0, self.GRID_HEIGHT - 1))
            if food not in self.snake:
                return food
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                # Handle player name input
                if self.input_active:
                    if event.key == pygame.K_RETURN and self.player_name:
                        self.input_active = False
                    elif event.key == pygame.K_BACKSPACE:
                        self.player_name = self.player_name[:-1]
                    elif len(self.player_name) < 20:
                        self.player_name += event.unicode
                    continue
                
                # Handle game states
                if event.key == pygame.K_ESCAPE:
                    return False
                
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_h:
                        self.show_high_scores = not self.show_high_scores
                    elif event.key == pygame.K_s and not self.input_active:
                        self.input_active = True
                else:
                    if event.key == pygame.K_p:
                        self.paused = not self.paused
                    
                    if not self.paused:
                        if event.key == pygame.K_UP and self.direction != (0, 1):
                            self.direction = (0, -1)
                        elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                            self.direction = (0, 1)
                        elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                            self.direction = (-1, 0)
                        elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                            self.direction = (1, 0)
        
        return True
    
    def update_game(self):
        """Update game logic"""
        if self.game_over or self.paused:
            return
        
        # Move snake
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        # Check collision with walls
        if (new_head[0] < 0 or new_head[0] >= self.GRID_WIDTH or
            new_head[1] < 0 or new_head[1] >= self.GRID_HEIGHT or
            new_head in self.snake):
            self.game_over = True
            return
        
        # Add new head
        self.snake.insert(0, new_head)
        
        # Check food collision
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
    
    def draw_grid(self):
        """Draw game grid"""
        for x in range(0, self.WIDTH, self.GRID_SIZE):
            pygame.draw.line(self.screen, self.GRAY, (x, 0), (x, self.HEIGHT), 1)
        for y in range(0, self.HEIGHT, self.GRID_SIZE):
            pygame.draw.line(self.screen, self.GRAY, (0, y), (self.WIDTH, y), 1)
    
    def draw_snake(self):
        """Draw snake"""
        for i, segment in enumerate(self.snake):
            color = self.DARK_GREEN if i == 0 else self.GREEN
            rect = pygame.Rect(segment[0] * self.GRID_SIZE, 
                             segment[1] * self.GRID_SIZE,
                             self.GRID_SIZE, self.GRID_SIZE)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, self.BLACK, rect, 1)
    
    def draw_food(self):
        """Draw food"""
        rect = pygame.Rect(self.food[0] * self.GRID_SIZE,
                          self.food[1] * self.GRID_SIZE,
                          self.GRID_SIZE, self.GRID_SIZE)
        pygame.draw.rect(self.screen, self.RED, rect)
        pygame.draw.rect(self.screen, self.BLACK, rect, 1)
    
    def draw_ui(self):
        """Draw UI elements"""
        # Score and level
        score_text = self.font.render(f"Score: {self.score}", True, self.WHITE)
        level_text = self.font.render(f"Level: {self.level}", True, self.WHITE)
        speed_text = self.font.render(f"Speed: {self.speed}", True, self.WHITE)
        
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(level_text, (10, 40))
        self.screen.blit(speed_text, (10, 70))
        
        # Pause text
        if self.paused:
            pause_text = self.big_font.render("PAUSED", True, self.WHITE)
            self.screen.blit(pause_text, (self.WIDTH // 2 - pause_text.get_width() // 2, 
                                        self.HEIGHT // 2 - 50))
    
    def draw_game_over(self):
        """Draw game over screen"""
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(self.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game over text
        game_over_text = self.big_font.render("GAME OVER", True, self.RED)
        score_text = self.font.render(f"Final Score: {self.score} | Level: {self.level}", True, self.WHITE)
        
        self.screen.blit(game_over_text, (self.WIDTH // 2 - game_over_text.get_width() // 2, 100))
        self.screen.blit(score_text, (self.WIDTH // 2 - score_text.get_width() // 2, 180))
        
        # Instructions
        instructions = [
            "Press R to Restart",
            "Press S to Save Score",
            "Press H to View High Scores",
            "Press ESC to Quit"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.font.render(instruction, True, self.WHITE)
            self.screen.blit(text, (self.WIDTH // 2 - text.get_width() // 2, 250 + i * 40))
        
        # Player name input
        if self.input_active:
            input_text = self.font.render("Enter your name: " + self.player_name, True, self.GREEN)
            self.screen.blit(input_text, (self.WIDTH // 2 - input_text.get_width() // 2, 450))
            
            if self.player_name:
                enter_text = self.font.render("Press ENTER to save", True, self.WHITE)
                self.screen.blit(enter_text, (self.WIDTH // 2 - enter_text.get_width() // 2, 500))
    
    def draw_high_scores(self):
        """Draw high scores screen"""
        overlay = pygame.Surface((self.WIDTH, self.HEIGHT))
        overlay.set_alpha(220)
        overlay.fill(self.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Title
        title = self.big_font.render("HIGH SCORES", True, self.BLUE)
        self.screen.blit(title, (self.WIDTH // 2 - title.get_width() // 2, 50))
        
        # Get scores from database
        scores = self.db.get_high_scores(10)
        
        # Column headers
        headers = ["Rank", "Name", "Score", "Level", "Date"]
        for i, header in enumerate(headers):
            text = self.font.render(header, True, self.WHITE)
            x_pos = 100 + i * 150
            self.screen.blit(text, (x_pos, 150))
        
        # Draw scores
        if scores:
            for rank, (name, score, level, date) in enumerate(scores, 1):
                date_str = date.strftime("%Y-%m-%d") if isinstance(date, datetime) else str(date)
                row_data = [str(rank), name[:15], str(score), str(level), date_str]
                
                for i, data in enumerate(row_data):
                    color = self.GREEN if rank == 1 else self.WHITE
                    text = self.font.render(data, True, color)
                    x_pos = 100 + i * 150
                    self.screen.blit(text, (x_pos, 200 + rank * 40))
        else:
            no_scores = self.font.render("No high scores yet!", True, self.WHITE)
            self.screen.blit(no_scores, (self.WIDTH // 2 - no_scores.get_width() // 2, 200))
        
        # Back instruction
        back_text = self.font.render("Press H to return to game", True, self.WHITE)
        self.screen.blit(back_text, (self.WIDTH // 2 - back_text.get_width() // 2, 550))
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            running = self.handle_events()
            
            if not self.show_high_scores:
                self.update_game()
            
            # Drawing
            self.screen.fill(self.BLACK)
            self.draw_grid()
            self.draw_snake()
            self.draw_food()
            self.draw_ui()
            
            if self.game_over:
                self.draw_game_over()
                
                # Save score if player entered name
                if self.input_active == False and self.player_name:
                    success = self.db.save_score(self.player_name, self.score, self.level)
                    if success:
                        status_text = self.font.render("Score saved successfully!", True, self.GREEN)
                        self.screen.blit(status_text, (self.WIDTH // 2 - status_text.get_width() // 2, 550))
                    self.player_name = ""  # Reset name after saving
            
            if self.show_high_scores:
                self.draw_high_scores()
            
            pygame.display.flip()
            self.clock.tick(self.speed)
        
        # Cleanup
        self.db.close()
        pygame.quit()
        sys.exit()

def setup_database():
    """Set up database before running the game"""
    try:
        # First connect without database
        config = DB_CONFIG.copy()
        config.pop('database')
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # Create database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        print(f"Database '{DB_CONFIG['database']}' created or already exists")
        
        cursor.close()
        connection.close()
        
        # Now connect with database to create table
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS high_scores (
                id INT AUTO_INCREMENT PRIMARY KEY,
                player_name VARCHAR(50) NOT NULL,
                score INT NOT NULL,
                level INT NOT NULL,
                game_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("Table 'high_scores' created or already exists")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("Database setup completed successfully!")
        
    except Error as e:
        print(f"Error setting up database: {e}")
        print("\nPlease make sure:")
        print("1. MySQL server is running")
        print("2. Update DB_CONFIG with your MySQL credentials")
        print("3. Install mysql-connector-python: pip install mysql-connector-python")

if __name__ == "__main__":
    print("=" * 50)
    print("SNAKE GAME WITH MYSQL CONNECTIVITY")
    print("=" * 50)
    
    # Setup database
    setup_database()
    
    # Start game
    print("\nStarting game...")
    print("\nCONTROLS:")
    print("↑ ↓ ← → : Move Snake")
    print("P : Pause/Resume")
    print("R : Restart (after game over)")
    print("S : Save Score (after game over)")
    print("H : View High Scores")
    print("ESC : Quit Game")
    print("=" * 50)
    
    game = SnakeGame()
    game.run()
