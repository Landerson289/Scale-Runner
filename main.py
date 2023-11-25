import pygame
import random
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
alphaString = "ABCDEFG"
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


pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption('Scale Runner!')

slowFactor = 4000
gravity = 250
bpm = 120

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
        note, freq, wavelength = row.split("	")
        if note[0] == " ":
          note = note[1:]

        if "/" in note:
          for i in note.split("/"):
            frequencies[i] = float(freq)
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

    data = b""
    for i in range(1,fpc):
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
    sampleWidth = oldFile.getsampwidth()
    sampleRate = oldFile.getframerate()*BbFreq/frequency
    length = oldFile.getnframes()
    data = oldFile.readframes(length)
    oldFile.close()

    newFile = wave.open(f"{self.name}/{note}.wav", "w")
    newFile.setnchannels(1)
    newFile.setsampwidth(sampleWidth)
    newFile.setframerate(sampleRate)
    newFile.writeframesraw(data)
    newFile.close()


class Player:
  def __init__(self, level):
    self.pos = [64.0,134.0]
    self.sprite = pygame.image.load("player.png")
    self.sprite = pygame.transform.scale(self.sprite, (16,16))
    var = pygame.PixelArray(self.sprite)
    var.replace((0,0,0),(255,0,255))
    del var
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

  def drawTrail(self):
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
      if -0.5 < (note.beat - self.level.beat) < 0.5 and note.y-16 < self.pos[1] < note.y+16:
        note.play()
        nextNote = self.jumpTo(note.length, note.beat)
        print(nextNote.beat)

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
          noteBeforeBeat = note
      elif note.beat >= nextBeat:
        if abs(noteAfterBeat.beat - nextBeat) > abs(note.beat - nextBeat):
          noteAfterBeat = note

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
      self.y = 198 - ((noteOrder.index(self.pitch) - e3)*16) - 8
      self.track = mixer.Sound(f"{manager.name}/{pitch}.wav")
    else:
      self.y = 70
    self.manager = manager
    
    self.isPlaying = False

  def show(self):
    self.x = 64 * (self.beat - self.level.beat) + 64

    screen.blit(self.sprite, (self.x,self.y))

    if self.dotted == True:
      pygame.draw.circle(screen, (0,0,0), (self.x+50, self.y+8), 8/2)

  def update(self):
    if self.isPlaying and self.level.beat >= self.beat + self.length:
      self.isPlaying = False
      self.track.stop()
      

  def play(self):
    if self.volume != self.manager.volume:
      self.track.set_volume(self.manager.volume)
    self.track.play()
    self.isPlaying = True

master = AudioManager("master")

wholeBeat = 0 # For testing
debugMenu = Debug()
debugMenu.showMenu = True

class Level:
  def __init__(self, name):
    self.name = name
    self.beat = -1.5
    self.lastTime = time.time()
    self.deltaTime = 0.001
    self.notes = self.loadLevel()
    self.doubleBarLine = Note("DoubleBarLine", "None", self.notes[-1].beat + self.notes[-1].length, master, self)
    self.player = Player(self)
    self.lastNote = False

  def drawBackground(self):
    screen.fill((255,255,255))
    for i in range(5):
      pygame.draw.rect(screen, (0,0,0), (0, i*32+70, 400, 4))


  def loadLevel(self):
    notes = []
    with open(f"level/{self.name}") as data:
      list = data.read().splitlines()
      for note in list:
        if len(note.split(" ")) == 3:
          beat, type, pitch = note.split(" ")
        else:
          beat, type1, type2, pitch = note.split(" ")
          type = type1 + " " + type2
        notes.append(Note(type, pitch, float(beat), master, self))
    return notes
    
  def playLevel(self):
    global gameState
    self.currentTime = time.time()
    self.lastTime = time.time()
    self.deltaTime = self.currentTime - self.lastTime
    self.lastNote = False
    self.beat = -1.5
    self.player.pos = [64.0,134.0]
    UIfont = pygame.font.Font(None, 32)
    while gameState == "play":
      self.lastTime = self.currentTime
      self.currentTime = time.time()
      self.deltaTime = self.currentTime - self.lastTime
      debugMenu.push("fps", 1/self.deltaTime)
    
      self.drawBackground()
      
      self.beat += 1/(bpm*60)*slowFactor*self.deltaTime
    
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
      if self.beat >= self.doubleBarLine.beat:
        gameState = "win"
        return level
      if self.player.pos[1] >= 300:
        gameState = "lose"
        return level
      if debugMenu.showMenu:
        debugMenu.show()

      beatUI = UIfont.render(f"beat: {int(self.beat//4)}.{int(self.beat%4+1)}", True, (0,0,0))
      bpmUI = UIfont.render(f"bpm: {bpm}", True, (0,0,0))
      screen.blit(beatUI, (20,20))
      screen.blit(bpmUI, (20,50))
      pygame.display.update()

