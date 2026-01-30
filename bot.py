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
        self.best_coverage = 0
        self.coverage = 0
        self.debug = 'No debug.'
        self.phase = self.set_phase(game)

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
            return game.blacks_value
        else:
            return game.whites_value

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
        
    def set_phase(self, game):
        
        for piece in self.get_team(game):
            if piece.type in ['king', 'bishop', 'knight'] and not piece.has_moved:
                return 'opening'
        return 'middle'
        
    def find_piece_to_help(self, game):

        best = None
        best_protection = 0
        reachable_team = []
        
        for piece in self.team:
            moves = game.get_legal_moves(piece)
            original_cell = piece.position
            for move in moves:
                original_content = self.get_cell_content(game, move)
                content = self.get_cell_content(game, move)
                if not self.is_move_safe(game, piece, move):
                    continue
                game.make_test_move(piece, move)
                new_moves = self.get_covering_moves(game, piece)
                for new_move in new_moves:
                    content = self.get_cell_content(game, new_move)
                    if content and content.color == self.color and \
                    content not in reachable_team:
                        reachable_team.append(content)
                game.make_test_move(piece, original_cell)
                game.board[move[0]][move[1]] = original_content

        for piece in reachable_team:
            data = self.get_cell_data(game, piece.position)
            if best == None or data[3] - data[1] < best_protection or \
            (data[3] - data[1] <= best_protection and self.color == 'black' and \
            piece.position[0] > best.position[0]) or \
            (data[3] - data[1] <= best_protection and self.color == 'white' and \
            piece.position[0] < self.best_piece.position[0]):
                best = piece
                best_protection = data[3] - data[1]
        return best

    def get_passive_move(self, game):
        
        self.priority = 0
        self.opening(game)
        self.mid_game(game)
        self.get_random_move(game)
    
    def opening(self, game):

        if self.phase != 'opening':
            return
        if game.turns <= 2:
            if game.board[4][3] != None or game.board[4][5] != None:
                self.best_piece = self.get_cell_content(game, (1, 3))
                self.best_move = (3, 3)
                self.debug = 'First move.'
                return
            else:
                self.best_piece = self.get_cell_content(game, (1, 4))
                self.best_move = (3, 4)
                self.debug = 'First move.'
                return
        for piece in self.get_team(game):
            if piece.has_moved or piece.type == 'queen':
                continue
            moves = game.get_legal_moves(piece)
            for move in moves:
                if not self.is_move_safe(game, piece, move):
                    continue
                if not self.best_move and piece.type == 'pawn' and self.priority <= 1:
                    self.find_good_pawn_move(game, piece, move)
                if piece.type == 'knight':
                    self.find_good_knight_move(game, piece, move)
                if piece.type == 'bishop':
                    self.find_good_bishop_move(game, piece, move)
        if self.best_move:
            return
        for piece in self.get_team(game):
            if piece.type != 'pawn':
                continue
            moves = game.get_legal_moves(piece)
            for move in moves:
                if self.is_move_safe(game, piece, move):
                    self.best_piece, self.best_move = piece, move
                    self.debug = 'Random pawn move.'
            
    def mid_game(self, game):

        if self.phase != 'middle':
            return
        vulnerable_piece = self.find_piece_to_help(game)
        if self.best_move or not vulnerable_piece:
            return
        for piece in self.team:
            if piece.type != 'pawn' and game.turns <= 6:
                continue
            if (piece.type == 'rook' and piece.has_moved == False) or (piece.type == 'king' 
            and piece.has_moved == False and not game.is_in_check(self.color)):
                continue
            moves = game.get_legal_moves(piece)
            for move in moves:
                if not self.is_move_safe(game, piece, move) or len(self.get_team(game)) <= 1:
                   continue
                if piece.type == 'rook':
                    self.find_good_rook_move(game, piece, move)
                if (self.will_move_help(game, piece, vulnerable_piece, move)) and \
                self.priority < vulnerable_piece.value:
                    self.best_piece, self.best_move = piece, move
                    self.priority = vulnerable_piece.value
                    self.debug = 'Supporting ' + vulnerable_piece.type + ' in ' + str(vulnerable_piece.position) + '.'

    def end_game(self, game):
        return

    def get_random_move(self, game):

        if self.best_move:
            return
        for piece in self.get_team(game):
            moves = game.get_legal_moves(piece)
            for move in moves:
                if self.is_move_safe(game, piece, move) and \
                len(game.get_legal_moves(piece)) > self.coverage:
                    self.best_piece, self.best_move = piece, move
                    self.coverage = len(game.get_legal_moves(piece))
                    self.debug = 'Doing a random but safe move.'
                    return
        for piece in self.get_team(game):
            moves = game.get_legal_moves(piece)
            for move in moves:
                self.best_piece, self.best_move = piece, move
                self.debug = 'Doing a completely random move.'

    def find_good_knight_move(self, game, piece, move):

        if (move[0] in [0, 7] or move[1] in [0, 7]):
            return
        for row in range(8):
            if piece.color == 'white' and move[0] < row:
                continue
            if piece.color == 'black' and move[0] > row:
                continue
            content = game.board[row][move[1]]
            if (content and content.type == 'pawn' and 
            content.color == piece.color and \
            self.coverage < len(self.get_covering_moves(game, piece))):
                self.best_piece, self.best_move = piece, move
                self.coverage = len(game.get_legal_moves(piece))
                self.priority = 3
                self.debug = 'Knight moves to cover more space.'
    
    def find_good_bishop_move(self, game, piece, move):

        covering = len(game.get_legal_moves(piece))
        prev_pos = piece.position
        prev_content = game.board[move[0]][move[1]]
        
        game.make_test_move(piece, move)
        new_covering = len(game.get_legal_moves(piece))
        if (new_covering > covering and self.coverage < new_covering):
            game.make_test_move(piece, prev_pos)
            game.board[move[0]][move[1]] = prev_content
            self.coverage = new_covering
            self.best_piece, self.best_move = piece, move
            self.debug = 'Bishop moves to cover more space.'
            self.priority = 3
        else:
            game.make_test_move(piece, prev_pos)
            game.board[move[0]][move[1]] = prev_content

    def find_good_pawn_move(self, game, piece, move):

        vulnerable = self.find_piece_to_help(game)
        prev_cell = piece.position
        prev_content = self.get_cell_content(game, move)
        prev_coverage = 0
        coverage = 0

        if vulnerable and self.will_move_help(game, piece, vulnerable, move):
            self.best_piece, self.best_move = piece, move
            self.priority = 1
            self.debug = 'Pawn supports ' + vulnerable.type + '.'
        for ally in self.get_team(game):
            if ally.type in ['knight', 'bishop']:
                prev_coverage += len(game.get_legal_moves(ally))
        game.make_test_move(piece, move)
        for ally in self.get_team(game):
            if ally.type in ['knight', 'bishop']:
                if ally.type == 'knight':
                    moves = game.get_legal_moves(ally)
                    for move in moves:
                        if move[0] in [0, 7] or move[1] in [0, 7]:
                            continue
                        else:
                            coverage += 1
                else:
                    coverage += len(game.get_legal_moves(ally))
        if coverage > prev_coverage and coverage > self.best_coverage:
            self.best_piece, self.best_move = piece, move
            self.best_coverage = coverage
            self.priority = 1
            self.debug = 'Pawn opens space for allies.'
        game.make_test_move(piece, prev_cell)
        game.board[move[0]][move[1]] = prev_content

    def find_good_rook_move(self, game, piece, move):

        coverage = len(game.get_legal_moves(piece))

        if coverage > self.coverage and self.priority < 5:
            self.coverage = coverage
            self.best_piece, self.best_move = piece, move
            self.priority = 5
            self.debug = 'Rook moving to cover more space.'

    def get_cell_data(self, game, cell):

        # rank 0: AMOUNT of enemies covering the cell (1 pawn + 1 rook = 2).
        # rank 1: VALUE of enemies covering the cell (1 pawn + 1 rook = 6).
        # rank 2-3: same thing but for allies.
        # rank 4-5: VALUE of the weakest enemy / ally attacking the cell.

        data = [0, 0, 0, 0, None, []]

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
        already_harmed = []

        game.make_test_move(piece, move)
        if original_content and (original_content.value > piece.value \
        or not self.is_in_danger(game, piece)):
            game.make_test_move(piece, original_cell)
            game.board[move[0]][move[1]] = original_content
            return True
        if self.can_enemy_checkmate(game):
            game.make_test_move(piece, original_cell)
            game.board[move[0]][move[1]] = original_content
            return False
        for ally in self.get_team(game):
            if self.is_in_danger(game, ally):
                already_harmed.append(ally)
        for ally in self.get_team(game):
            if self.is_in_danger(game, ally) and ally not in already_harmed:
                game.make_test_move(piece, original_cell)
                game.board[move[0]][move[1]] = original_content
                return False
        for enemy in self.get_enemies(game):
            moves = game.get_legal_moves(enemy)
            prev_cell = enemy.position
            for move_en in moves:
                prev_content = self.get_cell_content(game, move_en)
                game.make_test_move(enemy, move_en)
                if self.is_in_danger(game, piece):
                    game.make_test_move(enemy, prev_cell)
                    game.board[move_en[0]][move_en[1]] = prev_content
                    game.make_test_move(piece, original_cell)
                    game.board[move[0]][move[1]] = original_content
                    return False
                game.make_test_move(enemy, prev_cell)
                game.board[move_en[0]][move_en[1]] = prev_content
        if self.is_in_danger(game, piece):
            game.make_test_move(piece, original_cell)
            game.board[move[0]][move[1]] = original_content
            return False
        else:
            game.make_test_move(piece, original_cell)
            game.board[move[0]][move[1]] = original_content
            return True
    
    def is_in_danger(self, game, piece):

        data = self.get_cell_data(game, piece.position)
        if data[4] and (not data[2] or (piece.value > data[4]) or \
        (piece.value >= data[4] and self.value < 0)):
            return True
        if (data[0] == 0 or (data[0] <= data[2]) or \
        (data[0] <= data[2] and self.value >= 0) or \
        (data[5] < data[4])):
            return False
        return True
    
    def will_move_protect(self, game, piece_moving, piece_defended, move):

        original_cell = piece_moving.position
        original_content = self.get_cell_content(game, move)

        game.make_test_move(piece_moving, move)
        if self.is_in_danger(game, piece_defended):
            game.make_test_move(piece_moving, original_cell)
            game.board[move[0]][move[1]] = original_content
            return False
        game.make_test_move(piece_moving, original_cell)
        game.board[move[0]][move[1]] = original_content
        return True
    
    def will_move_help(self, game, piece, piece_defended, move):

        original_cell = piece.position
        original_content = self.get_cell_content(game, move)
        original_data = self.get_cell_data(game, piece_defended.position)

        game.make_test_move(piece, move)
        data = self.get_cell_data(game, piece_defended.position)
        if data[2] > original_data[2]:
            game.make_test_move(piece, original_cell)
            game.board[move[0]][move[1]] = original_content
            return True
        else:
            game.make_test_move(piece, original_cell)
            game.board[move[0]][move[1]] = original_content
            return False

    def attack(self, game, piece, moves):

        for move in moves:
            content = self.get_cell_content(game, move)
            data = self.get_cell_data(game, piece.position)
            if content and piece.type == 'pawn' and content.type == 'pawn' \
            and not self.priority and data[5] == 1:
                self.best_piece, self.best_move = piece, move
                self.priority = 1
                self.debug = 'Pawn attacks to prevent another attack.'
            if not self.is_move_safe(game, piece, move) and \
            content and content.value <= piece.value:
                continue
            if content and content.value > self.priority:
                self.best_piece, self.best_move = piece, move
                self.priority = content.value
                self.debug = 'Attacking ' + content.type + '.'
            if self.is_move_safe(game, piece, move):
                self.look_for_fork(game, piece, move)

    def look_for_fork(self, game, piece, move):

        nb_targets = 0
        biggest_target = 0
        almost_biggest_target = 0
        prev_cell = piece.position
        prev_content = self.get_cell_content(game, move)

        game.make_test_move(piece, move)
        moves = game.get_legal_moves(piece)
        for target in moves:
            content = self.get_cell_content(game, target)
            if not content:
                continue
            value = content.value
            if content.type == 'king':
                value = 10
            if value > piece.value or self.is_move_safe(game, piece, target):
                nb_targets += 1
                if biggest_target and value <= biggest_target:
                    almost_biggest_target = value
                if value > biggest_target:
                    biggest_target = value
                if nb_targets >= 2 and self.priority < almost_biggest_target:
                    self.best_piece, self.best_move = piece, move
                    self.priority = almost_biggest_target
                    self.debug = 'Doing a fork to pieces of value ' + str(biggest_target) + ' and ' + str(almost_biggest_target) + '.'
        game.make_test_move(piece, prev_cell)
        game.board[move[0]][move[1]] = prev_content
    
    def play_king(self, game, piece, moves):

        for move in moves:
            if piece.has_moved == False and (move in [(0, 2), (0, 6), (7, 2), (7, 6)]):
                self.best_piece, self.best_move = piece, move
                self.priority = 0.5
                self.debug = 'Putting king in safety.'
                break
    
    def duck(self, game, piece):

        doomed = True
        for ally in self.get_team(game):
            moves = game.get_legal_moves(ally)
            for move in moves:
                if ally.type == 'king' and not ally.has_moved:
                    continue
                if not self.is_move_safe(game, ally, move):
                    continue
                if ally.type == 'knight' and (move[0] in [0, 7] or move[1] in [0, 7]):
                    continue
                if self.will_move_protect(game, ally, piece, move):
                    content = self.get_cell_content(game, move)
                    if content and self.priority < piece.value + content.value:
                        self.priority = piece.value + content.value
                        self.debug =  piece.type + ' in danger, attacking.'
                        self.best_piece, self.best_move = ally, move
                        doomed = False
                    elif self.priority < piece.value:
                        self.priority = piece.value
                        self.debug = piece.type + ' in danger, trying to help it.'
                        self.best_piece, self.best_move = ally, move
                        doomed = False
        if doomed:
            moves = game.get_legal_moves(piece)
            for move in moves:
                content = self.get_cell_content(game, move)
                if content and content.value > self.priority:
                    self.best_piece, self.best_move = piece, move
                    self.priority = content.value
                    self.debug = piece.type + ' doomed, sacrificing it.'
                
    def check_promote(self, game, piece):

        if piece.type != 'pawn':
            return
        if piece.color == 'black' and piece.position[0] != 6:
            return
        if piece.color == 'white' and piece.position[0] != 1:
            return
        moves = game.get_legal_moves(piece)
        for move in moves:
            if self.is_move_safe(game, piece, move) and self.priority < 9:
                self.best_piece, self.best_move = piece, move
                self.priority = 9

    def can_enemy_checkmate(self, game):

        for piece in self.get_enemies(game):
            original_cell = piece.position
            moves = game.get_legal_moves(piece)
            for move in moves:
                original_content = self.get_cell_content(game, move)
                game.make_test_move(piece, move)
                if not game.is_in_check(self.color):
                    game.make_test_move(piece, original_cell)
                    game.board[move[0]][move[1]] = original_content
                    continue
                for team in self.get_team(game):
                    moves_team = game.get_legal_moves(team)
                    if len(moves_team) != 0:
                        team_safe = True
                        break
                if team_safe == False:
                    game.make_test_move(piece, original_cell)
                    game.board[move[0]][move[1]] = original_content
                    return True
                game.make_test_move(piece, original_cell)
                game.board[move[0]][move[1]] = original_content
        return False

    def look_for_checkmate(self, game):

        enemy_safe = False
        team_safe = False

        for piece in self.get_team(game):
            original_cell = piece.position
            moves = game.get_legal_moves(piece)
            for move in moves:
                original_content = self.get_cell_content(game, move)
                game.make_test_move(piece, move)
                if not game.is_in_check(self.enemy_color):
                    game.make_test_move(piece, original_cell)
                    game.board[move[0]][move[1]] = original_content
                    continue
                for enemy in self.get_enemies(game):    
                    moves_en = game.get_legal_moves(enemy)
                    if len(moves_en) != 0:
                        enemy_safe = True
                        break
                if enemy_safe == False:
                    game.make_test_move(piece, original_cell)
                    game.board[move[0]][move[1]] = original_content
                    self.best_piece, self.best_move = piece, move
                    self.debug = 'Found checkmate.'
                    return
                game.make_test_move(piece, original_cell)
                game.board[move[0]][move[1]] = original_content

        for piece in self.get_enemies(game):
            original_cell = piece.position
            moves = game.get_legal_moves(piece)
            for move in moves:
                original_content = self.get_cell_content(game, move)
                game.make_test_move(piece, move)
                if not game.is_in_check(self.color):
                    game.make_test_move(piece, original_cell)
                    game.board[move[0]][move[1]] = original_content
                    continue
                for enemy in self.get_team(game):
                    moves_en = game.get_legal_moves(enemy)
                    if len(moves_en) != 0:
                        team_safe = True
                        break
                if team_safe == False:
                    game.make_test_move(piece, original_cell)
                    game.board[move[0]][move[1]] = original_content
                    self.best_piece, self.best_move = piece, move
                    self.debug = 'Avoiding checkmate.'
                game.make_test_move(piece, original_cell)
                game.board[move[0]][move[1]] = original_content
                    
    def play(self, game):

        can_checkmate = False

        self.look_for_checkmate(game)
        if self.best_piece:
            can_checkmate = True
        for piece in self.get_team(game):
            if can_checkmate:
                break
            if self.is_in_danger(game, piece):
                self.duck(game, piece)
            moves = game.get_legal_moves(piece)
            if piece.type == 'king' and self.priority == 0:
                self.play_king(game, piece, moves)
            else:
                self.attack(game, piece, moves)
        if self.best_move == None and not can_checkmate:
            self.get_passive_move(game)
        if not self.best_move or not self.best_piece:
            print("Error.")
            game.game_over = True
            game.winner = 'Player'
            return
        game.make_move(self.best_piece, self.best_move)
        self.debug += ' Phase: ' + str(self.phase) + '.'
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

# Don't know how to checkmate in endgames.
# Don't understand pieces behing others.
