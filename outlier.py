def outlier(data,factor = [],measure='',locparameter='mean',std = 1):
    groups = df.groupby(factor)[measure]

    groups_mean = groups.transform(locparameter)
    groups_std = groups.transform('std')
    m = df['actRT'].between(groups_mean.sub(groups_std.mul(std)),
                          groups_mean.add(groups_std.mul(std)),
                          inclusive=False)
    #print(m)
    new_df = df.loc[m]
    return new_df
# TO DO:
##number of outliers groupwise
###other methods of outlier like using iqr