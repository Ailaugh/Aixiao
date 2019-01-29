from django.shortcuts import render
from django.shortcuts import render,HttpResponseRedirect,HttpResponse

from Buyer.models import *
from Seller.views import *
import hashlib

def cookieValid(fun):
    def inner(request,*args,**kwargs):
        cookie = request.COOKIES
        username = cookie.get("user_name")
        session = request.session.get("username") #获取session
        user = Buyer.objects.filter(username = username).first()
        if user and session == username: #校验session
            return fun(request,*args,**kwargs)
        else:
            return HttpResponseRedirect("/login/")
    return inner

@cookieValid
def index(request):
    data = []
    goods = Goods.objects.all()
    for good in goods:
        goods_img = good.image_set.first()
        img = goods_img.img_adress.url
        data.append(
            {"id": good.id,"img": img.replace("media","static"), "name": good.goods_name, "price": good.goods_now_price}
        )
    return render(request,"buyer/index.html",{"datas": data})


'''登录'''
def login(request):
    result = {"statue": "error","data": ""}
    if request.method == "POST" and request.POST:
        username = request.POST.get("username")
        user = Buyer.objects.filter(username = username).first()
        if user:
            password = setPassword(request.POST.get("userpass"))
            db_password = user.password
            if password == db_password:
                response = HttpResponseRedirect("/")
                response.set_cookie('user_id',user.id)
                response.set_cookie('user_name', user.username)
                request.session["username"] = user.username
                return response
            else:
                result["data"] = "密码错误"
        else:
            result["data"] = "用户名不存在"
    return render(request,'buyer/login.html',{"result":result})


'''注册'''
def register(request):
    if request.method=="POST" and request.POST:
        username=request.POST.get('username')
        userword=request.POST.get('userpass')
        buyer=Buyer()
        buyer.username=username
        buyer.password=setPassword(userword)
        buyer.save()
        return HttpResponseRedirect("/login/")
    return render(request,'buyer/register.html')

'''清除cookie'''
def logout(request):
    response=HttpResponseRedirect('/login/')
    response.delete_cookie('user_id')
    response.delete_cookie('user_name')
    del request.session['username']
    return response

import time,datetime,random
from django.core.mail import EmailMultiAlternatives
from django.http import JsonResponse
from Buyer.models import EmailValid

def getRandomData():
    result = str(random.randint(1000,9999))
    return result

def sendMessage(request):
    result = {"staue": "error","data":""}
    if request.method == "GET" and request.GET:
        recver = request.GET.get("email")
        try:
            subject = "aixiao"
            text_content = "hello python"
            value = getRandomData()
            html_content = """
            <div>
                <p>
                    尊敬的q商城用户，您的用户验证码是:%s,打死不要告诉别人。
                </p>
            </div>
            """%value
            message = EmailMultiAlternatives(subject,text_content,"15835370708  @163.com",[recver])
            message.attach_alternative(html_content,"text/html")
            message.send()
        except Exception as e:
            result["data"] = str(e)
        else:
            result["staue"] = "success"
            result["data"] = "success"
            email = EmailValid()
            email.value = value
            email.times = datetime.datetime.now()
            email.email_address = recver
            email.save()
        finally:
            return JsonResponse(result)

def register_email(request):
    result = {"statu": "error","data":""}
    if request.method == "POST" and request.POST:
        username = request.POST.get("username")
        code = request.POST.get("code")
        userpass = request.POST.get("userpass")
        email = EmailValid.objects.filter(email_address = username).first()
        if email:
            if code == email.value:
                now = time.mktime(
                    datetime.datetime.now().timetuple()
                )
                db_now = time.mktime(email.times.timetuple())
                if now - db_now >= 86400:
                    result["data"] = "验证码过期"
                    email.delelt()
                else:
                    buyer = Buyer()
                    buyer.username = username
                    buyer.email = username
                    buyer.password = setPassword(userpass)
                    buyer.save()
                    result["statu"] = "success"
                    result["data"] = "恭喜！注册成功"
                    email.delete()
                    return HttpResponseRedirect("/login/")
            else:
                result["data"] = "验证码错误"
        else:
            result["data"] = "验证码不存在"
    return render(request, 'buyer/register_mail.html',locals())

