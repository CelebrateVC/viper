import requests,re,os,shutil, argparse
from bs4 import BeautifulSoup

dl=True

class external_page:
    def __init__(self,url,callme=True):
        self.imageurl=None
        if callme:
            domain = re.findall('://(.*?)\\.\\w*/',url)[0].split('www.')[-1]
            bb=BeautifulSoup(requests.get(url).content)
            self.domain=domain
            

            if domain == 'imgbox':
                list_of_images=[k for k in bb.find_all('img') if 'title' in k.attrs]
                if len(list_of_images) == 1:
                    self.imageurl = list_of_images[0].attrs['src']
                else:
                    raise Exception('multiple possible images for link: {}'.format(url))
            elif domain == 'imx':
                raise Exception('This domain uses a Javascript contunue button that cannot be clicked in good faith to the user')
            elif domain == 'imagebam':
                list_of_images= [k for k in bb.find_all('meta') if 'property' in k.attrs]
                if len(list_of_images) == 1:
                    self.imageurl = list_of_images[0].attrs['content']
                else:
                    raise Exception('multiple possible images for link: {}'.format(url))

            elif re.match('img\\d*\\.imagevenue',domain): # img{number}.imagevenue
                link_to_image_link=[k for k in bb.find_all('a') if 'title' in k.attrs]
                if len(link_to_image_link) == 0:
                    link_to_image_link=[l for l in [k for k in bb.find_all('a') if k.has_attr('href')] if l.attrs['href']!='#']
                    
                    if len(link_to_image_link)==0:                      
                        raise Exception('no continue link for link {}'.format(url))
                
                if len(link_to_image_link) == 1:
                    uu=link_to_image_link[0].attrs['href']
                    while uu!=url and len(bb.find_all('img'))==0:
                        bb=BeautifulSoup(requests.get(uu).content)
                        url=uu
                        uu=[k for k in bb.find_all('a') if 'title' in k.attrs][0].attrs['href']
                    if uu==url:
                        raise Exception('cannot scrape {} circular reference of links'.format(uu))
                    else:
                        self.imageurl=bb.find('img').attrs['src']

            elif domain == 'turboimagehost':
                self.imageurl = bb.find('img').attrs['src']

            elif domain == 'pixhost':
                images=bb.find_all('img',class_='image-img')
                if len(images) == 1:
                    self.imageurl=images[0].attrs['src']
                else:
                    raise Exception('multiple images for link: {}'.format(url))

            else:
                raise Exception('''unkown external domain {}, if this is a major domain, for your use on this site, feel free to add functionality for it'''.format(domain))

class internal_page:
    def __init__(self,url,startingpath=''):
        print(url)
        bb=BeautifulSoup(requests.get(url).content)
        
        if url.strip().lower() == 'https://vipergirls.to/forum.php':
            print('feeling brave are we?')
            subs=['https://vipergirls.to/'+r.attrs['href'] for k in bb.find_all('div',class_='forumrow') for r in k.find_all('a') if r.attrs['href'][:5]=='forum']
            
            if not os.path.isdir('forum'):
                os.mkdir('forum')
            
            for sub in subs:
                internal_page(sub,'forum/')
                
                
        elif re.match('https://vipergirls.to/forums/[^/]*$',url.strip().lower()): # subforum
            
            forumname=re.findall('https://vipergirls.to/forums/([^/]*)',url.strip().lower())[0]
            print('scraping subforum {} '.format(forumname))
            
            threads = ['https://vipergirls.to/'+k.attrs['href'] for k in bb.find_all('a', class_='title')]
            
            pages   = int(bb.find('div',id='threadpagestats').text.split()[-1])/25
            pages   = int(pages) if pages%1==0 else int(pages//1)+1
            
            print(os.path.isdir(startingpath+forumname),startingpath+forumname)
            if not os.path.isdir(startingpath+forumname):
                os.mkdir(startingpath+forumname)            
            
            for thread in threads:
                internal_page(thread,startingpath+forumname+'/')
                
            for page in range(2,pages+1):
                internal_page(url+'/page'+str(page),startingpath+forumname+'/')
                
        elif re.match('https://vipergirls.to/forums/[^/]*/page\\d+',url):
            threads = ['https://vipergirls.to/'+k.attrs['href'] for k in bb.find_all('a', class_='title')]
            
            for thread in threads:
                internal_page(thread,startingpath)
                
        elif re.match('https://vipergirls.to/threads/[^/]*',url):
            for post in bb.find_all('li',class_='postbitim'):
                
                postID=post.attrs['id']
                failpic=0
                ext=external_page('',callme=False)
                
                if not os.path.isdir(startingpath+postID+'/'):
                    os.mkdir(startingpath+postID+'/')
                else:
                    if os.path.isfile(startingpath+postID+'/err.log'):
                        os.remove(startingpath+postID+'/err.log')
                
                for i,picture in enumerate(post.find_all('a',target='_blank')):
                    try:
                        ext=external_page(picture.attrs['href'])
                    except ConnectionError:
#                        some domains are no longer valid and timeout, if this happens, regardless of policy skip post immediately
                        break
                    except Exception as e:
                        print(picture.attrs['href'],postID,":",e)
                        failpic+=1
                        if failpic>args.errs:
                            break
                    if dl and ext.imageurl is not None :
                        
                        flnm = ext.imageurl.split('/')[-1]
                        
                        if flnm not in os.listdir(startingpath+postID+'/'):
                            try:
                                with requests.get(ext.imageurl, stream=True) as r:
                                        with open(startingpath+postID+'/'+flnm, 'wb') as f:
                                            shutil.copyfileobj(r.raw, f)
                            except:
                                try: os.remove(startingpath+postID+'/'+flnm)
                                except: pass 
                                continue
                            if os.path.getsize(startingpath+postID+'/'+flnm)==13:
                                os.remove(startingpath+postID+'/'+flnm)
                                with open(startingpath+postID+'/err.log','a') as f:
                                    f.write(picture.attrs['href']+'\n')
                
                
                        


                if len(os.listdir(startingpath+postID))==0:
                    os.rmdir(startingpath+postID)


            if re.match('https://vipergirls.to/threads/[^/]*$',url): # page 1
                pages = bb.find('a',class_='popupctrl').text.split()[-1]
                if pages.isnumeric():
                    for page in (range(2,int(pages)+1) if pages else []):
                        internal_page(url+'/page'+str(page),startingpath)

                        
if __name__=='__main__':
    parser=argparse.ArgumentParser('program for scraping vipergirls.to\'s hotlinked images')
    parser.add_argument('directory',help='OS Path for the extracts to dump to, default current directory',type=str,default=os.getcwd())
    parser.add_argument('URLs', help='single or multiple urls in vipergirls.to to dump',type=str,nargs='+')
    parser.add_argument('--errs',help='(default 3) Number of allowable images placed on unknown imagehosts before skipping post, set low to speed process and reduce stdout spam, set high if it is likely that the image hosts will change mid post and you want to be thorough ',type=int,default=3)
    parser.add_argument('--prefix',help='the prefix name applied to high level folders made by program, if this is used to define a folder, assumption is made that that file exists',type=str,default='')
    
    args=parser.parse_args()
    
    os.chdir(args.directory)
    
    if '/' in args.prefix:
        if not os.path.isdir('/'.join(args.prefix.split('/')[:-1])):
            raise FileExistsError('cannot define prefix for subfolders that do not exist')
    
    for url in args.URLs:
        internal_page(url,args.prefix)
    
    
    
    
    
    
