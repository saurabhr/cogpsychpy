import pandas as pd
import scipy as sp
from scipy.stats import t
import numpy as np

#from: http://www.cookbook-r.com/Graphs/Plotting_means_and_error_bars_%28ggplot2%29/
## Gives count, mean, standard deviation, standard error of the mean, and confidence interval (default 95%).
##   data: a data frame.
##   measurevar: the name of a column that contains the variable to be summariezed
##   groupvars: a vector containing names of columns that contain grouping variables
##   conf_interval: the percent range of the confidence interval (default is 95%)
def summarySE(data, measurevar, groupvars, conf_interval=0.95):
    def std(s):
        return np.std(s, ddof=1)
    def stde(s):
        return std(s) / np.sqrt(len(s))

    def ci(s):
        # Confidence interval multiplier for standard error
        # Calculate t-statistic for confidence interval: 
        # e.g., if conf.interval is .95, use .975 (above/below), and use df=N-1
        ciMult = t.ppf(conf_interval/2.0 + .5, len(s)-1)
        return stde(s)*ciMult
    def ciUp(s):
        return np.mean(s)+ci(s)
    def ciDown(s):
        return np.mean(s)-ci(s)
    
    data = data[groupvars+measurevar].groupby(groupvars).agg([len, np.mean, std, stde, ciUp, ciDown, ci])

    data.reset_index(inplace=True)


    data.columns = groupvars+ ['_'.join(col).strip() for col in data.columns.values[len(groupvars):]]

    return data


#from: http://www.cookbook-r.com/Graphs/Plotting_means_and_error_bars_%28ggplot2%29/
## Norms the data within specified groups in a data frame; it normalizes each
## subject (identified by idvar) so that they have the same mean, within each group
## specified by betweenvars.
##   data: a data frame.
##   idvar: the name of a column that identifies each subject (or matched subjects)
##   measurevar: the name of a column that contains the variable to be summariezed
##   betweenvars: a vector containing names of columns that are between-subjects variables
def normDataWithin(data, idvar, measurevar, betweenvars=[]):
    def std(s):
        return np.std(s, ddof=1)

    #temp = data[data.cond == "PC_IDLE"]
    #temp = temp[idvar+betweenvars+measurevar]
    #temp.columns = idvar+betweenvars + [x+"_PC_IDLE" for x in measurevar]

    data_subjMean = data.groupby(idvar+betweenvars).agg([np.mean])
    data_subjMean.reset_index(inplace=True)
    data_subjMean.columns = idvar+betweenvars + ['_'.join(col).strip() for col in data_subjMean.columns.values[len(idvar+betweenvars):]]

    data = pd.merge(data, data_subjMean, on=idvar+betweenvars)
    #data = pd.merge(data, temp, on=idvar+betweenvars)

    for obj in measurevar:
        data[obj+"_norm"] = data[obj] - data[obj+"_mean"] + data[obj].mean()
        #data[obj+"_norm"] = std(data[obj])/data[obj+"_std"]*(data[obj] - data[obj+"_mean"]) + data[obj].mean()
        #data[obj+"_norm"] = data[obj] - data[obj+"_PC_IDLE"]
        #del data[obj+"_mean"]
        #del data[obj+"_std"]
    
    return data



#from: http://www.cookbook-r.com/Graphs/Plotting_means_and_error_bars_%28ggplot2%29/
## Summarizes data, handling within-subjects variables by removing inter-subject variability.
## It will still work if there are no within-S variables.
## Gives count, un-normed mean, normed mean (with same between-group mean),
##   standard deviation, standard error of the mean, and confidence interval.
## If there are within-subject variables, calculate adjusted values using method from Morey (2008).
##   data: a data frame.
##   measurevar: the name of a column that contains the variable to be summariezed
##   betweenvars: a vector containing names of columns that are between-subjects variables
##   withinvars: a vector containing names of columns that are within-subjects variables
##   idvar: the name of a column that identifies each subject (or matched subjects)
##   conf_interval: the percent range of the confidence interval (default is 95%)
def summarySEwithin(data, measurevar, betweenvars=[], withinvars=[], idvar=[], conf_interval=.95):
    # Get the means from the un-normed data
    datac = summarySE(data, measurevar, groupvars=betweenvars+withinvars, conf_interval=conf_interval)
    for e in measurevar:
        del datac[e+"_std"]
        del datac[e+"_stde"]
        del datac[e+"_ci"]
        del datac[e+"_ciUp"]
        del datac[e+"_ciDown"]

    # Norm each subject's data
    ndata = normDataWithin(data, idvar, measurevar, betweenvars)

    # This is the name of the new columns
    measurevar_n = [x+"_norm" for x in measurevar]+measurevar
    
    # Collapse the normed data - now we can treat between and within vars the same
    ndatac = summarySE(ndata, measurevar_n, groupvars=betweenvars+withinvars,
                      conf_interval=conf_interval)
    # Apply correction from Morey (2008) to the standard error and confidence interval
    #  Get the product of the number of conditions of within-S variables
    nWithinGroups = 1
    for v in withinvars:
        nWithinGroups = nWithinGroups*len(ndatac[v].unique())
    correctionFactor = np.sqrt( nWithinGroups / (nWithinGroups-1) )
    
    # Apply the correction factor
    for m in measurevar_n:
        ndatac[m+"_std"] = ndatac[m+"_std"] * correctionFactor
        ndatac[m+"_stde"] = ndatac[m+"_stde"] * correctionFactor
        ndatac[m+"_ci"] = ndatac[m+"_ci"] * correctionFactor
    
    return ndatac
