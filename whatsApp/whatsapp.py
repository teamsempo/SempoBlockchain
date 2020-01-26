from time import sleep
from datetime import datetime

import sentry_sdk

import requests
from requests.auth import HTTPBasicAuth

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from RedisQueue import RedisQueue

from json import dumps
from pusher import Pusher

import config

class WhatsAppReader():

    def send_active_contact_message(self,messsage):

        chatbox = self.driver.find_element_by_css_selector('._2S1VP')

        chatbox.clear()
        chatbox.send_keys(messsage)
        chatbox.send_keys(Keys.RETURN)


    def select_user_by_phone(self,phone_number):

        searchbox = self.driver.find_element_by_css_selector('.jN-F5')

        searchbox.clear()
        searchbox.send_keys(phone_number)

        sleep(0.3)

        elapsed = 0
        while elapsed < 5:
            try:
                matched_sidebar_elements = self.driver.find_elements_by_class_name('_2EXPL')
                selected_element = self.try_to_select_a_contact_from_sidebar(matched_sidebar_elements, searchbox)

                if selected_element:
                    searchbox.clear()
                    closebutton = self.driver.find_element_by_css_selector('.C28xL')
                    closebutton.click()
                    return True

            except NoSuchElementException:
                pass

            except StaleElementReferenceException:
                pass

            sleep(0.3)
            elapsed += 0.3

        searchbox.clear()
        closebutton = self.driver.find_element_by_css_selector('.C28xL')
        closebutton.click()
        return False

    def try_to_select_a_contact_from_sidebar(self, sidebar_elements, searchbox):

        for element in sidebar_elements:
            icons = element.find_elements_by_css_selector("._3ZW2E")

            if len(icons) > 0:

                element.click()

                searchbox.clear()

                return True

            else:

                return False


    def find_chat_elements(self):

        try:
            chatbox = self.driver.find_element_by_css_selector('._9tCEa')

            return chatbox.find_elements_by_xpath("child::*[not(div[contains(@class, 'message-out')])]")

        except NoSuchElementException:
            return None

    def extract_message_from_chat_element(self, chat_element):
        data_attribute = chat_element\
            .find_element_by_css_selector('[data-pre-plain-text]').get_attribute("data-pre-plain-text")

        date, username = data_attribute.strip('[').strip(': ').split('] ')

        text = chat_element.find_element_by_css_selector('.selectable-text').text

        return {'text': text, 'date': date, 'username': username}

    def find_last_unread_in_chat(self):

        chat_elements = self.find_chat_elements()

        return self.extract_message_from_chat_element(chat_elements[-1])

    def find_unread_convos(self):

        convo_elements = self.driver.find_elements_by_css_selector('._2wP_Y')

        convo_dicts = []

        transform_extractor = lambda x: int(x.value_of_css_property('transform').split(',')[-1][:-1])

        for element in convo_elements:

            transform = transform_extractor(element)

            unread = bool(len(element.find_elements_by_css_selector('.CxUIE')))

            if unread:
                convo_dicts.append({'element': element,
                                     'transform': transform
                                    })

        sorted_elements = sorted(convo_dicts, key=lambda x: x['transform'], reverse = True)

        return sorted_elements


    def find_last_unread_message(self, oldest_convo = True):

        chat_elements = self.find_chat_elements()

        if chat_elements is not None:
            most_recent_message = self.find_last_unread_in_chat()

            if most_recent_message != self.previous_read_message and self.previous_read_message is not None:
                self.previous_read_message = most_recent_message
                return most_recent_message


        unread_convos = self.find_unread_convos()

        if len(unread_convos) == 0:
            return None

        convo_index = 0

        while convo_index < len(unread_convos):

            if oldest_convo != True:
                unread_convos.reverse()

            unread_convos[convo_index]['element'].click()

            message = self.find_last_unread_in_chat()

            if message != self.previous_read_message:

                self.previous_read_message = message

                return message

            convo_index += 1

        return None

    def logout_if_possible(self):

        try:
            element = self.driver.find_element_by_css_selector('._1qi0v')
            element.click()

        except NoSuchElementException:
            pass



    def find_scan_code(self, timeout = 30):
        element = WebDriverWait(self.driver, timeout).until(lambda x: x.find_element_by_class_name('_2EZ_m'))

        data = element.get_attribute('data-ref')

        return data

    def refresh_code(self):

        try:
            element = self.driver.find_element_by_css_selector('._2zblx')
            element.click()

        except NoSuchElementException:
            pass

    def check_if_in_chat(self):

        try:
            self.driver.find_element_by_css_selector('.RLfQR')
            return True

        except NoSuchElementException:

            return False

    def __init__(self, command_executor = None, session_id = None, previous_read_message = None):

        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")

        chrome_options.add_argument("--user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'")

        chrome_options.add_argument('--verbose')
        chrome_options.add_argument('--log-path=/tmp/chrome.log')


        if command_executor == None:
            if config.CHROMEDRIVER_LOCATION == 'None': #Launching in docker container
                chrome_options.add_argument('--headless')
                self.driver = webdriver.Chrome(chrome_options=chrome_options)
                self.driver.set_window_size(1920, 1080)

            else:
                self.driver = webdriver.Chrome(config.CHROMEDRIVER_LOCATION, chrome_options=chrome_options)

            self.driver.get('https://web.whatsapp.com')

            print(self.driver.session_id )
            print(self.driver.command_executor._url)

            self.find_scan_code()

        else:
            self.driver = webdriver.Remote(command_executor=command_executor,desired_capabilities={})
            self.driver.close()
            self.driver.session_id = session_id

        self.previous_read_message = previous_read_message

