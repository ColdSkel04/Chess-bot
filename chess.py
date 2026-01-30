#!/usr/bin/env python3

import pygame
import bot
import time

SQUARE_SIZE = 80
PIECE_WIDTH = 45
PIECE_HEIGHT = 75

class Piece:

    def __init__(self, color, piece_type, position):
        self.color = color
        self.type = piece_type
        self.position = position
        self.has_moved = False
        self.image = self.load_image()
        self.value = self.get_value()
    
    def load_image(self):
        prefix = 'W' if self.color == 'white' else 'B'
        type_name = self.type.capitalize()
        img = pygame.image.load(f"assets/pieces/{prefix}_{type_name}.png")
        return pygame.transform.scale(img, (PIECE_WIDTH, PIECE_HEIGHT))
    
    def get_value(self):
        if self.type == 'pawn' or self.type == 'king':
            return 1
        elif self.type == 'bishop' or self.type == 'knight':
            return 3
        elif self.type == 'rook':
            return 5
        elif self.type == 'queen':
            return 9
        return 1

    def get_pseudo_legal_moves(self, board):
        """Get moves without considering check"""
        moves = []
        row, col = self.position
        
        if self.type == 'pawn':
            moves = self._get_pawn_moves(board, row, col)
        elif self.type == 'rook':
            moves = self._get_rook_moves(board, row, col)
        elif self.type == 'knight':
            moves = self._get_knight_moves(board, row, col)
        elif self.type == 'bishop':
            moves = self._get_bishop_moves(board, row, col)
        elif self.type == 'queen':
            moves = self._get_queen_moves(board, row, col)
        elif self.type == 'king':
            moves = self._get_king_moves(board, row, col)
        
        return moves
    
    def _get_pawn_moves(self, board, row, col):
        moves = []
        direction = -1 if self.color == 'white' else 1
        
        # Move forward one square
        new_row = row + direction
        if 0 <= new_row < 8 and board[new_row][col] is None:
            moves.append((new_row, col))
            
            # Move forward two squares on first move
            if not self.has_moved:
                new_row2 = row + 2 * direction
                if 0 <= new_row2 < 8 and board[new_row2][col] is None and board[row + direction][col] is None:
                    moves.append((new_row2, col))
        
        # Capture diagonally
        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board[new_row][new_col]
                if target and target.color != self.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def _get_rook_moves(self, board, row, col):
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + dr * i, col + dc * i
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                
                target = board[new_row][new_col]
                if target is None:
                    moves.append((new_row, new_col))
                elif target.color != self.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
        
        return moves
    
    def _get_knight_moves(self, board, row, col):
        moves = []
        knight_moves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]
        
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board[new_row][new_col]
                if target is None or target.color != self.color:
                    moves.append((new_row, new_col))
        
        return moves
    
    def _get_bishop_moves(self, board, row, col):
        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + dr * i, col + dc * i
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                
                target = board[new_row][new_col]
                if target is None:
                    moves.append((new_row, new_col))
                elif target.color != self.color:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
        
        return moves
    
    def _get_queen_moves(self, board, row, col):
        return self._get_rook_moves(board, row, col) + self._get_bishop_moves(board, row, col)
    
    def _get_king_moves(self, board, row, col):
        moves = []
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = board[new_row][new_col]
                if target is None or target.color != self.color:
                    moves.append((new_row, new_col))
        
        return moves


