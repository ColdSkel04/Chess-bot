#!/usr/bin/env python3

import random
import torch
import torch.nn as nn
import pygame
import sys
from pathlib import Path

SQUARE_SIZE = 80
PIECE_WIDTH = 45
PIECE_HEIGHT = 75
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
RESET   = "\033[0m"


class AI_machine:

    def __init__(self, color = 'None'):

        self.reward = 0
        self.color = color
        return
    
    def get_allies(self, game):

        allies = []
        for row in range(8):
            for col in range(8):
                content = game.board[row][col]
                if content and content.color == game.current_turn:
                    allies.append(content)
        return allies
    
    def get_enemies(self, game):

        enemies = []
        for row in range(8):
            for col in range(8):
                content = game.board[row][col]
                if content and content.color != game.current_turn:
                    enemies.append(content)
        return enemies

    def get_all_moves(self, game, color):

        team = None
        moves = []
        if game.current_turn == color:
            team = self.get_allies(game)
        else:
            team = self.get_enemies(game)
        for piece in team:
            for move in game.get_legal_moves(piece):
                moves.append((piece, move))
        return moves
    
    def get_cell_content(self, game, cell):

        for row in range(8):
            for col in range(8):
                if (row, col) == cell:
                    return game.board[row][col]
        return None
    
    def play(self, game):

        net = ChessNet()

        if Path("chess_net.pth").exists():
            net.load_state_dict(torch.load("chess_net.pth"))
        moves = self.get_all_moves(game, self.color)
        best_score = -999
        best_move = None
        for piece, move in moves:
            game.make_move(piece, move)
            game.current_turn = self.color
            score = net(self.board_to_tensor(game)).item()
            game.undo_single_move(game.move_history[-1])
            game.move_history.pop()
            if score > best_score:
                best_score = score
                best_move = piece, move
        game.make_move(best_move[0], best_move[1])

    def board_to_tensor(self, game):
        
        board_array = []
        for row in range(8):
            for col in range(8):
                content = game.board[row][col]
                if content:
                    if content.color == 'white':
                        board_array.append(content.value)
                    else:
                        board_array.append(content.value * -1)
                else:
                    board_array.append(0)
        tensor = torch.tensor(board_array, dtype = torch.float32)
        if game.current_turn == 'white':
            return tensor
        return -tensor

    def choose_move(self, game, net, color, epsilon = 0.2):
        
        moves = self.get_all_moves(game, color)
        if random.random() < epsilon:
            return random.choice(moves)
        best_score = -999
        best_move = None
        for piece, move in moves:
            game.make_move(piece, move, check_game_over = False)
            score = net(self.board_to_tensor(game)).item()
            game.undo_single_move(game.move_history[-1])
            game.move_history.pop()
            if score > best_score:
                best_score = score
                best_move = piece, move
        return best_move

    def sim_game(self, game, net):

        winner = None
        memory = []

        while not game.game_over:
            state = self.board_to_tensor(game)
            memory.append(state)
            if not self.get_all_moves(game, game.current_turn):
                game.check_if_game_is_over()
                break
            piece, move = self.choose_move(game, net, game.current_turn)
            game.make_move(piece, move)
            game.turns += 1
        winner = game.winner    
        return memory, winner
    
    def sim_game_and_show(self, game, net):

        winner = None
        memory = []

        while not game.game_over:
            state = self.board_to_tensor(game)
            memory.append(state)
            if not self.get_all_moves(game, game.current_turn):
                game.check_if_game_is_over()
                break
            piece, move = self.choose_move(game, net, game.current_turn)
            game.make_move(piece, move)
            game.turns += 1
            game.draw()
        winner = game.winner
        return memory, winner
    
    def train_from_game(self, game, net, optimizer, states, reward):

        loss_fn = torch.nn.MSELoss()
        total_loss = 0
        discount = 0.99

        for i, state in enumerate(states):
            prediction = net(state)
            current_reward = reward if i % 2 == 0 else -reward
            current_reward = -current_reward if current_reward == 0.10 else current_reward
            discounted_reward = current_reward * (discount ** (len(states) - i - 1))
            target = torch.tensor([discounted_reward], dtype = torch.float32)
            total_loss += loss_fn(prediction, target)
        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()
        winner_name = "White" if game.winner == "white" else ("Black" if game.winner == "black" else "Draw")
        avg_loss = total_loss.item() / len(states)
        if winner_name == "White":
            print(f"{YELLOW}Winner: {winner_name:5}{RESET} ", end = "")
        elif winner_name == "Black":
            print(f"{BLUE}Winner: {winner_name:5}{RESET} ", end = "")
        else:
            print(f"Winner: {winner_name:5} ", end = "")
        print(f"| Moves: {len(states):3} | Total Loss: {total_loss.item():6.2f} | Avg Loss/Move: {avg_loss:4.2f} | Ending: {game.ending:18.18s}")

    def game_reward(self, winner):

        if winner == 'white':
            self.reward += 1
        if winner == 'black':
            self.reward -= 1
        if winner == 'nobody':
            self.reward -= 0.3

    def training_loop(self, game, net, optimizer):

        states, winner = self.sim_game(game, net)
        self.game_reward(winner)
        self.train_from_game(game, net, optimizer, states, self.reward)
        self.reward = 0
        game.reset()

    def training_loop_and_show(self, game, net, optimizer):

        states, winner = self.sim_game_and_show(game, net)
        self.game_reward(winner)
        self.train_from_game(game, net, optimizer, states, self.reward)
        self.reward = 0
        game.reset()
            
