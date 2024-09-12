import tkinter
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import sv_ttk
import numpy as np
import time
from threading import Thread
import threading
from skimage import restoration, filters, color, io, measure
from scipy import ndimage as ndi
import skimage
from skimage.future import graph
from skimage.segmentation import slic
from skimage import img_as_float
tabNum = 0
imgtk = {}
image1 = {}
image2 = []
newimg = {}
def thread(start, command):
  if start:
    Thread(target=command).start()
  else:
    Thread(target=command).stop()
  return

  
class MainApplication(Tk):
  def __init__(self):
    global newimg
    self.started = False
    super().__init__()
    
    self.title("Image to heightmap")
    self.geometry('800x600')
    self.rlBlImg = {}
    self.depthImg = {}
    self.nb = ttk.Notebook(self)
    sv_ttk.set_theme("light")
    self.frm1 = frm(self.nb, True, False)
    self.frm2 = frm(self.nb, False, False)
    self.frm3 = frm(self.nb, False, True)
    self.progress1 = ttk.Progressbar(self.frm2, mode="indeterminate", length=200)
    self.nb.add(self.frm1, text="First tab")
    self.nb.add(self.frm2, text="Second tab", )
    self.nb.add(self.frm3, text="image")
    self.nb.grid()
    self.nb.hide(self.frm2)
    def paginate(child, container, dir):
      global tabNum
      if child.checDir(self, dir):
        self.nb.add(self.nb.tabs()[tabNum+dir])
        self.nb.select(self.nb.tabs()[tabNum+dir])
        self.nb.hide(self.nb.tabs()[tabNum])

        tabNum += dir
        
    def openFile():
      global imgtk
      global image1
      image1 = Image.open(filedialog.askopenfilename())
      imgtk = ImageTk.PhotoImage(image = image1)
      imgtk.image = imgtk
      self.frm1.img(imgtk)
      self.frm2.img(imgtk)
    def rlBall(image):
      if self.started == False:
        global image2
        image2 = image
        progress(self, False)
        self.rb = processing("bgGen")
        self.rb.daemon = True
        self.rb.start()
        self.started = True
        app.after(1000, app.statusTest, "bgGen")
    def depthTex():
      if self.started == False:
        progress(self, False)
        self.dt = processing("depth")
        self.dt.daemon = True
        self.dt.start()
        self.started = True        
        app.after(1000, app.statusTest, "depth")
    def thresCall(thres, image):
      global newimg
      image = np.asarray(image)
      img = threshold(image, thres, self.rlBlImg)
      newimg = img
      img = Image.fromarray(newimg)
      img.image = img
      self.frm2.img(ImageTk.PhotoImage(image = img))
    def threshold(image, thres, background):
      image = np.array(image)
      thres = int(thres)
      background = color.rgb2gray(color.rgba2rgb(background))*255 < (thres)
      fill = ndi.binary_fill_holes(background)
      image[fill == True] = 0
      return image
    def progress(self, remove):
      if remove:
        self.progress1.grid_remove()
      else:
        self.progress1.grid(row=2, columnspan=3, sticky="EW", pady=10, padx=10)
        self.progress1.start()
    self.nb.paginate = paginate
    self.nb.rlBall = rlBall
    self.nb.depthTex = depthTex
    self.progress = progress
    thres = 10
    s = ttk.Scale(self.frm2, orient=HORIZONTAL, length=200, from_=1.0, to=255, variable=thres, command= lambda thres: thresCall(s.get(), image1))
    s.grid(row="1", sticky='EW', columnspan="3", pady=10, padx=10)
    self.frm1.open = ttk.Button(self.frm1, text="Open File", command= lambda: openFile())
    self.frm1.open.grid(row=1, column=1)
  def statusTest(self, cmd):
    if self.started == True:
      global image2
      global newimg
      if cmd == "bgGen":
        self.rlBlImg = self.rb.bgGen(image2)
        self.rb.join()
        self.started = False
        self.progress(self, True)
      elif cmd == "depth":
        self.depthImg = self.dt.depth(image2, newimg)
        self.dt.join()
        self.started = False
        self.progress(self, True)
    app.after(10000, self.statLoop, cmd)
  def statLoop(self, cmd):
    self.statusTest(cmd)
class frm(ttk.Frame):
  def __init__(self, container, first, last):
    super().__init__(container)
    self.forBut = ttk.Button(self, text="Next", command= lambda: container.paginate(self, container,  1))
    self.bacBut = ttk.Button(self, text="Back", command= lambda: container.paginate(self, container, -1))
    self.genBtn = ttk.Button(self, text="Generate", command= lambda: container.rlBall(image1))
    self.depBtn = ttk.Button(self, text="Generate Depth Map", command= lambda: container.depthTex())
    self.bacBut.grid(column=0, row=10, sticky="s")
    self.forBut.grid(column=2, row=10, sticky="s")
    
    if first:
      self.bacBut["state"] = DISABLED
    elif last:
      self.forBut["state"] = DISABLED
    if "frm2" in str(self):
      self.genBtn.grid(row=10, column=1)
    if "frm3" in str(self):
      self.depBtn.grid(row=10, column=1)
  def img(self, img):
    self.imgfrm = ttk.Label(self, image = img)
    self.imgfrm.image = img
    self.imgfrm.grid(row=0, column=1)
  def checDir(self, container, dir):
    global tabNum
    try:
      container.nb.tabs()[tabNum+dir]
      return True
    except IndexError:
      return False
      
class processing(Thread):
  def __init__(self, image):
    super().__init__()
    self.image = image
  def test(image, frame):
    image = color.rgb2gray(color.rgba2rgb(image))
    
    return image * 255
  def bgGen(self, image):
    background = restoration.rolling_ball(image, radius=16)
    return background
  def depth(self, image, foreground):
    np_img = np.asarray(color.rgba2rgb(image)) #Convert to RGB colour space for later processing
    #segmentation stage
    #SLIC image segmentation
    labels1 = slic(np_img, compactness=30, n_segments=400, start_label=1) 
    #colour reduction
    g = graph.rag_mean_color(np_img, labels1) 
    labels2 = graph.cut_threshold(labels1, g, 50)
    out2 = color.label2rgb(labels2, np_img, kind='avg', bg_label=0) 
    edges = filters.roberts(color.rgb2gray(out2)) #Roberts filtering for basic colour bordering to enhance tactile interpretation
    edges_base = filters.roberts(color.rgb2gray(color.rgba2rgb(foreground))) #roberts filtering to reintroduce the textures of the image such as hair, paint strokes etc.
    chull_diff = img_as_float(edges_base.copy()) 
    chull_diff[edges.astype(bool)] = 0.75
    io.imsave("Result.png", chull_diff)
    return chull_diff
  def run(self):
    pass
    
if __name__ == '__main__':
  app = MainApplication()
  app.mainloop()

  