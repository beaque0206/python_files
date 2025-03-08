GAME_LEVELS = {
    # dungeon layout: max moves allowed
    "game1.txt": 7,     
    "game2.txt": 12,    
    "game3.txt": 19,
}

PLAYER = "O"
KEY = "K"
DOOR = "D"
WALL = "#"
MOVE_INCREASE = "M"
SPACE = " "

TASK_ONE = 1
TASK_TWO = 2
MASTERS = 3

DIRECTIONS = {
    "w": (-1, 0),
    "s": (1, 0),
    "d": (0, 1),
    "a": (0, -1)
}

INVESTIGATE = "I"
QUIT = "Q"
HELP = "H"

VALID_ACTIONS = [INVESTIGATE, QUIT, HELP]
VALID_ACTIONS.extend(list(DIRECTIONS.keys()))
    
HELP_MESSAGE = f"Here is a list of valid actions: {VALID_ACTIONS}"
INVALID = """That's invalid."""
WIN_TEXT = "You have won the game with your strength and honour!"
LOSE_TEST = "You have lost all your strength and honour."

def load_game(filename):
    """Create a 2D array of string representing the dungeon to display.   
    Parameters:
        filename (str): A string representing the name of the level.

    Returns:
        (list<list<str>>): A 2D array of strings representing the 
            dungeon.
    """
    dungeon_layout = []

    with open(filename, 'r') as file:
        file_contents = file.readlines()

    for i in range(len(file_contents)):
        line = file_contents[i].strip()
        row = []
        for j in range(len(file_contents)):
            row.append(line[j])
        dungeon_layout.append(row)
    
    return dungeon_layout

class Entity:
    """ Entity is a parent class for items and other entity objects.
        Methods are inerited by child classes except for methods overridden.
    """

    _id = "Entity"

    def __init__(self):
        """
        Something the player can interact with
        """
        self._collidable = True

    def get_id(self):
        """returns an entity's ID (str)"""
        return self._id

    def set_collide(self, collidable):
        """sets whether entity can be collided with """
        self._collidable = collidable

    def can_collide(self):
        """Returns(bool): True if entity can be collided with, False otherwise """
        return self._w

    def __str__(self):
        return f"{self.__class__.__name__}({self._id!r})"

    def __repr__(self):
        return str(self)


class Wall(Entity):
    """Wall class is the boundary or blocks that prevents player from going towards a direction """

    _id = WALL
    
    def __init__(self):
        """ Constructor of the Wall class - a special entity that cannot be collided with.
        Inherits methods from Entity
        """
        super().__init__()
        self.set_collide(False)


class Item(Entity):
    """Item is an abstract child class of Entity. Item is also a parent class for Key and MoveIncrease
        Constructor of Item class.
        Item can be collided with to store the item into the player's inventory
    """
    def on_hit(self, game):
        """Not implemented for abstract item class but on_hit of child class is implemented"""
        raise NotImplementedError


class Key(Item):
    """Key - a special item needed to open the door and win the game.
        Constructor of Key class.
        collision state is not defined as all items (parent class) can be collided with
    """

    _id = KEY

    def on_hit(self, game):
        """Stores the key in the player's inventory and removes the key from the game display

        Parameters:
            game (class): GameLogic is the default setting of game. This parameter is used to access the
            key and player in the game.
        """
        player = game.get_player()
        player.add_item(self)
        game.get_game_information().pop(player.get_position())


class MoveIncrease(Item):
    """MoveIncrease class - a special item that increases the number of counts when hit by player. """

    _id = MOVE_INCREASE

    def __init__(self, moves=5):
        """Constructor of MoveIncrease class. Collision state is not defined as all items (parent class) can be
        collided with

        Parameters:
            moves(int): the number of moves to be added. Default setting is 5
        """
        super().__init__()
        self._moves = moves

    def on_hit(self, game):
        """increases player's move count and removes the item from the display"""
        player = game.get_player()
        player.change_move_count(self._moves)
        game.get_game_information().pop(player.get_position())


class Door(Entity):
    """Door class- entity needed to be opened with key to win the game """
    _id = DOOR

    def on_hit(self, game):
        """User wins when player reaches door with key. - Sets win state to true
            Returns:
                Prints warning if the player doesn't have the key
        """
        player = game.get_player()
        for item in player.get_inventory():
            if item.get_id() == KEY:
                game.set_win(True)
                return

        print("You don't have the key!")


class Player(Entity):
    """Player class represents the entity the user will be controlling"""

    _id = PLAYER

    def __init__(self, move_count):
        """Constructor of Player class - entity that represents the player and player position

        Parameters:
        move_count(int): represents how many moves the player has based on the name of dungeon
        """
        super().__init__()
        self._move_count = move_count #initial or remaining number of moves the player is allowed to make
        self._inventory = [] #where items can be stored
        self._position = None

    def set_position(self, position):
        """Sets or changes the position of the player

        Parameters:
            postuple(tuple): the new position the player will take
        """
        self._position = position

    def get_position(self):
        """Returns:
            tuple: representation of player's position in the game
        """
        return self._position

    def change_move_count(self, number):
        """
        Parameters:
            number (int): number to be added to move count
        """
        self._move_count += number

    def moves_remaining(self):
        """Returns:
            (int): moves remaining for the game
        """
        return self._move_count

    def add_item(self, item):
        """Adds item (Item) to inventory
        """
        self._inventory.append(item)

    def get_inventory(self):
        """Returns:
            (list): list of objects in the player's inventory
        """
        return self._inventory