from Seller.models import Seller
def goods_details(request,id):
    good = Goods.objects.get(id=int(id)) #一个商品
    good_img = good.image_set.first().img_adress.url.replace("media","static")

    seller = good.seller #商品对应的商铺 外键 --> 主
    goods = seller.goods_set.all() #主 --> 外
    data = []
    for g in goods:
        goods_img = g.image_set.first()
        img = goods_img.img_adress.url
        data.append(
            {"id": g.id, "img": img.replace("media","static"), "name": g.goods_name, "price": g.goods_now_price}
        )
    return render(request,"buyer/goods_details.html",locals())

def carJump(request,goods_id):
    goods=Goods.objects.get(id=int(goods_id))
    id=request.COOKIES.get('user_id')
    if request.method=='POST' and request.POST:
        count = request.POST.get("count")
        img = request.POST.get("good_img")
        buyCar = BuyCar.objects.filter(user=int(id), goods_id=int(goods_id)).first()  # 查询是否存在在购物车当中
        if not buyCar:  # 不存在
            buyCar = BuyCar()  # 实例化模型
            buyCar.goods_num = int(count)  # 添加数量
            buyCar.goods_id = goods.id
            buyCar.goods_name = goods.goods_name
            buyCar.goods_price = goods.goods_now_price
            buyCar.user = Buyer.objects.get(id=request.COOKIES.get("user_id"))
            buyCar.save()
        else:  # 存在
            buyCar.goods_num += int(count)  # 数量相加
            buyCar.save()
        all_price = float(buyCar.goods_price) * int(count)
        return render(request, "buyer/buyCar_jump.html", locals())
    else:
        return HttpResponse("404 not fond")

from Buyer.models import BuyCar

@cookieValid
def carList(request):
    id=request.COOKIES.get("user_id") #获取用户身份
    goodList = BuyCar.objects.filter(user = int(id)) #查询指定用户的购物车商品信息
    price_list = []
    address_list = Address.objects.filter(buyer=int(id))
    prices=0
    for goods in goodList:
        g=Goods.objects.get(id=goods.goods_id)
        img=g.image_set.all().first().img_adress.url.replace('media','static')
        all_price = float(goods.goods_price) * int(goods.goods_num)
        prices+=all_price
        price_list.append({"price": all_price,"goods":goods,'img':img}) #添加总数
    result={"prices":prices,"price_list":price_list}
    return render(request,"buyer/car_list.html",locals())

@cookieValid
def delete_goods(request,goods_id):
    id=request.COOKIES.get('user_id')
    goods=BuyCar.objects.filter(user=int(id),goods_id=int(goods_id))
    goods.delete()
    return HttpResponseRedirect('http://127.0.0.1:8000/buyer/carList/')

@cookieValid
def clear_goods(request):
    id=request.COOKIES.get('user_id')
    goods=BuyCar.objects.filter(user=int(id))
    goods.delete()
    return HttpResponseRedirect('http://127.0.0.1:8000/buyer/carList/')

'''订单页'''
from Buyer.models import Order
from Buyer.models import OrderGoods
def add_order(request):
    buyer_id = request.COOKIES.get("user_id") #用户的id
    goods_list = [] #订单商品的列表
    if request.method == "POST" and request.POST:
        requestData = request.POST #请求数据
        addr = requestData.get("address") #寄送地址的id
        pay_method = requestData.get("pay_Method") #支付方式
        #获取商品信息
        all_price = 0 #总价
        for key,value in requestData.items(): #循环所有的数据
            if key.startswith("name"): #如果键以name开头，我们就任务是一条商品信息的id
                buyCar = BuyCar.objects.get(id=int(value)) #获取商品
                price = float(buyCar.goods_num) * float(buyCar.goods_price) #单条商品的总价

                g = Goods.objects.get(id=buyCar.goods_id)
                img = g.image_set.all().first().img_adress.url.replace("media", "static")

                all_price += price #加入总价
                goods_list.append({"price":price,"buyCar":buyCar,'img':img}) #构建数据模型{"小计总价":price,"商品信息":buyCar}
        # 存入订单库
        Addr = Address.objects.get(id=int(addr)) #获取地址数据
        order = Order() #保存到订单
        #订单编号 日期 + 随机 + 订单 + id

        now = datetime.datetime.now()
        order.order_num = now.strftime("%Y%m%d")+str(random.randint(10000,99999))
        order.order_time = now
        # 状态 未支付 1 支付成功 2 配送中 3 交易完成 4 已取消 0
        order.order_statue = 1
        order.total = all_price
        order.user = Buyer.objects.get(id = int(buyer_id))
        order.order_address = Addr
        order.save()
        #总价
        order.order_num=order.order_num+str(order.id)
        order.save()

        for good in goods_list: #循环保存订单当中的商品
            g = good["buyCar"]
            g_o = OrderGoods()
            g_o.goods_id = g.id
            g_o.goods_name = g.goods_name
            g_o.goods_price = g.goods_price
            g_o.goods_num = g.goods_num
            g_o.goods_picture = g.goods_picture
            g_o.order = order
            g_o.save()
        return render(request,"buyer/enterOrder.html",locals())
    else:
        return HttpResponseRedirect("/buyer/carList/")
