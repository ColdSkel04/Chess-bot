#!/usr/bin/env python3

class AI:

    def __init__(self, game, color):

        self.color = color
        self.enemy_color = self.get_enemy_color()
        self.whites = self.get_white_pieces(game)
        self.blacks = self.get_black_pieces(game)
        self.team = self.get_team(game)
        self.enemies = self.get_enemies(game)
        self.best_piece = None
        self.best_move = None
        self.value = self.get_value(game)
        self.priority = 0
        self.coverage = 0
        self.debug = "No debug."

    def get_white_pieces(self, game):

        white_pieces = []
        for row in range(8):
            for col in range(8):
                piece = game.board[row][col]
                if piece is not None and piece.color == 'white' and piece not in white_pieces:
                    white_pieces.append(piece)
        return white_pieces

    def get_black_pieces(self, game):

        black_pieces = []
        for row in range(8):
            for col in range(8):
                piece = game.board[row][col]
                if piece is not None and piece.color == 'black' and piece not in black_pieces:
                    black_pieces.append(piece)
        return black_pieces
    
    def get_value(self, game):

        if self.color == 'black':
            return game.get_value('black') - game.get_value('white')
        else:
            return game.get_value('white') - game.get_value('black')

    def get_cell_content(self, game, cell):

        for row in range(8):
            for col in range(8):
                if (row, col) == cell:
                    return game.board[row][col]
        return None

    def get_team(self, game):

        if self.color == 'black':
            return self.get_black_pieces(game)
        else:
            return self.get_white_pieces(game)
        
    def get_enemies(self, game):

        if self.color == 'black':
            return self.get_white_pieces(game)
        else:
            return self.get_black_pieces(game)
        
    def get_enemy_color(self):

        if self.color == 'black':
            return 'white'
        else:
            return 'black'
        
    def find_piece_to_help(self, game):

        best = None
        best_protection = 0
        reachable_team = []
        
        for piece in self.team:
            moves = game.get_legal_moves(piece)
            original_cell = piece.position
            for move in moves:
                original_content = self.get_cell_content(game, move)
                original_en_passant = game.en_passant_target
                if not self.is_move_safe(game, piece, move):
                    continue
                game.make_test_move(piece, move)
                new_moves = self.get_covering_moves(game, piece)
                for new_move in new_moves:
                    content = self.get_cell_content(game, new_move)
                    if content and content.color == self.color and content not in reachable_team:
                        reachable_team.append(content)
                game.make_test_move(piece, original_cell)
                game.board[move[0]][move[1]] = original_content
                game.en_passant_target = original_en_passant

        for piece in reachable_team:
            data = self.get_cell_data(game, piece.position)
            if best == None or data[3] - data[1] < best_protection or \
            (data[3] - data[1] <= best_protection and self.color == 'black' and \
            piece.position[0] > best.position[0]) or \
            (data[3] - data[1] <= best_protection and self.color == 'white' and \
            best and piece.position[0] < best.position[0]):
                best = piece
                best_protection = data[3] - data[1]
        return best

    def get_passive_move(self, game):

        self.priority = 0
        self.opening(game)
        self.mid_game(game)
        self.get_random_move(game)

    def opening(self, game):

        is_opening_done = True
        for piece in self.get_team(game):
            if not piece.has_moved and (piece.type == 'knight' or piece.type == 'bishop'):
                is_opening_done = False
                break
        if is_opening_done:
            return
        if game.turns <= 2:
            if game.board[4][3] != None or game.board[4][5] != None:
                self.best_piece = self.get_cell_content(game, (1, 3))
                self.best_move = (3, 3)
                return
            else:
                self.best_piece = self.get_cell_content(game, (1, 4))
                self.best_move = (3, 4)
                return
        for piece in self.get_team(game):
            moves = game.get_legal_moves(piece)
            for move in moves:
                if self.best_move and piece.type == 'pawn':
                    self.find_good_pawn_move(game, piece, move)
                if piece.type == 'knight':
                    self.find_good_knight_move(game, piece, move)
                if piece.type == 'bishop':
                    self.find_good_bishop_move(game, piece, move)
            
    def mid_game(self, game):

        if self.best_move:
            return
        vulnerable_piece = self.find_piece_to_help(game)
        for piece in self.team:
            if (piece.type == 'rook' and piece.has_moved == False) or (piece.type == 'king' 
            and piece.has_moved == False and not game.is_in_check(self.color)):
                continue
            moves = game.get_legal_moves(piece)
            for move in moves:
                if not self.is_move_safe(game, piece, move) or len(self.get_team(game)) <= 1:
                   continue
                if vulnerable_piece and self.will_move_help(game, piece, vulnerable_piece, move):
                    self.best_piece, self.best_move = piece, move
                    self.debug = "Pieces support themselves."

    def get_random_move(self, game):

        if self.best_move:
            return
        for piece in self.get_team(game):
            moves = game.get_legal_moves(piece)
            for move in moves:
                if self.is_move_safe(game, piece, move):
                    self.best_piece, self.best_move = piece, move
                    self.debug = "That was random but safe."
                    return
        # Last resort - any legal move
        for piece in self.get_team(game):
            moves = game.get_legal_moves(piece)
            if moves:
                self.best_piece, self.best_move = piece, moves[0]
                self.debug = "That was random."
                return

    def find_good_knight_move(self, game, piece, move):

        if (move[0] in [0, 7] or move[1] in [0, 7]):
            return
        for row in range(8):
            if piece.color == 'white' and move[0] < row:
                continue
            if piece.color == 'black' and move[0] > row:
                continue
            content = game.board[row][move[1]]
            #if not piece.has_moved or (content and content.type == 'pawn' and 
            #content.color == piece.color and self.priority < len(game.get_legal_moves(piece))):
            if not piece.has_moved:
                self.debug = "Knight covers more space."
                self.best_piece, self.best_move = piece, move
                self.priority = len(game.get_legal_moves(piece))
    
    def find_good_bishop_move(self, game, piece, move):

        covering = len(game.get_legal_moves(piece))
        prev_pos = piece.position
        prev_content = game.board[move[0]][move[1]]
        prev_en_passant = game.en_passant_target
                
        game.make_test_move(piece, move)
        new_covering = len(game.get_legal_moves(piece))
        if not piece.has_moved or (new_covering > covering and self.priority < new_covering):
            self.priority = new_covering
            self.best_piece, self.best_move = piece, move
            self.debug = "Bishop covers more space."
        game.make_test_move(piece, prev_pos)
        game.board[move[0]][move[1]] = prev_content
        game.en_passant_target = prev_en_passant

    def find_good_pawn_move(self, game, piece, move):

        vulnerable = self.find_piece_to_help(game)
        prev_cell = piece.position
        prev_content = self.get_cell_content(game, move)
        prev_coverage = 0
        coverage = 0
        prev_en_passant = game.en_passant_target

        if vulnerable and self.will_move_help(game, piece, vulnerable, move):
            self.best_piece, self.best_move = piece, move
            self.debug = "Pawn supports."
        for ally in self.get_team(game):
            if ally.type in ['knight', 'bishop']:
                prev_coverage += len(game.get_legal_moves(ally))
        game.make_test_move(piece, move)
        for ally in self.get_team(game):
            if ally.type in ['knight', 'bishop']:
                coverage += len(game.get_legal_moves(ally))
        if coverage > prev_coverage and coverage > self.coverage:
            self.best_piece, self.best_move = piece, move
            self.coverage = coverage
            self.debug = "Pawn opens space."
        game.make_test_move(piece, prev_cell)
        game.board[move[0]][move[1]] = prev_content
        game.en_passant_target = prev_en_passant
    
    def get_cell_data(self, game, cell):

        # rank 0: AMOUNT of enemies covering the cell (1 pawn + 1 rook = 2).
        # rank 1: VALUE of enemies covering the cell (1 pawn + 1 rook = 6).
        # rank 2-3: same thing but for allies.
        # rank 4-5: VALUE of the weakest enemy / ally attacking the cell.

        data = [0, 0, 0, 0, 0, 0]

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

    def is_move_safe(self, game, piece, move):

        original_cell = piece.position
        original_content = self.get_cell_content(game, move)
        original_en_passant = game.en_passant_target
        safe = True

        game.make_test_move(piece, move)    
        data = self.get_cell_data(game, piece.position)
        if data[4] and (piece.value > data[4] or (piece.value >= data[4] and self.value < 0)):
            safe = False
        elif not (data[0] == 0 or (data[1] < data[3] and data[0] <= data[2]) or \
        (data[1] <= data[3] and data[0] <= data[2] and self.value >= 0)):
            safe = False
        game.make_test_move(piece, original_cell)
        game.board[move[0]][move[1]] = original_content
        game.en_passant_target = original_en_passant
        return safe
    
    def is_in_danger(self, game, piece):
        
        data = self.get_cell_data(game, piece.position)
        if data[4] and ((piece.value > data[4]) or (piece.value >= data[4] and self.value < 0)):
            return True
        if (data[0] == 0 or (data[1] < data[3] and data[0] <= data[2]) or \
        (data[1] <= data[3] and data[0] <= data[2] and self.value >= 0)):
            return False
        return True
    
    def will_move_protect(self, game, piece_moving, piece_defended, move):

        original_cell = piece_moving.position
        original_content = self.get_cell_content(game, move)
        original_en_passant = game.en_passant_target

        if not self.is_move_safe(game, piece_moving, move):
            return False
        game.make_test_move(piece_moving, move)
        data = self.get_cell_data(game, piece_defended.position)
        protected = False
        if data[4] and (piece_defended.value > data[4] or \
        (piece_defended.value >= data[4] and self.value < 0)):
            protected = False
        elif (data[0] == 0 or (data[1] < data[3] and data[0] <= data[2]) or \
        (data[1] <= data[3] and data[0] <= data[2] and self.value >= 0)):
            self.best_piece, self.best_move = piece_moving, move
            protected = True
            self.debug = "Helping a piece in danger."
        game.make_test_move(piece_moving, original_cell)
        game.board[move[0]][move[1]] = original_content
        game.en_passant_target = original_en_passant
        return protected
    
    def will_move_help(self, game, piece, piece_defended, move):

        original_cell = piece.position
        original_content = self.get_cell_content(game, move)
        original_data = self.get_cell_data(game, piece_defended.position)
        original_en_passant = game.en_passant_target

        game.make_test_move(piece, move)
        data = self.get_cell_data(game, piece_defended.position)
        helps = data[2] > original_data[2]
        game.make_test_move(piece, original_cell)
        game.board[move[0]][move[1]] = original_content
        game.en_passant_target = original_en_passant
        return helps

    def attack(self, game, piece, moves):

        for move in moves:
            if not self.is_move_safe(game, piece, move):
                continue
            content = self.get_cell_content(game, move)
            if content != None and content.value > self.priority:
                self.best_piece, self.best_move = piece, move
                self.priority = content.value
                self.debug = "Attack."
            self.look_for_fork(game, piece, move)

    def look_for_fork(self, game, piece, move):

        nb_targets = 0
        biggest_target = 0
        almost_biggest_target = 0
        prev_cell = piece.position
        prev_content = self.get_cell_content(game, move)
        prev_en_passant = game.en_passant_target

        game.make_test_move(piece, move)
        moves = game.get_legal_moves(piece)
        for target in moves:
            content = self.get_cell_content(game, target)
            if not content:
                continue
            value = content.value
            if content.type == 'king':
                value = 10
            if value > piece.value:
                nb_targets += 1
                if biggest_target and piece.value < value <= biggest_target:
                    almost_biggest_target = value
                if value > biggest_target:
                    biggest_target = value
                if nb_targets >= 2:
                    self.best_piece, self.best_move = piece, move
                    self.priority = almost_biggest_target
                    self.debug = "Fork."
        game.make_test_move(piece, prev_cell)
        game.board[move[0]][move[1]] = prev_content
        game.en_passant_target = prev_en_passant
    
    def play_king(self, game, piece, moves):

        for move in moves:
            if piece.has_moved == False and (move in [(0, 2), (0, 6), (7, 2), (7, 6)]):
                self.best_piece, self.best_move = piece, move
                self.debug = "Castling."
                break
    
    def duck(self, game, piece):

        for ally in self.get_team(game):
            moves = game.get_legal_moves(ally)
            for move in moves:
                if ally.type == 'knight' and (move[0] in [0, 7] or move[1] in [0, 7]):
                    continue
                if self.will_move_protect(game, ally, piece, move):
                    self.best_piece, self.best_move = ally, move
                    self.priority = piece.value
                    self.debug = "Ducking."
                    return
                
    def look_for_checkmate(self, game):

        enemy_safe = False
        for piece in self.get_team(game):
            original_cell = piece.position
            moves = game.get_legal_moves(piece)
            for move in moves:
                original_content = self.get_cell_content(game, move)
                original_en_passant = game.en_passant_target
                game.make_test_move(piece, move)
                if not game.is_in_check(self.enemy_color):
                    game.make_test_move(piece, original_cell)
                    game.board[move[0]][move[1]] = original_content
                    game.en_passant_target = original_en_passant
                    continue
                enemy_safe = False
                for enemy in self.get_enemies(game):
                    moves_en = game.get_legal_moves(enemy)
                    if len(moves_en) != 0:
                        enemy_safe = True
                        break
                if enemy_safe == False:
                    game.make_test_move(piece, original_cell)
                    game.board[move[0]][move[1]] = original_content
                    game.en_passant_target = original_en_passant
                    self.best_piece, self.best_move = piece, move
                    self.debug = "Checkmate found."
                    return
                game.make_test_move(piece, original_cell)
                game.board[move[0]][move[1]] = original_content
                game.en_passant_target = original_en_passant
                    
    def play(self, game):

        can_checkmate = False
        self.look_for_checkmate(game)
        if self.best_piece:
            can_checkmate = True
        for piece in self.get_team(game):
            if can_checkmate:
                break
            if self.is_in_danger(game, piece) and piece.value > self.priority:
                self.duck(game, piece)
                self.priority = piece.value
            moves = game.get_legal_moves(piece)
            if piece.type == 'king':
                self.play_king(game, piece, moves)
            else:
                self.attack(game, piece, moves)
        if self.best_move == None:
            self.get_passive_move(game)
        if self.best_move == None:
            print("Error.")
            game.game_over = True
            game.winner = 'Player'
            return
        if self.best_piece.type == 'pawn' and self.best_move[0] in [0, 7]:
            self.best_piece.type = 'queen'
            self.best_piece.image = self.best_piece.load_image()
            self.best_piece.value = 9
        game.make_move(self.best_piece, self.best_move)
        print(self.debug)
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
        if piece.color == 'white':
            if col != 0:
                moves.append((row - 1, col - 1))
            if col != 7:
                moves.append((row - 1, col + 1))
        if piece.color == 'black':
            if col != 0:
                moves.append((row + 1, col - 1))
            if col != 7:
                moves.append((row + 1, col + 1))
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
        return self.get_rook_covers(game, row, col) + self.get_bishop_covers(game, row, col)
    
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