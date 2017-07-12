#coding:utf-8
import requests
import random
import time
import re
import json
import StringIO
import execjs
from PIL import Image

headers = {
    'connection': "keep-alive",
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    'accept': "*/*",
    'accept-encoding': "gzip, deflate, sdch, br",
    'accept-language': "zh-CN,zh;q=0.8",
    'referer':'http://uems.sysu.edu.cn/jwxt/',
    'cache-control': "no-cache"
}
session=requests.session()

def get_gt_challenge(session):#第一个包
    url='http://uems.sysu.edu.cn/jwxt/StartCaptchaServlet'
    params={'ts':'%.16f'%random.random()}
    response=session.get(url,params=params,headers=headers)
    json_dict=response.json()
    gt,challenge=json_dict['gt'],json_dict['challenge']
    return gt,challenge

def get_frontlib(gt,session):#第二个包 返回的js直接浏览器执行 执行的结果是加载geetest.5.7.0.js 模拟的时候可以去掉此步骤
    url='http://api.geetest.com/getfrontlib.php'
    random_str='%d'%(time.time()*1000+random.random()*10000)  #gt.js  parseInt(Math.random() * 10000) + (new Date()).valueOf()
    params={
        'gt':gt,
        'callback':'geetest_'+random_str
    }
    response=session.get(url,params=params,headers=headers)
    return response.text

def get_php(gt,challenge,session): #第三个包 返回图片的url等其他数据
    url='http://api.geetest.com/get.php'
    random_str='%d'%(time.time()*1000+random.random()*10000)  #geetest.5.7.0.js  d.id=1499744411340  d.id=o() o=function (){return parseInt(1e4*Math.random())+(new Date).valueOf()}
    params={
        'gt':gt,
        'challenge':challenge,
        'product':'float',
        'offline':'false',
        'type':'slide',
        'callback':'geetest_'+random_str
    }
    response=session.get(url,params=params,headers=headers)
    image_dict=json.loads(re.search('\((.*)\)',response.text).group(1))
    fullbg_url='http://static.geetest.com/'+image_dict['fullbg']
    bg_url='http://static.geetest.com/'+image_dict['bg']
    challenge=image_dict['challenge'] #新的challenge
    #slice_url='http://static.geetest.com/'+image_dict['slice']
    return fullbg_url,bg_url,challenge



def crack_img(url,file_name,session): #还原图片
    headers={'user-agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
    content=session.get(url,headers=headers).content
    mem=StringIO.StringIO(content)
    im=Image.open(mem)
    im_new=Image.new('RGB',(260,116))
    n=[39, 38, 48, 49, 41, 40, 46, 47, 35, 34, 50, 51, 33, 32, 28, 29, 27, 26, 36, 37, 31, 30, 44, 45, 43, 42, 12, 13, 23, 22, 14, 15, 21, 20, 8, 9, 25, 24, 6, 7, 3, 2, 0, 1, 11, 10, 4, 5, 19, 18, 16, 17]  #geetest.5.7.0.js 提取出来的
    new_boxes=[(i*10,0,i*10+10,58) for i in range(26)]+[(i*10,58,i*10+10,116) for i in range(26)]
    for i in range(len(n)):
        x_offset= (n[i] % 26) * 12 + 1
        y_offset= 58 if n[i] > 25 else 0
        box=(x_offset,y_offset,x_offset+10,y_offset+58)
        region=im.crop(box)
        new_box=new_boxes[i]
        im_new.paste(region,new_box)
    im_new.save(file_name)
    return im_new
def column_diff(img1,img2,x,height,max_diff):#判断2张图片具体某一列是否相同
    for y in range(height):
        pix1=img1.getpixel((x,y))
        pix2=img2.getpixel((x,y))
        diff=reduce(lambda x,y:x+y,[pix1[i]-pix2[i] for i in range(3)])
        if diff>max_diff:return True
    return False

def which_column_diff(img1,img2,width,height,max_diff):#返回图片差异处的横坐标x-5
    for x in range(width):
        if column_diff(img1,img2,x,height,max_diff): return x-5

        
        
def compile_js():
    e=execjs.get('PHANTOMJS') #设置系统环境变量PHANTOMJS 值是phantomjs的exe的路径
    with open('emulate.js') as f:
        comp=e.compile(f.read())
        return comp
    
def get_userresponse(dis,challenge,comp):#第四个包的参数userresponse
    return comp.call('bat',dis,challenge)
    
def get_a(arr,comp):#第四个包的参数a
    #random_id='%d'%(time.time()*1000+random.random()*10000)
    return comp.call('nas',arr)

def get_arr(dis,passtime):#模拟鼠标运动轨迹数组arr
    arr_length=random.randint(50,70)
    passtime_arr=sorted(random.sample(range(passtime),arr_length))
    x_arr=sorted(random.sample(range(dis),arr_length))
    y_arr_back=[1+i for i in range(7) for j in range(random.randint(6,10))]
    y_arr=[0 for i in range(arr_length-len(y_arr_back))]+y_arr_back
    len(y_arr)
    arr=[(x_arr[i],y_arr[i],passtime_arr[i]) for i in range(arr_length)]
    arr.insert(0,(0,0,0))
    arr.insert(0,(-21,-18,0))
    arr.append((dis,arr[-1][1],passtime))    
    return arr

def ajax_php(gt,challenge,userresponse,passtime,a,session):#第四个包 发送识别出的验证码的数据
    url='http://api.geetest.com/ajax.php'
    random_str='%d'%(time.time()*1000+random.random()*10000)  #gt.js  parseInt(Math.random() * 10000) + (new Date()).valueOf()
    params={
        'gt':gt,
        'challenge':challenge,
        'userresponse':userresponse,
        'passtime':passtime,
        'imgload':'154',
        'a':a,
        'callback':'geetest_'+random_str
    }
    response=session.get(url,params=params,headers=headers)
    return response.text

if __name__='__main__':
    gt,challenge=get_gt_challenge(session)#第一个数据包
    get_frontlib(gt,session)               #第二个包
    fullbg_url,bg_url,challenge=get_php(gt,challenge,session) #第三个包

    fullbg_img=crack_img(fullbg_url,'fullbg.jpg',session) #还原fullbg
    bg_img=crack_img(bg_url,'bg.jpg',session)  #还原bg
    passtime=2428          #设置滑动鼠标总时间
    dis=which_column_diff(fullbg_img,bg_img,260,116,150)  #判断鼠标应该滑动的距离
    arr=get_arr(dis,passtime)  #模拟鼠标运动轨迹数组arr
    comp=compile_js()        #编译js文件

    userresponse=get_userresponse(dis,challenge,comp) #运行js文件得出userresponse用于第四个包
    a=get_a(arr,comp)  #运行js文件得出a用于第四个包
    print 'a=%s gt=%s challenge=%s userresponse=%s passtime=%s'%(a,gt,challenge,userresponse,passtime)
    print ajax_php(gt,challenge,userresponse,passtime,a,session)#第四个包 模拟滑动鼠标提交验证