class ChessNet(nn.Module):

    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(64, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 1)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        return torch.tanh(self.fc3(x))

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
        new_row = row + direction
        if 0 <= new_row < 8 and board[new_row][col] is None:
            moves.append((new_row, col))
            if not self.has_moved:
                new_row2 = row + 2 * direction
                if 0 <= new_row2 < 8 and board[new_row2][col] is None and board[row + direction][col] is None:
                    moves.append((new_row2, col))
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

class ChessGameMachine:

    def __init__(self):
        
        self.show = self.show_training()
        self.current_turn = 'white'
        self.game_over = False
        self.winner = None
        self.last_move = None
        self.en_passant_target = None
        self.turns = 1
        self.ending = 'None.'
        
        # Move history for undo functionality
        self.move_history = []
        
        # Captured pieces tracking
        self.white_captured = []
        self.black_captured = []
        self.setup_board()

    def show_training(self):

        if len(sys.argv) > 1:
            pygame.init()
            info = pygame.display.Info()
            self.screen = pygame.display.set_mode((info.current_w, info.current_h))
            pygame.display.set_caption("Bot training")
            self.clock = pygame.time.Clock()
            self.screen_width = info.current_w
            self.screen_height = info.current_h
            self.board_offset_x = (self.screen_width - SQUARE_SIZE * 8) // 2
            self.board_offset_y = (self.screen_height - SQUARE_SIZE * 8) // 2
            return True
        return False
    
    def setup_board(self):

        self.board = [[None for i in range(8)] for i in range(8)]

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

        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.type == 'king' and piece.color == color:
                    return (row, col)
        return None
    
    def is_square_attacked(self, position, by_color):
        
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

        king_pos = self.find_king(color)
        if not king_pos:
            return False
        opponent_color = 'black' if color == 'white' else 'white'
        return self.is_square_attacked(king_pos, opponent_color)
    
    def would_be_in_check(self, piece, new_pos):

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

        x, y = pos
        col = (x - self.board_offset_x) // SQUARE_SIZE
        row = (y - self.board_offset_y) // SQUARE_SIZE
        
        if 0 <= row < 8 and 0 <= col < 8:
            return (row, col)
        return None
    
    def check_if_game_is_over(self):

        checkmate = True
        blacks = self.get_black_pieces()
        whites = self.get_white_pieces()

        if self.turns >= 250:
            self.winner = 'nobody'
            self.game_over = True
            self.ending = 'Max turns reached.'
            return
        for piece in blacks:
            if len(self.get_legal_moves(piece)) != 0:
                checkmate = False
                break
        if checkmate and self.is_in_check('black'):
            self.winner = 'white'
            self.game_over = True
            self.ending = 'White won.'
            return
        if checkmate and not self.is_in_check('black'):
            self.winner = 'nobody'
            self.game_over = True
            self.ending = 'Stalemate.'
            return
        checkmate = True
        for piece in whites:
            if len(self.get_legal_moves(piece)) != 0:
                checkmate = False
                break
        if checkmate and self.is_in_check('white'):
            self.winner = 'black'
            self.game_over = True
            self.ending = 'Black won.'
            return
        if checkmate and not self.is_in_check('white'):
            self.winner = 'nobody'
            self.game_over = True
            self.ending = 'Stalemate.'
            return
        for piece in whites:
            if piece.type in ['pawn', 'rook', 'queen'] or (piece.type == 'bishop' and len(whites) >= 3):
                return
        for piece in blacks:
            if piece.type in ['pawn', 'rook', 'queen'] or (piece.type == 'bishop' and len(blacks) >= 3):
                return
        self.winner = 'nobody'
        self.game_over = True
        self.ending = 'Lack of material.'
    
    def make_move(self, piece, new_pos, check_game_over = True):

        old_row, old_col = piece.position
        new_row, new_col = new_pos
        
        # Save move state for undo
        move_data = {
            'piece': piece,
            'old_pos': (old_row, old_col),
            'new_pos': new_pos,
            'captured': self.board[new_row][new_col],
            'had_moved': piece.has_moved,
            'en_passant_target': self.en_passant_target,
            'castling_rook': None,
            'castling_rook_old_pos': None,
            'castling_rook_had_moved': None,
            'en_passant_captured': None,
            'en_passant_captured_pos': None,
            'promotion_from': None
        }

        # Handle castling
        if piece.type == 'king' and abs(new_col - old_col) == 2 and not piece.has_moved:
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
            
            # Track captured piece
            if piece.color == 'white':
                self.white_captured.append(captured_pawn)
            else:
                self.black_captured.append(captured_pawn)
        
        # Track regular captures
        if self.board[new_row][new_col]:
            if piece.color == 'white':
                self.white_captured.append(self.board[new_row][new_col])
            else:
                self.black_captured.append(self.board[new_row][new_col])
        
        # Move the piece
        self.board[old_row][old_col] = None
        self.board[new_row][new_col] = piece
        piece.position = new_pos
        piece.has_moved = True
        
        # Set en passant target
        if piece.type == 'pawn' and abs(new_row - old_row) == 2:
            direction = -1 if piece.color == 'white' else 1
            self.en_passant_target = (old_row + direction, old_col)
        else:
            self.en_passant_target = None
        
        self.last_move = ((old_row, old_col), new_pos)
        
        # Check for pawn promotion
        if piece.type == 'pawn' and (new_row == 0 or new_row == 7):
            piece.type = 'queen'
            piece.image = piece.load_image()
            piece.value = 9
            move_data['promotion_from'] = 'pawn'
            move_data['promoted_to'] = 'queen'

        # Save move to history
        self.move_history.append(move_data)
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        if check_game_over:
            self.check_if_game_is_over()
    
    def undo_single_move(self, move_data):

        piece = move_data['piece']
        old_pos = move_data['old_pos']
        new_pos = move_data['new_pos']
        captured = move_data['captured']
        
        # Handle promotion undo
        if move_data['promotion_from']:
            piece.type = move_data['promotion_from']
            piece.image = piece.load_image()
            piece.value = piece.get_value()
        
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
        self.game_over = False
        self.winner = None
        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
    
    def draw(self):

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
        
        # Draw pieces
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    x = self.board_offset_x + col * SQUARE_SIZE + (SQUARE_SIZE - PIECE_WIDTH) // 2
                    y = self.board_offset_y + row * SQUARE_SIZE + (SQUARE_SIZE - PIECE_HEIGHT) // 2
                    self.screen.blit(piece.image, (x, y))

        font = pygame.font.Font(None, 48)
        if self.game_over:
            if self.winner == 'white':
                text = font.render(f"GAME OVER! White Wins!", True, (255, 50, 50))
            elif self.winner == 'black':
                text = font.render(f"GAME OVER! Black Wins!", True, (255, 50, 50))
            else:
                text = font.render(f"GAME OVER! Nobody Wins!", True, (255, 50, 50))
            text_rect = text.get_rect(center=(self.screen_width // 2, self.board_offset_y - 60))
            
            bg_rect = text_rect.inflate(40, 20)
            pygame.draw.rect(self.screen, (0, 0, 0), bg_rect)
            pygame.draw.rect(self.screen, (255, 50, 50), bg_rect, 3)
            
            self.screen.blit(text, text_rect)
        else:
            if self.current_turn == 'white':
                turn_text = "White's Turn"
            else:
                turn_text = "Black's Turn"
            if self.is_in_check(self.current_turn):
                turn_text += " - CHECK!"
            text = font.render(turn_text, True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen_width // 2, self.board_offset_y - 50))
            self.screen.blit(text, text_rect)
        pygame.display.flip()
    
    def draw_captured_pieces(self):

        start_x_left = self.board_offset_x - 250
        start_y = self.board_offset_y
        font = pygame.font.Font(None, 28)
        label = font.render("White's value: " + str(self.get_value('white') - self.get_value('black')), True, (255, 255, 255))
        self.screen.blit(label, (start_x_left, start_y - 80))
    
    def reset(self):

        self.current_turn = 'white'
        self.game_over = False
        self.winner = None
        self.turns = 1
        self.ending = 'None.'
        self.move_history = []
        self.white_captured = []
        self.black_captured = []
        self.setup_board()

    def run_training(self):

        ai = AI_machine()
        net = ChessNet()
        optimizer = torch.optim.Adam(net.parameters(), lr = 0.0001)
        if Path("chess_net.pth").exists():
            net.load_state_dict(torch.load("chess_net.pth"))
        episode = 0

        while True:
            ai.training_loop(self, net, optimizer)
            episode += 1
            if episode % 50 == 0:
                torch.save(net.state_dict(), "chess_net.pth")
                print(f"{RED}Episode {episode} completed{RESET}")

    def run_and_show(self):

        ai = AI_machine()
        net = ChessNet()
        optimizer = torch.optim.Adam(net.parameters(), lr = 0.0001)
        if Path("chess_net.pth").exists():
            net.load_state_dict(torch.load("chess_net.pth"))
        episode = 0

        while True:
            self.draw()
            ai.training_loop_and_show(self, net, optimizer)
            episode += 1
            if episode % 50 == 0:
                torch.save(net.state_dict(), "chess_net.pth")
                print(f"{RED}Episode {episode} completed.{RESET}")
            self.clock.tick(60)

def main_training():

    game = ChessGameMachine()
    if game.show:
        game.run_and_show()
    else:
        game.run_training()

if sys.argv[0] == './machine.py':
    main_training()