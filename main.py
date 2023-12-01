import pygame
import math as maths
import sys
import struct
import time
from pygame import mixer
import wave
import os
import shutil


gameState = "title"

blue = (47,54,153)

red = (237,28,36)


#Initialise pygame
pygame.init()
noteOrder = []
alphaString = "CDEFGAB"
for i in range(9):
  for j in range(7):
    noteOrder.append(f"{alphaString[j]}{i}")
    if f"{alphaString[j]}{i}" == "E3":
      e3 = len(noteOrder) - 1

noteLengths = {
  "DoubleBarLine": -1,
  "Quaver" : 0.5,
  "Crotchet" : 1,
  "Minim" : 2,
  "Semibreve" : 4
}

noteDims = {
  "DoubleBarLine": (20, 128),
  "Quaver" : (48, 72),
  "Crotchet" : (32, 72),
  "Minim" : (32, 72),
  "Semibreve" : (32, 16)
}

keySharps = {
  "C": [],
  "D": ["F", "C"],
  "E": ["F", "G", "C", "D"],
  "F": [],
  "G": [],
  "A": [],
  "B": ["C", "D", "F", "A"],
}

keyFlats = {
  "C": [],
  "D": [],
  "E": [],
  "F": ["B"],
  "G": [],
  "A": [],
  "B": [],
}


#pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption('Scale Runner!')

slowFactor = 3000
gravity = 250

lastTime = time.time()


class Debug:
  def __init__(self):
    pygame.font.init()
    self.font = pygame.font.Font(None,16)
    self.showMenu = False
    self.bugs = {}

  def push(self, name, value):
    self.bugs[name] = str(value)

  def show(self):
    index = 0
    for i in self.bugs:
      text = self.font.render(i + ": " + self.bugs[i], True, (0,0,0))
      screen.blit(text, (0, index*16))
      index += 1
      
