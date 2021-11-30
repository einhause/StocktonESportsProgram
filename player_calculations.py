import requests
import json

apikey = ""  # omitted for github reupload


def createNull(a):
    test = {"summonerName": a, "tier": "UNRANKED", "rank": "UNRANKED", "queueType": "UNRANKED", "leaguePoints": 0,
            "wins": 0, "losses": 0}
    return test


def createPlayer(a):
    global apikey
    UserRequest = requests.get(
        "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{}?api_key={}".format(a, apikey))
    json_object_string = UserRequest.text
    json_object = json.loads(json_object_string)
    SummonerNum = (json_object["id"])
    UserRankedRequest = requests.get(
        "https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{}?api_key={}".format(SummonerNum, apikey))

    json_object_string2 = UserRankedRequest.text
    json_object2 = json.loads(json_object_string2)
    output = {}
    try:
        if json_object2[1]["queueType"] == "RANKED_FLEX_SR":
            output = json_object2[0]
        else:
            output = json_object2[1]
    except IndexError:
        try:
            if json_object2[0]["queueType"] == "RANKED_FLEX_SR":
                output = json_object2[0]
            else:
                output = json_object2[0]
        except IndexError:
            return createNull(a)

    return output


def GetType(json_object2):
    return json_object2["queueType"]


def PlayerInfo(json_object2):
    return [json_object2["summonerName"], json_object2["tier"], json_object2["rank"], json_object2["leaguePoints"],
            json_object2["wins"], json_object2["losses"]]


def playerRank(json_object2):
    return json_object2["tier"] + " " + json_object2["rank"]


def tierNumber(i):
    switcher = {
        "UNRANKED UNRANKED": int(0),
        "IRON I": int(-65),
        "IRON II": int(-80),
        "IRON III": int(-90),
        "IRON IV": int(-100),
        "BRONZE I": int(-22),
        "BRONZE II": int(-30),
        "BRONZE III": int(-36),
        "BRONZE IV": int(-45),
        "SILVER I": int(-1),
        "SILVER II": int(-6),
        "SILVER III": int(-11),
        "SILVER IV": int(-17),
        "GOLD I": int(10),
        "GOLD II": int(6),
        "GOLD III": int(3),
        "GOLD IV": int(1),
        "PLATINUM I": int(24),
        "PLATINUM II": int(20),
        "PLATINUM III": int(18),
        "PLATINUM IV": int(12),
        "DIAMOND I": int(60),
        "DIAMOND II": int(52),
        "DIAMOND III": int(43),
        "DIAMOND IV": int(33),
        "MASTER I": int(80),
        "GRAND MASTER I": int(90),
        "CHALLENGER I": int(100),
    }
    return switcher.get(i, "Invalid rank")


def get_emblem_image(tier):
    if tier == 'BRONZE':
        return 'imgs/ranked-emblems/Emblem_Bronze.png'
    elif tier == 'CHALLENGER':
        return 'imgs/ranked-emblems/Emblem_Challenger.png'
    elif tier == 'DIAMOND':
        return 'imgs/ranked-emblems/Emblem_Diamond.png'
    elif tier == 'GOLD':
        return 'imgs/ranked-emblems/Emblem_Gold.png'
    elif tier == 'GRANDMASTER':
        return 'imgs/ranked-emblems/Emblem_Grandmaster.png'
    elif tier == 'IRON':
        return 'imgs/ranked-emblems/Emblem_Iron.png'
    elif tier == 'MASTER':
        return 'imgs/ranked-emblems/Emblem_Master.png'
    elif tier == 'PLATINUM':
        return 'imgs/ranked-emblems/Emblem_Platinum.png'
    elif tier == 'SILVER':
        return 'imgs/ranked-emblems/Emblem_Silver.png'
    else:
        return 'imgs/esportslogo.jpg'


def getName(json_object2):
    a = json_object2['summonerName']
    return a


def FetchPlayerNumericle(json_object2):
    return tierNumber(json_object2["tier"] + " " + json_object2["rank"])


def teamOverAll(a):
    overallpoints = 0
    for i in range(len(a)):
        overallpoints = tierNumber(playerRank(a[i])) + overallpoints
    return overallpoints


