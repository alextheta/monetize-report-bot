from datetime import date
import datetime
import time
import argparse
import requests
import telebot

appodealTaskStatusCheckRetry = 20
appodealTaskStatusCheckTime = 2
appodealRequestDataString = 'https://api-services.appodeal.com/api/v2/stats_api?api_key={apiKey}&user_id={userId}&date_from={dateFrom}&date_to={dateTo}&detalisation%5B%5D=app'
appodealRequestStatusString = 'https://api-services.appodeal.com/api/v2/check_status?api_key={apiKey}&user_id={userId}&task_id={taskId}'
appodealRequestResultString = 'https://api-services.appodeal.com/api/v2/output_result?api_key={apiKey}&user_id={userId}&task_id={taskId}'

appodealAppReportString = '''
 App *{appName}* on Appodeal ({dateFrom} - {dateTo})
                Revenue: {revenue}
                eCPM: {eCPM}
'''


def appodeal_test_connection():
    currentDay = datetime.date.today()
    appodealDataRequest = appodealRequestDataString.format(apiKey=appodealApiKey, userId=appodealUserId, dateFrom=currentDay, dateTo=currentDay)

    try:
        dataResponse = requests.get(appodealDataRequest).json()
    except Exception as e:
        return False

    print(dataResponse)
    if (not 'code' in dataResponse or dataResponse['code'] != 0):
        return False

    return True


# init
parser = argparse.ArgumentParser(description="Monetize bot", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--token", help="Telegram bot token", required=True)
parser.add_argument("--ad-api", help="Appodeal API key", required=True)
parser.add_argument("--ad-uid", help="Appodeal user ID", required=True)
args = parser.parse_args()
config = vars(args)

botToken = config['token']
appodealApiKey = config['ad_api']
appodealUserId = config['ad_uid']

bot = telebot.TeleBot(botToken)
if (appodeal_test_connection() == False):
    print("Failed to test Appodeal credentials")
    exit(-1)
else:
    print("Appodeal credentials OK")

print("Running...")
# init end


def appodeal_request(timescale):
    # data request
    currentDay = datetime.date.today()
    if (timescale == 'day'):
        previousDate = currentDay - datetime.timedelta(days=1)
    if (timescale == 'month'):
        previousDate = currentDay.replace(day=1)

    dataRequest = appodealRequestDataString.format(apiKey=appodealApiKey, userId=appodealUserId, dateFrom=previousDate, dateTo=currentDay)
    # status wait
    try:
        dataResponse = requests.get(dataRequest).json()
    except Exception as e:
        return str(e), False

    print(dataResponse)
    if (not 'code' in dataResponse or dataResponse['code'] != 0):
        return dataResponse['message'], False
    taskId = dataResponse['task_id']
    statusRequest = appodealRequestStatusString.format(apiKey=appodealApiKey, userId=appodealUserId, taskId=taskId)

    taskCompleted = False
    for attempt in range(appodealTaskStatusCheckRetry):
        time.sleep(appodealTaskStatusCheckTime)
        statusResponse = requests.get(statusRequest).json()
        print(statusResponse)
        if (statusResponse['task_status'] == '1'):
            taskCompleted = True
            break

    if (not taskCompleted):
        return 'Response wait timeout', False

    # result output
    resultRequest = appodealRequestResultString.format(apiKey=appodealApiKey, userId=appodealUserId, taskId=taskId)
    resultResponse = requests.get(resultRequest).json()
    resultResponse['dateFrom'] = str(previousDate)
    resultResponse['dateTo'] = str(currentDay)
    print(resultResponse)
    return resultResponse, True


def build_report(data):
    apps = ''
    totalRevenue = 0
    totalECPM = 0

    for app in data['data']:
        appRevenue = round(app['revenue'], 3)
        appECPM = round(app['ecpm'], 3)
        apps += appodealAppReportString.format(appName=app['app_name'], revenue=appRevenue, eCPM=appECPM, dateFrom=data['dateFrom'], dateTo=data['dateTo'])
        totalRevenue += appRevenue
        totalECPM += appECPM

    result = apps + '\n*Total revenue*: {revenue}\n*Total eCPM*: {eCPM}'.format(revenue=round(totalRevenue, 3), eCPM=round(totalECPM, 3))
    return result


def fix_escape_characters(input):
    return input.translate(str.maketrans({
        ".":  r"\.",
        "(":  r"\(",
        ")":  r"\)",
        "-":  r"\-"
    }))


def report(message, timescale):
    data, status = appodeal_request(timescale)
    if (status):
        report = build_report(data)
        bot.reply_to(message, fix_escape_characters(report), parse_mode="MarkdownV2")
    else:
        bot.reply_to(message, "Error: " + data)


@bot.message_handler(commands=["start"])
def handle_start(m, res=False):
    bot.send_message(m.chat.id, 'Monetize report bot is here')


@bot.message_handler(commands=['report_day'])
def handle_report(message):
    report(message, 'day')


@bot.message_handler(commands=['report_month'])
def handle_report(message):
    report(message, 'month')


bot.polling(none_stop=True, interval=0)