class AudioManager:
  def __init__(self, name):
    self.volume = 0.5
    self.noteFrequencies = self.getFrequencies()
    self.sampleRate = 88200
    self.sampleWidth = 1
    self.name = name
    try:
      os.mkdir(f"{self.name}")
    except:
      pass
    
    for i in self.noteFrequencies:
      self.newGenerateNote(i)

  def getFrequencies(self):
    frequencies = {}
    with open("soundData.txt", "r") as f:
      for row in f.read().splitlines():
        #print(row.split("	"))
        if row[0] != "/":
          note, freq, wavelength = row.split("	")
          if note[0] == " ":
            note = note[1:]

          # B5 in the sound data is B4 in the rest of the code (idk why) etc
          # So some code has been added below to fix this
          index = 0
          #print(note)
          for char in note:
            if "A" != note[0] and "B" != note[0]:
              if char in "1234567890":
                newChar = str(int(char) - 2)
                note = note[0:index] + newChar + note[index+1:]
            else:
              if char in "1234567890":
                newChar = str(int(char) - 2)
                note = note[0:index] + newChar + note[index+1:]
            index += 1
          #print(note)
          
  
          if "/" in note:
            for i in note.split("/"):
              
              frequencies[i.replace(" ", "")] = float(freq)
          else:
            frequencies[note] = float(freq)
    return frequencies
    

  def generateNote(self, note):
    w = wave.open(f"{self.name}/{note}.wav", "w")
    w.setnchannels(1)
    w.setsampwidth(self.sampleWidth)
    w.setframerate(self.sampleRate)
    amplitude = 100
    frequency = self.noteFrequencies[note]
    fpc = int(self.sampleRate*self.sampleWidth/frequency) # frames per cycle
    #print(44100/32767*frequency)
    data = b""
    for i in range(1,fpc):
      #value = int(amplitude*(i%modCoefficient))
      #value = int(32767//i)
      #value = int(32767*maths.sin(2*maths.pi*i/fpc)) # Current best
      value = 0
      for h in range(1,2):
        value += 32767*maths.sin((h)*2*maths.pi*i/fpc)/h
        if value > 32767:
          value = 32767
        if value < -32767:
          value = -32767
      

      data += struct.pack("<h", int(value))
    data = data * int(99999//fpc)
    w.writeframesraw(data)
    w.close()

  def newGenerateNote(self, note):
    path = shutil.copyfile("piano-bb_A#_major.wav",f"{self.name}/{note}.wav")

    ### Open the file
    oldFile = wave.open(f"{self.name}/{note}.wav")
    BbFreq = 932.33
    frequency = self.noteFrequencies[note]
    ### Calculate the sampleRAte
    #print(note)
    #print(oldFile.getframerate())
    sampleWidth = oldFile.getsampwidth()
    sampleRate = oldFile.getframerate()/BbFreq*frequency
    #print(note)
    #print("NSR",sampleRate)
    #print("OSR",oldFile.getframerate())
    #print("OF",BbFreq)
    #print("NF",frequency)
  
    length = oldFile.getnframes()
    data = oldFile.readframes(length)
    #print(sampleRate)
    oldFile.close()

    newFile = wave.open(f"{self.name}/{note}.wav", "w")
    newFile.setnchannels(1)
    newFile.setsampwidth(sampleWidth)
    newFile.setframerate(sampleRate)
    newFile.writeframesraw(data)
    newFile.close()

class Player:
  def __init__(self, level, loadSprites):
    self.pos = [64.0,134.0]
    #self.vel = [0,5]
    if loadSprites:
      self.sprite = pygame.image.load("player.png")
      self.sprite = pygame.transform.scale(self.sprite, (16,16))
      var = pygame.PixelArray(self.sprite)
      var.replace((0,0,0),(255,0,255))
      del var
      self.trailOn = True
    self.lastPositions = []
    
    nextNote = level.notes[0]

    self.level = level

    self.a = 1/6*gravity
    self.b = (self.pos[1]-nextNote.y)/(level.beat-nextNote.beat) - 1/6*gravity*(level.beat + nextNote.beat)
    self.c = self.pos[1] - self.a*level.beat**2 - self.b*level.beat
  
  def update(self):
    self.lastPositions.append([self.level.beat,self.pos[1]])
    
    self.pos[1] = self.a*self.level.beat**2 + self.b*self.level.beat + self.c

  def show(self):
    screen.blit(self.sprite, (self.pos[0],self.pos[1]))
    self.drawTrail()

    ### TESTING
    #for note in self.level.notes:
    #  testX1 = 64 * (note.beat - self.level.beat + 0.5) + 64
    #  testX2 = 64 * (note.beat - self.level.beat - 0.1) + 64
    #  pygame.draw.line(screen, (255,0,255), (testX1, note.y), (testX2, note.y), 4)
    #  pygame.draw.line(screen, (255,0,255), (note.x, note.y-8), (note.x, note.y+16), 4)

  def drawTrail(self):
    if self.trailOn:
      count = 0
      for i in range(1, len(self.lastPositions)//20):
        count += 1
        pos = self.lastPositions[len(self.lastPositions) - i*20]
        size = 16/(i+0.01)**0.3
        x  = 64 * (pos[0] - self.level.beat) + 64
        pygame.draw.circle(screen, (255,0,255), (x+8, pos[1] + 8), size/2)
        if i >= 50:
          break
      
  def jump(self):
    for note in self.level.notes:
      if -0.5 < (note.beat - self.level.beat) < 0.1 and note.y-8 < self.pos[1] < note.y+16:
        note.play()
        nextNote = self.jumpTo(note.length, note.beat)
        #print(nextNote.beat)

        self.a = 1/6*gravity
        self.b = (self.pos[1]-nextNote.y)/(self.level.beat-nextNote.beat) - 1/6*gravity*(self.level.beat + nextNote.beat)
        self.c = self.pos[1] - self.a*self.level.beat**2 - self.b*self.level.beat

  def jumpTo(self, length, noteBeat):
    nextBeat = noteBeat + length
    noteBeforeBeat = self.level.notes[0] # Find the nearest note before the beat
    noteAfterBeat = self.level.notes[-1] # Find the nearest note after the beat
    for note in self.level.notes:
      if note.beat <= nextBeat:
        if abs(noteBeforeBeat.beat - nextBeat) > abs(note.beat - nextBeat):
          #print("B")
          noteBeforeBeat = note
      elif note.beat >= nextBeat:
        if abs(noteAfterBeat.beat - nextBeat) > abs(note.beat - nextBeat):
          noteAfterBeat = note
          #print("A")

    if abs(noteAfterBeat.beat - nextBeat) >= abs(noteBeforeBeat.beat - nextBeat):
      targetNote = noteBeforeBeat
    else:
      targetNote = noteAfterBeat
      
    if self.level.lastNote == True:
      targetNote = self.level.doubleBarLine
      
    if targetNote == self.level.notes[-1]:
      self.level.lastNote = True
      
    return targetNote

class Note:
  def __init__(self, type, pitch, beat, manager, level):
    self.type = type
    if self.type.split(" ")[0] == "dotted":
      self.dotted = True
      self.type = type.split(" ")[1]
      self.length = 1.5 * noteLengths[type.split(" ")[1]]
    else:
      self.length = noteLengths[type]
      self.dotted = False
    self.pitch = pitch
    self.level = level
    self.beat = beat
    self.volume = manager.volume
    self.sprite = pygame.image.load(f"{self.type}.png")
    self.sprite = pygame.transform.scale(self.sprite, noteDims[self.type])
    self.x = 64 * (self.beat - self.level.beat) + 64
    if self.pitch != "None":
      #print(self.pitch)
      if "#" in self.pitch or "b" in self.pitch:
        self.y = 198 - ((noteOrder.index(self.pitch[0]+self.pitch[2]) - e3)*16) - 8
      else:
        self.y = 198 - ((noteOrder.index(self.pitch) - e3)*16) - 8
      #if self.y <= 
      if self.pitch[0] in keySharps[self.level.key]:
        self.track = mixer.Sound(f"{manager.name}/{pitch[0]}#{pitch[1]}.wav") # Split the octave an the note and put the sharp in between
      elif self.pitch[0] in keyFlats[self.level.key]:
        self.track = mixer.Sound(f"{manager.name}/{pitch[0]}b{pitch[1]}.wav") # Split the octave an the note and put the flat in between
      else:
        self.track = mixer.Sound(f"{manager.name}/{pitch}.wav")
    else:
      self.y = 70
    self.manager = manager
    
    self.isPlaying = False

  def show(self):
    self.x = 64 * (self.beat - self.level.beat) + 64
    if -noteDims[self.type][0] <= self.x <= 400:
      if self.type != "Quaver":
        screen.blit(self.sprite, (self.x,self.y))
      else:
        screen.blit(self.sprite, (self.x-10, self.y))
  
      if self.dotted == True:
        pygame.draw.circle(screen, (0,0,0), (self.x+50, self.y+8), 8/2)
        
      if self.pitch != "None":
        if self.y >= 70+4*32:
          # Find the number of notes between e3 and the note
          if "#" in self.pitch or "b" in self.pitch:
            inbetweenNotes = noteOrder.index("E3") - noteOrder.index(self.pitch[0]+self.pitch[2])
          else:
            inbetweenNotes = noteOrder.index("E3") - noteOrder.index(self.pitch)
          
          # Half it and draw that many ledger lines
          ledgerLines = inbetweenNotes // 2
          for i in range(ledgerLines):
            y = i*32+70+5*32
            x = self.x
            pygame.draw.line(screen, (0,0,0), (x,y), (x+35,y), 4)
            
        if self.y <= 70:
          inbetweenNotes = noteOrder.index(self.pitch) - noteOrder.index("F4")

          ledgerLines = inbetweenNotes // 2
          for i in range(ledgerLines):
            y = 70 - ledgerLines*32
            x = self.x
            pygame.draw.line(screen, (0,0,0), (x,y), (x+35,y), 4)
            
      if "#" in self.pitch:
        screen.blit(self.level.sharpImg, (self.x+35, self.y))

      if "b" in self.pitch:
        screen.blit(self.level.flatImg, (self.x+35, self.y))          

  def update(self):
    if self.isPlaying and self.level.beat >= self.beat + self.length:
      self.isPlaying = False
      self.track.stop()
      

  def play(self):
    #print(self.pitch)
    if self.volume != self.manager.volume:
      self.track.set_volume(self.manager.volume)
    self.track.play()
    self.isPlaying = True


master = AudioManager("master")






wholeBeat = 0 # For testing
debugMenu = Debug()
debugMenu.showMenu = True

class Level:
  def __init__(self, name, bpm):
    self.name = name
    self.bpm = float(bpm)
    self.beat = -1.5
    self.lastTime = time.time()
    self.deltaTime = 0.001
    if len(self.name) <= 2:
      self.key = self.name
    else:
      self.key = "C"
    self.lastNote = False
    self.locked = True
    self.completed = False
    self.notes = self.loadLevel()
    self.doubleBarLine = Note("DoubleBarLine", "None", self.notes[-1].beat + self.notes[-1].length, master, self)
    self.player = Player(self, True)

  def drawBackground(self):
    screen.fill((255,255,255))
    for i in range(5):
      pygame.draw.rect(screen, (0,0,0), (0, i*32+70, 400, 4))


  def loadLevel(self):
    notes = []
    with open(f"level/{self.name}") as data:
      list = data.read().splitlines()
      #print(list)
      for note in list:
        if note == "" or note == " " or note[0] == "/":
          pass
        else:
          if len(note.split(" ")) == 3:
            #print(note)
            beat, type, pitch = note.split(" ")
          else:
            try:
              beat, type1, type2, pitch = note.split(" ")
            except:
              print(note)
              sys.exit()
            type = type1 + " " + type2
          notes.append(Note(type, pitch, float(beat), master, self))
    return notes

  def initClefAndScale(self):
    self.clef = pygame.image.load("Treble Clef.png")
    height = self.clef.get_height()
    scale = height/128
    #print(scale/clef.get_width())
    self.clef = pygame.transform.scale(self.clef, (self.clef.get_width()/scale,128))
    sharps = keySharps[self.key]
    flats = keyFlats[self.key]
    self.sharpImg = pygame.image.load("Sharp.png")
    self.sharpImg = pygame.transform.scale(self.sharpImg, (16,17))
    self.flatImg = pygame.image.load("Flat.png")
    self.flatImg = pygame.transform.scale(self.flatImg, (13,41))

    self.sharpYs = []

    for sharp in sharps:
      if sharp < "C":
        pitch = sharp+"3"
      else:
        pitch = sharp+"4"
      sharpY = 198 - ((noteOrder.index(pitch) - e3)*16) - 16
      self.sharpYs.append(sharpY)

    self.flatYs = []

    for flat in flats:
      if flat < "C":
        pitch = flat+"3"
      else:
        pitch = flat+"4"
      flatY = 198 - ((noteOrder.index(pitch) - e3)*16) - 64
      self.flatYs.append(flatY)
    
  def showClefAndScale(self):
    clefX = 64 * (-1 - self.beat) + 64
    clefY = 70
    screen.blit(self.clef, (clefX, clefY))

    for y in self.sharpYs:
      screen.blit(self.sharpImg, (clefX+30, y))

    for y in self.flatYs:
      screen.blit(self.flatImg, (clefX+30, y))
    
    
  def playLevel(self):
    global gameState
    self.currentTime = time.time()
    self.lastTime = time.time()
    self.deltaTime = self.currentTime - self.lastTime
    self.lastNote = False
    self.beat = -1.5
    
    self.player.__init__(self, False)
    
    UIfont = pygame.font.Font(None, 32)
    self.initClefAndScale()
    while gameState == "play":
      self.lastTime = self.currentTime
      self.currentTime = time.time()
      self.deltaTime = self.currentTime - self.lastTime
      debugMenu.push("fps", 1/self.deltaTime)
    
      self.drawBackground()
      
      self.beat += (self.bpm*60)*1/slowFactor*self.deltaTime

      self.showClefAndScale()
    
      self.player.update()
      self.player.show()
      for note in self.notes:
        note.show()
        note.update()
      self.doubleBarLine.show()
    
      for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
          if event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()
          elif event.key == pygame.K_SPACE:
            self.player.jump()
        if event.type == pygame.MOUSEBUTTONDOWN:
          self.player.jump()
      if self.beat >= self.doubleBarLine.beat:
        gameState = "win"
        return level
      if self.player.pos[1] >= 300:
        gameState = "lose"
        return level
      if debugMenu.showMenu:
        debugMenu.show()

      beatUI = UIfont.render(f"beat: {int(self.beat//4)}.{int(self.beat%4+1)}", True, blue)
      bpmUI = UIfont.render(f"bpm: {self.bpm}", True, blue)
      screen.blit(beatUI, (20,20))
      screen.blit(bpmUI, (380 - bpmUI.get_width(),20))
      pygame.display.update()

class Button:
  def __init__(self,x, y, newState, text, align):
    self.y = y
    self.newState = newState
    self.text = text
    self.font = pygame.font.Font(None, 24)
    self.txtObj = self.font.render(self.text, True, (0,0,0))
    if align == "r":
      self.x = x - self.txtObj.get_width()
    elif align == "c":
      self.x = x - self.txtObj.get_width()//2
    else:
      self.x = x  


    self.boxObj = (self.x, self.y, self.txtObj.get_width() + 5, self.txtObj.get_height() + 5)
    self.shadowObj = (self.x+2, self.y+2, self.txtObj.get_width() + 7, self.txtObj.get_height()+7)
     

  def show(self):
    pygame.draw.rect(screen, (0,0,0), self.shadowObj)
    pygame.draw.rect(screen, (255,255,255), self.boxObj)
    screen.blit(self.txtObj, (self.x, self.y))

  def isClicked(self):
    if pygame.mouse.get_pos()[0] > self.x and pygame.mouse.get_pos()[0] < self.x + self.txtObj.get_width() + 5 and pygame.mouse.get_pos()[1] > self.y and pygame.mouse.get_pos()[1] < self.y + self.txtObj.get_height() + 5:
      return True
    return False
def titleScreen():
  global gameState
  titleImage = pygame.image.load("logo.png")
  titleImage = pygame.transform.scale(titleImage, (300,150))
  titleFont = pygame.font.Font(None, 32)
  text = titleFont.render("PRESS 'SPACE' TO PLAY", True, (0,0,0))
  while gameState == "title":
    screen.fill((47,54,153))
    imgX = 200 - titleImage.get_width()//2
    imgY = 150 - titleImage.get_height()//2 + maths.sin(time.time()*5)*5
    screen.blit(titleImage, (imgX,imgY))
    txtX = 200 - text.get_width()//2
    txtY = 233 - text.get_height()//2
    screen.blit(text, (txtX, txtY))
    
    pygame.display.update()
    for event in pygame.event.get():
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()
        elif event.key == pygame.K_SPACE:
          gameState = "menu"
      if event.type == pygame.MOUSEBUTTONDOWN:
        gameState = "menu"
def menu():
  global gameState, levels
  counter = 0
  hFont = pygame.font.Font(None, 96) # Header Font
  txtFont = pygame.font.Font(None, 32)
  settings = Button(400, 0, "settings", "SETTINGS", "r")
  tutorial = Button(0, 0, "tutorial", "HOW TO PLAY", "l")
  lockImg = pygame.image.load("lock.png")
  lockImg = pygame.transform.scale(lockImg, (50,78))
  tickImg = pygame.image.load("Tick.png")
  tickImg = pygame.transform.scale(tickImg, (86,91))
  while gameState == "menu":
    screen.fill((47,54,153))
    keys = list(levels.keys())
    level = keys[counter]
    if levels[level].locked == False:
      nameObj = hFont.render(level, True, (0,0,0))
    else:
      nameObj = lockImg
    prevKey = keys[(counter-1)%len(keys)]
    if levels[prevKey].locked == False:
      lnameObj = hFont.render(prevKey, True, (0,0,0))
    else:
      lnameObj = lockImg

    nextKey = keys[(counter+1)%len(keys)]
    if levels[nextKey].locked == False:
      rnameObj = hFont.render(nextKey, True, (0,0,0))
    else:
      rnameObj = lockImg
    
    pygame.draw.rect(screen, (0,0,0), (130, 25, 150 ,260)) # Draw a shadow
    pygame.draw.rect(screen, (255,255,255), (125, 20, 150, 260))

    ### Left and right item select
    pygame.draw.rect(screen, (0,0,0), (-65, 75, 150 ,260)) # Draw a shadow
    pygame.draw.rect(screen, (150,150,150), (-70, 70, 150, 260))

    pygame.draw.rect(screen, (0,0,0), (325, 75, 150 ,260)) # Draw a shadow
    pygame.draw.rect(screen, (150,150,150), (320, 70, 150, 260))

    
    txtX = 200 - nameObj.get_width()//2
    txtY = 25
    screen.blit(nameObj, (txtX, txtY))

    if levels[level].completed == True:
      tickX = 200-tickImg.get_width()//2
      tickY = 150-tickImg.get_height()//2
      screen.blit(tickImg, (tickX, tickY))

    ltxtX =  5 - lnameObj.get_width()//2
    ltxtY = 75
    screen.blit(lnameObj, (ltxtX, ltxtY))
    if levels[prevKey].completed == True:
      ltickX = 5-tickImg.get_width()//2
      ltickY = 200-tickImg.get_height()//2
      screen.blit(tickImg, (ltickX, ltickY))

    rtxtX =  395 - rnameObj.get_width()//2
    rtxtY = 75
    screen.blit(rnameObj, (rtxtX, rtxtY))
    if levels[nextKey].completed == True:
      rtickX = 395-tickImg.get_width()//2
      rtickY = 200-tickImg.get_height()//2
      screen.blit(tickImg, (rtickX, rtickY))

    settings.show()
    tutorial.show()
    

    for event in pygame.event.get():
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()
      if event.type == pygame.MOUSEBUTTONDOWN:
        mousePos = pygame.mouse.get_pos()
        if settings.isClicked():
          gameState = settings.newState
          return
        if tutorial.isClicked():
          gameState = tutorial.newState
        elif 0 <= mousePos[0] <= 125:
          counter -= 1
          counter = counter%len(keys)
        elif mousePos[0] <= 275:
          #if levels[level].locked == False:
            gameState = "play"
            return level
        else:
          counter += 1
          counter = counter%len(keys)
      

    
    

    pygame.display.update()
def winScreen(level):
  global gameState
  pygame.mixer.stop()
  hFont = pygame.font.Font(None, 64)
  winText1 = hFont.render("LEVEL", True, (0,0,0))
  winText2 = hFont.render("COMPLETED!", True, (0,0,0))
  keys = list(levels.keys())
  levels[keys[(keys.index(level)+1)%len(keys)]].locked = False
  levels[level].completed = True
  while gameState == "win":
    screen.fill((47,54,153))
    txtX1 = 200 - winText1.get_width()//2
    txtY1 = 100 - winText1.get_height()//2 - maths.sin(time.time()*5)*5
    txtX2 = 200 - winText2.get_width()//2
    txtY2 = 100 - winText2.get_height()//2 - maths.sin(time.time()*5)*5 + winText1.get_height() 
    screen.blit(winText1, (txtX1,txtY1))
    screen.blit(winText2, (txtX2,txtY2))
    pygame.display.update()
    
    for event in pygame.event.get():
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()
        elif event.key == pygame.K_SPACE:
          gameState = "menu" 
      if event.type == pygame.MOUSEBUTTONDOWN:
        gameState = "menu"        
def loseScreen(level):
  global gameState
  pygame.mixer.stop()
  hFont = pygame.font.Font(None, 64)
  winText1 = hFont.render("YOU", True, (0,0,0))
  winText2 = hFont.render("FAILED!", True, (0,0,0))

  playAgain = Button(100, 200, "play", "PLAY AGAIN", "c")
  menu = Button(300, 200, "menu", "MAIN MENU", "c")
  
  while gameState == "lose":
    screen.fill((47,54,153))
    txtX1 = 200 - winText1.get_width()//2
    txtY1 = 100 - winText1.get_height()//2
    txtX2 = 200 - winText2.get_width()//2
    txtY2 = 100 - winText2.get_height()//2 + winText1.get_height()

    playAgain.show()
    menu.show()

    screen.blit(winText1, (txtX1, txtY1))
    screen.blit(winText2, (txtX2, txtY2))

    for event in pygame.event.get():
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()
      if event.type == pygame.MOUSEBUTTONDOWN:
        if playAgain.isClicked():
          gameState = playAgain.newState
          return
        if menu.isClicked():
          gameState = menu.newState
          return
    

    pygame.display.update()
def settings():
  global gameState, master
  font = pygame.font.Font(None, 32)
  volumeText = font.render("VOLUME", True, (0,0,0))
  back = Button(0, 0, "menu", "BACK", "l")
  sliderX = master.volume * 100 +150
  pickUp = False
  trail = Button(200, 250, None, "ON", "c")
  trailText = font.render("TRAIL", True, (0,0,0))
  while gameState == "settings":
    screen.fill((47,54,153))
    
    back.show()
    trail.show()
    screen.blit(volumeText, (200-volumeText.get_width()//2, 75))
    pygame.draw.rect(screen, (174, 198, 207), (150, 125, 100, 5))
    pygame.draw.circle(screen, (10,10,70), (sliderX, 128), 10)

    screen.blit(trailText, (200 - trailText.get_width()//2, 200))

    if pickUp:
      if pygame.mouse.get_pos()[0] <= 150:
        sliderX = 150
      elif pygame.mouse.get_pos()[0] >= 250:
        sliderX = 250
      else:
        sliderX = pygame.mouse.get_pos()[0]
    
    for event in pygame.event.get():
      if event.type == pygame.MOUSEBUTTONDOWN:
        if back.isClicked():
          gameState = "menu"
        if trail.isClicked():
          for level in levels:
            player = levels[level].player
            player.trailOn = not player.trailOn
          if trail.text == "ON":
            trail.text = "OFF"
            trail.txtObj = trail.font.render(trail.text, True, (0,0,0))
          else:
            trail.text = "ON"
            trail.txtObj = trail.font.render(trail.text, True, (0,0,0))
        
        if 150 <= pygame.mouse.get_pos()[0] <= 250 and 120 < pygame.mouse.get_pos()[1] < 130:
          pickUp = True
      if event.type == pygame.MOUSEBUTTONUP:
        pickUp = False
        master.volume = (sliderX - 150)/100
    pygame.display.update()
def tutorial():
  global gameState
  txtFont = pygame.font.Font(None, 24)
  hFont = pygame.font.Font(None, 64)

  bodies = [
    txtFont.render("Each level is a different song which", True, (0,0,0)),
    txtFont.render("you must help the purple pointer to", True, (0,0,0)),
    txtFont.render("navigate in order to play the song.", True, (0,0,0)),
    txtFont.render("", True, (0,0,0)),
    txtFont.render("In order to do this, you must press", True, (0,0,0)),
    txtFont.render("the space bar, click the mouse or tap", True, (0,0,0)),
    txtFont.render("the screen when the purple pointer", True, (0,0,0)),
    txtFont.render("collides with a note to play it.", True, (0,0,0)),
    txtFont.render("This will give the pointer enough", True, (0,0,0)),
    txtFont.render("of a jump to get to the next note.", True, (0,0,0))
  ]
  header = hFont.render("HOW TO PLAY", True, (0,0,0))
  back = Button(0, 0, "menu", "BACK", "l")

  while gameState == "tutorial":
    screen.fill((47,54,153))
    back.show()
    
    h = 0
    for body in bodies:
      screen.blit(body, (200 - body.get_width()//2, 100 + h))
      h += body.get_height() + 1
    screen.blit(header, (200-header.get_width()//2, 50))

    for event in pygame.event.get():
      if event.type == pygame.MOUSEBUTTONDOWN:
        if back.isClicked():
          gameState = "menu"
    pygame.display.update()


def getLevels():
  metaData = open("level/metaData").read()
  levelData = metaData.split(",")
  levels = {}
  print(f"loading {len(levelData)} levels")
  for datum in levelData:
    print(datum)
    name, bpm = datum.split(":")
    level = Level(name, bpm)
    levels[name] = level
    
  print("DONE!")
  return levels
  
#getLevels()

levels = getLevels()
level = "C"
levels[level].locked = False

while gameState != "quit":
  if gameState == "title":
    titleScreen()
  elif gameState == "menu":
    level = menu()
  elif gameState == "settings":
    settings()
  elif gameState == "play":
    level = levels[level].playLevel()
  elif gameState == "win":
    winScreen(level)
  elif gameState == "lose":
    loseScreen(level)
  elif gameState == "tutorial":
    tutorial()
