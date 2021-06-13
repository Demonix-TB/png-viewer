# -*- coding: UTF-8 -*-
from os import environ
from random import randint
from time import sleep
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "no, stop, don't be adware"#stops pygame from acting like shellbased adware aka disables pygame shell advert
import sys, os, pygame, zlib, numpy#, time, timeit, math, binascii
#might replace pygame with something faster later, it does it's job for now
#from pygame.locals import *
pygame.init()
CRC_FLAG = True
PLTE_FLAG = False
image_data = []
PALETTE = []
iwidth = iheight = bit_depth = color_mode = compression_type = filter_method = interlace = bytes_per_pixel = None
#a program to open and view .PNG files without processing through external libraries, with the exception of physically displaying the image, and for now zlib for decompression
#created by simply following the Portable Network Graphics (PNG) Specification (Second Edition) @ https://www.w3.org/TR/2003/REC-PNG-20031110

#A Note: V tomto programu píši i české i anglické komentáře, podle toho jak zrovna přemýšlím.
#If you're bilingual this shouldn't pose any problems, but if you aren't, tak je to špatný, and I am sorry for doing this.
#Code is being somewhat actively maintained at https://github.com/Demonix-TB/png-viewer
#Vytvořeno jako školní ročníková práce, T.B. IT3A 2020.
### marks distinct sections of the program

### CRC
def crc_32(data,crc=0,polynomial=0xedb88320): #celý chunk bere jako jeden binarni stream, prejede pres něj >> if xor polynomu a vyjde cislo crc
    crc = 0xffffffff & ~crc
    for i,j in enumerate(data):
        crc = crc ^ data[i]
        #print(-(crc & 1),~(crc & 1)+1)
        for _ in range(8):
            
            crc = (crc >> 1) ^ (polynomial & ~(crc & 1)+1)
            # if crc & 1 is 0 then ~ of it will be all 1's adding 1 to it makes it 0 again
            # jelikož  a ^ 0 = a je to vlastně převedení na to jestli budeme provadět (crc >> 1) ^ polynomial, nebo jen crc >> 1 
            
            #funguje jako
            #crc = (crc & 1 ? (crc >> 1) ^ polynomial: crc >> 1)
            #bez použití if branch
    #h = data % polynomial
    print("crc is ",crc, 0xffffffff & ~crc)
    return 0xffffffff & ~crc

#měsíc práce a teď zjistím že pro IDAT chunky je to moc pomalé vypočítat v reálném čase
# a musím použít precomputed tabulky nebo zlib FML D:
#tak jako zatím nemusím ale nechce se mi
## update: OPTIMALIZACE POMOHLY

def checkcrc(data):
    crcRes = crc_32(data)
    #print(data[0:4],crcRes)
    infilecrc = int.from_bytes(file.read(4),'big')
    #print(infilecrc)
    if crcRes != infilecrc:
        file.seek(-24,os.SEEK_CUR)
        debug = [int.from_bytes(file.read(4),'big') for x in range(8)]
        print('PNG datastream corrupted, terminating. debug info:', crcRes, infilecrc, debug)
        sys.exit(0)

### Mandatory Chunk methods
def IHDR(file,length):
    #print('IHDR')
    data = file.read(length)
    
    global iwidth, iheight, bit_depth, color_mode, compression_type, filter_method, interlace, bytes_per_pixel
    
    iwidth = int.from_bytes(data[0:4],'big')
    iheight = int.from_bytes(data[4:8],'big')
    bit_depth = int.from_bytes(data[8:9],'big')
    color_mode = int.from_bytes(data[9:10],'big')
    compression_type = int.from_bytes(data[10:11],'big')
    filter_method = int.from_bytes(data[11:12],'big')
    interlace = int.from_bytes(data[12:13],'big')    
    ### bytes per pixel

    if color_mode == 0:
        bytes_per_pixel = 1
    elif color_mode == 2:
        bytes_per_pixel = 3
    elif color_mode == 3:
        #for x in decomp_data:
        global PLTE_FLAG
        PLTE_FLAG = True
        bytes_per_pixel = 1
    elif color_mode == 4:
        bytes_per_pixel = 2
    elif color_mode == 6:
        bytes_per_pixel = 4
    else:
        print("invalid colortype",color_mode)
        sys.exit(0)
    ### 
    #print('IHDR done')
    #print([iwidth,iheight,bit_depth,color_mode,compression_type,filter_method,interlace])
    checkcrc(b'IHDR'+data)
    return

