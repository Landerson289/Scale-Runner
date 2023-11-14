import pygame
import random
import math as maths
import sys
import struct
import time
from pygame import mixer
import wave
import os

pygame.init()


noteOrder = ["E3", "F3", "G3", "A3", "B3", "C4", "D4", "E4", "F4"]
noteLengths = {
  "DoubleBarLine": -1,
  "Crotchet" : 1,
  "Minim" : 2,
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
    self.font = pygame.font.Font("MotorolaScreentype.ttf",16)
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
    self.noteFrequencies = self.getFrequencies()
    self.sampleRate = 88200
    self.sampleWidth = 1
    self.name = name
    try:
      os.mkdir(f"{self.name}")
    except:
      pass
    
    for i in self.noteFrequencies:
      self.generateNote(i)

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
      if -note.length/2 < (note.beat - self.level.beat) < note.length/2 and note.y-16 < self.pos[1] < note.y+16:
        note.play()
        nextNote = self.jumpTo(note.length, note.beat)

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
    return targetNote


class Note:
  def __init__(self, type, pitch, beat, manager, level):
    self.type = type
    self.length = noteLengths[type]
    self.pitch = pitch
    self.level = level
    self.beat = beat
    self.sprite = pygame.image.load(f"{type}.png")
    self.sprite = pygame.transform.scale(self.sprite, (32,72))
    self.x = 64 * (self.beat - self.level.beat) + 64
    if self.pitch != None:
      print(self.pitch)
      self.y = 198 - (noteOrder.index(self.pitch)*16) - 8
      self.track = mixer.Sound(f"{manager.name}/{pitch}.wav")
    else:
      self.y = 70
    self.manager = manager
    
    self.isPlaying = False

  def show(self):
    self.x = 64 * (self.beat - self.level.beat) + 64

    screen.blit(self.sprite, (self.x,self.y))

  def update(self):
    if self.isPlaying and self.level.beat >= self.beat + self.length:
      self.isPlaying = False
      self.track.stop()
      

  def play(self):
    self.track.play()
    self.isPlaying = True
    
class Level:
  def __init__(self, name):
    self.name = name
    self.beat = -1.5
    self.currentTime = time.time()
    self.lastTime = time.time()
    self.deltaTime = 0.001
    self.notes = self.loadLevel()
    self.doubleBarLine = Note("DoubleBarLine", None, self.notes[-1].beat +1, master, self)
    self.player = Player(self)

  def drawBackground(self):
    screen.fill((255,255,255))
    for i in range(5):
      pygame.draw.rect(screen, (0,0,0), (0, i*32+70, 400, 4))


  def loadLevel(self):
    notes = [] # Read notes from level files
    for i in range(len(noteOrder)):
      notes.append(Note("Crotchet", noteOrder[i], i, master, self))
    return notes
    
  def playLevel(self):
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
      if self.beat <= self.doubleBarLine.beat:
        gameState = "win"
      if self.player.pos[1] <= 300:
        gameState = "lose"
      if debugMenu.showMenu:
        debugMenu.show()
      pygame.display.update()

master = AudioManager("master")
debugMenu = Debug()
debugMenu.showMenu = True

gameState = "menu"
testLevel = Level("0")

while gameState != "quit":
  if gameState == "menu":
    pass
  elif gameState == "play":
    testLevel.playLevel()
  elif gameState == "win":
    pass
  elif gameState == "lose":
    pass
