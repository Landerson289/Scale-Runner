import pygame
import random
import math
import time
from pygame import mixer

pygame.font.init()
testFont=pygame.font.Font("MotorolaScreentype.ttf",16)

noteOrder = ["E4", "F4", "G4", "A3", "B3", "C3", "D3", "E3", "F3"]
noteLengths = {
  "Crotchet" : 1,
  "Minim" : 2,
}

pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption('Scale Runner!')

slowFactor = 10
gravity = 10
bpm = 120

lastTime = time.time()

def drawBackground():
  screen.fill((255,255,255))
  for i in range(5):
    pygame.draw.rect(screen, (0,0,0), (0, i*32+70, 400, 4))

class Player:
  def __init__(self):
    self.pos = [64.0,134.0]
    self.vel = [0,5]
    self.sprite = pygame.image.load("player.png")
    self.sprite = pygame.transform.scale(self.sprite, (16,16))
    var = pygame.PixelArray(self.sprite)
    var.replace((0,0,0),(255,0,255))
    del var
    self.lastPositions = []

  def update(self):
    self.vel[1] += gravity * deltaTime
    self.lastPositions.append([beat,self.pos[1]])
    self.pos[1] += self.vel[1] * deltaTime

  def show(self):
    screen.blit(self.sprite, (self.pos[0],self.pos[1]))
    self.drawTrail()

  def drawTrail(self):
    text = testFont.render(str(len(self.lastPositions)), True, (0,0,0))
    screen.blit(text, (2,2))

    count = 0

    for i in range(1, len(self.lastPositions)//20):
      count += 1
      pos = self.lastPositions[len(self.lastPositions) - i*20]
      
      size = 16/(i+0.1)**0.5
      x  = 64 * (pos[0] - beat) + 64
      pygame.draw.circle(screen, (255,0,255), (x, pos[1]), size/2)

      if i >= 50:
        break
      

  def jump(self):
    for note in notes:
      if -note.length/2 < (note.beat - beat) < note.length/2 and note.y-16 < self.pos[1] < note.y+16:

        nextNote = self.jumpTo(note.length, note.beat)
        
        self.vel[1] = (self.pos[1]-nextNote.y)/(beat-nextNote.beat) - 1/6*gravity*(beat + nextNote.beat)

  def jumpTo(self, length, noteBeat):
    nextBeat = noteBeat + length
    noteBeforeBeat = notes[0] # Find the nearest note before the beat
    noteAfterBeat = notes[-1] # Find the nearest note after the beat
    for note in notes:
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
  def __init__(self, type, pitch, beat):
    self.type = type
    self.length = noteLengths[type]
    self.pitch = pitch
    self.beat = beat
    self.sprite = pygame.image.load(f"{type}.png")
    self.sprite = pygame.transform.scale(self.sprite, (32,72))
    self.x = 64 * (self.beat - beat) + 64
    self.y = 198 - (noteOrder.index(self.pitch)*16) - 8

  def show(self):
    self.x = 64 * (self.beat - beat) + 64

    screen.blit(self.sprite, (self.x,self.y))


player = Player()
notes = []
for i in range(len(noteOrder)):
  notes.append(Note("Crotchet", noteOrder[i], i))



beat = -1.5
currentTime = time.time()
lastBeat = time.time()

while True:
  lastTime = currentTime
  currentTime = time.time()
  deltaTime = currentTime - lastTime

  drawBackground()
  beat += 1/(bpm*60)*slowFactor

  player.update()
  player.show()
  for note in notes:
    note.show()

  for event in pygame.event.get():
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        pygame.quit()
        sys.exit()
      elif event.key == pygame.K_SPACE:
        player.jump()


  pygame.display.update()