class ChessGame:

    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.screen = pygame.display.set_mode((info.current_w, info.current_h))
        pygame.display.set_caption("Chess Game")
        self.clock = pygame.time.Clock()
        
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        self.board_offset_x = (self.screen_width - SQUARE_SIZE * 8) // 2
        self.board_offset_y = (self.screen_height - SQUARE_SIZE * 8) // 2
        
        self.board = [[None for i in range(8)] for i in range(8)]
        self.selected_piece = None
        self.valid_moves = []
        self.current_turn = 'white'
        self.game_over = False
        self.winner = None
        self.last_move = None
        self.en_passant_target = None
        self.promoting_pawn = None

        self.turns = 1
        self.blacks_value = self.get_value('black')
        self.whitess_value = self.get_value('white')
        self.color = 'white'
        self.color_ai = 'black'
        self.blacks = self.get_black_pieces()
        
        # NEW: Move history for undo functionality
        self.move_history = []
        
        # NEW: Captured pieces tracking
        self.white_captured = []
        self.black_captured = []
        
        # NEW: Undo button rect
        self.undo_button_rect = None
        
        self.setup_board()
    
    def setup_board(self):
        """Initialize the chess board with pieces"""
        # Pawns
        for col in range(8):
            self.board[1][col] = Piece('black', 'pawn', (1, col))
            self.board[6][col] = Piece('white', 'pawn', (6, col))
        
        # Rooks
        self.board[0][0] = Piece('black', 'rook', (0, 0))
        self.board[0][7] = Piece('black', 'rook', (0, 7))
        self.board[7][0] = Piece('white', 'rook', (7, 0))
        self.board[7][7] = Piece('white', 'rook', (7, 7))
        
        # Knights
        self.board[0][1] = Piece('black', 'knight', (0, 1))
        self.board[0][6] = Piece('black', 'knight', (0, 6))
        self.board[7][1] = Piece('white', 'knight', (7, 1))
        self.board[7][6] = Piece('white', 'knight', (7, 6))
        
        # Bishops
        self.board[0][2] = Piece('black', 'bishop', (0, 2))
        self.board[0][5] = Piece('black', 'bishop', (0, 5))
        self.board[7][2] = Piece('white', 'bishop', (7, 2))
        self.board[7][5] = Piece('white', 'bishop', (7, 5))
        
        # Queens
        self.board[0][3] = Piece('black', 'queen', (0, 3))
        self.board[7][3] = Piece('white', 'queen', (7, 3))
        
        # Kings
        self.board[0][4] = Piece('black', 'king', (0, 4))
        self.board[7][4] = Piece('white', 'king', (7, 4))
    
    def get_value(self, color):

        value = 0
        if color == 'black':
            team = self.get_black_pieces()
        else:
            team = self.get_white_pieces()
        for piece in team:
            value += piece.value
        return value

    def get_white_pieces(self):

        white_pieces = []

        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.color == 'white' and piece not in white_pieces:
                    white_pieces.append(piece)
        return white_pieces

    def get_black_pieces(self):

        black_pieces = []

        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece is not None and piece.color == 'black' and piece not in black_pieces:
                    black_pieces.append(piece)
        return black_pieces

    def find_king(self, color):
        """Find the king's position"""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.type == 'king' and piece.color == color:
                    return (row, col)
        return None
    
    def is_square_attacked(self, position, by_color):
        """Check if a square is attacked by a given color"""
        row, col = position
        
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece.color == by_color:
                    # Get pseudo legal moves (we can't use legal moves here to avoid recursion)
                    moves = piece.get_pseudo_legal_moves(self.board)
                    if position in moves:
                        return True
        return False
    
    def is_in_check(self, color):
        """Check if the king of the given color is in check"""
        king_pos = self.find_king(color)
        if not king_pos:
            return False
        
        opponent_color = 'black' if color == 'white' else 'white'
        return self.is_square_attacked(king_pos, opponent_color)
    
    def would_be_in_check(self, piece, new_pos):
        """Check if a move would leave the king in check"""
        old_row, old_col = piece.position
        new_row, new_col = new_pos
        
        # Temporarily make the move
        captured = self.board[new_row][new_col]
        self.board[new_row][new_col] = piece
        self.board[old_row][old_col] = None
        old_position = piece.position
        piece.position = new_pos
        
        # Check if king is in check
        in_check = self.is_in_check(piece.color)
        
        # Undo the move
        self.board[old_row][old_col] = piece
        self.board[new_row][new_col] = captured
        piece.position = old_position
        
        return in_check
    
    def get_legal_moves(self, piece):
        """Get all legal moves (excluding moves that would leave king in check)"""
        pseudo_legal = piece.get_pseudo_legal_moves(self.board)
        legal_moves = []
        
        for move in pseudo_legal:
            if not self.would_be_in_check(piece, move):
                legal_moves.append(move)
        
        # Add castling for king
        if piece.type == 'king':
            legal_moves.extend(self.get_castling_moves(piece))
        
        # Add en passant for pawns
        if piece.type == 'pawn':
            legal_moves.extend(self.get_en_passant_moves(piece))
        
        return legal_moves
    
    def get_castling_moves(self, king):
        """Get castling moves for the king"""
        if king.has_moved or self.is_in_check(king.color):
            return []
        
        moves = []
        row, col = king.position
        
        # Kingside castling
        rook = self.board[row][7]
        if rook and rook.type == 'rook' and not rook.has_moved:
            if all(self.board[row][c] is None for c in range(col + 1, 7)):
                # Check that king doesn't move through check
                if not self.is_square_attacked((row, col + 1), 'black' if king.color == 'white' else 'white'):
                    if not self.would_be_in_check(king, (row, col + 2)):
                        moves.append((row, col + 2))
        
        # Queenside castling
        rook = self.board[row][0]
        if rook and rook.type == 'rook' and not rook.has_moved:
            if all(self.board[row][c] is None for c in range(1, col)):
                # Check that king doesn't move through check
                if not self.is_square_attacked((row, col - 1), 'black' if king.color == 'white' else 'white'):
                    if not self.would_be_in_check(king, (row, col - 2)):
                        moves.append((row, col - 2))
        
        return moves
    
    def get_en_passant_moves(self, pawn):
        """Get en passant moves for a pawn"""
        if not self.en_passant_target:
            return []
        
        row, col = pawn.position
        target_row, target_col = self.en_passant_target
        direction = -1 if pawn.color == 'white' else 1
        
        # Check if pawn is in correct position for en passant
        if row + direction == target_row and abs(col - target_col) == 1:
            return [(target_row, target_col)]
        
        return []
    
    def get_square_from_pos(self, pos):
        """Convert pixel position to board coordinates"""
        x, y = pos
        col = (x - self.board_offset_x) // SQUARE_SIZE
        row = (y - self.board_offset_y) // SQUARE_SIZE
        
        if 0 <= row < 8 and 0 <= col < 8:
            return (row, col)
        return None

    def handle_click(self, pos):
        """Handle mouse click on the board"""
        if self.game_over:
            return
        
        # NEW: Check if undo button was clicked
        if self.undo_button_rect and self.undo_button_rect.collidepoint(pos):
            self.undo_move()
            return
        
        if self.current_turn == 'black':
            return
        
        # Handle promotion selection
        if self.promoting_pawn and self.color == 'white':
            self.handle_promotion_click(pos)
            return
        
        square = self.get_square_from_pos(pos)
        if square is None:
            return
        
        row, col = square
        
        # If a piece is already selected
        if self.selected_piece:
            # Try to move to the clicked square
            if square in self.valid_moves:
                self.make_move(self.selected_piece, square)
                self.selected_piece = None
                self.valid_moves = []
            # Clicked on another piece of the same color
            elif self.board[row][col] and self.board[row][col].color == self.current_turn:
                self.selected_piece = self.board[row][col]
                self.valid_moves = self.get_legal_moves(self.selected_piece)
            # Clicked elsewhere, deselect
            else:
                self.selected_piece = None
                self.valid_moves = []
        else:
            # Select a piece if it's the current player's turn
            piece = self.board[row][col]
            if piece and piece.color == self.current_turn:
                self.selected_piece = piece
                self.valid_moves = self.get_legal_moves(piece)
    
    def check_if_game_is_over(self):

        checkmate = True
        for piece in self.get_black_pieces():
            if len(self.get_legal_moves(piece)) != 0:
                checkmate = False
                break
        if checkmate and self.is_in_check('black'):
            self.winner = 'white'
            self.game_over = True
            return
        if checkmate and not self.is_in_check('black'):
            self.winner = 'nobody'
            self.game_over = True
            return
        checkmate = True
        for piece in self.get_white_pieces():
            if len(self.get_legal_moves(piece)) != 0:
                checkmate = False
                break
        if checkmate and self.is_in_check('white'):
            self.winner = 'black'
            self.game_over = True
            return
        if checkmate and not self.is_in_check('white'):
            self.winner = 'nobody'
            self.game_over = True
            return 
    
    def make_move(self, piece, new_pos):
        """Make a move and handle special moves"""
        old_row, old_col = piece.position
        new_row, new_col = new_pos
        
        # NEW: Save move state for undo
        move_data = {
            'piece': piece,
            'old_pos': (old_row, old_col),
            'new_pos': new_pos,
            'captured': self.board[new_row][new_col],
            'had_moved': piece.has_moved,
            'en_passant_target': self.en_passant_target,
            'castling_rook': None,
            'castling_rook_old_pos': None,
            'en_passant_captured': None,
            'promotion_from': None
        }
        
        piece.has_moved = True

        # Handle castling
        if piece.type == 'king' and abs(new_col - old_col) == 2:
            # Move rook
            if new_col > old_col:  # Kingside
                rook = self.board[old_row][7]
                move_data['castling_rook'] = rook
                move_data['castling_rook_old_pos'] = (old_row, 7)
                move_data['castling_rook_had_moved'] = rook.has_moved
                self.board[old_row][7] = None
                self.board[old_row][5] = rook
                rook.position = (old_row, 5)
                rook.has_moved = True
            else:  # Queenside
                rook = self.board[old_row][0]
                move_data['castling_rook'] = rook
                move_data['castling_rook_old_pos'] = (old_row, 0)
                move_data['castling_rook_had_moved'] = rook.has_moved
                self.board[old_row][0] = None
                self.board[old_row][3] = rook
                rook.position = (old_row, 3)
                rook.has_moved = True
        
        # Handle en passant
        if piece.type == 'pawn' and self.en_passant_target == new_pos:
            # Remove the captured pawn
            direction = -1 if piece.color == 'white' else 1
            captured_pawn_row = new_row - direction
            captured_pawn = self.board[captured_pawn_row][new_col]
            move_data['en_passant_captured'] = captured_pawn
            move_data['en_passant_captured_pos'] = (captured_pawn_row, new_col)
            self.board[captured_pawn_row][new_col] = None
            
            # NEW: Track captured piece
            if piece.color == 'white':
                self.white_captured.append(captured_pawn)
            else:
                self.black_captured.append(captured_pawn)
        
        # NEW: Track regular captures
        if self.board[new_row][new_col]:
            if piece.color == 'white':
                self.white_captured.append(self.board[new_row][new_col])
            else:
                self.black_captured.append(self.board[new_row][new_col])
        
        # Move the piece
        self.board[old_row][old_col] = None
        self.board[new_row][new_col] = piece
        piece.position = new_pos
        
        # Set en passant target
        if piece.type == 'pawn' and abs(new_row - old_row) == 2:
            direction = -1 if piece.color == 'white' else 1
            self.en_passant_target = (old_row + direction, old_col)
        else:
            self.en_passant_target = None
        
        piece.has_moved = True
        self.last_move = (old_pos := (old_row, old_col), new_pos)
        
        # Check for pawn promotion
        if piece.type == 'pawn' and (new_row == 0 or new_row == 7):
            if piece.color == self.color:
                self.promoting_pawn = piece
                move_data['promotion_from'] = 'pawn'
                self.move_history.append(move_data)
                return
            else:
                self.board[new_row][new_col] = Piece(self.color_ai, 'queen', (new_row, new_col))

        # NEW: Save move to history
        self.move_history.append(move_data)

        # Switch turn
        if not self.game_over:
            self.current_turn = 'black' if self.current_turn == 'white' else 'white'
            self.turns += 1
    
    # NEW: Undo functionality
    def undo_move(self):
        """Undo the last move"""
        if not self.move_history or self.game_over:
            return
        
        # Only allow undo on player's turn and when not promoting
        if self.current_turn != 'white' or self.promoting_pawn:
            return
        
        # Pop the last move (player's move)
        if len(self.move_history) < 1:
            return
        
        # Undo AI's move first if it exists
        if len(self.move_history) >= 2:
            ai_move = self.move_history.pop()
            self._undo_single_move(ai_move)
        
        # Undo player's move
        player_move = self.move_history.pop()
        self._undo_single_move(player_move)
        
        self.current_turn = 'white'
        self.turns = max(1, self.turns - 2)
    
    def _undo_single_move(self, move_data):
        """Undo a single move from move data"""
        piece = move_data['piece']
        old_pos = move_data['old_pos']
        new_pos = move_data['new_pos']
        captured = move_data['captured']
        
        # Handle promotion undo
        if move_data['promotion_from']:
            piece.type = move_data['promotion_from']
            piece.image = piece.load_image()
        
        # Move piece back
        self.board[new_pos[0]][new_pos[1]] = None
        self.board[old_pos[0]][old_pos[1]] = piece
        piece.position = old_pos
        piece.has_moved = move_data['had_moved']
        
        # Restore captured piece
        if captured:
            self.board[new_pos[0]][new_pos[1]] = captured
            # Remove from captured list
            if piece.color == 'white' and captured in self.white_captured:
                self.white_captured.remove(captured)
            elif piece.color == 'black' and captured in self.black_captured:
                self.black_captured.remove(captured)
        
        # Undo castling
        if move_data['castling_rook']:
            rook = move_data['castling_rook']
            rook_old_pos = move_data['castling_rook_old_pos']
            self.board[rook.position[0]][rook.position[1]] = None
            self.board[rook_old_pos[0]][rook_old_pos[1]] = rook
            rook.position = rook_old_pos
            rook.has_moved = move_data['castling_rook_had_moved']
        
        # Undo en passant
        if move_data['en_passant_captured']:
            captured_pawn = move_data['en_passant_captured']
            captured_pos = move_data['en_passant_captured_pos']
            self.board[captured_pos[0]][captured_pos[1]] = captured_pawn
            # Remove from captured list
            if piece.color == 'white' and captured_pawn in self.white_captured:
                self.white_captured.remove(captured_pawn)
            elif piece.color == 'black' and captured_pawn in self.black_captured:
                self.black_captured.remove(captured_pawn)
        
        # Restore en passant target
        self.en_passant_target = move_data['en_passant_target']

    def make_test_move(self, piece, new_pos):
        """Make a move and handle special moves"""
        old_row, old_col = piece.position
        new_row, new_col = new_pos

        # Handle castling
        if piece.type == 'king' and abs(new_col - old_col) == 2:
            return
        
        # Handle en passant
        if piece.type == 'pawn' and self.en_passant_target == new_pos:
            return
        
        # Move the piece
        self.board[old_row][old_col] = None
        self.board[new_row][new_col] = piece
        piece.position = new_pos
    
    def handle_promotion_click(self, pos):
        """Handle clicking on promotion choice"""
        choices = ['queen', 'rook', 'bishop', 'knight']
        choice_width = 80
        choice_height = 80
        
        start_x = self.screen_width // 2 - (len(choices) * choice_width) // 2
        start_y = self.screen_height // 2 - choice_height // 2
        
        x, y = pos
        if start_y <= y <= start_y + choice_height:
            for i, piece_type in enumerate(choices):
                choice_x = start_x + i * choice_width
                if choice_x <= x <= choice_x + choice_width:
                    # Promote the pawn
                    self.promoting_pawn.type = piece_type
                    self.promoting_pawn.image = self.promoting_pawn.load_image()
                    
                    # NEW: Update the last move in history with promotion info
                    if self.move_history:
                        self.move_history[-1]['promoted_to'] = piece_type
                    
                    self.promoting_pawn = None
                    
                    # Switch turn
                    self.current_turn = 'black' if self.current_turn == 'white' else 'white'
                    return
    
    def draw(self):
        """Draw the chess board and pieces"""
        self.screen.fill((40, 40, 40))
        
        # Draw squares
        colors = [(240, 217, 181), (181, 136, 99)]
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                rect = pygame.Rect(
                    self.board_offset_x + col * SQUARE_SIZE,
                    self.board_offset_y + row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE
                )
                pygame.draw.rect(self.screen, color, rect)
        
        # Highlight if king is in check
        if self.is_in_check(self.current_turn):
            king_pos = self.find_king(self.current_turn)
            if king_pos:
                row, col = king_pos
                rect = pygame.Rect(
                    self.board_offset_x + col * SQUARE_SIZE,
                    self.board_offset_y + row * SQUARE_SIZE,
                    SQUARE_SIZE,
                    SQUARE_SIZE
                )
                pygame.draw.rect(self.screen, (255, 0, 0), rect, 5)

        # Highlight selected piece
        if self.selected_piece and not self.game_over:
            row, col = self.selected_piece.position
            rect = pygame.Rect(
                self.board_offset_x + col * SQUARE_SIZE,
                self.board_offset_y + row * SQUARE_SIZE,
                SQUARE_SIZE,
                SQUARE_SIZE
            )
            pygame.draw.rect(self.screen, (255, 255, 0), rect, 4)
        
        # Highlight valid moves
        for move_row, move_col in self.valid_moves:
            center_x = self.board_offset_x + move_col * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = self.board_offset_y + move_row * SQUARE_SIZE + SQUARE_SIZE // 2
            
            # Different indicator for capture vs empty square
            if self.board[move_row][move_col]:
                pygame.draw.circle(self.screen, (255, 100, 100), (center_x, center_y), 15)
            else:
                pygame.draw.circle(self.screen, (100, 255, 100), (center_x, center_y), 12)
        
        # Draw pieces
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    x = self.board_offset_x + col * SQUARE_SIZE + (SQUARE_SIZE - PIECE_WIDTH) // 2
                    y = self.board_offset_y + row * SQUARE_SIZE + (SQUARE_SIZE - PIECE_HEIGHT) // 2
                    self.screen.blit(piece.image, (x, y))
        
        # NEW: Draw captured pieces
        self.draw_captured_pieces()
        
        # NEW: Draw undo button
        self.draw_undo_button()
        
        # Draw promotion dialog
        if self.promoting_pawn:
            self.draw_promotion_dialog()
        
        self.check_if_game_is_over()
        # Draw turn indicator or game over message
        font = pygame.font.Font(None, 48)
        if self.game_over:
            if self.color == self.winner:
                text = font.render(f"GAME OVER! Player Wins!", True, (255, 50, 50))
            elif self.winner in ['black', 'white']:
                text = font.render(f"GAME OVER! Clifford Wins!", True, (255, 50, 50))
            else:
                text = font.render(f"GAME OVER! Nobody Wins! (Stalemate)", True, (255, 50, 50))
            text_rect = text.get_rect(center=(self.screen_width // 2, self.board_offset_y - 60))
            
            bg_rect = text_rect.inflate(40, 20)
            pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
            pygame.draw.rect(self.screen, (255, 50, 50), bg_rect, 3)
            
            self.screen.blit(text, text_rect)
        else:
            if self.current_turn == 'white':
                turn_text = "Player's Turn"
            else:
                turn_text = "Clifford's Turn"
            if self.is_in_check(self.current_turn):
                turn_text += " - CHECK!"
            text = font.render(turn_text, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen_width // 2, self.board_offset_y - 50))
            self.screen.blit(text, text_rect)
        pygame.display.flip()
    
    # NEW: Draw captured pieces
    def draw_captured_pieces(self):
        """Draw the captured pieces on the sides of the board"""
        piece_size = 50
        padding = 5
        start_x_left = self.board_offset_x - 250
        start_x_right = self.board_offset_x + SQUARE_SIZE * 8 - 820
        start_y = self.board_offset_y
        
        font = pygame.font.Font(None, 28)
        if self.color == 'white':
            label = font.render("Player value:  " + str(self.get_value('white') - self.get_value('black')), True, (255, 255, 255))
        else:
            label = font.render("Player value:  " + str(self.get_value('black') - self.get_value('white')), True, (255, 255, 255))
        self.screen.blit(label, (start_x_left - 20, start_y - 80))
        
        # Draw white's captures (left side)
        label = font.render("White captured:", True, (255, 255, 255))
        self.screen.blit(label, (start_x_left - 120, start_y - 30))
        
        for i, piece in enumerate(self.white_captured):
            y_pos = start_y + (i * (piece_size + padding))
            img = pygame.transform.scale(piece.image, (piece_size - 5, piece_size + 10))
            self.screen.blit(img, (start_x_left, y_pos))
        
        # Draw black's captures (right side)
        label = font.render("Black captured:", True, (255, 255, 255))
        self.screen.blit(label, (start_x_right, start_y - 30))
        
        for i, piece in enumerate(self.black_captured):
            y_pos = start_y + (i * (piece_size + padding))
            img = pygame.transform.scale(piece.image, (piece_size - 5, piece_size + 10))
            self.screen.blit(img, (start_x_right, y_pos))
    
    # NEW: Draw undo button
    def draw_undo_button(self):
        """Draw the undo button"""
        if not self.move_history or self.current_turn != 'white' or self.game_over or self.promoting_pawn:
            self.undo_button_rect = None
            return
        
        button_width = 120
        button_height = 40
        button_x = self.screen_width // 2 - button_width // 2
        button_y = self.board_offset_y
        
        self.undo_button_rect = pygame.Rect(button_x + 500, button_y, button_width, button_height)
        
        # Draw button background
        pygame.draw.rect(self.screen, (70, 70, 70), self.undo_button_rect)
        pygame.draw.rect(self.screen, (200, 200, 200), self.undo_button_rect, 2)
        
        # Draw button text
        font = pygame.font.Font(None, 32)
        text = font.render("Undo", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.undo_button_rect.center)
        self.screen.blit(text, text_rect)
    
    def draw_promotion_dialog(self):
        """Draw the promotion selection dialog"""
        choices = ['queen', 'rook', 'bishop', 'knight']
        choice_width = 80
        choice_height = 80
        
        # Draw background
        dialog_width = len(choices) * choice_width + 40
        dialog_height = choice_height + 60
        dialog_x = self.screen_width // 2 - dialog_width // 2
        dialog_y = self.screen_height // 2 - dialog_height // 2
        
        pygame.draw.rect(self.screen, (50, 50, 50), (dialog_x, dialog_y, dialog_width, dialog_height))
        pygame.draw.rect(self.screen, (255, 255, 255), (dialog_x, dialog_y, dialog_width, dialog_height), 3)
        
        # Draw title
        font = pygame.font.Font(None, 32)
        text = font.render("Choose Promotion:", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.screen_width // 2, dialog_y + 20))
        self.screen.blit(text, text_rect)
        
        # Draw piece choices
        start_x = self.screen_width // 2 - (len(choices) * choice_width) // 2
        start_y = dialog_y + 50
        
        for i, piece_type in enumerate(choices):
            x = start_x + i * choice_width
            rect = pygame.Rect(x, start_y, choice_width, choice_height)
            pygame.draw.rect(self.screen, (100, 100, 100), rect)
            pygame.draw.rect(self.screen, (200, 200, 200), rect, 2)
            
            # Draw piece image
            prefix = 'W' if self.promoting_pawn.color == 'white' else 'B'
            img = pygame.image.load(f"assets/pieces/{prefix}_{piece_type.capitalize()}.png")
            img = pygame.transform.scale(img, (60, 70))
            self.screen.blit(img, (x + 10, start_y + 5))
    
    def run(self):
        """Main game loop"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and self.current_turn == 'white' \
                and not self.game_over:
                    if event.button == 1:
                        self.handle_click(event.pos)
                if self.current_turn == 'black' and not self.game_over:
                    self.draw()
                    #time.sleep(0.5)
                    ai = bot.AI(self, 'black')
                    ai.play(self)
            self.draw()
            self.clock.tick(60)
        pygame.quit()


def main():
    game = ChessGame()
    game.run()

main()