class GameLogic:
    """GameLogic class stores information about the game, dungeon, positions, win state.
        This class also contains methods that changes entities' information
    """
    def __init__(self, dungeon_name="game1.txt"):
        """Constructor of the GameLogic class.

        Parameters:
            dungeon_name (str): The name of the level.
        """
        self._dungeon = load_game(dungeon_name)
        self._dungeon_size = len(self._dungeon)
        self._player = Player(GAME_LEVELS[dungeon_name])
        self._game_information = self.init_game_information()
        self._win = False

    def get_positions(self, entity):
        """ Returns a list of tuples containing all positions of a given Entity
             type.

        Parameters:
            entity (str): the id of an entity.

        Returns:
            (list<tuple<int, int>>): Returns a list of tuples representing the 
            positions of a given entity id.
        """
        positions = []
        for row, line in enumerate(self._dungeon):
            for col, char in enumerate(line):
                if char == entity:
                    positions.append((row, col))

        return positions

    def init_game_information(self):
        """creates the initial game information of the game. Also sets the initial position of the player

        Returns:
        (dictionary<tuple:entity>): tuples representing the positions of the entities
        player entity not included in the dictionary
        """
        player_pos = self.get_positions(PLAYER)[0]
        key_position = self.get_positions(KEY)[0]
        door_position = self.get_positions(DOOR)[0]
        wall_positions = self.get_positions(WALL)
        move_increase_positions = self.get_positions(MOVE_INCREASE)
        
        self._player.set_position(player_pos)

        information = {
            key_position: Key(),
            door_position: Door(),
        }

        for wall in wall_positions:
            information[wall] = Wall()

        for move_increase in move_increase_positions:
            information[move_increase] = MoveIncrease()

        return information

    def get_player(self):
        """Returns the player class of the game's player"""
        return self._player

    def get_entity(self, position):
        """returns which entity is in a given position

        Parameters:
            (tuple): the position being investigated

        Returns:
            Entity() in the position
        """
        return self._game_information.get(position)

    def get_entity_in_direction(self, direction):
        """returns the entity in a given direction from player position.
        If no entity is in the direction or if the direction is out of bounds of the dungeon size,
        the method will return none
        
        Parameters:
            direction(str): string that represents the direction from player position that will be investigate

        Returns:
            Entity() in the direction of the player
        """
        new_position = self.new_position(direction)
        return self.get_entity(new_position)

    def get_game_information(self):
        """Returns:
            dictionary{tuple:entity}: tuple representing positions of entities not including player
        """
        return self._game_information

    def get_dungeon_size(self):
        """Returns:
            (int): side length of the dungeon
        """
        return self._dungeon_size

    def move_player(self, direction):
        """moves the player towards a direction. updates the position of the player

        Parameters:
            direction(str): string representation of direction the player will move
        """
        new_pos = self.new_position(direction)
        self.get_player().set_position(new_pos)
        
    def collision_check(self, direction):
        """
        Check to see if a player can travel in a given direction
        Parameters:
            direction (str): a direction for the player to travel in.

        Returns:
            (bool): False if the player can travel in that direction without colliding otherwise True.
        """
        new_pos = self.new_position(direction)
        entity = self.get_entity(new_pos)
        if entity is not None and not entity.can_collide():
            return True
        
        return not (0 <= new_pos[0] < self._dungeon_size and 0 <= new_pos[1] < self._dungeon_size)

    def new_position(self, direction):
        """returns the new position player will take

        Parameters:
            direction(str): string representation of direction the player will take
        Returns:
            tuple(int,int): representation of new x(row) and y(col) position of the player
        """
        x, y = self.get_player().get_position()
        dx, dy = DIRECTIONS[direction]
        return x + dx, y + dy

    def check_game_over(self):
        """checks if the player still has moves to go on with the game

        Returns:
            (Bool): True if player can still go on and False if the game is over
        """
        return self.get_player().moves_remaining() <= 0

    def set_win(self, win):
        """Sets the win state of the player

        Parameters:
            (bool): True if player wins, False otherwise
        """
        self._win = win

    def won(self):
        """Returns the win state of the player

        Returns:
            Bool: True if the winner has won, False otherwise
        """
        return self._win

import PIL
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import simpledialog
from PIL import Image
from PIL import ImageTk


