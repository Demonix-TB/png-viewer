#open-a-png-with-almost-no-zlib
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "no,stop,fckin adware"#stops pygame from acting like shellbased adware
import sys, os, pygame, zlib, timeit #, math #, binascii
#from pygame.locals import *
pygame.init()
   
def crc_32(data,crc=0,polynomial=0xedb88320): #celý chunk bere jako jeden binarni stream, prejede pres něj >> if xor polynomu a vyjde cislo crc
    crc = 0xffffffff & ~crc
    for i in range(len(data)):
        crc = crc ^ data[i]
        for j in range(8):
            crc = (crc >> 1) ^ (polynomial & -(crc & 1))
            #funguje jako
            #crc = (crc & 1 ? crc ^ polynomial >> 1: crc >> 1)
            #bez použití if branch
    return 0xffffffff & ~crc

#měsíc práce a teď zjistím že pro IDAT chunky je to moc pomalé vypočítat v reálném čase
# a musím použít precomputed tabulky nebo zlib FML D:
#tak jako zatím nemusím ale nechce se mi

def checkcrc(data):
    usezlib=True
    #if len(data)<2048:
        #usezlib=False
    #if usezlib:
     #   crcRes = zlib.crc32(data)
    #else:
    crcRes = crc_32(data)
    #print(data[0:4],crcRes)
    infilecrc = int.from_bytes(file.read(4),'big')
    #print(infilecrc)
    if crcRes != infilecrc:
        file.seek(-24,os.SEEK_CUR)
        debug = [int.from_bytes(file.read(4),'big') for x in range(8)]
        print('PNG datastream corrupted, ',crcRes,infilecrc,debug)#terminating.
        #sys.exit(0)

def IHDR(file,length):
    print('IHDR')
    data = file.read(length)
    
    global iwidth
    iwidth = int.from_bytes(data[0:4],'big')
    global iheight
    iheight = int.from_bytes(data[4:8],'big')
    global bit_depth
    bit_depth = int.from_bytes(data[8:9],'big')
    global color_mode
    color_mode = int.from_bytes(data[9:10],'big')
    global compression_type
    compression_type = int.from_bytes(data[10:11],'big')
    global filter_method
    filter_method = int.from_bytes(data[11:12],'big')
    global interlace
    interlace = int.from_bytes(data[12:13],'big')
    #print('IHDR done')
    #print([iwidth,iheight,bit_depth,color_mode,compression_type,filter_method,interlace])
    checkcrc(b'IHDR'+data)
    return