def RecommendPlayer(a, b, c, team):
    if len(a) < 5:
        a = teamOverAll(a)
        b = teamOverAll(b)
        if len(c) >= 1:
            if a == b:
                return getName(c[0]) + " " + playerRank(c[0]) + " is recommended for " + team + " team."
            if a > b:
                reference = -9999
                referencei = 0
                for i in range(len(c)):
                    if tierNumber(playerRank(c[i])) + a <= b:
                        if tierNumber(playerRank(c[i])) + a >= reference:
                            reference = tierNumber(playerRank(c[i])) + a
                            referencei = i
                        if tierNumber(playerRank(c[i])) + a == b:
                            referencei = i
                            return getName(c[i]) + " " + playerRank(c[i]) + " is recommended for " + team + " team."
                if tierNumber(playerRank(c[referencei])) + a > b:
                    pass
                else:
                    return getName(c[referencei]) + " " + playerRank(
                        c[referencei]) + " is recommended for " + team + " team."
            if a < b:
                reference = 9999
                referencei = 0
                for i in range(len(c)):
                    if tierNumber(playerRank(c[i])) + a >= b:
                        if tierNumber(playerRank(c[i])) + a <= reference:
                            reference = tierNumber(playerRank(c[i])) + a
                            referencei = i
                        if tierNumber(playerRank(c[i])) + a == b:
                            referencei = i
                            return getName(c[i]) + " " + playerRank(c[i]) + " is recommended for " + team + " team."
                if tierNumber(playerRank(c[referencei])) + a < b:
                    pass
                else:
                    return getName(c[referencei]) + " " + playerRank(
                        c[referencei]) + " is recommended for " + team + " team."

            reference1 = a
            reference2 = b

            referenceLower = -9999
            referenceUpper = 9999
            referencei1 = 0
            referencei2 = 0
            average = (a + b) / 2
            averageArange, averageBrange = 0, 0
            if a > b:
                averageArange = (reference2 + average) / 2
                averageBrange = (reference1 + average) / 2
            if b > a:
                averageArange = (reference1 + average) / 2
                averageBrange = (reference2 + average) / 2
            for i in range(len(c)):
                if reference1 + tierNumber(playerRank(c[i])) >= averageArange and tierNumber(
                        playerRank(c[i])) + reference1 <= averageBrange:
                    if averageArange <= tierNumber(playerRank(c[i])) + reference1 <= average and tierNumber(
                            playerRank(c[
                                           i])) + reference1 > referenceLower:
                        referenceLower = tierNumber(playerRank(c[i])) + reference1
                        referencei1 = i

                    if averageBrange >= tierNumber(playerRank(c[i])) + reference1 >= average and tierNumber(
                            playerRank(c[
                                           i])) + reference1 < referenceUpper:
                        referenceUpper = tierNumber(playerRank(c[i])) + reference1
                        referencei2 = i

                    if tierNumber(playerRank(c[i])) + reference1 == average:
                        return getName(c[i]) + " " + playerRank(c[i]) + " is recommended for " + team + " team."

            if referenceLower == -9999:
                referenceLower = 0
            if referenceUpper == 9999:
                referenceUpper = average * 2

            referenceLower = average - referenceLower
            referenceUpper = referenceUpper - average
            referencei = referencei1
            if referenceLower < referenceUpper:
                referencei = referencei1
            if referenceLower > referenceUpper:
                referencei = referencei2
            if referenceLower == average and referenceUpper == average:
                return getName(c[0]) + " " + playerRank(c[0]) + " is recommended for " + team + " team."

            return getName(c[referencei]) + " " + playerRank(c[referencei]) + " is recommended for " + team + " team."
        else:
            return "There are no players in the queue currently."
    else:
        return "Team is already full."


def PlaceRecommend(a, b, c):
    if len(a) < 5:
        a = teamOverAll(a)
        b = teamOverAll(b)
        if len(c) >= 1:
            if a == b:
                return c[0]
            if a > b:
                reference = -9999
                referencei = 0
                for i in range(len(c)):
                    if tierNumber(playerRank(c[i])) + a <= b:
                        if tierNumber(playerRank(c[i])) + a >= reference:
                            reference = tierNumber(playerRank(c[i])) + a
                            referencei = i
                        if tierNumber(playerRank(c[i])) + a == b:
                            return c[i]
                if tierNumber(playerRank(c[referencei])) + a > b:
                    pass
                else:
                    return c[referencei]
            if a < b:
                reference = 9999
                referencei = 0
                for i in range(len(c)):
                    if tierNumber(playerRank(c[i])) + a >= b:
                        if tierNumber(playerRank(c[i])) + a <= reference:
                            reference = tierNumber(playerRank(c[i])) + a
                            referencei = i
                        if tierNumber(playerRank(c[i])) + a == b:
                            return c[i]
                if tierNumber(playerRank(c[referencei])) + a < b:
                    pass
                else:
                    return c[referencei]

            reference1 = a
            reference2 = b

            referenceLower = -9999
            referenceUpper = 9999
            referencei1 = 0
            referencei2 = 0
            average = (a + b) / 2
            averageArange, averageBrange = 0, 0
            if a > b:
                averageArange = (reference2 + average) / 2
                averageBrange = (reference1 + average) / 2
            if b > a:
                averageArange = (reference1 + average) / 2
                averageBrange = (reference2 + average) / 2
            for i in range(len(c)):
                if reference1 + tierNumber(playerRank(c[i])) >= averageArange and tierNumber(
                        playerRank(c[i])) + reference1 <= averageBrange:
                    if averageArange <= tierNumber(playerRank(c[i])) + reference1 <= average and tierNumber(
                            playerRank(c[
                                           i])) + reference1 > referenceLower:
                        referenceLower = tierNumber(playerRank(c[i])) + reference1
                        referencei1 = i

                    if averageBrange >= tierNumber(playerRank(c[i])) + reference1 >= average and tierNumber(
                            playerRank(c[
                                           i])) + reference1 < referenceUpper:
                        referenceUpper = tierNumber(playerRank(c[i])) + reference1
                        referencei2 = i

                    if tierNumber(playerRank(c[i])) + reference1 == average:
                        return c[i]

            if referenceLower == -9999:
                referenceLower = 0
            if referenceUpper == 9999:
                referenceUpper = average * 2

            referenceLower = average - referenceLower
            referenceUpper = referenceUpper - average
            referencei = referencei1
            if referenceLower < referenceUpper:
                referencei = referencei1
            if referenceLower > referenceUpper:
                referencei = referencei2
            if referenceLower == average and referenceUpper == average:
                return c[0]

            return c[referencei]


def sort_players(A, inhouse_points):
    for i in range(len(A)):
        for j in range(len(A)):

            lp1 = inhouse_points[A[i]['summonerName']]
            lp2 = inhouse_points[A[j]['summonerName']]

            if lp1 > lp2:
                temp = A[j]
                A[j] = A[i]
                A[i] = temp
    return A