class GameApp:
    """Constructor of GameApp class which is a communicator between GameLogic and display of game"""
    def __init__(self, master, task=TASK_TWO, dungeon_name="game2.txt"):
        """takes iformation from GameLogic class such as
        game information, dungeon, player and entity information
        Parameters:
            master: (root)
            task: (constant or integer)
            dungeon_name: dungeon file to open
        """
        #define all variables
        self._master = master
        self._dungeon_name = dungeon_name
        self._game = GameLogic(self._dungeon_name)
        self._dungeon_size = self._game.get_dungeon_size()
        self._playermoves = self._game.get_player().moves_remaining()
        self._task = task
        self._master = master
        self._action = None
        self._all_info = [] #tuple for storing information of every move for masters task
        #filenames for highscores
        if  self._dungeon_name== "game1.txt":
            self._hsfilename= "Key_Cave_High_Scores_G1.txt"
        elif  self._dungeon_name =="game2.txt":
            self._hsfilename = "Key_Cave_High_Scores_G2.txt"
        else:
            self._hsfilename = "Key_Cave_High_Scores_G3.txt"
        
        #define  master
        master.title("Key Cave Adventure Game")
        master.title_label = tk.Label(master, text="Key Cave Adventure Game",
                                      bg = "Medium spring green")
        master.title_label.pack(side = tk.TOP, expand = True, fill = tk.BOTH)
        #Show Keypad and bind events to link to methods
        self._KP = KeyPad(master)
        self._KP.pack(side=tk.RIGHT,anchor="center")
        self._KP.bind("<Button-1>",self.click)
        self._KP.bind_all("<KeyPress>",self.kpress)
        #Show Dungeon Map or Advanced Dungeon Map if Task 2
        if self._task == 1:
            self._DM = DungeonMap(self._master,size=self._dungeon_size)
        else:
            self._DM = AdvancedDungeonMap(self._master,size=self._dungeon_size)
        self._DM.pack(side=tk.TOP,anchor="w")
        self._DM.draw_grid(self._game.get_game_information(),self._game.get_player().get_position())
        #if Task 2 show status bar and menu bar
        if self._task == 2 or self._task == 3:
            self.load_bar()
            
        if self._action is not None: #if key is pressed or clicked execute move
            self.play()
            
    def play(self):
        """Handles top interaction with user"""
        #define variables
        game_information = self._game.get_game_information()
        dungeon_size = self._game.get_dungeon_size()
        player = self._game.get_player()
        player_pos = player.get_position()
        #if task2 or masters, update number of moves shown
        if self._task == 2 or self._task == 3:
            strmoves = str(player.moves_remaining())
            self._SB.update_moves(strmoves)
            
        #set action from keypad press or click  
        action = self._action 
        
        # Move Player
        if action in DIRECTIONS:
            direction = action
            self._previouspos = player.get_position()
            # if player does not collide move them
            if not self._game.collision_check(direction):
                self._game.move_player(direction)
                entity = self._game.get_entity(player.get_position())
                # process on_hit and check win state
                if entity is not None:
                    entity.on_hit(self._game)
                    if self._game.won():
                        """if masters task, save time won and unbind keypad to
                        stop player from moving in the game when typing name"""
                        if self._task == 3: 
                            self._minutes = self._SB._minutes
                            self._seconds = self._SB._seconds
                            #convert time to total seconds for one value reference
                            self._totalseconds = (self._minutes*60)+self._seconds
                            self.check_highscore()
                            self._KP.unbind("<Button-1>")
                            self._KP.unbind_all("<KeyPress>")
                        else:
                            #show regular messagebox for other tasks
                            messagebox.showinfo(title="Game End", message=WIN_TEXT)
                        return

            #update information shown
            player.change_move_count(-1)
            self._DM.empty()
            if self._task == 2 or self._task == 3:
                self._SB.update_moves(player.moves_remaining())
                info = (self._SB._minutes, self._SB._seconds,self._previouspos)
                self._all_info.append(info)
                
            #redraw grid
            self._DM.draw_grid(game_information,player.get_position())
            #revert action to none until key clicked or pressed
            self._action = None

            #check if game is over
            if self._game.check_game_over():
                messagebox.showinfo(title="Game End", message=LOSE_TEST)
                return
        
    def load_bar(self):
        """Method that shows the file menu bar and the status bar at the bottom
            when task 2 or masters is chosen. Also Rebinds keypad for when game is over and key
            pad was unbinded

        Returns: Menu bar and Status Bar. 
        """
        # File menu
        menubar = tk.Menu(self._master)
        # tell master what its menu is
        self._master.config(menu=menubar)
        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        #add options for menu
        filemenu.add_command(label="New game", command=self.new_game)
        filemenu.add_command(label="Load game", command=self.load_game)
        filemenu.add_command(label="Save game", command=self.save_game)
        filemenu.add_command(label="Quit", command=self.quit_game)
        if self._task == 3:
            filemenu.add_command(label = "High scores", command = self.show_top3)
        self._filename = None
        #Show Status Bar
        self._SB = StatusBar(self._master,parent=self._DM,moves= self._playermoves)
        self._SB.pack(side=tk.LEFT,fill=tk.X)
        self._SB.newgame.bind("<Button-1>",self.new_game)

        #Show additional life frame if task set to masters
        if self._task == MASTERS:
            self._Lives = LivesStatusBar(self._master, parent=self._SB)
            self._Lives.pack(side=tk.RIGHT, anchor = "e", fill = tk.X)
            self._Lives.lifebutton.bind("<Button-1>",self.lifeclick)

        #rebind keypad
        self._KP.bind("<Button-1>",self.click)
        self._KP.bind_all("<KeyPress>",self.kpress)

    def destroy_bar(self):
        """Method that deletes status bar and lives"""
        self._SB.destroy()
        if self._task == 3:
            self._Lives.destroy()

    def lifeclick(self,e):
        """Method called when button for use life is clicked.

        Returns: changes position of player, the time elapsed, the # of moves left
        the # of lives left and removes the previous position from move list tuple
        """
        totalinfo=len(self._all_info)
        #reference to the last move on the list and storing them in variables
        prevmove_info = self._all_info[totalinfo-1]
        prevminutes = prevmove_info[0]
        prevseconds = prevmove_info[1]
        prevpos = prevmove_info[2]
        #set the player position and time
        self._game.get_player().set_position(prevpos)
        self._SB._minutes = prevminutes
        self._SB._seconds = prevseconds
        #remove last move information from tuple
        self._all_info.pop(totalinfo-1)
        #redraw the dungeon map
        self._DM.empty()
        self._DM.draw_grid(self._game.get_game_information(),prevpos)

    def click(self,e):
        """Method that sets the right letter corresponding to the clicked rectangle from keypad

        Parameters: e - event of clicking on keypad
        
        Returns: sets letter to self._action and calls play method
        """
        self._action = self._KP.pixel_to_direction(e)
        self.play()
        
    def kpress(self,e):
        """Method that sets the right letter corresponding to the pressed letter on keyboard

        Parameters: e - event of pressing on keyboard
        
        Returns: sets letter to self._action and calls play method
        """
        self._action = e.char
        self.play()
         
    def new_game(self,e=1):
        """Method for resetting all variables and returning to initial game display.

        Returns: dungeon map display and status bar with resetted time and move count
        """
        #Reset variables
        self._DM.empty()
        self.destroy_bar()
        #redraw dungeon map
        self._game = GameLogic(self._dungeon_name)
        self._DM.draw_grid(self._game.get_game_information(),self._game.get_player().get_position())
        #reset status bar
        if self._task == 3 or self._task==2:
            self.load_bar()
            
    def save_game(self):
        """Method for saving vital information of the game which includes dungeon name, game information,
        player position, moves remaining, and time elapsed.

        Returns: text file saved into user's chosen file location and file name.
        """
        #ask for file name
        if self._filename is None:
            filename = filedialog.asksaveasfilename()
            if filename:
                self._filename = filename
        #write information in text. one line per variable
        if self._filename:
            #save time and dungeon name into variables
            seconds = self._SB._seconds
            minutes = self._SB._minutes
            dungeon = self._dungeon_name
            #if key is not in inventory, store position of key in dungeon
            inv = self._game.get_player().get_inventory()
            gameinfo = self._game.get_game_information().keys()
            if KEY not in inv:
                keypos = self._game.get_positions(KEY)
            #if move increase is not in dungeon, set number to 0 otherwise set it to 1
            m = self._game.get_positions(MOVE_INCREASE)
            if m[0] not in gameinfo:
                movpos = 0
            else:
                movpos = 1
            #if masters task save info on lives
            if self._task == 3:
                lifecount = self._Lives._lives
                allinf=self._all_info
                move_information =""
                
                #if the less than 3 moves is recorded, set boundary to number of records
                if len(allinf)<3:
                    boundary = len(allinf)
                else:
                    #if more than 2 records recorded, set boundary to 3 because of 3 lives limit
                    boundary = 3
                if len(allinf)!=0:
                    #loops over all the information in moves tuple and collecting them as
                    #string ready to be written in file for saving
                    for c in range(0,boundary):
                        move_information += str(str(allinf[c][0])+"-"+
                                             str(allinf[c][1])+"-"+
                                             str(allinf[c][2][0])+"-"+
                                             str(allinf[c][2][1])+"\n")
            else:
                lifecount = None
                move_information = ""
            #create file for storing information
            fd = open(self._filename, 'w')
            
            """writes information in the following order (per line):
                1. items in inventory
                2. moveincrease variable (0 if already used, 1 otherwise
                3. player position
                4. moves remaining
                5. minutes passed
                6. seconds passed
                7. dungeon name
                8. lives left
                9. previous moves
            """
            linetowrite=(str(inv)+"\n"+str(movpos)+"\n"+str(self._game.get_player().get_position())+"\n"+
                     str(self._game.get_player().moves_remaining())+"\n"+
                     str(minutes)+"\n"+str(seconds)+"\n"+str(dungeon)+"\n"+
                         str(lifecount)+"\n"+move_information)
            fd.writelines(linetowrite)
            fd.close()
            
    def load_game(self):
        """Loads previously saved game
        Returns: sets dungeon name, game information, player position,
                remaining moves, and time elapsed
                Shows new dungeon and status bar
        """
        #open file chosen by player
        filename = filedialog.askopenfilename()
        #open file for reading
        if filename:
            self._filename = filename
            fd = open(filename, 'r')
            storage=[] #temporary storage for each line
            #loop for storing information from file to storage
            for line in fd:
                line = line.rstrip("\n")
                storage.append(line)

            #create new game based on loaded information
            dungeonname = storage[6]
            self._game = GameLogic(dungeonname)
            
            #get initial positions of moveincrease and key
            m = self._game.get_positions(MOVE_INCREASE)
            k = self._game.get_positions(KEY)
            inv = storage[0]
            
            #if key is in inventory, remove key from dungeon and put it in player inventory
            if KEY in inv:
                self._game.get_player().add_item(KEY)
                self._game.get_game_information().pop(k[0])

            #if move increase is 0, remove it from dungeon
            movpos = int(storage[1])
            if movpos == 0:
                self._game.get_game_information().pop(m[0])

            #sets values to player position based on loaded information   
            playerpos=storage[2]
            playerpos=playerpos.split("(")[1].split(")")[0].partition(",")
            playerpos=(int(playerpos[0]),int(playerpos[2]))
            #change player move count
            player = self._game.get_player()   
            player._move_count=int(storage[3])
            player.set_position(playerpos)
            
            fd.close()
        #delete previous dungeon map and status bar
        self._DM.destroy()
        self.destroy_bar()
        #show new dungeon map
        self._DM = AdvancedDungeonMap(self._master,size=self._game.get_dungeon_size())
        self._DM.pack(side=tk.TOP,anchor="w")
        self._DM.draw_grid(self._game.get_game_information(),playerpos)
        #show status bar with updated time and movecount
        self.load_bar()
        self._SB._minutes=int(storage[4].strip())
        self._SB._seconds=int(storage[5].strip())
        self._SB.update_moves(int(storage[3]))
        #if masters update lives frame with loaded lives remaining
        if len(storage)>8:
            self._Lives._life = int(storage[7])
            #loop to restore previous moves into move information tuple
            self._all_info = []
            for c in range(8,11):
                minfo = storage[c].split("-")
                onemove = (int(minfo[0]),int(minfo[1]),
                           (int(minfo[2]),int(minfo[3])))
                self._all_info.append(onemove)
                             
        
    def quit_game(self):
        """ Closes the application if player confirms quitting

        Returns: close application
        """
        MsgBox = tk.messagebox.askquestion('Quit Game',"Are you sure you want to quit?",icon = 'warning')
        if MsgBox == 'yes':
           self._master.destroy()

    def check_highscore(self):
        """Method for checking if player makes it to top 3 high scores

        Returns: calls winmessage for entering name"""
        #set different file names for different dungeons

            
        #sets initial ranking of player
        self._rank = 0
        
        #open file if it exists, otherwise create a new file
        try:
            self._hs = open(self._hsfilename,"r+")   
        except FileNotFoundError:
            self._hs = open(self._hsfilename,"a")
            self.winmessage()
            
        #call method for reading the file and store it in hs_info variable
        hs_info = self.read_hsfile(filename = self._hs)

        #loop going through the time records of top players to compete with
        c = 1     
        for c in range(1,len(hs_info)+1):

            if int(hs_info[c-1][1])< (self._totalseconds):
                c += 1
            else:
                break
            
        #sets the rank of the player based on result from loop
        self._rank = c

        #if the player made it to top 3, call method for win prompt
        if self._rank <4:
            self.winmessage()
        else:
            messagebox.showinfo(title="Game End", message=WIN_TEXT)

    def read_hsfile(self, filename):
        """Method for reading through high score file

        Parameters: filename (file to read)
        
        Returns: (list<tuple<string,int>) high score information: name, totalseconds as list
        """
        fn = filename
        self._lines = [] #create storage for each line in file
        
        for line in fn:
            line = line.rstrip("\n") #remove new lines
            self._lines.append(line)
        
        high_scores_info = []
        c = 0 #counter for how many lines have been read
        #loop over each line to clean lines
        for i in self._lines:
            c += 1
            if c<4:
                #split the lines to 2 values and stores in info
                info = i.split(": ") 
                each = (info[0],info[1])
                high_scores_info.append(each)
                
        return(high_scores_info)
       
    def winmessage(self):
        """Method for win messagebox prompt. Called when user is in top 3.

        Returns: Win window with message and textbox for user name input
        """
        #new window for message
        self._top = tk.Toplevel()
        self._top.title("You Win!")
        self._top.geometry("400x70")
        
        msg = str("You won in {0}m and {1}s! Enter your name:").format(self._minutes,self._seconds)
        msg_label = tk.Label(self._top, text= msg)
        msg_label.pack(expand=True)
        
        self._name_textbox = tk.Entry(self._top, width = 40)
        self._name_textbox.pack()
                            
        enter_btn = tk.Button(self._top, text = "Enter", command = self.write_wininfo)
        enter_btn.pack()

    def write_wininfo(self):
        """Method that writes the win information in high score files

        Returns: Updates high score files and calls prompt to show top 3
        """
        self._playername = self._name_textbox.get() 
        self._top.destroy() #close win window
        
        record =str(self._playername)+": "+str(self._totalseconds)
        
        #if no other record yet, no need to compare
        if self._rank == 0:
            self._hs.write(record)
        else:
            self._lines.insert(self._rank-1,record)
            if len(self._lines)>3: #remove last player out of list
                self._lines.pop()
            self._hs.truncate(0)
            self._hs.seek(0)
            for i in self._lines:
                i = i.strip()
                self._hs.write(str(i)+"\n")
        
        self._hs.close()
        self.show_top3()

    def show_top3(self):
        """Prompt new window for top 3 players"""
        self._toplist = tk.Toplevel()
        self._toplist.title("Top 3")
        self._toplist.geometry("150x150")
        self._hs = None

        HS_label = tk.Label(self._toplist, text ="High Scores",
                            font ="Arial 16 bold", bg = "Medium spring green" )
        HS_label.pack(side=tk.TOP,expand = True, fill = tk.BOTH)
        
        #check if file exists
        try:
            self._hs = open(self._hsfilename,"r+")
            
        except FileNotFoundError:
            top_list = ""

        if self._hs != None:
            topscore_info = self.read_hsfile(filename = self._hs)
            top_list = ""
        
            #gathers information from read file and stores it in tuple as strings
            for i in range(0,len(topscore_info)):
                m = int(topscore_info[i][1])//60
                s = int(topscore_info[i][1])%60
                top_list += topscore_info[i][0]+": "+str(m)+"m"+str(s)+"s \n"
        
        top_label = tk.Label(self._toplist,text=str(top_list))
        top_label.pack(side=tk.TOP,expand=True)
        
        top_button = tk.Button(self._toplist,text="Done",command = self._toplist.destroy)
        top_button.pack(side=tk.TOP)
        
