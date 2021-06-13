#open-a-png-with-almost-no-zlib
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "no,stop,fckin adware"#stops pygame from acting like shellbased adware
import sys, os, pygame, asyncio, zlib, timeit #, math #, binascii
#from pygame.locals import *


async def main(fp):   #filepath == fp, relative path works too
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
        print("crc is ",0xffffffff & ~crc, crc)
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
        print(data[0:4],crcRes)
        infilecrc = int.from_bytes(file.read(4),'big')
        print(infilecrc)
        try:
            crcRes == infilecrc       
        except:
            print('PNG datastream corrupted, terminating.',crcRes)
            sys.exit(0)
    
    def IHDR(file,length):
        #print('IHDR')
        data=file.read(length)
        width=int.from_bytes(data[0:4],'big')
        height=int.from_bytes(data[4:8],'big')
        depth=int.from_bytes(data[8:9],'big')
        colormode=int.from_bytes(data[9:10],'big')
        compressiontype=int.from_bytes(data[10:11],'big')
        filtermethod=int.from_bytes(data[11:12],'big')
        interlace=int.from_bytes(data[12:13],'big')
        #print('IHDR done')
        print([width,height,depth,colormode,compressiontype,filtermethod,interlace])
        return data, [width,height,depth,colormode,compressiontype,filtermethod,interlace]
    
    def IDAT(file,length,flags,MainAsCaller=True):
        print('IDAT')
        data=file.read(length)
        fulldata = data
        #print(len(fulldata))
        checkNextidat = file.read(12)
        if checkNextidat[8:] == b'IDAT':
            #print('next is IDAT')
            
            new_data = IDAT(file,int.from_bytes(checkNextidat[4:8],'big'),flags,False)
            fulldata = data + new_data
            #new_data
            #print(len(fulldata))
        
        if MainAsCaller == False:
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
            if flags[3] == 0:
                pass
            elif flags[3] == 2:
                bytes_per_pixel = 3
            elif flags[3] == 3:
                #for x in decompdata:
                pass        
            elif flags[3] == 4:
                pass
            elif flags[3] == 6:
                bytes_per_pixel = 4
            else:
                print("invalid colortype",flags[3])
                sys.exit(0)
            ### scan line serialisation,,,gotta redo partially :/!
            serialised_data = []
            filtertypes=[]
            for i in range(flags[1]):
                filtertypes.append(decompdata[i*flags[0]*bytes_per_pixel+i])
                serialised_data.append(decompdata[
                    i*flags[0]*bytes_per_pixel+i+1:
                    (i+1)*flags[0]*bytes_per_pixel+i+1])
            print('filtertypes:',filtertypes)#'scanlines',serialised_data,[len(serialised_data[x]) for x in range(len(serialised_data))])
            filtered_data = []
            prv_scl = [0] * flags[0] * bytes_per_pixel
            
            ### filtering of the scanlines of pixels
            for ft,scl in zip(filtertypes,serialised_data):
                filtered_scl = []
                #print("scl",scl,len(scl))
                if ft == 0: #x = x
                    filtered_scl = scl[:]
                    #print('OK,0')
                elif ft == 1: #x = x + a
                    prvpx_scl = [0] * bytes_per_pixel
                    prvpx_scl += scl[:]
                    #filtered_scl = [ch & 0xff for ch in map(int.__add__, prvpx_scl, scl)]
                    for i in range(len(scl)):
                        prvpx_scl[i+bytes_per_pixel] = (scl[i] + prvpx_scl[i]) & 0xff
                    filtered_scl = prvpx_scl[bytes_per_pixel:]
                    
                elif ft == 2: #x = x + b
                    filtered_scl = [(x + b) & 0xff for x, b in zip(scl,prv_scl)]
                    
                elif ft == 3:
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
                    
                elif ft == 4: #doesn't really work but it's almost done
                    #debug_statement = input("justa debugger,press enter")
                    #print("scl", scl,len(scl))
                    prvpx_scl = [0 for z in range(bytes_per_pixel)] #a                
                    prvpx_scl += scl[:-bytes_per_pixel] #-bpp
                    #print("prvpx_scl | a",prvpx_scl,len(prvpx_scl))
                    #print("prv_scl | b",prv_scl,len(prv_scl))
                    prvpx_of_prv_scl = [0 for z in range(bytes_per_pixel)] #c
                    prvpx_of_prv_scl += prv_scl[:-bytes_per_pixel] #-bpp
                    #print("prvpx_of_prv_scl | c",prvpx_of_prv_scl,len(prvpx_of_prv_scl))
                    #p = 
                    #for i in range(bytes_per_pixel,len(scl)):
                     #   p[i-bytes_per_pixel] = 
                    p = [ch for ch in map(lambda a, b, c: a + b - c, prvpx_scl, prv_scl, prvpx_of_prv_scl)]
                    #print("p",p,len(p))
                    pa = [abs(ch) for ch in map(int.__sub__, p, prvpx_scl)]
                    #print("pa",pa,len(pa))
                    pb = [abs(ch) for ch in map(int.__sub__, p, prv_scl)]
                    #print("pb",pb,len(pb))
                    pc = [abs(ch) for ch in map(int.__sub__, p, prvpx_of_prv_scl)]
                    #print("pc",pc,len(pc))
                    Pr = prvpx_of_prv_scl[:]
                    #print("Pr",Pr,len(Pr))
                    for i in range(flags[0]):
                        if (pa[i] <= pb[i] and pa[i] <= pc[i]):
                            Pr[i] = prvpx_scl[i]
                        elif pb <= pc:
                            Pr[i] = prv_scl[i]
                    #print("Pr znovu",Pr,len(Pr))
                    filtered_scl = [ch & 0xff for ch in map(int.__add__,scl,Pr)]
                    #print(filtered_scl,len(Pr))
                    
                else:
                    print('fatal error wtf')
                    sys.exit(0)
                prv_scl = filtered_scl[:] #b
                filtered_data += filtered_scl[:]
                #print(filtered_scl)
                
            stop = timeit.default_timer()
            print("program runtime ", stop - start)
            
            with open('filtered_data.txt','w+') as debug: #uncomment to debug
                debug.write(str(filtered_data))
                debug.close()
            with open('serialised_unf_data.txt','w+') as debug: #uncomment to debug
                debug.write(str(serialised_data)+"\n\n"+str(filtertypes))
                debug.close()
            #print("filtered data:",filtered_data)
            #debuggerstatement=input("press enter, this is a debug statement")    
            #scf = 1
            scf = 1 #scalefactor
            
            
            PNG = pygame.display.set_mode((flags[0]*scf,flags[1]*scf),depth=24)
            PNG_area = pygame.Surface((flags[0]*scf,flags[1]*scf))
            pixel_i = 0
            print('height:',flags[1], 'width:',flags[0])
            #BG = pygame.Surface((flags[0]*scf,flags[1]*scf))
            #BG.fill((128,128,128,255))
            #PNG.blit(BG,(0,0))
            for height in range(flags[1]):
                #print(height)
                for width in range(flags[0]):
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
            
            print('IDAT DONE')
            clock = pygame.time.Clock()
            while True:
                for event in pygame.event.get():
                    if event.type == "QUIT":
                        pygame.quit()
                        
                clock.tick(30)
                pygame.display.update()
                
                #serialised_data += itr
                #for i in range(flags[0]):
                 #   serialised_data += [zip(itr,itr,itr)]
                    
                #serialised_data[scl*flags[1]][decompdata[scl*(flags[0]):scl*flags[0]+flags[0]+1]]
                #flags[0] == width in pixels
            #print(serialised_data)
            #filteridat(serialised_data,flags)
            #if flags[3] #colormode flag
        file.seek(-12,os.SEEK_CUR)
        #print('IDAT done')
        #print(len(dataforcrc))
        return fulldata
        
    def IEND(file,length,flags):
        file.read(length)
        checkcrc(b'IEND'+data)
        print('IEND')
        
        print('Time:',stop-start)
        file.close()
        sys.exit(0)
        
    def unsupportedCh(file,length,flags):
        print('unknown chunk type, something went wrong?')
        data = file.read(length)
        #sys.exit(0)
        return data
        
    def gAMA(file,length,flags):
        print('gAMA')
        data = file.read(length)
        return data
        
    def cHRM(file,length,flags):
        print('cHRM')
        data = file.read(length)
        return data
    
    def sRGB(file,length,flags):
        print('sRGB')
        data = file.read(length)
        return data
        
    def pHYs(file,length,flags):
        print('pHYs')
        data = file.read(length)
        print(int.from_bytes(data[0:3],'big'))
        print(int.from_bytes(data[4:7],'big'))
        print(data[8])
        return data
        
    with open(fp,"rb") as file: #testfiles C:\Users\Tobiáš Brichta\Desktop\development\largetestimage.png
        #testerror.png, large-png-png-collections-at-sccprecat-large-png-3035_2860.png, text2.png,epiceasteregg0.png   
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
            
        length = int.from_bytes(file.read(4),'big') #IHDR
        chunktype = file.read(4)
        data, flags = IHDR(file,length)
        checkcrc(chunktype+data)    
            
        while True:
            length = int.from_bytes(file.read(4),'big')
        
            #print(length)
            chunktype=file.read(4)
            if chunktype in mandatoryChunks:
                data = mandatoryChunks[chunktype](file,length,flags)
            elif chunktype in supAuxChunks:
                data = supAuxChunks[chunktype](file,length,flags)          
            else:
                print(chunktype)
                data = unsupportedCh(file,length,chunktype)
            #nothing = file.read(4)    
            checkcrc(chunktype+data)
            
#filepath = input("please enter an absolute or relative path to a .png file:")
async def realmain():
    filecount = int(input('how many files do you wish to open?:'))
    filepaths = [''] * filecount
    for i in range(filecount):
        filepaths[i] = input("please enter an absolute or relative path to a .png file:")
    print(filepaths)
    for filepath in filepaths:
        await main(filepath)
loop = asyncio.get_event_loop()
loop.run_until_complete(realmain())