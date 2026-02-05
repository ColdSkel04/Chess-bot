#!/usr/bin/env python3

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

class AI:

    def __init__(self, game, color):

        self.color = color
        self.opponent_color = 'black' if color == 'white' else 'white'
        self.allies = self.get_allies(game)
        self.enemies = self.get_enemies(game)
        self.board = game.board
        self.history = []
        self.moves = self.get_all_moves(game)
        return
    
    def get_allies(self, game):

        allies = []
        for row in range(8):
            for col in range(8):
                content = game.board[row][col]
                if content and content.color == self.color:
                    allies.append(content)
        return allies
    
    def get_enemies(self, game):

        enemies = []
        for row in range(8):
            for col in range(8):
                content = game.board[row][col]
                if content and content.color != self.color:
                    enemies.append(content)
        return enemies

    def get_all_moves(self, game, color):

        team = None
        if self.color == color:
            team = self.get_allies(game)
        else:
            team = self.get_enemies(game)
        return team
        
    def sim_move(self, game, piece, move):

        moved = piece.has_moved
        extra = None
        content = game.board[move[0]][move[1]]

        if piece.type == 'king' and abs(piece.position[1] - move[1]) == 2 \
        and not piece.has_moved:
            extra = 'c'
            if piece.color == 'white':
                extra += 'w'
            else:
                extra += 'b'
            if move[1] == 6:
                extra += 'k'
            else:
                extra += 'q'
        if piece.type == 'pawn' and move[0] in [0, 7]:
            extra = 'p'
        if piece.type == 'pawn' and move[1] != piece.position[1] and \
        game.board[move[0]][move[1]] == None:
            extra = 'e'
        self.history.append([piece, piece.position, content, moved, extra])
        game.make_move(piece, move)

    def undo_moves(self, game, nb = 1):

        for nb in range(nb):
            action = self.history[nb]
            cur_pos = piece.position
            piece = action[0]
            prev_pos = action[1]
            content = action[2]
            moved = action[3]
            extra = action[4]

            game.make_move(piece, prev_pos)
            game.board[cur_pos[0]][cur_pos[1]] = content
            piece.has_moved = moved
            if extra == None:
                self.history.remove(action)
                return
            if extra == 'p':
                piece.type = 'pawn'
                piece.image = piece.load_image()
                piece.value = 1
            if extra[0] == 'c':
                if extra == 'cwk':
                    rook = game.board[7][5]
                    rook.position = (7, 7)
                    game.board[7][7] = rook
                    game.board[7][5] = None
                    rook.has_moved = False
                if extra == 'cwq':
                    rook = game.board[7][3]
                    rook.position = (7, 0)
                    game.board[7][0] = rook
                    game.board[7][3] = None
                    rook.has_moved = False
                if extra == 'cbk':
                    rook = game.board[0][5]
                    rook.position = (0, 7)
                    game.board[0][7] = rook
                    game.board[0][5] = None
                    rook.has_moved = False
                if extra == 'cbq':
                    rook = game.board[0][3]
                    rook.position = (0, 0)
                    game.board[0][0] = rook
                    game.board[0][3] = None
                    rook.has_moved = False
            if extra == 'e':
                if piece.color == 'white':
                    game.board[prev_pos[0]][cur_pos[1]] = piece
                    content = game.board[prev_pos[0]][cur_pos[1]]
                    content.color = 'black'
                if piece.color == 'black':
                    game.board[prev_pos[0]][cur_pos[1]] = piece
                    content = game.board[prev_pos[0]][cur_pos[1]]
                    content.color = 'white'
            self.history.remove(action)

    def board_to_array(game):
        
        tensor_board = []
        for row in range(8):
            for col in range(8):
                content = game.board[row][col]
                if content:
                    if content.color == 'white':
                        tensor_board.append(content.value)
                    else:
                        tensor_board.append(content.value * -1)
                else:
                    tensor_board.append(0)
        return tensor_board

    def play(self, game):

        # Load data
        net = ChessNet()
        net.load_state_dict(torch.load("chess_net.pth"))
        net.eval()

        # Train
        tensor = self.board_to_array(game)
        train_loader = DataLoader(tensor, batch_size = len(tensor) * 0.2, shuffle = True)
        model = ChessNet
        loss_fn = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr = 0.001)
        for epoch in range(3):
            tt_loss = 0
            for move in train_loader:
                outputs = model(move)
                loss = loss_fn(outputs) # Label?
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                tt_loss += loss.item()

        # Save
        torch.save(net.state_dict(), "chess_net.pth")
            
class ChessNet(nn.Module):

    def __init__(self, ai, game):
        super().__init__()
        nb_moves = len(ai.get_all_moves(game, ai.color))
        self.fc1 = nn.Linear(nb_moves, nb_moves * 0.5)
        self.fc2 = nn.Linear(nb_moves * 0.5, nb_moves * 0.25)
        self.fc3 = nn.Linear(nb_moves * 0.25, 1)

    def forward(self, x, ai, game):
        x = x.view(-1, len(ai.get_all_moves(game, ai.color)))
        x = torch.relu(self.fc1(x))
        x = self.fc3(x)
        return x

