#debugger

import requests
import json
import time
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--server', help='address:port of the server you connect to')
parser.add_argument('-g', '--game-id', help='a unique code used to join your game(you can make one up)')
parser.add_argument('-n', '--name', help='your display name in the game')
parser.add_argument('-p', '--players', help='amount of players. no need for that setting if you join an existing game')

args = parser.parse_args()              
         
address = args.server+'/'
game = args.game_id
player = args.name
players_count = int(args.players)
jarjar = {} #for session id

def send_create(game_name, player_name, players_count):
    r = requests.post(address+'create/'+game_name, data={'player_name':player_name,'players_count':players_count}, cookies=jarjar)
    return r

def send_join(game_name, player_name):
    r = requests.post(address+'join/'+game_name, data={'player_name':player_name}, cookies=jarjar)
    return r

def send_start(game_name):
    r = requests.get(address+'start/'+game_name, cookies=jarjar)
    return r

def send_status(game_name):
    r = requests.get(address+'status/'+game_name, cookies=jarjar)
    return r

def send_play(game_name, move_type, move_params):
    r = requests.post(address+'play/'+game_name, data={'move_type':move_type, 'move_params':move_params}, cookies=jarjar)
    return r


###test script for example usage of all functions
##a1 = send_create(game,player, 3)
##c1 = a1.cookies
##
##a2 = send_join(game,player+'1')
##c2 = a2.cookies
##
##a3 = send_join(game,player+'2')
##c3 = a3.cookies
##
##jarjar = c1
##send_start(game)
##
##q = send_status(game)
##status = json.loads(q.content.decode('utf-8'))
##print(status)
###will only work if it's this player's turn
##send_play(game, 'play', 0)
##send_play(game, 'hint', ['adm1','y'])
##send_play(game, 'discard', 0)

def nice_announce(move):
    q = move.split(':')
    if q[1]=='play':
        return '{} played {}'.format(q[0][2:-1],q[2])
    elif q[1]=='discard':
        return '{} discarded {}'.format(q[0][2:-1],q[2])
    elif q[1]=='hint':
        return '{} gave {} a hint: {} is in {}'.format(q[0][2:-1],q[2][2:-1],q[3],str(q[4]).replace('0','x').replace('1','v'))
    else:
        return 'wat???'
    
def print_status(status):
    #make this prettier with colors and stuff?
    print('Your fireworks:\n===========\n\tRed: {}\n\tGreen: {}\n\tBlue: {}\n\tYellow: {}\n\tWhite: {}\n\n'.format(status['board']['r'], status['board']['g'],
                                                                                                                   status['board']['b'], status['board']['y'], status['board']['w']))
    print('Discards:\n===========\n\tRed: {}\n\tGreen: {}\n\tBlue: {}\n\tYellow: {}\n\tWhite: {}\n\n'.format(','.join(status['discards']['r']), ','.join(status['discards']['g']),
                                                                                                                 ','.join(status['discards']['b']), ','.join(status['discards']['y']), ','.join(status['discards']['w'])))
    print('Hints remaining: {} \\ Fuse length: {} \\ Cards remaining: {}\nScore: {}\nLatest moves:\n\n{}'.format(status['hint_count'],status['fail_count'],status['deck'],status['score'],'\n'.join(nice_announce(i) for i in status['latest'])))

    hands = [i+': '+str(status['other_hands'][i]) for i in status['order']]
    print('\nPlayer hands:\n\n\t{}'.format('\n\t'.join(hands)))
    
r = send_create(game,player, players_count)
jarjar = r.cookies
if r.content == b'1':
    print('created game %s' % game)
    while 1:
        r = send_start(game)
        if r.content == b'1':
            break
        time.sleep(1)
        print('waiting for all players to join...')
        
else:
    r = send_join(game, player)
    if r.content == b'1':
        print('joined game %s' % game)
        while 1:
            r = send_status(game)
            if r.content != b'0':
                break
            time.sleep(1)
            print('waiting for all players to join...')
                
    else:
        print('failed to join game, bye:D')
        raise Exception('wtf lol')
    
turn = -1

while 1:
    r = send_status(game)
    status = json.loads(r.content.decode('utf-8'))
    if turn == status['turn']:
        time.sleep(1)
    else:
        print_status(status)
        turn = status['turn']
        current_player = status['order'][status['turn'] % len(status['order'])]
        while current_player == player:
            print('your turn!')
            try:
                move = input('>').split(' ')
                move_type = move[0]
                move_params = move[1:]
                r = send_play(game, move_type, move_params)
                if r.content == b'1':
                    break
                else:
                    print('you cannot do that!')
            except:
                print('wrong syntax:(\n\\tpossible options:\n\n\tplay <index> - plays the card at <index> from your hand\n\tdiscard <index> - discards the card at <index> from your hand\n\thint <player> <letter> - give a hint to <player>, <letter> is one of 1,2,3,4,5,r,g,b,w,y')
            
        


  