class AbstractGrid(tk.Canvas):
    """ Abstract view class that provides base functionality for other view classes"""
    
    def __init__(self,master,rows, cols, width, height, **kwargs):
        """ Abstract Grid with number of rows and columns and pixel dimensions

        Parameters:
            master: (root)
            rows: (int)
            cols: (int)
            width: (int)
            height: (int)
            **kwargs: all other arguments of tk.Canvas
        """
        super().__init__(master, bg="white", width=width, height=height)
        self._rownum = rows
        self._colnum = cols
        self._width = width
        self._height = height
        self._master = master

    def get_bbox(self, position):
        """Method for finding the positions bounds of an entity

        Parameters:
            position: row, col position

        Returns:
            all positions (list(int,int,int,int)): top left corner pixel (x,y)
            and bottom right corner (x,y)
        """
        #divide the whole width of the grid with number of rows to define width per row
        w = self._width/self._rownum
        #set the x and y coordinate of top corner
        X_coor_top = (position[1])*w
        Y_coor_top = (position[0])*w
        # set x and y coordinate of bottom corner by adding width size to top corner
        X_coor_bottom = X_coor_top + w
        Y_coor_bottom = Y_coor_top + w
        return(X_coor_top,Y_coor_top,X_coor_bottom, Y_coor_bottom)

    def get_position_center(self, position):
        """Method for getting the associated center pixel point of a position
        Parameters:
            position: row, col position

        Returns:
            <tuple(int,int)>: x and y point of center
        """
        bounds = self.get_bbox(position)
        #center is half the width of the cell
        half_width = (self._width/self._rownum)/2
        return(bounds[0] +half_width, bounds[1] + half_width)

    def pixel_to_position(self,pixel):
        """Converts the x and y pixel position to a row and col position
        Parameters:
            Pixel (list): x and y coordinate of point being investigated

        Returns:
            <tuple(int,int)>: row and col position
        """
        c = pixel[0]*self._rownum/self._width
        r = pixel[1]*self._colnum/self._height
        return(r,c)
        
        
