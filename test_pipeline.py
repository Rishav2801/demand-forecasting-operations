import unittest
import numpy as np
import pandas as pd
from pipeline import features, conformal_radius, FEATURES
class ForecastTests(unittest.TestCase):
    def test_future_target_cannot_change_current_features(self):
        x=pd.DataFrame({'dteday':pd.date_range('2020-01-01',periods=90).astype(str),'cnt':np.arange(90),'holiday':0,'workingday':1})
        original=features(x)
        x.loc[60:,'cnt']=999999
        changed=features(x)
        pd.testing.assert_frame_equal(original.loc[original.dteday<='2020-03-01',FEATURES],changed.loc[changed.dteday<='2020-03-01',FEATURES])
    def test_corrected_quantile(self):
        self.assertEqual(conformal_radius(np.arange(1,101),.1),91)
    def test_target_components_excluded(self):
        self.assertFalse(set(['cnt','casual','registered','temp'])&set(FEATURES))
if __name__=='__main__': unittest.main()
