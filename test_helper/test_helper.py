import hashlib
from PIL import Image
import numpy as np
import requests
from requests_oauthlib import OAuth1
from dateutil import parser
import tweepy
import json
from datetime import timedelta


class TestFailure(Exception):
    pass
class PrivateTestFailure(Exception):
    pass

class Test(object):
    passed = 0
    numTests = 0
    failFast = False
    private = False

    @classmethod
    def setFailFast(cls):
        cls.failFast = True

    @classmethod
    def setPrivateMode(cls):
        cls.private = True

    @classmethod
    def assertTrue(cls, result, msg="", msg_success=""):
        cls.numTests += 1
        if result == True:
            cls.passed += 1
            print "1 test passed. " + msg_success
        else:
            print "1 test failed. " + msg
            if cls.failFast:
                if cls.private:
                    raise PrivateTestFailure(msg)
                else:
                    raise TestFailure(msg)

    @classmethod
    def assertEquals(cls, var, val, msg="", msg_success=""):
        cls.assertTrue(var == val, msg, msg_success)

    @classmethod
    def assertEqualsHashed(cls, var, hashed_val, msg="", msg_success=""):
        cls.assertEquals(cls._hash(var), hashed_val, msg, msg_success)

    @classmethod
    def assertEqualsImagesHashed(cls, img_path, hashed_img, hashed_img_mode, hashed_img_size, msg="", msg_success=""):
        # We show the correct image size and mode without hashing
        assert cls._img_mode(img_path) == hashed_img_mode, "Different kinds of images. The image mode should be {}.".format(hashed_img_mode)
        assert cls._img_size(img_path) == hashed_img_size, "Different sizes. The image size should be {}.".format(hashed_img_size)
        cls.assertEquals(cls._dhash(img_path), hashed_img, msg, msg_success)

    @classmethod
    def printStats(cls):
        print "{0} / {1} test(s) passed.".format(cls.passed, cls.numTests)

    @classmethod
    def _hash(cls, x):
        return hashlib.sha1(str(x)).hexdigest()

    @classmethod
    def _dhash(cls, image_path, hash_size=8):
        # Grayscale and shrink the image in one step.
        image = Image.open(image_path)
        image = image.convert('L').resize(
            (hash_size + 1, hash_size),
            Image.ANTIALIAS,
        )
        # Compare adjacent pixels.
        difference = []
        for row in xrange(hash_size):
            for col in xrange(hash_size):
                pixel_left = image.getpixel((col, row))
                pixel_right = image.getpixel((col + 1, row))
                difference.append(pixel_left > pixel_right)
        # Convert the binary array to a hexadecimal string.
        decimal_value = 0
        hex_string = []
        for index, value in enumerate(difference):
            if value:
                decimal_value += 2**(index % 8)
            if (index % 8) == 7:
                hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
                decimal_value = 0
        return ''.join(hex_string)

    @classmethod
    def _img_mode(cls, image_path):
        image = Image.open(image_path)
        return image.mode

    @classmethod
    def _img_size(cls, image_path):
        image = Image.open(image_path)
        return image.size
    
    # Some specific cases:
    # Lab 3.1 Ex. 4
    @classmethod
    def euclideanDistMatrix(cls, a, b, det, msg="", msg_success=""):
        if type(a) != np.ndarray or type(b) != np.ndarray:
            print 'Arrays "a" and "b" should numpy arrays'
            cls.assertEquals(False, True, msg, msg_success)
            return
        mask = lambda x: len(zip(*np.where((x < -100) | (x > 100)))) == 0 and x.dtype == 'int32'
        if not mask(a) or not mask(b):
            print 'Arrays "a" and "b" should contains integer numbers from -100 to 100'
            cls.assertEquals(False, True, msg, msg_success)
            return
        c = np.sqrt(np.power(a,2) + np.power(b,2))
        cls.assertEquals(det, np.linalg.det(c), msg, msg_success)
        
    # Lab 8.1 Ex.1
    @classmethod
    def twitterFriendsList(cls, friends, url, auth, params, msg="", msg_success=""):
        res = requests.get(url, auth=auth, params=params)
        data = res.json()
        fr = []
        for i in data['users']:
            fr.append({'name': i['name'], 'followers_count': i['followers_count']})
        fr.sort(key=lambda x: -x['followers_count'])
        cls.assertEquals(friends, fr, msg, msg_success)
        
    # Lab 8.1 Ex.2
    @classmethod
    def twitterRecentTweets(cls, tweets, url, auth, params, msg="", msg_success=""):
        res = requests.get(url, auth=auth, params=params)
        data = res.json()
        result = []
        for i in data:
            if i['retweet_count'] > 0:
                result.append({
                        'created_at':i['created_at'], 
                        'author':i['user']['name'], 
                        'text':i['text'], 
                        'retweet_count': i['retweet_count']
                    })
        cls.assertEquals(tweets, result, msg, msg_success)
        
    # Lab 8.1 Ex.3
    @classmethod
    def twitterHashtagsTweets(cls, tweets, url, msg="", msg_success=""):
        if url != 'https://stream.twitter.com/1.1/statuses/filter.json?track=twitter,tweet,world':
            cls.assertEquals(True, False, 'Incorrect URL', '')
            return
        if not isinstance(tweets, list):
            cls.assertEquals(True, False, 'Incorrect data type', '')
            return
        if isinstance(tweets, list) and len(tweets) != 5:
            cls.assertEquals(True, False, 'Incorrect content', '')
            return
        if isinstance(tweets, list) and len(tweets) == 5 and False in map(lambda x: isinstance(x, list), tweets):
            cls.assertEquals(True, False, 'Incorrect content', '')
            return
        i = 0
        while True:
            try:
                x = tweets[0][i]['created_at']
                break
            except:
                i += 1
        i = -1
        while True:
            try:
                y = tweets[4][i]['created_at']
                break
            except:
                i -= 1
        diff = parser.parse(y).minute*60 + parser.parse(y).second - (parser.parse(x).minute*60 + parser.parse(x).second)
        cls.assertEquals(0 < diff <= 301, True, msg, msg_success)
    
    # Lab 8.1 Ex.3
    @classmethod
    def twitterHashtagsTweetsCount(cls, amount_list, tweets, url, msg="", msg_success=""):
        if url != 'https://stream.twitter.com/1.1/statuses/filter.json?track=twitter,tweet,world':
            cls.assertEquals(True, False, 'Incorrect URL', '')
            return
        try:
            x = []
            for group in tweets:
                c = 0
                for i in group:
                    if ('lang' in i and i['lang'] == 'en') or ('user' in i and i['user']['followers_count'] > 1000):
                        c += 1
                x.append(c)
            cls.assertEquals(x, amount_list, msg, msg_success)
        except:
            cls.assertEquals(False, True, msg, msg_success)
    
    # Lab 8.1 Ex.4
    @classmethod
    def twitterBillGates(cls, data, api, msg="", msg_success=""):
        BillGates = api.get_user("BillGates")
        result = {'created_at': BillGates.created_at, 'last_tweet_text': api.home_timeline(BillGates.id)[0].text}
        cls.assertEquals(data, result, msg, msg_success)

    # Lab 8.2 Ex.5.1
    @classmethod
    def existCollections(cls, client, msg="", msg_success=""):
        cls.assertEquals(True, 'users' in client.twitter.collection_names() and 'tweets' in client.twitter.collection_names(), msg, msg_success)

    # Lab 8.2 Ex.5.2
    @classmethod
    def countRecord(cls, data, client, msg="", msg_success=""):
        result = client.twitter.tweets.count()
        cls.assertEquals(10000, result, msg, msg_success)
   
    # Lab 8.2 Ex.5.3
    @classmethod
    def existField(cls, data, client, msg="", msg_success=""):
        q_t = {
            "created_at": {"$exists": True},
            "author_id": {"$exists": True},
            "author_name": {"$exists": True},
            "retweet_count": {"$exists": True},
            "id": {"$exists": True},
            "lang": {"$exists": True},
            "source": {"$exists": True},
            "text": {"$exists": True}
        }
        q_u = {
            "created_at": {"$exists": True},
            "id": {"$exists": True},
            "name": {"$exists": True},
            "description": {"$exists": True},
            "followers_count": {"$exists": True},
            "friends_count": {"$exists": True},
            "lang": {"$exists": True},
            "profile_image_url": {"$exists": True},
            "location": {"$exists": True},
            "time_zone": {"$exists": True},
            "tweets": {"$exists": True}
        }
        result = client.twitter.tweets.count() == client.twitter.tweets.count(q_t) \
                 and client.twitter.users.count() == client.twitter.users.count(q_u)
        if result:
            for i in client.twitter.users.find():
                if i['tweets'] != cls._tweets_ids(i['id']):
                    result = False
                    break
        cls.assertEquals(True, result, msg, msg_success)
        
    @classmethod
    def _tweets_ids(cls, author_id):
        return list( set( list(client.twitter.tweets.aggregate([
            {"$match": {"author_id":author_id }},
            {"$group": {"_id": {"author_id": "$author_id"}, "ids": {"$push": "$id"}} },
            {"$project": {"ids": 1}}
        ]))[0]['ids'] ) )

    # Lab 8.2 Ex.5.4
    @classmethod
    def bigDataTweets(cls, data, client, msg="", msg_success=""):
        td = timedelta(minutes=30)
        start = list(client.twitter.tweets.aggregate([{"$sort":{"created_at":1}},{"$limit":1},{"$project": {"created_at":1}}]))[0]['created_at']
        end = list(client.twitter.tweets.aggregate([{"$sort":{"created_at":-1}},{"$limit":1},{"$project": {"created_at":1}}]))[0]['created_at']
        data = list(client.twitter.tweets.aggregate([{
                    "$match":{
                        "text":{"$regex":"#BigData"},
                        "retweet_count":0,
                        "created_at":{"$lte":end-td}
                    }
                }]))
        col_name = 'bigdata_tweets_'+start.strftime("%Y-%m-%d %H:%M:%S")+'_'+end.strftime("%Y-%m-%d %H:%M:%S")
        result = client.twitter[col_name].count() == len(data)
        cls.assertEquals(True, result, msg, msg_success)

    # Lab 8.2 Ex.5.5
    @classmethod
    def top5Tweets(cls, data, client, msg="", msg_success=""):
        q = [
            {
                "$group": {
                    "_id": {
                        "lang": "$lang"
                    }
                }
            },
            {"$project": 
                 {"_id":1}
            }
        ]
        result = {}
        for lang in list(client.twitter.tweets.aggregate(q)):
            query = [
                    {
                        "$match":{
                            "lang":lang['_id']['lang']
                        }
                    },
                    {
                      "$sort":  {
                            "retweet_count": -1,
                            "created_at": 1
                        }
                    },
                    {"$project": 
                         {"created_at":1,"author_name":1,"text":1,"_id":-1}
                    },
                    {
                        "$limit":5
                    }
                ]
            result[lang['_id']['lang']] = []
            for i in list(client.twitter.tweets.aggregate(query)):
                del(i['_id'])
                result[lang['_id']['lang']].append(i)
        cls.assertEquals(data, result, msg, msg_success)

    # Lab 8.2 Ex.5.6
    @classmethod
    def timeZoneTweets(cls, data, client, msg="", msg_success=""):
        result = {}
        for i in list(client.twitter.users.aggregate([{"$group": {"_id": {"time_zone": "$time_zone"}}}])):
            q = [
                {
                   "$match": { 
                        "time_zone":i['_id']['time_zone'],
                        "$or":[
                            {"lang":"en"},
                            {"lang":"es"},
                            {"lang":"fr"}
                        ]
                    }
                },
                {"$project": 
                     {"name":1,"profile_image_url":1,"tweets":1,"ff":{"$add":["$friends_count","$followers_count"]}}
                },
                {
                    "$sort": {
                        "ff":-1
                    }
                },
                {
                    "$limit":1
                },
                {"$project": 
                     {"name":1,"profile_image_url":1,"tweets":1}
                }
            ]
            t = list(client.twitter.users.aggregate(q))
            if(len(t)):
                del(t[0]['_id'])
                t[0]['tweets'] = cls._getTweetsByIDS(t[0]['tweets'], client)
                result[i['_id']['time_zone']] = t[0]
        cls.assertEquals(data, result, msg, msg_success)
        
    @classmethod
    def _getTweetsByIDS(cls, ids, client):
        ids = list(set(ids))
        result = {}
        for i in list(client.twitter.tweets.aggregate([
                {"$match": {"id":{"$in":ids}}},
                {"$project": {'_id':-1,"id":1,"created_at":1,"text":1}}
            ])):
            del(i['_id'])
            t = i.copy()
            del(t['id'])
            result[i['id']] = t
        return result.values()