class DungeonMap(AbstractGrid):
    """View class that inherits from AbstractGrid where entities are displayed"""
    def __init__(self,master, size, width = 600 , **kwargs):
        """Square size grid
        Parameters:
            master: root
            size: square size of grid represented by number of rows
            width: pixel size of grid with 600 as default
        """
        super().__init__(master,size,size,width,width,**kwargs)
        self._rownum = size
        self._colnum = size
        self._width = width
        self._height = width
        self._master = master
        
        
    def draw_grid(self,dungeon,player_position):
        """Method of drawing the dungeonmap based on dungeon information
        Parameters:
            dungeon: contains display information about entities
            player_position <tuple(int,int)>: row, col position of player
        Returns:
            created rectangles for entities with color and text displaying type of entity
        """
        #loop over every position in dungeon to identify entity and associate
        #corresponding text and color
        for pos in dungeon:
            #convert position to pixel bounds and find center
            bounds = self.get_bbox(pos)
            center = self.get_position_center(pos)
            if dungeon[pos]._id == WALL:
                color = "Dark grey"
                label = ""
            elif dungeon[pos]._id == DOOR:
                color = "Red"
                label = "Nest"
            elif dungeon[pos]._id == KEY:
                color = "Yellow"
                label = "Trash"
            else:
                color = "Orange"
                label = "Banana"
            #create rectangle for each entity
            self.create_rectangle(*bounds, fill = color)
            self.create_text(*center, text = label)

        #convert player position to pixel position and find center
        player_bounds = self.get_bbox(player_position)
        player_center = self.get_position_center(player_position)
        #create rectangle for player
        self.create_rectangle(*player_bounds, fill ="Medium spring green")  
        self.create_text(*player_center, text = "Ibis")

    def empty(self): 
        self.delete("all")
        
    
