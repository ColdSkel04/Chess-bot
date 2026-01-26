#!/usr/bin/env python3

class AI:

    def __init__(self, game, color):

        self.color = color
        self.whites = self.get_white_pieces(game)
        self.blacks = self.get_black_pieces(game)
        self.team = self.get_team(self.color, self.whites, self.blacks)
        self.best_piece = None
        self.best_move = None
        self.value = self.get_value(game)

    def get_white_pieces(self, game):

        white_pieces = []

        for row in range(8):
            for col in range(8):
                piece = game.board[row][col]
                if piece is not None and piece.color == 'white':
                    white_pieces.append(piece)
        return white_pieces

    def get_black_pieces(self, game):

        black_pieces = []

        for row in range(8):
            for col in range(8):
                piece = game.board[row][col]
                if piece is not None and piece.color == 'black':
                    black_pieces.append(piece)
        return black_pieces
    
    def get_value(self, game):

        if self.color == 'black':
            return game.blacks_value - game.whites_value
        else:
            return game.whites_value - game.blacks_value

    def get_cell_content(self, game, cell):

        for row in range(8):
            for col in range(8):
                if (row, col) == cell:
                    return game.board[row][col]
        return None

    def get_team(self, color, whites, blacks):

        if color == 'black':
            return blacks
        else:
            return whites

    def get_passive_move(self, game, team):
        
        if game.turns <= 2 and self.color == 'black' \
        and game.board[4][3] == None and game.board[4][5] == None:
            self.best_piece = self.get_cell_content(game, (1, 4))
            self.best_move = (3, 4)
            return
        if game.turns <= 2 and self.color == 'black':
            self.best_piece = self.get_cell_content(game, (1, 3))
            self.best_move = (3, 3)
            return
        for piece in team:
            if piece.type == 'rook' or (piece.type == 'king' and
            piece.has_moved == False and game.is_in_check(self.color) != True):
                continue
            moves = game.get_legal_moves(piece)
            for move in moves:
                self.best_piece = piece
                self.best_move = move
                return

    def get_covering_moves(self, game, piece):
        """Get moves without considering check and allies"""
        moves = []
        row, col = piece.position
        
        if piece.type == 'pawn':
            moves = self.get_pawn_covers(piece, row, col)
        elif piece.type == 'rook':
            moves = self.get_rook_covers(game, row, col)
        elif piece.type == 'knight':
            moves = self.get_knight_covers(row, col)
        elif piece.type == 'bishop':
            moves = self.get_bishop_covers(game, row, col)
        elif piece.type == 'queen':
            moves = self.get_queen_covers(game, row, col)
        elif piece.type == 'king':
            moves = self.get_king_covers(game, row, col)
        return moves
    
    def get_pawn_covers(self, piece, row, col):

        moves = []
        direction = -1 if piece.color == 'white' else 1

        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                moves.append((new_row, new_col))
        return moves
    
    def get_rook_covers(self, game, row, col):

        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + dr * i, col + dc * i
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                target = game.board[new_row][new_col]
                if target is None:
                    moves.append((new_row, new_col))
                elif target:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
        return moves
    
    def get_knight_covers(self, row, col):

        moves = []
        knight_moves = [
            (2, 1), (2, -1), (-2, 1), (-2, -1),
            (1, 2), (1, -2), (-1, 2), (-1, -2)
        ]
        
        for dr, dc in knight_moves:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                moves.append((new_row, new_col))
        return moves
    
    def get_bishop_covers(self, game, row, col):

        moves = []
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        
        for dr, dc in directions:
            for i in range(1, 8):
                new_row, new_col = row + dr * i, col + dc * i
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    break
                target = game.board[new_row][new_col]
                if target is None:
                    moves.append((new_row, new_col))
                elif target:
                    moves.append((new_row, new_col))
                    break
                else:
                    break
        return moves
    
    def get_queen_covers(self, game, row, col):
        return self.get_rook_covers(game, row, col) + \
        self.get_bishop_covers(game, row, col)
    
    def get_king_covers(self, game, row, col):

        moves = []
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                target = game.board[new_row][new_col]
                if target is None or target:
                    moves.append((new_row, new_col))
        return moves
    
    def get_cell_data(self, game, cell):

        # rank 0: AMOUNT of enemies covering the cell (1 pawn + 1 rook = 2).
        # rank 1: VALUE of enemies covering the cell (1 pawn + 1 rook = 6).
        # rank 2-3: same thing but for allies.
        # rank 4-5: VALUE of the weakest enemy / ally attacking the cell.

        data = [0, 0, 0, 0, None, None]

        for row in range(8):
            for col in range(8):
                piece = game.board[row][col]
                if piece == None:
                    continue
                moves = self.get_covering_moves(game, piece)
                for move in moves:
                    if move == cell:
                        if piece.color != self.color:
                            data[0] += 1
                            data[1] += piece.value
                            if not data[4] or piece.value < data[4]:
                                data[4] = piece.value
                        if piece.color == self.color:
                            data[2] += 1
                            data[3] += piece.value
                            if not data[5] or piece.value < data[5]:
                                data[5] = piece.value
        return data

    def is_safe_to_attack(self, game, piece, move):

        data = self.get_cell_data(game, move)
        if (data[0] == 0 or (data[1] < data[3] - piece.value and data[0] <= data[2]) or \
        (data[1] <= data[3] - piece.value and data[0] <= data[2] and self.value > 0)):
            return True
        return False
    
    def is_in_danger(self, game, piece):

        data = self.get_cell_data(game, piece.position)
        if data[4] and (piece.value > data[4] or \
        (piece.value >= data[4] and self.value < 0)):
            return True
        if (data[0] == 0 or (data[1] < data[3] and data[0] <= data[2]) or \
        (data[1] <= data[3] and data[0] <= data[2] and self.value >= 0)):
            return False
        return True
    
    def will_move_protect(self, game, piece_moving, piece_defended, move):

        original_cell = piece_moving.position
        original_content = self.get_cell_content(game, move)

        game.make_move(piece_moving, move)
        data = self.get_cell_data(game, piece_defended.position)
        if data[4] and (piece_defended.value > data[4] or \
        (piece_defended.value >= data[4] and self.value < 0)):
            game.make_move(piece_moving, original_cell)
            game.board[move[0]][move[1]] = original_content
            return False
        if (data[0] == 0 or (data[1] < data[3] and data[0] <= data[2]) or \
        (data[1] <= data[3] and data[0] <= data[2] and self.value >= 0)):
            game.make_move(piece_moving, original_cell)
            game.board[move[0]][move[1]] = original_content
            self.best_piece, self.best_move = piece_moving, move
            return True
        game.make_move(piece_moving, original_cell)
        game.board[move[0]][move[1]] = original_content
        return False

    def play_pawn(self, game, piece, moves):

        for move in moves:
            if self.get_cell_content(game, move) != None:
                self.best_piece, self.best_move = piece, move

    def play_bishop(self, game, piece, moves):

        for move in moves:
            if self.is_safe_to_attack(game, piece, move) == False:
                continue
            if self.get_cell_content(game, move) != None:
                self.best_piece, self.best_move = piece, move

    def play_knight(self, game, piece, moves):

        for move in moves:
            if self.is_safe_to_attack(game, piece, move) == False:
                continue
            if self.get_cell_content(game, move) != None:
                self.best_piece, self.best_move = piece, move

    def play_rook(self, game, piece, moves):

        for move in moves:
            if self.is_safe_to_attack(game, piece, move) == False:
                continue
            if self.get_cell_content(game, move) != None:
                self.best_piece, self.best_move = piece, move

    def play_queen(self, game, piece, moves):

        for move in moves:
            if self.is_safe_to_attack(game, piece, move) == False:
                continue
            if self.get_cell_content(game, move) != None:
                self.best_piece, self.best_move = piece, move
    
    def play_king(self, game, piece, moves):

        for move in moves:
            if piece.has_moved == False and (move in [(0, 2), (0, 6), (7, 2), (7, 6)]):
                self.best_piece, self.best_move = piece, move
                break
    
    def duck(self, game, piece):

        for ally in self.team:
            moves = game.get_legal_moves(ally)
            for move in moves:
                if self.will_move_protect(game, ally, piece, move):
                    self.best_piece, self.best_move = ally, move
                    return
                    
    def play(self, game):

        for piece in self.team:
            moves = game.get_legal_moves(piece)
            if self.is_in_danger(game, piece):
                self.duck(game, piece)
            if piece.type == 'pawn':
                self.play_pawn(game, piece, moves)
            if piece.type == 'bishop':
                self.play_bishop(game, piece, moves)
            if piece.type == 'knight':
                self.play_knight(game, piece, moves)
            if piece.type == 'rook':
                self.play_rook(game, piece, moves)
            if piece.type == 'queen':
                self.play_queen(game, piece, moves)
            if piece.type == 'king':
                self.play_king(game, piece, moves)
        if self.best_move == None:
            self.get_passive_move(game, self.team)
        game.make_move(self.best_piece, self.best_move)
        return
