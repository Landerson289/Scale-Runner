import sys
import pygame
import time
#from replit import audio
#from pygame import mixer
#from playsound import playsound

noteOrder = ["E4", "F4", "G4", "A3", "B3", "C3", "D3", "E3", "F3"]
noteLengths = {
  "Crotchet" : 1,
  "Minim" : 2,
}

pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption('Hello World!')

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

  def update(self):
    #self.pos[0] += self.speed * deltaTime
    self.vel[1] += gravity * deltaTime
    self.pos[1] += self.vel[1] * deltaTime

  def show(self):
    screen.blit(self.sprite, (self.pos[0],self.pos[1]))

  def jump(self):
    for note in notes:
      if 0< (note.beat - beat) < note.length and note.y-16 < self.pos[1] < note.y+16:
        #self.vel[1] = -1*abs(self.vel[1]) - 1 * (note.length)
        nextNote = self.jumpTo(note.length, note.beat)
        print(note.beat, nextNote.beat)
        #1/6at^2 + 1/2v*t + deltaY
        #1/6*gravity*nextNote.beat**2 + 1/2*self.vel[1] * nextNote.beat + (self.pos[1]-nextNote.y) = 0
        self.vel[1] = (-gravity*(nextNote.beat-beat)**2 - (self.pos[1] - nextNote.y))/(nextNote.beat-beat)
        break
        
        
  def jumpTo(self, length, noteBeat):
    nextBeat = noteBeat + length
    noteBeforeBeat = notes[0] # Find the nearest note before the beat
    noteAfterBeat = notes[-1] # Find the nearest note after the beat
    for note in notes:
      #print(note.beat, nextBeat, noteAfterBeat.beat, abs(noteAfterBeat.beat - nextBeat), abs(note.beat - nextBeat))
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
  #print(1/(bpm*60)*slowFactor)
  #print(" ",currentTime - lastTime)
  #if currentTime - lastBeat >= 1/(bpm*60)*slowFactor:
  #  beat += 1
  #  lastBeat = time.time()
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
  #time.sleep(100)