class KeyPad(AbstractGrid):
    """View class inheriting from Abstract Grid representing a GUI Keypad"""
    def __init__(self, master, width = 200, height = 100, **kwargs):
        """Keypad with north, south, east, west options
        Parameters:
            master
            width (int): width size of keypad, default is 200
            height (int): height of keypad with 100 as default
            **kwargs: all other arguments inherited
        Returns:
            Keypad view in window
        """
        super().__init__(master, width, height, width, height,**kwargs)
        self._width = width
        self._height = height
        self._button_width = self._width/3
        self._button_height = 50
        dirs = ("N","W","S","E")
        self._direction = None

        #loop over all directions in list
        for c,d in enumerate(dirs):
            #if direction is north, different way of finding position (top center)
            if d=="N":
                N_pixels = (self._button_width,0,self._button_width*2,self._button_height)
                self.create_rectangle(self._button_width, 0,self._button_width*2,
                                      self._button_height, fill="Dark Grey")
                self.create_text(self._button_width*1.5,25, text = d)
            else:
                #for all other directions create rectangle from left most to right
                self.create_rectangle((c-1)*self._button_width,self._button_height,
                                      c*self._button_width,self._button_height*2, fill="Dark Grey")
                self.create_text(((c-1)*self._button_width)+self._button_width/2,75,text = d)
        
    def pixel_to_direction(self,pixel):
        """Converts the x,y, pixel position to the direction of the arrow (w,a,s,d)
        Paramters:
            pixel<tuple(int),(int)>: x,y pixel position to be converted

        Returns:
            direction(character): w,a,s, or d
        """
        #if top rectangle, north
        if pixel.y<self._button_height:
            if pixel.x>(200/3) and pixel.x<(2*200/3):
                self._direction="w"
        #based on x axis of position, define the direction
        elif pixel.x<self._button_width:
            self._direction="a"
        elif pixel.x<2*self._button_width:
            self._direction="s"
        elif pixel.x<3*self._button_width:
            self._direction="d"
        return(self._direction)