def watch_for_qr_login():

    in_chat = whatsApp.check_if_in_chat()

    if not in_chat:

        scan_code = None
        broadcast_whatsApp_status('waiting for code scan')

        while not in_chat:

            sleep(0.5)

            whatsApp.logout_if_possible()

            whatsApp.refresh_code()

            try:
                new_code = whatsApp.find_scan_code(timeout=1)

                if new_code != scan_code and new_code is not None:
                    scan_code = new_code

                    print(datetime.utcnow())

                    print(scan_code)

                    broadcast_qr_code(scan_code)


            except TimeoutException:
                pass

            except StaleElementReferenceException as e:

                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                error_message = template.format(type(e).__name__, e.args)

                print('Incoming blockchain_task:')
                print(datetime.utcnow())
                print(error_message)

                pass

            in_chat = whatsApp.check_if_in_chat()

        broadcast_whatsApp_status('chat loaded')


def broadcast_qr_code(code):
    micro_q.set_info('whatsApp_qr_code', code)
    pusher_client.trigger(config.PUSHER_SUPERADMIN_ENV_CHANNEL, 'qr_code', dumps(code))

def broadcast_whatsApp_status(status):
    micro_q.set_info('whatsApp_status', status)
    pusher_client.trigger(config.PUSHER_SUPERADMIN_ENV_CHANNEL, 'status', dumps(status))

def parse_queue_task(task):

    try:
        phone_number = int(str(task.data.get('phone')).replace(' ', ''))

    except TypeError:
        response = {'status': 'fail', 'message': 'invalid phone number'}
        print(response)
        task.set_response(response)
        return

    except ValueError:
        response = {'status': 'fail', 'message': 'invalid phone number'}
        print(response)
        task.set_response(response)
        return

    contact = whatsApp.select_user_by_phone(phone_number)

    if not contact:
        response = {'status': 'fail', 'message': 'user not found'}
        print(response)
        task.set_response(response)
        return

    whatsApp.send_active_contact_message(task.data.get('message'))

    response = {'status': 'success'}
    print(response)
    task.set_response(response)
    return



if __name__ =='__main__':

    print('whatsapp starting: ' + str(datetime.utcnow()))
    sentry_sdk.init(config.SENTRY_SERVER_DSN, release=config.WEB_VERSION)


    try:

        pusher_client = Pusher(
        app_id=config.PUSHER_APP_ID,
        key=config.PUSHER_KEY,
        secret=config.PUSHER_SECRET,
        cluster=config.PUSHER_CLUSTER,
            ssl=True
        )

        micro_q = RedisQueue('WhatsApp-' + config.DEPLOYMENT_NAME, url=config.REDIS_URL)

        app_host = config.APP_HOST

        if config.location == 'PROD':
            sleep(30)

        r = requests.get(app_host + '/api/auth/check_basic_auth/',
                         auth=HTTPBasicAuth(config.BASIC_AUTH_USERNAME + 'foo',
                                            config.BASIC_AUTH_PASSWORD))

        # command_executor = 'http://127.0.0.1:50042'
        # session_id = 'aaba0eed62a856dcef2364d37d05d1a2'

        whatsApp = WhatsAppReader()

    except Exception:
        client.captureException()

        raise

    watch_for_qr_login()

    while True:

        watch_for_qr_login()

        try:
            message = whatsApp.find_last_unread_message()

            if message is not None:
                print(message)
                r = requests.post(app_host + '/api/whatsapp/',
                                  json=message,
                                  auth = HTTPBasicAuth(config.BASIC_AUTH_USERNAME, config.BASIC_AUTH_PASSWORD))

                whatsApp.send_active_contact_message(r.json().get('reply'))

                # broadcast_whatsApp_status(message)

            task = micro_q.get_nowait()

            if task:
                print(datetime.utcnow())
                print(task)
                parse_queue_task(task)


            sleep(0.2)

        except Exception as e:

            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            error_message = template.format(type(e).__name__, e.args)

            print(error_message)

            broadcast_whatsApp_status(error_message)