import re
import requests


class MarketData:
    '''
    Contains specfic market info from the PI API. Information includes
    bracket ranges, market pollster, and expiration status.
    
    Typical usage: init() -> (retreive the new polling numbers) -> buy_bracket_selector() 
    
    '''
    
    def __init__(self, market_num):
        '''
        Desc:
            Retrieves market data, generates bracket bounds, and checks if market
            is expired.
        
        Params: 
            market_num (int): PredictIt number assigned to specific market.
        
        '''
        assert isinstance(market_num, int)
        api_url = f'https://www.predictit.org/api/marketdata/markets/{market_num}'
        response = requests.get(api_url)
        self.market_num = market_num
        self.market_data = response.json()
        self.bracket_bounds = self.get_bracket_bounds()
        self.raise_for_expired_market()

    def buy_bracket_selector(self, raw_value):
        '''
        Desc:
            Given the polling raw value, this function will return the 
            corresponding bracket index the value corresponds to. This function
            only applies to poling markets.
            
            EG  raw_value = 4.1
                bracket_bounds = [2.2, 3.1, 5.0, 6.1, 7.9]
                returned value = 2
                
        Params:
            raw_value (numerical): literal polling value from polling src.
            
        Returns:
            target_bracket (int): Index of corresponding bracket. 
                Brackets are indexed base 0.
            
        '''
        #RCP polling values are NOT single value. Must convert.
        if self.get_market_pollster().lower() == 'rcp':    
            spread = self.rcp_value_interpreter(raw_value)
        else:
            spread = raw_value
        target_bracket = 0
        for bound in self.bracket_bounds:
            if (spread < bound):
                return target_bracket
            target_bracket += 1        
        
    def get_bracket_bounds(self):
        '''
        Desc:
            Retreives the upper bounds for all contracts within the market.
                            
        Returns:
            bracket_bounds (list of nums): Upper bounds as defined by the market.
                First value in list is the upper bound for the
                first bracket.
            
        '''
        contracts = self.market_data['contracts']
        bracket_bounds = []
        for con in contracts:
            #Bracket values must contain a decimal
            upper_bound = re.search('\d+\.\d+', con['shortName']).group()
            upper_bound = round(float(upper_bound), 1)
            bracket_bounds.append(upper_bound)
        bracket_bounds.sort()
        del bracket_bounds[0]
        bracket_bounds.append(999) #Arbitrarily large upper bound
        return bracket_bounds
                
    def rcp_value_interpreter(self, raw_rcp):
        '''
        Desc:
            Converts the raw polling data from RealClearPolitics into a single
            value for Trump v. Biden presidential polling market.
            
            EG  raw_rcp = ("trump", 2.5) = -2.5 (based on market organiziation)
                
        Params:
            raw_rcp (tuple(str, num)): polling value from RCP.
            
        Returns:
            spread (num): Converted single value which can be used to identify a bracket.
            
        '''
        leader = raw_rcp[0]
        spread = raw_rcp[1]
        if (spread < 0) or (spread > 20): #Checks for unexpected avg
            raise Exception('RCP average is bad. It is {}'.format(spread))
        if (leader.lower() == 'trump'): #Bracket ranges are relative to Trump
            spread *= -1.0
        elif (leader.lower() != 'biden'):
            raise Exception("Current leader is unknown. It is {}".format(leader.lower))
        return spread

    def get_market_pollster(self):
        mkt_name = self.market_data['name']
        pollsters = ['rcp', 'fte'] 
        for p in pollsters:
            if p in mkt_name.lower():
                return p
        raise Exception(f"The pollster: '{mkt_name}', is not recognized.")
    
    def raise_for_expired_market(self):
        if 'close' in self.market_data['status'].lower():
            raise Exception('This market is expired.')
            