class AdvancedDungeonMap(DungeonMap):
    """Extension of Dungeonmap class. Replaces rectangles with images of entities"""
    
    def __init__(self,master, size, width = 600 , **kwargs):
        """Map display for when task two is chosen
        Parameters:
            master
            size(int): size of the dungeon based on dungeon name
            width(int): pixel width of dungeon, default at 600
            **kwargs: all other arguments inherited
        """
        super().__init__(master,size,width,**kwargs)
        
    def draw_grid(self,dungeon,player_position):
        """creates an image for every row, col position in dungeon
        Paramters:
            dungeon(string): representation of type of dungeon
            player_position tuple<(int),(int)>: row, col position of player
        """
        s = int(self._width/self._rownum)
        #assign resized open images to their corresponding entity variables
        doorimg= Image.open('images/door.gif')
        doorimg = doorimg.resize((s,s),Image.ANTIALIAS)
        
        keyimg= Image.open('images/key.gif')
        keyimg= keyimg.resize((s,s),Image.ANTIALIAS)
        
        wallimg= Image.open('images/wall.gif')
        wallimg = wallimg.resize((s,s),Image.ANTIALIAS)
        
        moveimg= Image.open('images/moveIncrease.gif')
        moveimg = moveimg.resize((s,s),Image.ANTIALIAS)
        
        plimg= Image.open('images/player.gif')
        plimg = plimg.resize((s,s),Image.ANTIALIAS)
        
        spaceimg= Image.open('images/empty.gif')
        spaceimg = spaceimg.resize((s,s),Image.ANTIALIAS)

        #create dictionary for all images
        self.images = {
            "door": ImageTk.PhotoImage(doorimg),
            "key": ImageTk.PhotoImage(keyimg),
            "wall": ImageTk.PhotoImage(wallimg),
            "move": ImageTk.PhotoImage(moveimg),
            "player": ImageTk.PhotoImage(plimg),
            "space": ImageTk.PhotoImage(spaceimg)
        }
        
        #creates grass images for the all spaces within the walls
        for i in range(1,(self._rownum-1)):
            for c in range (1,self._colnum-1):
                self.create_image((i*s)+(s/2),(c*s)+(s/2),image=self.images["space"])
                
        #continuous loop that goes through all dungeon positions and creates image of entity
        for pos in dungeon:
            bounds = self.get_bbox(pos) #get pixel positions for images
            #sets the right image associated with the entity
            if dungeon[pos]._id == WALL:
                photoimg = self.images['wall']
            elif dungeon[pos]._id == DOOR:
                photoimg = self.images['door']
            elif dungeon[pos]._id == KEY:
                photoimg = self.images['key']
            else:
                photoimg = self.images['move']
                
            #create image in the right pixel position defined by bounds
            self.create_image(bounds[0]+(s/2),bounds[1]+(s/2), image=photoimg)
            
        #create image for the player 
        player_bounds = self.get_bbox(player_position)
        self.create_image(player_bounds[0]+(s/2),player_bounds[1]+(s/2), image=self.images["player"])

