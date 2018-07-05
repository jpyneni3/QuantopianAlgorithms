import pandas

#Built using manual strategy algorithm from 4646. Trades based on MACD and Bollinger Bands
#Bollinger Bands => sell when price goes through top band and comes back down
#                => buy when prices goes below bottom band and comes back up
#MACD            => buy when signal (ema12-ema26) crosses from negative to positive
#                => sell when signal (ema12-ema26) crosses from positive to negative
##

def getbbands(context, data, n=20):
    price_history = data.history(context.stock, 'price', n, '1d') #Price of last 19 days and today
    mean = price_history.mean()
    stdev = price_history.std()
    upper = mean + 2*stdev
    lower = mean - 2*stdev
    return upper,lower, mean

def getema(data, n=5):
    ema = data.ewm(span=n, min_periods=n, adjust=False).mean()
    return ema[-1]

def getmacd(context, data):
    prices_26 = data.history(context.stock, 'price', 26, '1d') #Price of last 25 days and today
    prices_12 = data.history(context.stock, 'price', 12, '1d') #Price of last 11 days and today
    ema26 = getema(prices_26, 26)
    ema12 = getema(prices_12, 12)
    return ema26-ema12

def initialize(context):
    context.stock = sid(23709)
    context.qty = 1000 #Shares to buy or sell
    context.stddev_limit = 1.75
    context.exits =[False]
    context.enters = [False]
    context.macd_hist = [0]
    schedule_function(order_handling, date_rules.every_day())

def order_handling(context, data):

    current_price = data.current(context.stock, 'price')
    upper_bb, lower_bb, sma = getbbands(context, data, 20)

    curr_macd = getmacd(context, data)
    print(curr_macd)
    print(context.macd_hist[-1])
    record(NFLX=current_price)
    record(Upper=upper_bb)
    record(MA20=sma)
    record(Lower=lower_bb)
    record(MACD=curr_macd)


    # At top of bands?
    if current_price >= upper_bb and context.exits[-1] == False: #Just reached upperband, wait until it comes back through to sell
        context.exits.append(True)
    elif current_price <= upper_bb and context.exits[-1]: #On the way back from upperband, close
        context.exits.append(False)
        if context.portfolio.positions[context.stock].amount >= 0: #If we own stock, close out
            # Close our long position if we have one
            close_position(context, data) #Sell what we have
            order(context.stock, -context.qty)  #Short a 1000
    # At bottom of bands?
    elif current_price <= lower_bb and context.enters[-1] == False :
        context.enters.append(True)
        # Are we short or neutral?
    elif current_price >= lower_bb and context.enters[-1]:
        context.enters.append(False)
        print("bought bb")
        if context.portfolio.positions[context.stock].amount <= 0:
            # Close our short position if we have one
            close_position(context, data)
            order(context.stock, context.qty) #Buy more
    if curr_macd > 0 and context.macd_hist[-1] < 0 : #go in because macd crossover from negative to positive
        print("bought macd")
        if context.portfolio.positions[context.stock].amount <= 0:
            # Close our short position if we have one
            close_position(context, data)
            order(context.stock, context.qty)
    elif curr_macd < 0 and context.macd_hist[-1] > 0: #go short because macd crossover from positive to negative
        print("sold macd")
        if context.portfolio.positions[context.stock].amount >= 0:
            # Close our long position if we have one
            close_position(context, data) #Sell what we have
            order(context.stock, -context.qty) #Short


    context.macd_hist.append(curr_macd)
    return

def close_position(context, data):
   # Open position?
   if context.portfolio.positions[context.stock].amount > 0:
        order(context.stock, -context.qty)
   elif context.portfolio.positions[context.stock].amount < 0:
        order(context.stock, context.qty)
   return