'''添加地址'''
from Buyer.models import Address
def addAddress(request):
    if request.method == "POST" and request.POST:
        buyer_id = request.COOKIES.get("user_id")
        buyer_name = request.POST.get("buyer")
        buyer_phone = request.POST.get("buyer_phone")
        buyer_address = request.POST.get("buyer_address")
        db_buyer = Buyer.objects.get(id = int(buyer_id))

        addr = Address()
        addr.recver = buyer_name
        addr.phone = buyer_phone
        addr.address = buyer_address
        addr.buyer = db_buyer
        addr.save()
        return HttpResponseRedirect("/buyer/address/")
    return render(request,"buyer/addAddress.html")
'''地址界面'''
def address(request):
    buyer_id = request.COOKIES.get("user_id")
    address_list = Address.objects.filter(buyer=int(buyer_id))
    return render(request,"buyer/address.html",locals())
'''修改地址'''
def changeAddress(request,address_id):
    addr = Address.objects.get(id=int(address_id))
    if request.method == "POST" and request.POST:
        buyer_name = request.POST.get("buyer")
        buyer_phone = request.POST.get("buyer_phone")
        buyer_address = request.POST.get("buyer_address")

        addr.recver = buyer_name
        addr.phone = buyer_phone
        addr.address = buyer_address
        addr.save()
        return HttpResponseRedirect("/buyer/address/")
    return render(request,"buyer/addAddress.html",locals())
'''删除地址'''
def delAddress(request,address_id):
    addr = Address.objects.get(id=int(address_id))
    addr.delete()
    return HttpResponseRedirect("/buyer/address/")
# Create your views here.

