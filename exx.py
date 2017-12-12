import hmac
import json, urllib2, hashlib,struct,sha,time
import sys
from collections import OrderedDict
import requests
#import pandas
requests.adapters.DEFAULT_RETRIES = 5
delay_time = 1
api_address=r"https://api.exx.com/"
class EXX():
    def __init__(self, config,name="EXX",base = "BTC",target="ETH",depth = False):
        # self.currency = target.lower()+'_'+base.lower()
        self.mykey = config[name]["access_key"]
        self.mysecret = config[name]["secret_key"]
        self.baseAPIUrl = "http://api.exx.com/data/v1/"
        self.baseTradeUrl = "http://trade.exx.com/api/"
        self.start_timeout = int(config[name]["timeout"])
        self.session = requests.Session()

    def __fill(self, value, lenght, fillByte):
        if len(value) >= lenght:
            return value
        else:
            fillSize = lenght - len(value)
        return value + chr(fillByte) * fillSize

    def __doXOr(self, s, value):
        slist = list(s)
        for index in xrange(len(slist)):
            slist[index] = chr(ord(slist[index]) ^ value)
        return "".join(slist)

    def __hmacSign(self, aValue, aKey):
        keyb = struct.pack("%ds" % len(aKey), aKey.encode("utf8"))
        value = struct.pack("%ds" % len(aValue), aValue.encode("utf8"))
        k_ipad = self.__doXOr(keyb, 0x36)
        k_opad = self.__doXOr(keyb, 0x5c)
        k_ipad = self.__fill(k_ipad, 64, 54)
        k_opad = self.__fill(k_opad, 64, 92)
        m = hashlib.sha512()
        m.update(k_ipad)
        m.update(value)
        dg = m.digest()

        m = hashlib.sha512()
        m.update(k_opad)
        subStr = dg[0:16]
        m.update(subStr)
        dg = m.hexdigest()
        return dg

    def __digest(self, aValue):
        value = struct.pack("%ds" % len(aValue), aValue.encode("utf8"))
        h = sha.new()
        h.update(value)
        dg = h.hexdigest()
        return dg

    def genReqTime(self):
        return str((int)(time.time() * 1000))

    def genSig(self, query):
        # SHA_secret = "yourSecretKey"
        # SHA_secret = self.__digest(self.mysecret)
        return  hmac.new(self.mysecret.encode('utf8'), query, digestmod=hashlib.sha512).hexdigest()

    def genUrl(self, base_url, uri, params=OrderedDict()):
        query = ""
        # params.update({"accesskey":self.mykey})]
        params.update({"nonce":self.genReqTime()})
        for key in sorted(params.keys()):
            query = "%s&%s=%s" % (query, key, params[key]) if len(query) != 0 else "%s=%s" % (key, params[key])
        # if len(query) > 0:
        #     query += "&"
        sig = self.genSig(query)
        print query
        query += '&signature=%s'%sig
        # self.mysecret="yourSecretKey"
        # print self.genSig("accesskey=yourAccessKey&nonce=1234567890123")
        # print query
        return base_url+uri + "?" + query

    # def getAllMarket(self,all_currency):
    #     res = {}
    #     for currency in all_currency:
    #         gt = self.getTicker(currency)
    #         res[currency] = {
    #             "last":float(gt["ticker"]["last"]),
    #             "last_last":(float(gt["ticker"]["low"])+float(gt["ticker"]["high"]))/2.0
    #         }
    #
    #     return res
    #
    # def getTicker(self,currency=None,tillOK= True):
    #     while True:
    #         try:
    #             uri = "ticker"
    #             params = OrderedDict()
    #             if currency == None:
    #                 params["currency"] = self.currency
    #             else:
    #                 params["currency"] = currency
    #             res = self.session.get(self.genUrl(self.baseAPIUrl,uri, params))
    #             js = json.loads(res.text)
    #             if not js or js.has_key("error"):
    #                 self.error("getTicker",js)
    #                 if not tillOK:
    #                     return None
    #                 continue
    #             return js
    #         except Exception, ex:
    #             self.error("getTicker",ex)
    #             if not tillOK:
    #                 return None
    #
    # def getKData(self,period="1min",start_time=-1,size=500):
    #     data = self.getK(start_time,period,size)
    #     result = pandas.DataFrame(data["data"])
    #     result.columns = ["date","open","high","low","close","volume"]
    #     result.date = pandas.to_datetime(result.date,unit='ms',utc=True)
    #     result = result.iloc[1:]
    #     result.date = result.date.map(lambda x:str(x))
    #     result = result.reindex(columns=["date","open","close","high","low","volume"])
    #     # result["date"] = result.apply(lambda x: time.localtime(x["timestamp"]),axis=1)
    #     return result
    #
    # def getK(self,since=-1,period="1min",size=1000,tillOK = True):
    #     while True:
    #         try:
    #             uri = "kline"
    #             params = OrderedDict()
    #             ####order can not change
    #             params["currency"] = self.currency
    #             params["type"] = period
    #             if since>0:
    #                 params["since"] = str(since)
    #             params["size"] = str(size)
    #             # params["merge"] = "0.5"
    #             res = self.session.get(self.genUrl(self.baseAPIUrl,uri, params))
    #             js = json.loads(res.text)
    #             if not js or js.has_key("error")or js.has_key('result') and js["result"] == False:
    #                 self.error("getK",js)
    #                 if not tillOK:
    #                     return None
    #                 continue
    #             return js
    #         except Exception, ex:
    #             self.error("getK",ex)
    #             if not tillOK:
    #                 return None
    #
    # def getDepth(self, size=10,tillOK = True):
    #     while True:
    #         try:
    #             uri = "depth"
    #             params = OrderedDict()
    #             ####order can not change
    #             params["currency"] = self.currency
    #             params["size"] = str(size)
    #             # params["merge"] = "0.5"
    #             res = self.session.get(self.genUrl(self.baseAPIUrl,uri, params),timeout=self.start_timeout)
    #             if res["status"] == False:
    #                 continue
    #             return json.loads(res.text)
    #         except Exception, ex:
    #             self.error("getDepth",ex)
    #             if tillOK:
    #                 continue
    #             else:
    #                 return None

    def getBalance(self):
        while True:
            try:
                uri = "getBalance"
                params =OrderedDict()
                params["accesskey"]=self.mykey
                res = self.session.get(self.genUrl(self.baseTradeUrl,uri,params),timeout=self.start_timeout)
                return json.loads(res.text)
            except Exception, ex:
                self.error("getBalance", ex)
                if tillOK:
                    continue
                else:
                    return None

    def buy(self,volume,price,currency,type):
        try:
            params=OrderedDict()
            uri = "order"
            params["method"] = "order"
            params["accesskey"] = self.mykey
            params["price"]=str(price)
            params["amount"] = str(volume)
            params["type"]= str(type)
            params["currency"]=str(currency)
            res = self.session.post(self.genUrl(self.baseTradeUrl,uri,params),timeout=self.start_timeout+5)
            print res
            js = json.loads(res.text)
            return js
        except Exception, ex:
            self.error("buy",ex)
            return None

    def sell(self,volume,price,currency,type):
        try:
            params=OrderedDict()
            uri = "order"
            params["method"] = "order"
            params["accesskey"] = self.mykey
            params["price"]=str(price)
            params["amount"] = str(volume)
            params["type"]=str(type)
            params["currency"]=str(currency)
            res = self.session.post(self.genUrl(self.baseTradeUrl,uri,params),timeout=self.start_timeout+5)
            return json.loads(res.text)
        except Exception, ex:
            self.error("sell",ex)
            return None

    def getOrder(self,currency,id):
        while True:
            try:
                params=OrderedDict()
                uri = "getOrder"
                params["method"] = "getOrder"
                params["accesskey"] = self.mykey
                params["id"] = id
                params["currency"]=str(currency)
                res = self.session.get(self.genUrl(self.baseTradeUrl,uri,params),timeout=self.start_timeout)
                js = json.loads(res.text)
                return js
            except Exception, ex:
                self.error("getOrder", ex)
                if tillOK:
                    continue
                else:
                    return None

    def deleteOrder(self,id,currency):
        try:
            params=OrderedDict()
            uri = "cancel"
            params["method"] = "cancel"
            params["accesskey"] = self.mykey
            params["id"] = id
            params["currency"]=str(currency)
            res = self.session.get(self.genUrl(self.baseTradeUrl,uri,params),timeout=self.start_timeout)
            js = json.loads(res.text)
            return js
        except Exception, ex:
            self.error("deleteOrder",ex)
            return None


    def error(self,func,err):
        time.sleep(delay_time)
        print >> sys.stderr, "EXX\t",func," error,", err

if __name__=="__main__":
    config = json.load(open('config.json','r'))
    exx = EXX(config)
    # print exx.getBalance()
    # print exx.buy(volume = 100,price=0.0001,currency='eos_eth',type='buy')
    # print exx.sell(volume=100, price=0.0001, currency='eos_eth', type='sell')
    # print exx.getOrder(id = '1562',currency = 'eos_eth')
    # print exx.deleteOrder(id = '1562',currency = 'eos_eth')