class StatusBar(tk.Frame):
    """View cklass that inherits from tk.Frame, where various game information is displayed"""
    def __init__(self,master,parent,moves):
        """StatusBar shows buttons for options, time elapsed, and remaining moves
        Paramters:
            master,parent
            moves (int): # of moves remaining
        """
        super().__init__(master)
        self._parent = parent
        self._master = master
        self._moves = moves
        #create string for remaining moves label
        self._movestring = str(self._moves)+str(" moves remaining")
        self._minutes = 0
        self._seconds = 0
        #create string for time label
        self._time= (str(self._minutes)+" m"+str(self._seconds)+" s")

        #load images and resize
        clockimg= Image.open('images/clock.gif')
        clockimg = clockimg.resize((75,75),Image.ANTIALIAS)
        lightningimg= Image.open('images/lightning.gif')
        lightningimg = lightningimg.resize((75,75),Image.ANTIALIAS)

        #create dictionary of all images
        self._images={
            "time":ImageTk.PhotoImage(clockimg),
            "movesleft":ImageTk.PhotoImage(lightningimg)
            }
        #create a frame for buttons of new game and quit options
        buttonframe=tk.Frame(self)
        buttonframe.pack(side=tk.LEFT,expand=True)
        self.newgame = tk.Button(buttonframe,text="New game",command = self.new_game)
        self.newgame.pack(side=tk.TOP, expand=True)
        self.quit= tk.Button(buttonframe,text="Quit", command = self.quit_game)
        self.quit.pack(side=tk.TOP,expand=True)

        #create separate frame for time information
        timeframe=tk.Frame(self)
        self.timeimage = tk.Label(timeframe,text="Time elapsed", image = self._images["time"])
        self.timeimage.pack(side=tk.LEFT)
        
        self.timelabel = tk.Label(timeframe,text="Time elapsed")
        self.timelabel.pack(side =tk.TOP, anchor = "center",expand=True)
        
        self.timerlabel = tk.Label(timeframe,text = self._time)
        self.timerlabel.pack(side=tk.TOP,anchor= "center",expand=True)
        
        timeframe.pack(side=tk.LEFT,expand=True)

        #create separate frame for move remaining information
        movesleft=tk.Frame(self)
        self.movesimage=tk.Label(movesleft,image=self._images["movesleft"])
        self.movesimage.pack(side=tk.LEFT)
            
        self.movelabel = tk.Label(movesleft,text="Moves left")
        self.movelabel.pack(side =tk.TOP, anchor = "center",expand=True)
        
        self.move2label = tk.Label(movesleft,text = self._movestring)
        self.move2label.pack(side=tk.TOP,anchor= "center",expand=True)
        movesleft.pack(side=tk.LEFT,expand=True)

        #cal update time method to start running timer
        self.update_time()
        
    def update_moves(self,moves):
        """Method for updating number of moves left displayed
        Parameters(moves:int) updated number of moves left
        """
        self._movestring = str(moves)+str(" moves remaining") 
        self.move2label.config(text = self._movestring)
        
    def new_game(self):
        None #new_game in GameApp class is called instead

    def quit_game(self):
        """Method prompting confirm window for quit button
            Returns:
            closes the application if yes and resumes game if no.
        """
        MsgBox = tk.messagebox.askquestion('Quit Game',"Are you sure you want to quit?",icon = 'warning')
        if MsgBox == 'yes':
           self._master.destroy()
    
    def update_time(self):
        """Method that creates continuous loop of adding seconds to time.
        Returns: sets the stringvariable in time label of status bar to their corresponding
        minutes and seconds
        """
      
        #if seconds is 59, it should go back to zero and add 1 minute. Otherwise, just add 1 second
        if self._seconds == 59:
            self._seconds = 0
            self._minutes += 1
        else:
            self._seconds += 1

        self._time = (str(self._minutes)+" m"+str(self._seconds)+" s")
        self.timerlabel.config(text = self._time)
        #loops over method every 1000 milliseconds    
        self.after(1000,self.update_time)  


class LivesStatusBar(tk.Frame):
    """Status Bar that shows number of lives left"""
    def __init__(self,master,parent):
        """Creates frame for lives information and button for using life option
        Parameters:
            master, parent
        """
        super().__init__(master)
        self._master = master
        self._parent = parent
        self._lives = 3
        #create string label for lives information
        self._lifestring = ("Lives Remaining: " + str(self._lives))
        self._lastmovetime = None
        #load and resize image
        lifeimage = Image.open('images/lives.gif')
        lifeimage = lifeimage.resize((75,75),Image.ANTIALIAS)
        self._lifeimage={"life":ImageTk.PhotoImage(lifeimage)}

        #create frame for lives information and button then pack
        lifeframe= tk.Frame(self)
        lifeimage = tk.Label(lifeframe,text="Lives Remaining", image = self._lifeimage["life"])
        lifeimage.pack(side=tk.LEFT)
        
        self.lifelabel = tk.Label(lifeframe,text=self._lifestring)
        self.lifelabel.pack(side =tk.TOP, anchor = "center",expand=True)
        
        self.lifebutton = tk.Button(lifeframe,text="Use Life",command = self.use_life)
        self.lifebutton.pack(side=tk.TOP,anchor= "center",expand=True)
        
        lifeframe.pack(side=tk.LEFT,expand=True)

    def use_life(self):
        #updates the number of lives shown when the player uses life
        self._lives = self._lives - 1
        self._lifestring = ("Lives Remaining: "+str(self._lives))
        self.lifelabel.config(text = self._lifestring)
    
def main():
    root=tk.Tk()
    app = GameApp(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
