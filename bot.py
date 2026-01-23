#!/usr/bin/env python3

class AI:

    def __init__(self, game, color):

        self.color = color
        self.whites = self.get_white_pieces(game)
        self.blacks = self.get_black_pieces(game)
        self.team = self.get_team(self.color, self.whites, self.blacks)
        self.best_piece = None
        self.best_move = None

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

    def get_random_move(self, game, team):
        
        if game.turns <= 2 and self.color == 'black' and game.board[4][3] == None:
            self.best_piece = self.get_cell_content(game, (1, 4))
            self.best_move = (3, 4)
            return
        if game.turns <= 2 and self.color == 'black' and game.board[4][3] != None:
            self.best_piece = self.get_cell_content(game, (1, 3))
            self.best_move = (3, 3)
            return
        for piece in team:
            moves = game.get_legal_moves(piece)
            for move in moves:
                self.best_piece = piece
                self.best_move = move
                return

    def get_cell_data(self, game, cell):

        # rank 0 is AMOUNT of enemies covering the cell, 
        # rank 1 the VALUE of enemies covering it (1 for pawns, 5 for rooks...)
        # rank 2-3 is the same but for allies.

        data = [0, 0, 0, 0]

        for row in range(8):
            for col in range(8):
                piece = game.board[row][col]
                if piece == None:
                    continue
                moves = game.get_legal_moves(piece)
                if piece.type == 'pawn' and piece.color == 'black':
                    if (row + 1, col) in moves:
                        moves.remove((row + 1, col))
                    if (row + 2, col) in moves:
                        moves.remove((row + 2, col))
                    if 0 < col:
                        moves.append((row + 1, col - 1))
                    if 7 > col:
                        moves.append((row + 1, col + 1))
                if piece.type == 'pawn' and piece.color == 'white':
                    if (row - 1, col) in moves:
                        moves.remove((row - 1, col))
                    if (row - 2, col) in moves:
                        moves.remove((row - 2, col))
                    if 0 < col:
                        moves.append((row - 1, col - 1))
                    if 7 > col:
                        moves.append((row - 1, col + 1))
                for move in moves:
                    if move == cell:
                        if piece.color == self.color:
                            data[2] += 1
                            if piece.type == 'pawn':
                                data[3] += 1
                            if piece.type == 'knight':
                                data[3] += 3
                            if piece.type == 'bishop':
                                data[3] += 3
                            if piece.type == 'rook':
                                data[3] += 5
                            if piece.type == 'queen':
                                data[3] += 9
                        if piece.color != self.color:
                            data[0] += 1
                            if piece.type == 'pawn':
                                data[1] += 1
                            if piece.type == 'knight':
                                data[1] += 3
                            if piece.type == 'bishop':
                                data[1] += 3
                            if piece.type == 'rook':
                                data[1] += 5
                            if piece.type == 'queen':
                                data[1] += 9
        return data

    def play_pawn(self, game, piece, moves):

        for move in moves:
            if self.get_cell_content(game, move) != None:
                self.best_piece, self.best_move = piece, move

    def play_bishop(self, game, piece, moves):

        for move in moves:
            data = self.get_cell_data(game, move)
            if self.get_cell_content(game, move) != None and data[1] < data[3]:
                self.best_piece, self.best_move = piece, move

    def play_knight(self, game, piece, moves):

        for move in moves:
            data = self.get_cell_data(game, move)
            if self.get_cell_content(game, move) != None and data[1] < data[3]:
                self.best_piece, self.best_move = piece, move

    def play_rook(self, game, piece, moves):

        for move in moves:
            data = self.get_cell_data(game, move)
            if self.get_cell_content(game, move) != None and data[1] < data[3]:
                self.best_piece, self.best_move = piece, move

    def play_queen(self, game, piece, moves):

        for move in moves:
            data = self.get_cell_data(game, move)
            if self.get_cell_content(game, move) != None and data[1] < data[3]:
                self.best_piece, self.best_move = piece, move
    
    def play_king(self, game, piece, moves):

        for move in moves:
            if piece.has_moved == False and (move[1] == 6 or move[1] == 2):
                self.best_piece, self.best_move = piece, move
                break
        
    def play(self, game):

        for piece in self.team:
            moves = game.get_legal_moves(piece)
            if game.turns <= 2 and piece.type != 'pawn':
                continue
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
            self.get_random_move(game, self.team)
        game.make_move(self.best_piece, self.best_move)
        return