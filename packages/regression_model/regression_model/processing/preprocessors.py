import numpy as np
import pandas as pd

from sklearn.base import BaseEstimator, TransformerMixin

from regression_model.processing.errors import InvalidModelInputError


# categorical missing value imputer
class CategoricalImputer(BaseEstimator,TransformerMixin):

    def __init__(self,variables=None):
        if not isinstance(variables,list):
            self.variables = [variables]

        else:
            self.variables = variables

    def fit(self,X,y=None):

        X = X.copy()    

        # make list of variable containing missing values
        self.cat_with_na = [var for var in X[self.variables].columns if X[
                                                var].isnull().sum()>1]

        return self

    def transform(self,X):
        X = X.copy()
        for feature in self.cat_with_na:
            X[feature] = X[feature].fillna('Not Av')

        return X



# Numerical missing value imputer
class NumericalImputer(BaseEstimator,TransformerMixin):

    def __init__(self,variables=None):
        if not isinstance(variables,list):
            self.variables = [variables]
        else:
            self.variables = variables

    def fit(self,X,y=None):
        # persist mode in a dictionary
        self.imputer_dict_ = {}

        for feature in self.variables:
            self.imputer_dict_[feature] = X[feature].mode()[0]

        
        # make list of variable containing missing values
        self.num_with_na = [var for var in X[self.variables].columns if X[
                                                var].isnull().sum()>1]
        
        return self

    def transform(self,X):
        X =X.copy()

        for feature in self.num_with_na:
            X[feature].fillna(self.imputer_dict_[feature],inplace=True)
        
        return X


# Temporal variable calculator
class TemporalVariableEstimator(BaseEstimator,TransformerMixin):

    def __init__(self,variables=None,reference_variable=None):

        if not isinstance(variables,list):
            self.variables = [variables]
        else:
            self.variables = variables

        self.reference_variable =reference_variable

    def fit(self,X,y=None):
        # we need this step to fit the sklearn pipeline
        return self

    def transform(self,X):
        X = X.copy()

        for feature in self.variables:
            X[feature] = X[self.reference_variable] - X[feature]

        return X


# frequent label categorical encoder
class RareLabelCategoricalEncoder(BaseEstimator,TransformerMixin):

    def __init__(self,tol=0.05,variables=None):
        
        self.tol = tol

        if not isinstance(variables,list):
            self.variables = [variables]
        else:
            self.variables = variables

    def fit(self,X,y=None):
        # perist frequent labels in dictionary
        self.encoder_dict_ = {}

        for var in self.variables:
            # the encoder will learn the most frequent categories
            t = pd.Series(X[var].value_counts()/np.float(len(X)))
            # frequent labels
            self.encoder_dict_[var] = list(t[t >= self.tol].index)

        return self
    
    def transform(self,X):
        X= X.copy()

        for feature in self.variables:
            X[feature] = np.where(X[feature].isin(self.encoder_dict_[
                            feature]),X[feature],'Rare')

        return X   



# string to numbers categorical encoder
class CategoricalEncoder(BaseEstimator,TransformerMixin):

    def __init__(self,variables=None):

        if not isinstance(variables,list):
            self.variables = [variables]
        else:
            self.variables = variables


    def fit(self,X,y=None):
        temp = pd.concat([X,y],axis=1)
        temp.columns = list(X.columns) + ['target']

        # persist transforming dictionary
        self.encoder_dict_ = {}

        for var in self.variables:
            t = temp.groupby([var])['target'].mean().sort_values(ascending=True).index
            self.encoder_dict_[var] = {k:i for i,k in enumerate(t,0)}

        return self

    def transform(self,X):
        # encode labels
        X = X.copy()

        for feature in self.variables:
            X[feature] = X[feature].map(self.encoder_dict_[feature])

        # check if transformer introduces NaN
        if X[self.variables].isnull().any().any():
            null_counts = X[self.variables].isnull().any()

            vars_ = {key: value for (key,value) in null_counts.items()
                            if value in True}
            raise errors.InvalidModelInputError(
                f'Categorical encoder has introduced NaN when '
                f'transforming categorical variables:  {vars_.keys()}')

        return X


# logarithm transformer
class LogTransformer(BaseEstimator,TransformerMixin):

    def __init__(self,variables=None):
        if not isinstance(variables,list):
            self.variables = [variables]
        else:
            self.variables = variables

    def fit(self,X,y=None):
        # to accomodate the pipeline
        return self

    def transform(self,X):

        X= X.copy()

        # check that the values are non-negative for log transform
        if not (X[self.variables] > 0).all().all():
            vars_ = self.variables[(X[self.variables] <=0).any()]
            raise errors.InvalidModelInputError(
                    f'Variables contain zero or negative values, '
                    f"can't apply log for vars: {vars_}" )

        for feature in self.variables:
            X[feature] = np.log(X[feature])

        return X

class DropUnecessaryFeatures(BaseEstimator,TransformerMixin):

    def __init__(self,variables_to_drop=None):

        self.variables = variables_to_drop

    def fit(self,X,y=None):
        return self

    def transform(self,X):
        # encode labels
        X = X.copy()
        X = X.drop(self.variables,axis=1)

        return X