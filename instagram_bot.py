from selenium import webdriver
# from selenium.webdriver.common.keys import Keys
import schedule
import time
from utility_methods.utility_methods import *
import urllib.request
import os
from time import sleep
import json
import glob
from random import randrange


class InstaBot:

    def __init__(self, username=None, password=None):
        """"
        Creates an instance of InstaBot class.

        Args:
            username:str: The username of the user, if not specified, read from configuration.
            password:str: The password of the user, if not specified, read from configuration.

        Attributes:
            driver_path:str: Path to the chromedriver.exe
            driver:str: Instance of the Selenium Webdriver (chrome 72)
            login_url:str: Url for logging into IG.
            nav_user_url:str: Url to go to a users homepage on IG.
            get_tag_url:str: Url to go to search for posts with a tag on IG.
            logged_in:bool: Boolean whether current user is logged in or not.
        """

        self.username = config['IG_AUTH']['USERNAME']
        self.password = config['IG_AUTH']['PASSWORD']

        self.login_url = config['IG_URLS']['LOGIN']
        self.nav_user_url = config['IG_URLS']['NAV_USER']
        self.get_tag_url = config['IG_URLS']['SEARCH_TAGS']
        self.suggested_url = config['IG_URLS']['SUGGESTED']

        self.no_unfollow_unsuccessful = 0

        self.driver = webdriver.Chrome(
            config['ENVIRONMENT']['CHROMEDRIVER_PATH'])

        self.logged_in = False

    @insta_method
    def login(self):
        """
        Logs a user into Instagram via the web portal
        """

        self.driver.get(self.login_url)

        sleep(2)

        username_input = self.driver.find_element_by_name('username')
        password_input = self.driver.find_element_by_name('password')
        login_btn = self.driver.find_element_by_xpath(
            '//button[@type="submit"]')

        username_input.send_keys(self.username)
        password_input.send_keys(self.password)
        login_btn.click()

        # sleep(2)
        # # clicking not now for save Login info
        # self.driver.find_element_by_xpath(
        #     '//button[text()="Not Now"]').click()

        # sleep(2)
        # # clicking not now for showing notifications
        # self.driver.find_element_by_xpath(
        #     '//button[text()="Not Now"]').click()

    @ insta_method
    def search_tag(self, tag):
        """
        Naviagtes to a search for posts with a specific tag on IG.

        Args:
            tag:str: Tag to search for
        """

        self.driver.get(self.get_tag_url.format(tag))

    @ insta_method
    def nav_user(self, user):
        """
        Navigates to a users profile page

        Args:
            user:str: Username of the user to navigate to the profile page of
        """

        self.driver.get(self.nav_user_url.format(user))

    @ insta_method
    def follow_user(self, user):
        """
        Follows user(s)

        Args:
            user:str: Username of the user to follow
        """

        self.nav_user(user)

        follow_buttons = self.find_buttons('Follow')

        for btn in follow_buttons:
            btn.click()

    @ insta_method
    def click_follow_button(self):
        """
        Clicks follow button
        """

        follow_buttons = self.find_buttons('Follow')
        if len(follow_buttons) == 0:
            follow_buttons = self.find_buttons('Follow Back')

        follow_buttons[0].click()

    @ insta_method
    def click_unfollow_button(self):
        """
        Clicks unfollow button
        """
        unfollow_btns = self.driver.find_elements_by_xpath(
            "//span[@aria-label='Following']")
        if len(unfollow_btns) == 0:
            unfollow_btns = self.driver.find_elements_by_xpath(
                '//button[text()="Requested"]')

        if unfollow_btns:
            for btn in unfollow_btns:
                btn.click()
                unfollow_confirmation = self.find_buttons('Unfollow')[0]
                unfollow_confirmation.click()
        else:
            print('No {} buttons were found.'.format('Following'))

    @ insta_method
    def unfollow_user(self, user):
        """
        Unfollows user(s)

        Args:
            user:str: Username of user to unfollow
        """

        self.nav_user(user)

        unfollow_btns = self.driver.find_elements_by_xpath(
            "//span[@aria-label='Following']")
        if len(unfollow_btns) == 0:
            unfollow_btns = self.driver.find_elements_by_xpath(
                '//button[text()="Requested"]')

        if unfollow_btns:
            for btn in unfollow_btns:
                btn.click()
                unfollow_confirmation = self.find_buttons('Unfollow')[0]
                unfollow_confirmation.click()
        else:
            is_Error_page = self.driver.find_elements_by_xpath(
                "//div[contains(@class, 'error-container')]")

            if is_Error_page:
                self.no_unfollow_unsuccessful += 1
                self.prYellow("Error Page")
            else:
                print('No {} buttons were found.'.format('Following'))

    @ insta_method
    def download_user_images(self, user):
        """
        Downloads all images from a users profile.

        """

        self.nav_user(user)

        img_srcs = []
        finished = False
        while not finished:

            finished = self.infinite_scroll()  # scroll down

            img_srcs.extend([img.get_attribute(
                'src') for img in self.driver.find_elements_by_class_name('FFVAD')])  # scrape srcs

        img_srcs = list(set(img_srcs))  # clean up duplicates

        for idx, src in enumerate(img_srcs):
            self.download_image(src, idx, user)

    @ insta_method
    def like_and_comment_latest_posts(self, n_posts, like=True):
        """
        prerequisite: should already be navigated to the users page
        Likes a number of a users latest posts, specified by n_posts.

        Args:
            n_posts:int: Number of most recent posts to like or unlike
            like:bool: If True, likes recent posts, else if False, unlikes recent posts

        """
        self.driver.execute_script("window.scrollTo(0, '1.8vh')")

        action = 'Like' if like else 'Unlike'

        imgs = self.driver.find_elements_by_xpath(
            "//div[contains(@class, 'v1Nh3 kIKUG  _bz0w')]")
        for img in imgs[:n_posts]:
            img.click()
            time.sleep(2)
            try:
                self.driver.find_element_by_xpath(
                    '//button[contains(@class, "wpO6b")]/*[name()="svg"][@aria-label="{}"]'.format(action)).click()

            except Exception as e:
                self.prYellow(e)

            # self.comment_post('beep boop testing bot')
            self.driver.find_element_by_xpath(
                '//button[contains(@class, "wpO6b")]/*[name()="svg"][@aria-label="Close"]').click()

        rand_end = len(imgs[:n_posts])
        rand_begin = 0 if rand_end < 4 else (rand_end-4)

        if rand_end != 0:
            imgs[randrange(rand_begin, rand_end)].click()
            self.comment_on_photo()
            self.driver.find_element_by_xpath(
                '//button[contains(@class, "wpO6b")]/*[name()="svg"][@aria-label="Close"]').click()

    # @insta_method
    # def comment_post(self, text):
        # """
        # Comments on a post that is in modal form
        # """

        # comment_input = self.driver.find_elements_by_class_name('Ypffh')[0]
        # comment_input.click()
        # comment_input.send_keys(text)
        # comment_input.send_keys(Keys.Return)

        # print('Commentd.')

    def download_image(self, src, image_filename, folder):
        """
        Creates a folder named after a user to to store the image, then downloads the image to the folder.
        """

        folder_path = './{}'.format(folder)
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)

        img_filename = 'image_{}.jpg'.format(image_filename)
        urllib.request.urlretrieve(src, '{}/{}'.format(folder, img_filename))

    def infinite_scroll(self):
        """
        Scrolls to the bottom of a users page to load all of their media

        Returns:
            bool: True if the bottom of the page has been reached, else false

        """

        SCROLL_PAUSE_TIME = 1

        self.last_height = self.driver.execute_script(
            "return document.body.scrollHeight")

        self.driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        time.sleep(SCROLL_PAUSE_TIME)

        self.new_height = self.driver.execute_script(
            "return document.body.scrollHeight")

        if self.new_height == self.last_height:
            return True

        self.last_height = self.new_height
        return False

    def find_buttons(self, button_text):
        """
        Finds buttons for following and unfollowing users by filtering follow elements for buttons. Defaults to finding follow buttons.

        Args:
            button_text: Text that the desired button(s) has
        """

        buttons = self.driver.find_elements_by_xpath(
            "//*[text()='{}']".format(button_text))

        return buttons

    def prYellow(self, skk):
        """
        Yellow color print to terminal

        """
        print("\033[93m {}\033[00m" .format(skk))

    def done(self):
        """
        Done indicator

        """
        self.nav_user('tejasn14')

    def _get_names(self):
        """
        scrolls to the bottom of the following / followers popup and returns an array of all the users

        """
        scroll_box = self.driver.find_element_by_xpath(
            "/html/body/div[4]/div/div[2]")
        last_ht, ht = 0, 1
        while (last_ht != ht) or (self.driver.find_elements_by_xpath("/html/body/div[4]/div/div[2]/ul/div/li[25]/div/svg")):
            last_ht = ht
            sleep(2)
            ht = self.driver.execute_script("""
                arguments[0].scrollTo(0, arguments[0].scrollHeight);
                return arguments[0].scrollHeight;
                """, scroll_box)
        links = scroll_box.find_elements_by_tag_name('a')
        names = [name.text for name in links if name.text != '']
        # close button
        self.driver.find_element_by_xpath("/html/body/div[4]/div/div[1]/div/div[2]/button")\
            .click()
        return names

    def get_followers(self):
        """
        returns a list of all followers

        """
        self.driver.find_element_by_xpath("//a[contains(@href,'/followers')]")\
            .click()
        sleep(2)
        return self._get_names()

    def get_following(self):
        """
        returns a list of all following

        """
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]")\
            .click()
        sleep(2)
        return self._get_names()

    def store_data(self):
        """
        stores data of all followers, following and not following back in Data Directory

        """
        self.nav_user(self.username)
        followers = self.get_followers()
        following = self.get_following()

        with open('./Data/'+self.username+'_followers_'+str(len(followers))+'.json', 'w') as filehandle:
            filehandle.writelines("%s\n" % place for place in followers)

        with open('./Data/'+self.username+'_following_'+str(len(following))+'.json', 'w') as filehandle:
            filehandle.writelines("%s\n" % place for place in following)

        not_following_back = [
            user for user in following if user not in followers]
        with open('./Data/'+self.username+'_not_following_back_'+str(len(not_following_back))+'.json', 'w') as filehandle:
            filehandle.writelines(
                "%s\n" % place for place in not_following_back)

    def get_not_following_back_from_file(self):
        """
        returns a list of all not following back which is retrieved from file in Data Directory

        """
        all_files = glob.glob("./Data/*.json")
        path = list(filter(lambda k: self.username +
                           '_not_following_back' in k, all_files))[0]

        not_following_back = []
        # open file and read the content in a list
        with open(path, 'r') as filehandle:
            filecontents = filehandle.readlines()

            for line in filecontents:
                # remove linebreak which is the last character of the string
                current_place = line[:-1]

                # add item to the list
                not_following_back.append(current_place)

        return not_following_back

    def unfollow_bulk_profile(self):
        """
        unfollows bulk by visiting their profile page. The list of unfollowers is
        retrieved from the not_following_back file in Data Directory

        """
        self.no_unfollow_unsuccessful = 0
        not_following_back = self.get_not_following_back_from_file()
        for follower in not_following_back:
            self.unfollow_user(follower)
        self.prYellow("Unsuccessful unfollows: " +
                      str(self.no_unfollow_unsuccessful))

    def unfollow_bulk_popup(self):
        """
        unfollows bulk through the following popup. The list of unfollowers is
        retrieved from the not_following_back file in Data Directory

        """
        self.nav_user(self.username)
        self.driver.find_element_by_xpath("//a[contains(@href,'/following')]")\
            .click()
        sleep(2)
        not_following_back_arr = self.get_not_following_back_from_file()
        # scrolling to the bottom
        scroll_box = self.driver.find_element_by_xpath(
            "/html/body/div[4]/div/div[2]")
        last_ht, ht = 0, 1
        while (last_ht != ht) or (self.driver.find_elements_by_xpath("/html/body/div[4]/div/div[2]/ul/div/li[25]/div/svg")):
            last_ht = ht
            sleep(2)
            ht = self.driver.execute_script("""
                arguments[0].scrollTo(0, arguments[0].scrollHeight);
                return arguments[0].scrollHeight;
                """, scroll_box)

        all_following_box = self.driver.find_element_by_xpath(
            "//div[contains(@class, 'PZuss')]")
        all_following = all_following_box.find_elements_by_tag_name('li')
        self.prYellow(len(all_following))
        for following in all_following:
            user_name = (following.find_element_by_tag_name('a')).text
            if user_name in not_following_back_arr:
                following.find_element_by_xpath(
                    '//button[text()="Following"]').click()
                sleep(1)
                unfollow_confirmation = self.find_buttons('Unfollow')[0]
                unfollow_confirmation.click()

    def like_and_follow_user_from_suggestion(self, n_users=50):
        all_suggestions = []
        while len(all_suggestions) == 0:
            self.driver.get(self.suggested_url)
            self.driver.execute_script("window.scrollTo(0, '10vh')")

            sleep(2)
            suggestions_box = self.driver.find_element_by_xpath(
                '//*[@id="react-root"]/section/main/div/div[2]')
            links = suggestions_box.find_elements_by_tag_name('a')
            all_suggestions = [name.text for name in links if name.text != '']
            # filter all verified accounts
            all_suggestions = [
                user for user in all_suggestions if 'Verified' not in user]

        for suggested_user in all_suggestions[:n_users]:
            # if "Verified" in suggested_user:
            # suggested_user = suggested_user.replace("Verified", "")

            self.nav_user(suggested_user)
            sleep(1)
            followers_span = self.driver.find_elements_by_xpath(
                "//span[contains(@class, 'g47SY')]")
            no_of_followers = followers_span[1].get_attribute('innerHTML')

            # self.click_follow_button()
            if(no_of_followers.isnumeric() and int(no_of_followers) > 30 and int(no_of_followers) < 9000):
                self.like_and_comment_latest_posts(randrange(10, 15))
            # else:
            #     self.click_unfollow_button()

    def comment_on_photo(self):

        all_comments = self.get_all_comments()
        comment = all_comments[randrange(len(all_comments))]
        comment_input = self.driver.find_element_by_xpath(
            '/html/body/div[4]/div[2]/div/article/div[2]/section[3]/div/form/textarea')
        comment_input.click()
        comment_input = self.driver.find_element_by_xpath(
            '/html/body/div[4]/div[2]/div/article/div[2]/section[3]/div/form/textarea')
        JS_ADD_TEXT_TO_INPUT = """
            var elm = arguments[0], txt = arguments[1];
            elm.value += txt;
            elm.dispatchEvent(new Event('change'));
            """
        self.driver.execute_script(
            JS_ADD_TEXT_TO_INPUT, comment_input, comment)
        comment_input.send_keys(' ')
        comment_input.submit()

    def get_all_comments(self):
        with open('./comments.json', 'r', encoding="utf8") as filehandle:
            all_comments = json.load(filehandle)

        return all_comments

    def auto_unfollow(self):
        while True:
            self.unfollow_bulk_profile()
            time.sleep(5400)

    def schedule_like_and_comment(self):
        while True:
            delay = randrange(600, 1080)  # 10,18
            self.schedule_like_and_comment_error_handler()
            time.sleep(delay)

    def schedule_like_and_comment_error_handler(self):
        try:
            self.like_and_follow_user_from_suggestion()
        except Exception as e:
            self.prYellow(e)


if __name__ == '__main__':

    config_file_path = './config.ini'
    logger_file_path = './bot.log'
    config = init_config(config_file_path)
    logger = get_logger(logger_file_path)

    bot = InstaBot()
    bot.login()
    # bot.store_data()
    # bot.unfollow_bulk_profile()

    # bot.like_and_follow_user_from_suggestion(15)
    # bot.nav_user('reythecat2020')
    # bot.like_and_comment_latest_posts(15)

    # bot.comment_on_photo()
    # bot.like_and_comment_latest_posts('johngfisher', 2, like=True)
    # self.prYellow(following)
