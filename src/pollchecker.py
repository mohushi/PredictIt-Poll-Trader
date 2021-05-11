import string
import random
import csv
import time
import requests
from marketdata import MarketData
import asyncio
import aiohttp
import bs4


class PollChecker:
    '''
    PollChecker comprises the entire asyncronous routine for quickly making
    URL requests to polling websites and reporting any changes. 
    
    The most common usage is: init() -> async_script()
    
    '''
    def __init__(self, market_num):
        '''
        Desc:
            Prompts user for proxy credentials and proxy settings.
            Retrieves necessary market data.
            
        Params: 
            market_num (int): PredictIt number assigned to specific market.

        '''
        self.market = MarketData(market_num)
        self.pollster = self.market.get_market_pollster()
        self.num_bots = input("How many checking bots to use? ")
        assert isinstance(self.num_bots, int), "Use a whole number of bots."
        self.username = input("Username for proxy service? ")
        self.password = input("Password for proxy service? ")

    async def fetch_ip(self, session):
        '''
        Desc:
            Asynchronous URL request to retreive the IP address.
            
        Params: 
            session (aiohttp ClientSession): Persistent http session used
                to preserve cookies and webdriver settings; for performance
                purposes.
            
        Returns:
            ip_address (str)

        '''
        proxy = self.get_proxy()
        assert proxy != None
        r = await session.get('https://ipinfo.io/ip', proxy = proxy, timeout = 5)
        ip = await r.text()
        return ip
    
    #Returns a random string of length 3 to change the proxy port.
    def proxy_id_generator(self):
        return ''.join(random.choice(string.ascii_letters) for i in range(3))
    

    def get_proxy(self):
        '''
        Desc:
            Retreives the proxy URL corresponding to the pollster. The RCP
            webpage has certain protections which require a rotating proxy,
            whereas FTE polls can be pulled with a sticky proxy. Throws
            ValueError if the market pollster is not recognized as rcp or fte.
            
        Returns:
            proxy_url (str): Specific proxy gateway to make URL requests through.

        '''
        if self.pollster == 'fte':
            proxy = f'http://user-{self.username}:{self.password}@gate.dc.smartproxy.com:20000'
        elif self.pollster == 'rcp':
            proxy_id = self.proxy_id_generator()
            proxy = f'http://user-{self.username}-session-{proxy_id}:{self.password}@gate.dc.smartproxy.com:20000'
        else:
            raise ValueError('Pollster is not recognized')
        return proxy

    async def fetch_rcp(self, session):
        '''
        Desc:
            Asynchronous URL request which retreives RealClearPolitics's
            current polling value.
            
        Params: 
            session (aiohttp ClientSession): Persistent http session used
                to preserve cookies and webdriver settings; for performance
                purposes.
            
        Returns:
            rcp_poll_results (tuple(str, float)): Current leader in polling and
                the leader's polling advantage over his competitor. 

        '''
        proxy = self.get_proxy('rcp')
        url = 'https://www.realclearpolitics.com/epolls/2020/president/us/general_election_trump_vs_biden-6247.html'
        chunk_size = 15000 #Polling value located in first 15k bits of request
        async with session.get(url, proxy = proxy, timeout = 5, chunked = chunk_size) as response:
            chunk = await response.content.read(chunk_size)
        decoded_chunk = chunk.decode('utf-8')
        return self.parse_rcp(decoded_chunk)    
    
    async def fetch_fte(self, session):
        '''
        Desc:
            Asynchronous URL request which retreives FiveThirtyEight's
            current polling value.
            
        Params: 
            session (aiohttp ClientSession): Persistent http session used
                to preserve cookies and webdriver settings; for performance
                purposes.
            
        Returns:
            fte_poll_result (float): Current FTE poll value. 
        
        '''
        proxy = self.get_proxy()
        url = 'https://projects.fivethirtyeight.com/trump-approval-data/approval_topline.csv'
        headers = {'Range': 'bytes=100-500'}
        async with session.get(url, timeout = 2, proxy = proxy, headers = headers) as response:
            chunk = await response.read()
        decoded_chunk = chunk.decode('utf-8')
        cr = csv.reader(decoded_chunk.splitlines(), delimiter = ',')
        my_list = list(cr)[0:4]
        for poll in my_list:
            if poll[1].lower() == 'all polls':
                est = round(float(poll[3]), 1)
                return est   
            
    async def fetch_poll_estimate(self, session):
        '''
        Desc:
            Wrapper function for fetching polls from different sources.
        
        Params: 
            session (aiohttp ClientSession): Persistent http session used
                to preserve cookies and webdriver settings; for performance
                purposes.
            
        Returns:
            poll_results (multiple types): current poll value of the pollster
                corresponding to the specific market.
        
        '''
        if self.pollster == 'rcp':
            return await self.fetch_rcp(session)
        elif self.pollster == 'fte':
            return await self.fetch_fte(session)
    
    async def detect_change_routine(self, identification, session):
        '''
        Desc:
            Continuously checks the polling value until it changes enough to
            change the bracket the value is located in. This function can be
            run multiple times asynchronously. Each function call is known
            as a bot or poll checking bot. Function will not terminate
            until a change has been detected.
        
        Params: 
            identification (int): The ID of the poll checking bot.
            
            session (aiohttp ClientSession): Persistent http session used
                to preserve cookies and webdriver settings; for performance
                purposes.
            
        Returns:
            new_bracket (int): The index of the new bracket which the polling
                value has just changed into.
        
        '''
        global TIMELINE #Tracks time between polling checks
        is_first = True
        reference_value = 0
        reference_bracket = 0    
        iteration = 1
        while (True):
            flag = True
            while (flag):
                try:
                    current_value = await self.fetch_poll_estimate(session)
                    elapsed = time.time() - TIMELINE
                    TIMELINE = time.time()
                    print("Bot: {0}\t Est: {1}\t Time: {2}\t Iter: {3}" \
                          .format(identification, current_value, round(elapsed, 3), iteration))
                    flag = False
                    iteration += 1
                except asyncio.CancelledError:
                    print('Exiting request loop!') 
                    return None
                except Exception as e:
                    print(f'Caught error in bot: {repr(e)}')
                    await asyncio.sleep(1)
            if (is_first):
                reference_value = current_value
                reference_bracket = self.market.buy_bracket_selector(reference_value)
                is_first = False
            elif (reference_value != current_value):
                new_bracket = self.market.buy_bracket_selector(current_value)
                if (new_bracket != reference_bracket):
                    print('----------CHANGE DETECTED----------')
                    return new_bracket
                reference_value = current_value
                      
    async def detect_change(self):
        '''
        Desc:
            Wrapper function for async poll change detection.
            This function will run until the polls change enough to place
            the value into a different bracket.
            num_bots determines how frequently polls are checked.
            
        Returns:
            new_bracket_index (int): int within [0, 8], indicating the
                new bracket the polling value is in.
        
        '''
        async with aiohttp.ClientSession() as session: 
            completed, futures = await asyncio.wait([self.detect_change_routine(i, session) for i in range(self.num_bots)], return_when = asyncio.FIRST_COMPLETED)
            for each in completed:
                return each.result()
    
    def async_script(self):
        '''
        Desc:
            Wrapper for the entire async routine. 
            User should need to call only this function for all asynchronous
            tasks. 
            
        Returns:
            new_value (int): Index corresponding to the bracket the polling
                value just switched to.
        
        '''
        new_value = asyncio.run(self.detect_change())
        return new_value    
    
    def request_rcp(self):
        '''
        Desc:
            Non-asynchronous URL request which retreives RealClearPolitics's
            current polling value.
            
        Returns:
            rcp_poll_results (tuple(str, float)): Current leader in polling and
                the leader's polling advantage over his competitor.
        
        '''
        url = 'https://www.realclearpolitics.com/epolls/2020/president/us/general_election_trump_vs_biden-6247.html'
        response = requests.get(url, timeout = 5)
        decoded_chunk = response.text
        return self.parse_rcp(decoded_chunk)
    
    def request_fte(self):
        '''
        Desc:
            Non-asynchronous URL request which retreives FiveThirtyEight's
            current polling value.
            
        Returns:
            fte_poll_result (float): Current FTE poll value. 
        
        '''
        url = 'https://projects.fivethirtyeight.com/trump-approval-data/approval_topline.csv'
        response = requests.get(url, timeout = 5)
        chunk = response.text
        cr = csv.reader(chunk.splitlines(), delimiter = ',')
        my_list = list(cr)[0:4]
        for poll in my_list:
            if poll[1].lower() == 'all polls':
                est = round(float(poll[3]), 1)
                return est 
            
    def parse_rcp(self, decoded_chunk):
        '''
        Desc:
            Parses the literal polling value from RCP into a PredictIt
            readable form.
        
        Params: 
            decoded_chunk (str): Text body of the URL response from the RCP
                polling page.
            
        Returns:
            rcp_poll_results (tuple(str, float)): Current leader in polling and
                the leader's polling advantage over his competitor.
        
        '''
        soup = bs4.BeautifulSoup(decoded_chunk, 'lxml')
        rcp_avg_row = soup.find('tr', attrs = {'class': 'rcpAvg'})
        avg = rcp_avg_row.find('td', attrs = {'class':'spread'}).text
        leader = str(avg.split()[0])
        spread = float(avg.split()[1])
        return (leader, spread)