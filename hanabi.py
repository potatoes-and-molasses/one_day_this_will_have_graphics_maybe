#hanabi.py
import random
import json

CARDS_PER_PLAYER = {3:5, 4:4, 5:4}

colors = ['r','g','b','y','w']
quantities = [3,2,2,2,1]
hint_count = 8
fail_count = 3

class deck:

    def __init__(self, colors=colors, quantities=quantities):
        cards = []
        for c in colors:
            for n,q in enumerate(quantities):
                cards = cards + [c+str(n+1) for i in range(q)]

        random.shuffle(cards)
        self.colors = colors
        self.quantities = quantities
        self.cards = cards
        
    def draw(self):
        if len(self.cards):
            return self.cards.pop()
        else:
            return None
            print('DEBUG:empty deck, cannot draw')

    def remaining(self):
        return len(self.cards)

class player:

    def __init__(self, nickname, uid):
        self.nickname = nickname
        self.uid = uid
        self.cards = []
        self.lastindex = 0

    def getcard(self, index):
        self.lastindex = index
        return self.cards.pop(index)

    def addcard(self, card):
        self.cards.insert(self.lastindex, card)
        
    def reposition(self, old_index, new_index):
        card = self.cards.pop(old_index)
        self.cards.insert(new_index, card)

    def where(self, ch):
        return [1 if ch in i else 0 for i in self.cards]

        
class game:

    def __init__(self, deck, players_list, hint_count=hint_count, fail_count=3):

        start_cards = CARDS_PER_PLAYER[len(players_list)]
        for p in players_list:
            for i in range(start_cards):
                p.addcard(deck.draw())

        self.deck = deck
        self.players_list = players_list
        random.shuffle(self.players_list)
        self.discards = {i:[] for i in self.deck.colors}
        self.playfield = {i:0 for i in self.deck.colors}
        self.hint_count = hint_count
        self.fail_count = fail_count
        self.score = 0
        self.turn = 0
        self.history = []

    def failed(self):
        if self.fail_count != 'KABOOM(you lost, but feel free to keep going)':
            self.fail_count -= 1
        if self.fail_count == 0:
            self.fail_count = 'KABOOM(you lost, but feel free to keep going)'
        
    def getopts(self, player):
        all_opts = self.deck.colors + [str(i+1) for i in range(len(self.deck.quantities))]
        d = {i:player.where(i) for i in all_opts}
        empty_opts = list(filter(lambda x: sum(d[x]) < 1, d))
        for i in empty_opts:
            d.pop(i)
            
        return d
        
    def move_discard(self, player, index):
        card = player.getcard(index)
        if card:
            print('DEBUG:{} discarded {}'.format(player.nickname, card))
            self.discards[card[0]].append(card)
            self.hint_count += 1
            self.turn += 1
            self.history.append('%s:discard:%s:%d' % (player.nickname, card, index))
        else:
            print('DEBUG:no card at that index')
            
        newcard = self.deck.draw()
        if newcard:
            player.addcard(newcard)
            print('DEBUG:{} drew {}'.format(player.nickname, newcard))
        else:
            print('DEBUG:no more cards to draw')

    def move_play(self, player, index):
        card = player.getcard(index)
        if card:
            print('DEBUG:{} played {}'.format(player.nickname, card))
            self.turn += 1
            self.history.append('%s:play:%s:%d' % (player.nickname, card, index))
            if self.playfield[card[0]] == int(card[1])-1:
                self.playfield[card[0]] += 1
                self.score += 1
                print('DEBUG:goodplay')
                if self.playfield[card[0]] == 5:
                    self.hint_count += 1
                    self.score += 1
                    print('DEBUG:full5 of{}!'.format(card[0]))
            else:
                self.fail()
                self.discards[card[0]].append(card)
                print('DEBUG:badplay')#maybe deduce a point for bad play, or maybe failing to discard and get a hint is punishment enough..
                if self.fail_count < 1:
                    print('DEBUG:gameoveralrdy')
        else:
            print('DEBUG:no card at that index')
            
        newcard = self.deck.draw()
        if newcard:
            player.addcard(newcard)
            print('DEBUG:{} drew {}'.format(player.nickname, newcard))
        else:
            print('DEBUG:no more cards to draw')
            
    def move_hint(self, src_player, dst_player, ch):
        if(self.hint_count > 0):
            opts = self.getopts(dst_player)
            if ch in opts:
                print('DEBUG:{} got hinted {} by {}'.format(dst_player.nickname, ch, src_player.nickname))
                print('DEBUG:results\n{}'.format(opts[ch]))
                self.hint_count -= 1
                self.turn += 1
                self.history.append('%s:hint:%s:%s:%s' % (src_player.nickname, dst_player.nickname, ch, opts[ch]))
                return 1
            else:
                print('DEBUG:{} cannot hint empty set')
                return -1
        else:
            print('DEBUG:no hints remaining')
                
        return 0

    
        