def IDAT(file,length,MainAsCaller=True,do_crc=True):
    print('IDAT')
    data=file.read(length)
    fulldata = data
    #print(len(fulldata))
    checkNextidat = file.read(12)
    if checkNextidat[8:] == b'IDAT': #recursively get all IDAT data
        #print('next is IDAT')
        fulldata = data + IDAT(file,int.from_bytes(checkNextidat[4:8],'big'),False)
        #print(len(fulldata))
    file.seek(-12,os.SEEK_CUR)
    if MainAsCaller == False:
        if do_crc:
            
            checkcrc(b'IDAT'+data)
        else:
            file.read(4)
        file.seek(-4-length,os.SEEK_CUR)
        return fulldata
    else:
        d = zlib.decompressobj()
        inflate = d.decompress(fulldata)
        decompdata = [x for x in inflate]
        #with open('imgoutputarr.txt','w+') as debug: #uncomment to debug
        #    debug.write(str(decompdata))
        #    debug.close()
        #if flags[5] != 0: #filter method flag, 0 == no filter
        ### bytes per pixel
        if color_mode == 0:
            pass
        elif color_mode == 2:
            bytes_per_pixel = 3
        elif color_mode == 3:
            #for x in decompdata:
            pass        
        elif color_mode == 4:
            pass
        elif color_mode == 6:
            bytes_per_pixel = 4
        else:
            print("invalid colortype",color_mode)
            sys.exit(0)
        ### scan line serialisation,,,gotta redo partially :/!
        serialised_data = []
        filtertypes=[]
        for i in range(iheight):
            filtertypes.append(decompdata[i*iwidth*bytes_per_pixel+i])
            serialised_data.append(decompdata[
                i*iwidth*bytes_per_pixel+i+1:
                (i+1)*iwidth*bytes_per_pixel+i+1])
        print('filtertypes:',filtertypes)#'scanlines',serialised_data,[len(serialised_data[x]) for x in range(len(serialised_data))])
        filtered_data = []
        prv_scl = [0] * iwidth * bytes_per_pixel
        
        ### filtering of the scanlines of pixels
        for ft,scl in zip(filtertypes,serialised_data): 
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
                ''' failed attempt 41324
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
                    filtered_scl[i] = (x + pr) & 0xff
                    ch_i += 1
                
            else:
                print('fatal error wtf')
                sys.exit(0)
            prv_scl = filtered_scl[:] #b
            filtered_data += filtered_scl[:]
            #print(filtered_scl)
            
        stop = timeit.default_timer()
        print("program runtime ", stop - start)
        '''
        with open('filtered_data.txt','w+') as debug: #uncomment to debug
            debug.write(str(filtered_data))
            debug.close()
        with open('serialised_unf_data.txt','w+') as debug: #uncomment to debug
            debug.write(str(serialised_data)+"\n\n"+str(filtertypes))
            debug.close()
        '''
        #print("filtered data:",filtered_data)
        #debuggerstatement=input("press enter, this is a debug statement")    
        #scf = 1
        scf = 1 #scalefactor
        
        
        PNG = pygame.display.set_mode((iwidth*scf,iheight*scf),depth=24)
        PNG_area = pygame.Surface((iwidth*scf,iheight*scf))
        pixel_i = 0
        print('height:',iheight, 'width:',iwidth)
        #BG = pygame.Surface((iwidth*scf,iheight*scf))
        #BG.fill((128,128,128,255))
        #PNG.blit(BG,(0,0))
        for height in range(iheight):
            #print(height)
            for width in range(iwidth):
                #print(width)
                color = filtered_data[pixel_i:pixel_i+bytes_per_pixel]
                
                #if len(color) != 4: color.append(0)
                #print(color)
                
                if scf > 1:
                    for x in range(scf):
                        for y in range(scf):
                            PNG_area.set_at((width*scf+x,height*scf+y),color)
                else:
                    PNG_area.set_at((width,height),color)
                pixel_i += bytes_per_pixel
                
        PNG.blit(PNG_area,(0,0))
        
        clock = pygame.time.Clock()
        while True:
            for event in pygame.event.get():
                if event.type == "QUIT":
                    pygame.quit()
            clock.tick(30)
            pygame.display.update()
            
            #serialised_data += itr
            #for i in range(iwidth):
             #   serialised_data += [zip(itr,itr,itr)]
                
            #serialised_data[scl*iheight][decompdata[scl*(iwidth):scl*iwidth+iwidth+1]]
            #iwidth == width in pixels
        #print(serialised_data)
        #filteridat(serialised_data,flags)
        #if color_mode #colormode flag
    #file.seek(-12,os.SEEK_CUR)
    #print('IDAT done')
    #print(len(dataforcrc))
    if do_crc:
            checkcrc(b'IDAT'+data)
    else:
        file.read(4)
    return
    
def IEND(file,length,flags):
    file.read(length)
    checkcrc(b'IEND'+data)
    print('IEND')
    
    print('Time:',stop-start)
    file.close()
    sys.exit(0)
    
def unsupportedCh(file,length,flags):
    print('unknown chunk type, something went wrong?')
    sys.exit(0)    
    
def gAMA(file,length):
    print('gAMA')
    data = file.read(length)
    checkcrc(b'gAMA'+data)
    return
    
def cHRM(file,length):
    print('cHRM')
    data = file.read(length)
    checkcrc(b'cHRM'+data)
    return

def sRGB(file,length):
    print('sRGB')
    data = file.read(length)
    checkcrc(b'sRGB'+data)
    return
    
def pHYs(file,length):
    print('pHYs')
    data = file.read(length)
    print(int.from_bytes(data[0:3],'big'))
    print(int.from_bytes(data[4:7],'big'))
    print(data[8])
    checkcrc(b'pHYs'+data)
    return
    
fp = input("Provide a relative or absolute .png file path to open:")
with open(fp,"rb") as file:    
    start = timeit.default_timer()
    mandatoryChunks = { #dicts of supported PNG chunks
        b'IHDR':IHDR,
        b'IDAT':IDAT,
        b'IEND':IEND
        }
    supAuxChunks = {
        b'gAMA':gAMA,
        b'cHRM':cHRM,
        b'sRGB':sRGB,
        b'pHYs':pHYs
                    } #none of the suplementary chunks are currently done
    
    #check PNG signature
    currentbytes = file.read(8)
    
    try:
        currentbytes == b'\x89PNG\r\n\x1a\n' #[137,80,78,71,13,10,26,10]
    except:
        print('The PNG signature does not match. Unknown Filetype or corrupted Datastream, terminating.')
        sys.exit(0)
        
    #length = int.from_bytes(file.read(4),'big') #IHDR
    #chunktype = file.read(4)
    #IHDR(file,length)
    #checkcrc(chunktype+data)    
        
    while True:
        length = int.from_bytes(file.read(4),'big')
    
        #print(length)
        chunktype=file.read(4)
        if chunktype in mandatoryChunks:
            mandatoryChunks[chunktype](file,length)
        elif chunktype in supAuxChunks:
            supAuxChunks[chunktype](file,length)          
        else:
            print(chunktype)
            unsupportedCh(file,length,chunktype)
        #nothing = file.read(4)    
        
        