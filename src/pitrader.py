from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import time
import pytz
import datetime


class PiTrader:
    '''
    Web bot capable of navigating to a PredictIt market page and conducting
    purchases.
    
    Typical usage: prepare_a_purchase() --> execute_order() --> close() (must conduct in this order)
    
    '''
    
    def __init__(self, market_num):
        '''
        Desc:
            Checks if PredictIt is under maintenance. If not, the bot logs in
            and navigates to a specific market page.
            
        Params:
            market_num (int): PredictIt number assigned to specific market.
        
        '''
        assert isinstance(market_num, int)
        self.raise_for_under_maintenance()
        self.market_url = f'https://www.predictit.org/markets/detail/{market_num}'
        self.order_button = None
        self.order_is_ready = False
        self.driver = self.HeadlessDriver()
        self.login()

    def prepare_a_purchase(self, bracket_num, quantity, is_yes):
        '''
        Desc:
            Wrapper function. 
            Prepares order so that execute_order() can be called.
            Must be run before every purchase.
            Shouldn't need to call select_contract() or enter_buy_info() separately.
            
        Params:
            bracket_num (int): Bracket to purchase shares from. Top to bottom, 0 -> 8.
            quantity (int): Number of shares to purchase.
            is_yes (bool): Indicate purchase of YES shares or NO shares.

        '''
        self.select_contract(bracket_num, is_yes)
        time.sleep(0.1)
        self.enter_buy_info(quantity)
        self.describe_order(bracket_num, quantity, is_yes)
        self.order_is_ready = True

    def execute_order(self):
        '''
        Desc:
            Executes a prepared order.
            Throws exception if order_is_ready = False.

        '''
        assert self.order_is_ready, 'Order is not prepared.'
        self.order_button.click()
        print(f'ORDER EXECUTED. Time is: {time.localtime()}')
        self.order_is_ready = False
        
    def close(self):
        self.driver.quit()
        
    def save_screenshot(self, filename):
        self.driver.save_screenshot(filename)
        
    def enter_buy_info(self, quantity):
        '''
        Desc:
            Enter final purchasing details (quantity and price).
            Call this function AFTER a specfic contract has been chosen.
            Throws exception if order button clicked before running this.    
        
        Params:
            quantity (int): Number of shares to purchase.
            
        '''
        assert isinstance(quantity, int)
        limit_price = 90 #Pay up to 90 cents per share
        price_box = self.driver.find_element_by_class_name('purchase-offer-value__input')
        price_box.clear()
        price_box.send_keys(limit_price)
        quantity_box = self.driver.find_element_by_class_name('purchase-quantity-value__input')
        quantity_box.clear()
        quantity_box.send_keys(quantity)
        check_box = self.driver.find_element_by_class_name('checkbox__tick')
        check_box.click()
        order_button = self.driver.find_element_by_class_name('purchase-offer-desktop__footer-next-button')
        self.order_button = order_button 
        
    def raise_for_under_maintenance(self):
        '''
        Desc:
            Raises exception if PI is under maintenance and no trades can occur.
            Assumes that maintenance time is 04:00 - 05:00 ET.

        '''
        tz = pytz.timezone('America/New_York')    
        current_eastern_time = datetime.datetime.now(tz)
        buffered_time = current_eastern_time + datetime.timedelta(minutes = 1) #Prevents trades near maintenance
        maintenance_start_time = buffered_time.replace(hour = 3, minute = 59, second = 0) 
        maintenance_end_time = buffered_time.replace(hour = 5, minute = 1, second = 0)
        if (buffered_time >= maintenance_start_time) and (buffered_time <= maintenance_end_time):
            raise Exception('PredictIt is currently under maintenance.')
     
    def describe_order(self, bracket_num, quantity, is_yes):
        s = 'NO'
        if is_yes:
            s = 'YES'
        print(f'Prepared to purchase {quantity} shares of BUY {s} in bracket {bracket_num}.')
        print('Execute order when ready.')
    
    def HeadlessDriver(self):
        '''
        Desc:
            Sets the options for the webdriver used to conduct trading.
        
        Returns:
            driver (chromedriver): webdriver for trading
        '''
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--window-size=1920x1080')
        driver = webdriver.Chrome(options = chrome_options, executable_path = r"chromedriver_win32\chromedriver.exe")
        return driver
    
    def login(self):
        '''
        Desc:
            Logs into PI and navigates to the market page.
            Prompts user for login info.

        '''
        self.driver.get(self.market_url)
        time.sleep(0.1)
        login_button = self.driver.find_element_by_id('login')
        login_button.click()   
        email_box = self.driver.find_element_by_id('username')
        user_login = input("Enter your PredictIt login: ")
        email_box.send_keys(user_login)
        pw_box = self.driver.find_element_by_id('password')
        user_pw = input("Enter your PredictIt password: ")
        pw_box.send_keys(user_pw)
        submit_button = self.driver.find_element_by_xpath("//button[@type='submit']")
        submit_button.click()
        time.sleep(1)
        
    def select_contract(self, bracket_num, is_yes):
        '''
        Desc:
            Clicks on a specific contract button.
            
        Params:
            bracket_num (int): Bracket to purchase shares from. Top to bottom, 0 -> 8.
            is_yes (bool): Indicate purchase of YES shares or NO shares.
            
        '''
        assert isinstance(bracket_num, int)
        assert isinstance(is_yes, bool)
        buy_buttons = self.driver.find_elements_by_class_name("market-contract-horizontal-v2__button-single")
        yes_buttons = buy_buttons[::2] #0-8
        no_buttons = buy_buttons[1::2] #0-8
        if is_yes:
            contract_button = yes_buttons[bracket_num]
        else:
            contract_button = no_buttons[bracket_num]
        contract_button.click()