def IDAT(file,length):
    #for the longest time I was getting all image data recursively from the first IDAT chunk,
    #which is terrible, so after another two days of work that attrocity is now gone
    
    #print('IDAT')
    data = file.read(length)
    global image_data
    image_data += data
    global CRC_FLAG
    if CRC_FLAG:            
        checkcrc(b'IDAT'+data)
    else:
        file.read(4)
    return

def PLTE(file,length):
    #print('PLTE')
    #print('Pallete type PNG files are not yet supported by this app. \nSorry.')
    data = file.read(length)
    global PALETTE
    PALETTE = {}
    for i in range(len(data)//3):
        r=int(data[i*3])
        g=int(data[i*3+1])
        b=int(data[i*3+2])
        pixel = [r,g,b]
        PALETTE.update({i: pixel[:]})    
    checkcrc(b'PLTE'+data)
    return   

def IEND(file,length):
    #print('IEND')
    data = file.read(length)
    checkcrc(b'IEND'+data)   
    global f_is_open
    f_is_open = False
    file.close()
    return



### Auxiliary/Ancillary chunk methods
def unsupportedCh(file,length):
    print('unknown chunk type, something went wrong?','length:',length,'file',file)
    return    

def sBIT(file,length):
    #print('sBIT')
    data = file.read(length)
    checkcrc(b'sBIT'+data)
    return

def gAMA(file,length):
    #print('gAMA')
    data = file.read(length)
    checkcrc(b'gAMA'+data)
    return
    
def cHRM(file,length):
    #print('cHRM')
    data = file.read(length)
    checkcrc(b'cHRM'+data)
    return

def sRGB(file,length):
    #print('sRGB')
    data = file.read(length)
    checkcrc(b'sRGB'+data)
    return

def iCCP(file,length):
    #print('iCCP')
    data = file.read(length)
    checkcrc(b'iCCP'+data)
    return

def tRNS(file,length):
    #print('tRNS')
    data = file.read(length)
    checkcrc(b'tRNS'+data)
    return

def zTXt(file,length):
    print('zTXt')
    data = bytes(file.read(length))
    checkcrc(b'zTXt'+data)
    data.split(b'\x00')
    print(hex(data[1]))
    bytes(list(data[1])[1:])
    inflated_text = str(zlib.decompress(bytes(data[1]),wbits = -zlib.MAX_WBITS))
    print(str(data[0]),inflated_text,sep=':\n')
    return

def tEXt(file,length):
    #print('tEXt')
    data = file.read(length)
    checkcrc(b'tEXt'+data)
    data.split(b'\x00')
    print(data[0],data[1],sep=':\n')
    return

def iTXt(file,length):#te
    #print('iTXt')
    data = file.read(length)
    checkcrc(b'iTXt'+data)
    print('information regarding this image:')
    print(data)
    return

def tIME(file,length):
    #print('tIME')
    data = file.read(length)
    checkcrc(b'tIME'+data)
    print('Last modified: ',int.from_bytes(data[0:1],'big'),' ',int.from_bytes(data[2],'big'),'.',int.from_bytes(data[3],'big')
          ,'. ',int.from_bytes(data[4],'big'),':',int.from_bytes(data[5],'big'),':',int.from_bytes(data[6],'big'))
    print(data)
    return
    
def pHYs(file,length):
    #print('pHYs')
    data = file.read(length)
    #print(int.from_bytes(data[0:3],'big'))
    #print(int.from_bytes(data[4:7],'big'))
    #print(data[8])
    checkcrc(b'pHYs'+data)
    return

def bKGD(file,length):
    #print('bKGD')
    data = file.read(length)
    checkcrc(b'bKGD'+data)
    return

def hIST(file,length):
    #print('hIST')
    data = file.read(length)
    checkcrc(b'hIST'+data)
    return

def sPLT(file,length):
    #print('sPLT')
    data = file.read(length)
    checkcrc(b'sPLT'+data)
    return

### open the image --- aka --- Main
def process_png():
    global image_data, bytes_per_pixel, PLTE_FLAG
    d = zlib.decompressobj()
    inflate = d.decompress(bytes(image_data))
    decomp_data = [x for x in inflate]
    #with open('imgoutputarr.txt','w+') as debug: #uncomment to debug
    #    debug.write(str(decomp_data))
    #    debug.close()
    serialised_data = []
    filtertypes=[]
 
    for i in range(iheight):
        filtertypes.append(decomp_data[i*iwidth*bytes_per_pixel+i])
        serialised_data.append(decomp_data[
            i * iwidth * bytes_per_pixel + i + 1:
            (i + 1) * iwidth * bytes_per_pixel + i + 1])
    
    if PLTE_FLAG:
        serialised_data = [item for sublist in serialised_data for item in sublist]
        #print(serialised_data)       
        
    #print('filtertypes:',filtertypes)#'scanlines',serialised_data,[len(serialised_data[x]) for x in range(len(serialised_data))])
    
    filtered_data = []
    prv_scl = [0] * iwidth * bytes_per_pixel
    
    ### filtering of the scanlines of pixels
    if not PLTE_FLAG:
        for i in range(iheight): #only works for non interlaced images, will break spectacularly if you try an interlaced image as those arent implemented yet
            ft = filtertypes[i]
            scl = serialised_data[i]
            filtered_scl = []
            #print("scl",scl,len(scl))
            if ft == 0: #no filtering x = x
                filtered_scl = scl[:]
                #print('OK,0')
            elif ft == 1: #previous filtering x = x + a
                prvpx_scl = [0] * bytes_per_pixel
                prvpx_scl += scl[:]
                #filtered_scl = [ch & 0xff for ch in map(int.__add__, prvpx_scl, scl)]
                for i in range(len(scl)):
                    prvpx_scl[i+bytes_per_pixel] = (scl[i] + prvpx_scl[i]) & 0xff
                filtered_scl = prvpx_scl[bytes_per_pixel:]
                
            elif ft == 2: #up filtering x = x + b
                filtered_scl = [(x + b) & 0xff for x, b in zip(scl,prv_scl)]
                
            elif ft == 3: #average filtering x = (x + b)//2
                prvpx_scl = [0] * bytes_per_pixel
                prvpx_scl += scl[:]
                #filtered_scl = [ch & 0xff for ch in map(int.__add__, prvpx_scl, scl)]
                for i in range(len(scl)):
                    prvpx_scl[i+bytes_per_pixel] = (scl[i] + (prvpx_scl[i] + prv_scl[i]) // 2) & 0xff #prvpx_scl[i] is same as scl[i-bpp]
                filtered_scl = prvpx_scl[bytes_per_pixel:]
                ''' failed attempt number 9999999999
                #list with bytes coresponding to the previous pixel in 
                prvpx_scl = [0 for z in range(bytes_per_pixel)]
                prvpx_scl += scl[:-bytes_per_pixel]
                #print(scl)
                #print(prv_scl)
                #print(prvpx_scl)
                filtered_scl = [ch & 0xff for ch in map(lambda scl, a, b: math.floor(a + b) + scl, scl, prvpx_scl, prv_scl)]'''
                
            elif ft == 4: #paeth filtering, this took like 2 months to fix because i was trying to optimise and forgot A has to be filtered
                                       
                filtered_scl = scl[:]
                
                ch_i = 0 - bytes_per_pixel
                for i in range(len(scl)):
                    x = scl[i]
                    if ch_i < 0:
                        a, c = 0, 0
                    else:
                        a = filtered_scl[ch_i]
                        c = prv_scl[ch_i]
                    b = prv_scl[i]
                    p = a + b - c
                    pa = abs(p - a)
                    pb = abs(p - b)
                    pc = abs(p - c)
                    
                    if pa <= pb and pa <= pc:
                        pr = a
                        
                    elif pb <= pc:
                        pr = b
                         
                    else:
                        pr = c
                    ch_i += 1
                    
                    filtered_scl[i] = x + pr & 0xff # option a
                    
                    #filtered_scl[i] = x + pr
               #filtered_scl = [_a & 0xff for _a in filtered_scl] # option b
                
            else:
                #print('fatal error wtf')#for now reached by interlaced images
                filtered_scl = [x & 0xff for x in scl[:]]
                #sys.exit(0)
                
            prv_scl = filtered_scl[:] #b
            filtered_data += filtered_scl[:]
            #print(filtered_scl)
    else:
        filtered_data = serialised_data
        #print(filtered_data)
    '''
    with open('filtered_data.txt','w+') as debug: #uncomment for debugging
        debug.write(str(filtered_data))
        debug.close()
    with open('serialised_unf_data.txt','w+') as debug: #uncomment to debug
        debug.write(str(serialised_data)+"\n\n"+str(filtertypes))
        debug.close()
    '''
    return filtered_data
    
def display_png(image,filename):
    global bytes_per_pixel
    #print("filtered data:",filtered_data)
    #debuggerstatement=input("press enter, this is a debug statement")    
    #scf = 1
    scf = 1 #scalefactor   
    pygame.display.set_caption(filename)
    PNG = pygame.display.set_mode((iwidth*scf,iheight*scf))
    PNG_area = pygame.Surface((iwidth*scf,iheight*scf))
    pixel_i = 0
    #print('height:',iheight, 'width:',iwidth)
    #BG = pygame.Surface((iwidth*scf,iheight*scf))
    #BG.fill((128,128,128,255))
    #PNG.blit(BG,(0,0))
    if PLTE_FLAG:
        global PALETTE
        
    txtfile = ""
    for height in range(iheight):
        #print(height)
        scanlinetext = ""
        for width in range(iwidth):
             
            #print(width)
            if PLTE_FLAG:
                #print(image[pixel_i])
                #print(PALETTE)
                color = PALETTE.get(image[pixel_i])

            else:
                color = image[pixel_i:pixel_i+bytes_per_pixel]
            
            #if len(color) != 4: color.append(0)
            #print(color)
            
            if scf > 1:
                for x in range(scf):
                    for y in range(scf):
                        PNG_area.set_at((width*scf+x,height*scf+y),color)

            else:
                #print(str(color))
                if color == (128, 255, 128):
                    color = (255, 0, 255)
                PNG_area.set_at((width,height),color)
            pixel_i += bytes_per_pixel
            scanlinetext+=' '.join([str(elem) for elem in color])+' '
        txtfile += scanlinetext + "\n"
    with open('textfile','w+') as txtf:
        txtf.write(txtfile)
        txtf.close()


            
    PNG.blit(PNG_area,(0,0))
    
    viewing = True 
    while viewing:
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print('shutting down')
                pygame.display.quit()
                pygame.quit()
                viewing = False            
        
        #serialised_data += itr
        #for i in range(iwidth):
         #   serialised_data += [zip(itr,itr,itr)]
            
        #serialised_data[scl*iheight][decomp_data[scl*(iwidth):scl*iwidth+iwidth+1]]
        #iwidth == width in pixels
    #print(serialised_data)
    #filteridat(serialised_data,flags)
        #if color_mode #colormode flag
    #file.seek(-12,os.SEEK_CUR)
    #print('IDAT done')
    #print(len(dataforcrc))

    #fp = tkinter.askopenfilename() i could do this but that would mean using yet another library and i do not want to do that
         
userinput = input("Provide a relative or absolute .png file path to open"+
                  "\n(optional flags:' -crc' = disable crc checking for image data for slightly faster results)"+
                  "\n> ")
userinput = userinput.split(' -')
fp = userinput[0]
display_filename = fp.split('\\')[-1]
#print(display_filename)
if len(userinput) != 1:
    if userinput[1] == 'crc':
        CRC_FLAG = False
        print('crc checking disabled')
  
#print(len(userinput))

    #pass #do nothing
with open(fp,"rb") as file:    
    #start = timeit.default_timer()
    mandatoryChunks = { #dicts of supported PNG chunks
        b'IHDR':IHDR,
        b'IDAT':IDAT,
        b'IEND':IEND,
        b'PLTE':PLTE
        }
    supAuxChunks = {
        b'sBIT':sBIT,
        b'gAMA':gAMA,
        b'cHRM':cHRM,
        b'sRGB':sRGB,
        b'iCCP':iCCP,
        b'pHYs':pHYs,
        b'tEXt':tEXt,
        b'zTXt':zTXt,
        b'iTXt':iTXt,
        b'tIME':tIME,
        b'bCKG':bKGD,
        b'hIST':hIST,
        b'sPLT':sPLT
                    } #most of the suplementary chunks are currently not working, they are only read and crc checked in order to not break anything 
    
    #check PNG signature
    currentbytes = file.read(8)
    
    try:
        currentbytes == b'\x89PNG\r\n\x1a\n' #[137,80,78,71,13,10,26,10]
    except:
        print('The PNG signature does not match. Unknown Filetype or corrupted Datastream, terminating.')
        sys.exit(0)
        
    f_is_open = True #changes to False in IDAT() on file close,
    #I know this is hacky and bad but for whatever reason I didn't want to write this in a class
    #so that's why there are globals in places.. sorry?
    while f_is_open:
        length = int.from_bytes(file.read(4),'big')
    
        #print(length)
        chunktype=file.read(4)
        if chunktype in mandatoryChunks:
            mandatoryChunks[chunktype](file,length)
        elif chunktype in supAuxChunks:
            supAuxChunks[chunktype](file,length)          
        else:
            print(chunktype)
            unsupportedCh(file,length)
        #nothing = file.read(4)
    processed_png = process_png()
    display_png(processed_png,display_filename)