###example  
##mydeck = deck()
##p1 = player('player1',1)
##p2 = player('player2',2)
##p3 = player('player3',3)
##mygame = game(mydeck, [p1,p2,p3])
    
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.web import server, resource
import cgi

prep_area = {}#contains game names+#of players, queued players, once full game will be created & moved to started games.
ongoing_games ={}#contains started games

class JoinGame(Resource):
    #isLeaf = True
    def getChild(self, name, request):        
        return JoinSub(name)

##    def render_GET(self, request):
##        return b"init game route, access with either a game id to join an existing game or / to start a new one" % (request.prepath,request.postpath,request.session)

class JoinSub(Resource):
    isLeaf = True
    def __init__(self, name):
        Resource.__init__(self)
        if name == b'':
            game_id = b'default'
        else:
            game_id = name
        self.name = game_id


    def render_POST(self, request):
        user_id = request.getSession().uid
        player_name = request.args[b'player_name'][0]
        if self.name in prep_area:
            players_count = prep_area[self.name]['players_count']
            players_list = prep_area[self.name]['players_list']
            if player_name in players_list.values():
                print('DEBUG:player with that name already exists')
            else:
                if (user_id not in players_list) and (players_count > len(players_list)):
                    prep_area[self.name]['players_list'][user_id] = player_name
                    print('DEBUG:joining game %s as %s(uid:%s)' % (self.name, player_name, user_id))
                    return b'1'
                else:
                    print('DEBUG:%s already in game or game is full' % (user_id,))
        else:
            print('DEBUG:game with such name is not in prep area')

        return b'0'

class CreateGame(Resource):
    def getChild(self, name, request):        
        return CreateSub(name)

class CreateSub(Resource):
    isLeaf = True
    def __init__(self, name):
        Resource.__init__(self)
        if name == b'':
            game_id = b'default'
        else:
            game_id = name
        self.name = game_id

    def render_POST(self, request):
        user_id = request.getSession().uid
        player_name = request.args[b'player_name'][0]
        players_count = int(request.args[b'players_count'][0])
        if self.name in prep_area or self.name in ongoing_games:
            print('DEBUG:game already in prep_area or ongoing')
        else:
            prep_area[self.name] = {'players_count':players_count, 'players_list':{user_id:player_name}}
            print('game %s added to prep area with %s(%s) as user' % (self.name, player_name, user_id))
            return b'1'
        
        return b'0'

class StartGame(Resource):
    def getChild(self, name, request):        
        return StartSub(name)          

class StartSub(Resource):
    isLeaf = True
    def __init__(self, name):
        Resource.__init__(self)
        if name == b'':
            game_id = b'default'
        else:
            game_id = name
        self.name = game_id

    def render_GET(self, request):
        user_id = request.getSession().uid
        if self.name in prep_area:
            players_list = prep_area[self.name]['players_list']
            players_count = prep_area[self.name]['players_count']
            if user_id in players_list:
                if len(players_list) == players_count:
                    player_objects = [player(players_list[i], i) for i in players_list]
                    base_deck = deck()
                    game_obj = game(base_deck, player_objects)
                    ongoing_games[self.name] = {'game':game_obj, 'players_list':players_list}
                    prep_area.pop(self.name)
                    print('DEBUG: started game %s, removed from prep and added to ongoing' % (self.name, ))
                    return b'1'
                else:
                    print('DEBUG: players joined game: %d/%d' % (len(players_list), players_count))
            else:
                print('DEBUG:user attempted to start game he is not a part of')

        return b'0'

class GameStatus(Resource):
    def getChild(self, name, request):        
        return StatusSub(name)

