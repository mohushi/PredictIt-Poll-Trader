<p align="center">
    <img width="966" height="600" src="banner_edit.png">
 </p>

# PredictIt Poll Trader

<!-- Describe your project in brief -->
A python library for automated trading on PredictIt political outcomes. Supports rapid change detection of polling numbers.

<!-- The project title should be self explanotory and try not to make it a mouthful. (Although exceptions exist- **awesome-readme-writing-guide-for-open-source-projects** - would have been a cool name)
Add a cover/banner image for your README. **Why?** Because it easily **grabs people's attention** and it **looks cool**(*duh!obviously!*).
The best dimensions for the banner is **1280x650px**. You could also use this for social preview of your repo.
I personally use [**Canva**](https://www.canva.com/) for creating the banner images. All the basic stuff is **free**(*you won't need the pro version in most cases*).
There are endless badges that you could use in your projects. And they do depend on the project. Some of the ones that I commonly use in every projects are given below. 
I use [**Shields IO**](https://shields.io/) for making badges. It is a simple and easy to use tool that you can use for almost all your badge cravings. -->

# Demo-Preview

<!-- Add a demo for your project -->
![Trading Demo](./references/combined_gif_FINAL.gif)

The primary use case of this library involves:

1) Logging into a PredictIt polling market
2) Rapidly and repeatedly checking the corresponding poll source (RealClearPolitics in this demo)
3) Automatically purchasing shares BEFORE other traders acknowledge a change in the underlying asset (approval ratings)


<!-- After you have written about your project, it is a good idea to have a demo/preview(**video/gif/screenshots** are good options) of your project so that people can know what to expect in your project. You could also add the demo in the previous section with the product description.
Here is a random GIF as a placeholder.
![Random GIF](https://media.giphy.com/media/ZVik7pBtu9dNS/giphy.gif) -->

# Table of contents

<!-- After you have introduced your project, it is a good idea to add a **Table of contents** or **TOC** as **cool** people say it. This would make it easier for people to navigate through your README and find exactly what they are looking for.

Here is a sample TOC(*wow! such cool!*) that is actually the TOC for this README. -->

- [PredictIt Poll Trader](#predictit-poll-trader)
- [Demo-Preview](#demo-preview)
- [Installation](#installation)
- [Requirements](#requirements)
- [Usage](#usage)
- [Project Background](#project-background)
- [License](#license)

# Installation
[(Back to top)](#table-of-contents)

To use this project, first clone the repo on your device using the command below:
Provide instructions on using chromedriver. What version?

```git init```

```git clone MY_GITHUB_REPO.git```

# Requirements
[(Back to top)](#table-of-contents)

1) PredictIt account
2) ChromeDriver 90.0.4430.24: https://chromedriver.chromium.org/downloads
3) SmartProxy account with a "Datacenter plan": https://smartproxy.com/proxies/datacenter-proxies/pricing

A SmartProxy account is required for critical functions of pollchecker.py. If your intent is only to automate trades, then a SmartProxy account, and by extension pollchecker.py, are unnecessary. 

# Usage
[(Back to top)](#table-of-contents)

The marketdata.py, pitrader.py, and pollchecker.py libraries provide the capability to pair poll change detection with automated trading on the PredictIt platform. This capability is demonstrated in the following example.

```python
from pitrader import PiTrader
from pollchecker import PollChecker

# Locate the market number from the URL. "https://www.predictit.org/markets/detail/7002/"
market_num = 7002

trader = PiTrader(market_num=market_num, email='johndoe@gmail.com', password='super_secret', chromedriver_path='./chromedriver', headless_mode=True)
checker = PollChecker(market_num=market_num, proxy_username='johndough', proxy_password='superer_secret', num_bots=5)

# Rapidly query the poll source until the value changes
target_bracket = checker.async_script()

# Automatically purchase shares in the new bracket
trader.prepare_a_purchase(bracket_num=target_bracket, quantity=100, is_yes=True, max_price=99)
trader.execute_order()
trader.close()
```

There are a few things to note here. 

* First, PollChecker is capable of checking and processing polls from both RealClearPolitics.com and FiveThirtyEight.com. PollChecker automatically detects the source from the market number through marketdata.py and thus the user doesn't need to specify the source explicitly. 

* Second, the PollChecker constructor specifies ```num_bots=5```. A bot represents an individual poll querying unit. The bots operate asynchronously, so increasing ```num_bots``` directly increases the frequency of querying and likewise increases SmartProxy costs. 

* Third, the ```headless_mode``` parameter in the PiTrader constructor can be set to false in order to see the workflow of the automated trader. It should be set to True outside of debugging to increase performance.

* Finally, the ```async_script()``` function from pollchecker.py runs until completion. That is, the function will only complete once the polling value has changed significantly enough to change the trading bracket that it falls into. For example, suppose in the screenshot below, that Trump's approval rating is currently 42.4% (bracket 3, 0-index). If FiveThirtyEight updates the approval rating to 42.6%, ```async_script()``` will NOT terminate becauses the rating remains in the same bracket and is thus immaterial to trading. However, if the rating instead changed from 42.4% to 43.9%, the function would terminate and return the target bracket of 6. In the code snippet above, this target bracket is passed to PiTrader which would automatically place buy orders on bracket 6 YES.

<p align="center">
  <img src="references/Purchase_example.png">
</p>


# Project Background
[(Back to top)](#table-of-contents)

### Motivation

I began this project with the intention of refining several aspects of my data science toolkit, namely web scraping and time series forecasting. Initially, I had planned on scraping historical approval ratings to train and tune an autoregressive forecasting model. The model would enable me to identify mispriced opportunities in the polling markets and exploit them for a small profit week-over-week (PredictIt caps positions to $850). 


While configuring the data pipeline, I noticed a small delay between updates from the polling sources and corresponding price corrections in the market. For example, if RealClearPolitics (RCP) updated the polling value from 4.9 to 5.1, then it took approximatedly 10 seconds for traders to recognize this change, sell shares corresponding to 4.9, and purchase shares corresponding to 5.1. Realizing the arbitrage opportunity, I pivoted to this automated trader project and focused on optimizing for speed through asynchronous processes.

<p align="center">
  <img src="ProfitOT_final.png">
</p>

### Results

I began this project in January 2020. At the time, I could check for updated polling numbers once per 30 seconds which was too slow to gain an edge. Other traders priced in the changes before I could react. By the beginning of February, I could scrape the RCP website once per second through use of proxy services and asynchronous web requests. Two weeks later, I managed to increase output to hundreds of requests a second. Additionally, I configured an automatic trader to execute orders corresponding to polling changes. By project end, my trading script could detect a change, decide on the next action, and execute said action on PredictIt in less than 2 seconds -- all in all, a 100x fold increase in performance.

# License
[(Back to top)](#table-of-contents)

[GNU General Public License version 3](https://opensource.org/licenses/GPL-3.0)