class Button:
  def __init__(self,x, y, newState, text, align):
    self.y = y
    self.newState = newState
    self.text = text
    self.font = pygame.font.Font(None, 32)
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
          
def menu():
  global gameState, levels
  counter = 0
  hFont = pygame.font.Font(None, 96) # Header Font
  txtFont = pygame.font.Font(None, 32)
  button = Button(400, 0, "settings", "SETTINGS", "r")
  while gameState == "menu":
    screen.fill((47,54,153))
    keys = list(levels.keys())
    level = keys[counter]
    nameObj = hFont.render(level, True, (0,0,0))
    lnameObj = hFont.render(keys[(counter-1)%len(keys)], True, (0,0,0))
    rnameObj = hFont.render(keys[(counter+1)%len(keys)], True, (0,0,0))
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

    ltxtX =  5 - lnameObj.get_width()//2
    ltxtY = 75
    screen.blit(lnameObj, (ltxtX, ltxtY))

    rtxtX =  395 - rnameObj.get_width()//2
    rtxtY = 75
    screen.blit(rnameObj, (rtxtX, rtxtY))

    button.show()
    

    for event in pygame.event.get():
      if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_ESCAPE:
          pygame.quit()
          sys.exit()
      if event.type == pygame.MOUSEBUTTONDOWN:
        mousePos = pygame.mouse.get_pos()
        if button.isClicked():
          gameState = button.newState
          return
        elif 0 <= mousePos[0] <= 125:
          counter -= 1
          counter = counter%len(keys)
        elif mousePos[0] <= 275:
          gameState = "play"
          return level
        else:
          counter += 1
          counter = counter%len(keys)
      

    
    

    pygame.display.update()
def winScreen(level):
  global gameState
  hFont = pygame.font.Font(None, 64)
  winText1 = hFont.render("LEVEL", True, (0,0,0))
  winText2 = hFont.render("COMPLETED!", True, (0,0,0))
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
def loseScreen(level):
  global gameState
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
  while gameState == "settings":
    screen.fill((47,54,153))
    
    back.show()
    screen.blit(volumeText, (200-volumeText.get_width()//2, 125))
    pygame.draw.rect(screen, (174, 198, 207), (150, 150, 100, 5))
    pygame.draw.circle(screen, (10,10,70), (sliderX, 152), 10)

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
        
        if 150 <= pygame.mouse.get_pos()[0] <= 250 and 145 < pygame.mouse.get_pos()[1] < 155:
          pickUp = True
      if event.type == pygame.MOUSEBUTTONUP:
        pickUp = False
        master.volume = (sliderX - 150)/100
    pygame.display.update()
          
  
def getLevels():
  metaData = open("level/metaData").read()
  levelNames = metaData.split(",")
  levels = {}
  
  for name in levelNames:
    level = Level(name)
    levels[name] = level

  return levels
  
getLevels()

levels = getLevels()
level = "test"

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