class StatusSub(Resource):
    isLeaf = True
    def __init__(self, name):
        Resource.__init__(self)
        if name == b'':
            game_id = b'default'
        else:
            game_id = name
        self.name = game_id

    def render_GET(self, request):
        user_id = request.getSession().uid
        if self.name in ongoing_games:
            game_obj = ongoing_games[self.name]['game']
            players_list = ongoing_games[self.name]['players_list']
            if user_id in players_list:
                other_players = filter(lambda x: user_id != x.uid, game_obj.players_list)
                current_player = list(filter(lambda x: user_id == x.uid, game_obj.players_list))[0]
                other_hands = {}
                for player in other_players:
                    other_hands[player.nickname.decode('utf-8')] = player.cards

                other_hands[current_player.nickname.decode('utf-8')] = ['??' for i in current_player.cards]
                
                
                status_json = {'board':game_obj.playfield, 'discards':game_obj.discards, 'hint_count':game_obj.hint_count, 'fail_count':game_obj.fail_count,
                               'score':game_obj.score,'deck':game_obj.deck.remaining(), 'turn':game_obj.turn, 'order':[player.nickname.decode('utf-8') for player in game_obj.players_list], 'other_hands':other_hands, 'latest':game_obj.history[1-len(game_obj.players_list):]}
                
                return bytes(json.dumps(status_json),'utf-8')
                
            else:
                print('DEBUG:player not participating in this game')
        else:
            print('DEBUG:game not started')

        return b'0'
                
class PlayGame(Resource):
    def getChild(self, name, request):        
        return PlaySub(name)

class PlaySub(Resource):
    isLeaf = True
    def __init__(self, name):
        Resource.__init__(self)
        if name == b'':
            game_id = b'default'
        else:
            game_id = name
        self.name = game_id

    def render_POST(self, request):
        user_id = request.getSession().uid
        if self.name in ongoing_games:
            game_obj = ongoing_games[self.name]['game']
            players_list = ongoing_games[self.name]['players_list']
            if user_id in players_list:
                current_player_turn = game_obj.players_list[game_obj.turn % len(players_list)]
                if user_id == current_player_turn.uid:
                    move_type = request.args[b'move_type'][0]
                    move_params = request.args[b'move_params']
                    if move_type == b'play':
                        card_index = int(move_params[0])
                        try:
                            print('DEBUG:player %s played index %d' % (current_player_turn.nickname, card_index))
                            game_obj.move_play(current_player_turn, card_index)  
                            return b'1'
                        except:
                            print('DEBUG:illegal card index')

                    elif move_type == b'discard':
                        card_index = int(move_params[0])
                        try:
                            print('DEBUG:player %s discarded index %d' % (current_player_turn.nickname, card_index))
                            game_obj.move_discard(current_player_turn, card_index)
                            return b'1'
                        except:
                            print('DEBUG:illegal card index')

                    elif move_type == b'hint':
                        target_player_name = move_params[0]
                        hint_ch = move_params[1]
                        #add input checking xd
                        
                        target_player = list(filter(lambda x: x.nickname == target_player_name, game_obj.players_list))
                        if len(target_player) == 1:
                            target_player = target_player[0]
                            if target_player!=current_player_turn:
                            #maybe some shenans with byte/str in hint_ch
                                print('DEBUG:player %s hinted %s at player %s' % (current_player_turn.nickname, hint_ch, target_player.nickname))
                                res = game_obj.move_hint(current_player_turn, target_player, hint_ch.decode('utf-8'))
                                if res == -1:
                                    print('DEBUG:hint empty set?? not allowed')
                                    return b'0'
                                elif res == 0:
                                    print('DEBUG:not enough hints remaining')
                                    return b'0'
                                #otherwise hint was a legal move and its ok:)
                                return b'1'
                            else:
                                print('DEBUG:is someone stupid/smart enough to hint themselves?')
                        else:
                            print('DEBUG:no player with that name found')
                            
                        
                            
                        
                        
                        
                        
                else:
                    print('DEBUG:not this player\'s turn')
                
                
            else:
                print('DEBUG:player not participating in this game')
        else:
            print('DEBUG:game not started')
        
        return b'0'
    
root = Resource()
root.putChild(b'join', JoinGame())
root.putChild(b'create', CreateGame())
root.putChild(b'start', StartGame())
root.putChild(b'status', GameStatus())
root.putChild(b'play', PlayGame())
#still need routes for: status(show the player other player hands, discards, current board), play(hint/discard/play card, with validity+turn checking), update(reports moves by others)
site = server.Site(root)
reactor.listenTCP(8080, site)
reactor.run()