'''支付宝支付'''
from alipay import AliPay
def Pay(oreder_id,money):
    alipay_public_key_string = '''-----BEGIN PUBLIC KEY-----
    MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvCMkbeH7OK8h3ymVRTW8dnnphyb2kLHFNqn3y6zXyUErXRv7Vb/oVsFgaVqYvK5824EKIVHex0qLuwMJMRPXS4dEy29J89QOH+PWuhm7kp29wSqfUxfAm27RTHquXukz+A9XGJ4pe2zL2SjaxpbhqhKhBlIEhtnt3GhPA+y727ZTNKfEd5e4lrdrbJQju+RulkXDzPe9WGpiykZo9fxs+OqVKKEoWVTRlGgatHfk8Pirwycm5N2jV9w9lIg7hZ9DoPk21WyztMkuEhXA5vICM9Z2jlrrpdQDYd0JHRV8DLFhFhyc1snuJwTw9Ilhn4d6X863PjSzQsiq75vTke12NwIDAQAB
-----END PUBLIC KEY-----'''

    app_private_key_string = '''-----BEGIN RSA PRIVATE KEY-----
    MIIEowIBAAKCAQEAvCMkbeH7OK8h3ymVRTW8dnnphyb2kLHFNqn3y6zXyUErXRv7Vb/oVsFgaVqYvK5824EKIVHex0qLuwMJMRPXS4dEy29J89QOH+PWuhm7kp29wSqfUxfAm27RTHquXukz+A9XGJ4pe2zL2SjaxpbhqhKhBlIEhtnt3GhPA+y727ZTNKfEd5e4lrdrbJQju+RulkXDzPe9WGpiykZo9fxs+OqVKKEoWVTRlGgatHfk8Pirwycm5N2jV9w9lIg7hZ9DoPk21WyztMkuEhXA5vICM9Z2jlrrpdQDYd0JHRV8DLFhFhyc1snuJwTw9Ilhn4d6X863PjSzQsiq75vTke12NwIDAQABAoIBAERRJotYQheFUPFucivdpYAIKQrQ1TwZsZl2AutM6lbEeXCoFo4+z6mhMtdO9KOfYOt8YidTSWho43CXW6EcqVNd3VdaJCqMWEywOWr+qSRGb39TcOOFfoVyqkHxUpxYZmyvdVsVI88T5LoIodj3NR7DAQIAinBFdqBQqFCuiFDxtri4dcqMKpeTn2p3A35SOswfid3jXDpVZxkx2PrRLltZS1mYuWjttZji6E/1BpWpB7lYyKO4f/rqgSfwWcP+oQVxyUWCfKEOUEp3XFHn1b93sNqbxSkH0w4mjPv9KnhGxaZPqfUY384NW1RX8ulzqlItWeAT2N3MuA2bdJ6JZ1ECgYEA4UBvwzZYm8RF1G67GQjruuavix70bMtXjgucScnSFYuNW2FwzpYz3VuR4TOxeOWTBCZof0WGQ9S8gLJRyePqzY9Rr8FZAYGqN+RP7kYxnTmLDVWkuv4VE+UxDhCoyd25wFd1ceNZlZcCPG6srvJt+n4zCfEracUOlFJcQrk0Wj0CgYEA1dG37JGU8V2ePjjg9aTGY6CAZ+j4g18UaF7JQFGvTzl5o4MHyP7XN+vlVhufFn7vAmYoP2az/vC2kxkO50/RG4OWB1rcqSWkjTkdVb6iJh6++6U5QiNK4sWyKiNFcuThO3F3d6nDueI/Z2sgoIDAj7ezmbUavyK/NdmD9SsZ/YMCgYEAtqnkeC/oJ1lBL4YkX6bmUwijrnQJzvgPJnev4/6wSRyEI2ifbEhOAuIxKKkc8Gdrk1/6OcuNmBA6VTtGLCyRyuTAX4CxxxD5kp2pXBa8QT3az5N2JNXLDfk8kKVd22XdLmc+LH8rtK1i+NLfYnfiS9JvXU6f4AQXUJyBiPJbzBkCgYBhEkH2460D2yWxR+9RdgofRsmk4w6Xzb2dGJMzYSI+zHAdvKn3JUMd/zlx2z5hXyUxKKHTDtRexHeO1ox+lSzw2c9t7WFKZW2MM8bOm6pPthuscTlKfm1MAMa+/J5V5/UdIIlFSUwzgrSYRfldBLbnSFYATUkkRykZ0HNpBbVZ8wKBgBtxEdMdFIOYmyjN1c5p6zyaZI/dxDsVj4M0Z5LWGn/+qWsRv18y8SFFl5K6rEWIdBT11EwvxJGQUBNtSLTrSDujeJ67ielrgq/PSUikdL6gUA0OUJGpokRKa7RnQWbuUBcpzX8oX4ePqVya59zlWSvWODpeT/R484cTIirJhE0+
-----END RSA PRIVATE KEY-----'''
    alipay = AliPay(
        appid="2016092400585980", #支付宝app的id
        app_notify_url=None, #会掉视图
        app_private_key_string = app_private_key_string, #私钥字符
        alipay_public_key_string = alipay_public_key_string, #公钥字符
        sign_type="RSA2", #加密方法
    )
#发起支付
    order_string = alipay.api_alipay_trade_page_pay(
        out_trade_no=oreder_id,
        total_amount=str(money),  # 将Decimal类型转换为字符串交给支付宝
        subject="商贸商城",
        return_url='127.0.0.1:8000/callbackPay/',
        notify_url=None  # 可选, 不填则使用默认notify url
)

# 让用户进行支付的支付宝页面网址
    return "https://openapi.alipaydev.com/gateway.do?"+order_string

def callbackPay(request):
    return HttpResponse('支付成功')

def paymethod(request):
    url=Pay('0000000001','500')
    return HttpResponseRedirect(url)