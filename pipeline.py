"""One-day-ahead demand backtesting with causal lags and calibrated intervals."""
import io
import zipfile
from reporting import export_sql_results
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from reporting import ROOT, fetch, manifest, save_json, report, preview

FEATURES=['lag_1','lag_7','lag_14','mean_7','mean_28','std_7','dow_sin','dow_cos','year_sin','year_cos','trend','holiday','workingday']

def features(raw):
    frame=raw.sort_values('dteday').copy().reset_index(drop=True)
    dates=pd.to_datetime(frame.dteday)
    assert dates.is_unique
    assert dates.diff().dropna().eq(pd.Timedelta(days=1)).all(), 'Daily grid must be complete'
    for lag in [1,7,14]: frame[f'lag_{lag}']=frame.cnt.shift(lag)
    frame['mean_7']=frame.cnt.shift(1).rolling(7).mean()
    frame['mean_28']=frame.cnt.shift(1).rolling(28).mean()
    frame['std_7']=frame.cnt.shift(1).rolling(7).std()
    frame['dow_sin']=np.sin(2*np.pi*dates.dt.dayofweek/7);frame['dow_cos']=np.cos(2*np.pi*dates.dt.dayofweek/7)
    frame['year_sin']=np.sin(2*np.pi*dates.dt.dayofyear/365.25);frame['year_cos']=np.cos(2*np.pi*dates.dt.dayofyear/365.25)
    frame['trend']=np.arange(len(frame))
    # No actual same-day weather, casual/registered counts, or target in features.
    return frame.dropna(subset=FEATURES).reset_index(drop=True)

def build(name):
    if name=='ridge': return make_pipeline(StandardScaler(),Ridge(alpha=100))
    if name=='gradient_boosting': return HistGradientBoostingRegressor(max_iter=160,max_leaf_nodes=12,l2_regularization=10,learning_rate=.05,random_state=42)
    raise ValueError(name)

def score(y,p):
    return {'mae':float(mean_absolute_error(y,p)),'rmse':float(np.sqrt(mean_squared_error(y,p))),'wape':float(np.abs(np.asarray(y)-p).sum()/np.asarray(y).sum())}

def conformal_radius(residuals,alpha=.1):
    residuals=np.sort(np.asarray(residuals))
    if not len(residuals): raise ValueError('Empty calibration sample')
    rank=min(len(residuals),int(np.ceil((len(residuals)+1)*(1-alpha))))
    return float(residuals[rank-1])

def main():
    source=fetch('https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip','bike.zip')
    with zipfile.ZipFile(source) as archive:
        filename=next(n for n in archive.namelist() if n.endswith('day.csv'))
        raw=pd.read_csv(io.BytesIO(archive.read(filename)))
    assert (raw.casual+raw.registered).equals(raw.cnt)
    frame=features(raw);x=frame[FEATURES];y=frame.cnt
    fold_rows=[]
    # Three 60-day validation windows entirely before calibration/test.
    for end in [280,340,400]:
        valid=slice(end,end+60)
        for name in ['seasonal_naive','ridge','gradient_boosting']:
            if name=='seasonal_naive': p=frame.lag_7.iloc[valid].to_numpy()
            else:
                model=build(name);model.fit(x.iloc[:end],y.iloc[:end]);p=np.maximum(0,model.predict(x.iloc[valid]))
            fold_rows.append({'model':name,'train_rows':end,'valid_start':frame.dteday.iloc[end],'valid_end':frame.dteday.iloc[end+59],**score(y.iloc[valid],p)})
    cv=pd.DataFrame(fold_rows)
    selected=cv.groupby('model').mae.mean().idxmin()
    train_end=460;cal_end=560
    if selected=='seasonal_naive':
        cal_pred=frame.lag_7.iloc[train_end:cal_end].to_numpy();pred=frame.lag_7.iloc[cal_end:].to_numpy()
    else:
        model=build(selected);model.fit(x.iloc[:train_end],y.iloc[:train_end])
        cal_pred=np.maximum(0,model.predict(x.iloc[train_end:cal_end]));pred=np.maximum(0,model.predict(x.iloc[cal_end:]))
    radius=conformal_radius(abs(y.iloc[train_end:cal_end].to_numpy()-cal_pred))
    truth=y.iloc[cal_end:].to_numpy();lower=np.maximum(0,pred-radius);upper=pred+radius
    baseline=frame.lag_7.iloc[cal_end:].to_numpy()
    metrics=score(truth,pred);base=score(truth,baseline)
    metrics.update({'interval_coverage':float(((truth>=lower)&(truth<=upper)).mean()),'mean_interval_width':float((upper-lower).mean()),'mae_improvement_vs_seasonal_naive':float(1-metrics['mae']/base['mae'])})
    predictions=pd.DataFrame({'date':frame.dteday.iloc[cal_end:],'actual':truth,'forecast':pred,'lower_90':lower,'upper_90':upper,'seasonal_naive':baseline})
    assert (predictions.lower_90<=predictions.forecast).all() and (predictions.forecast<=predictions.upper_90).all()
    export_sql_results(predictions, 'forecasts')
    scenarios=[]
    for shortage_cost in [1,2,4,8]:
        for label,capacity in [('point_forecast',pred),('upper_interval',upper),('seasonal_naive',baseline)]:
            under=np.maximum(truth-capacity,0);over=np.maximum(capacity-truth,0)
            scenarios.append({'shortage_unit_cost':shortage_cost,'surplus_unit_cost':1,'policy':label,'scenario_total_cost':float((under*shortage_cost+over).sum()),'shortfall_rentals':float(under.sum()),'surplus_rentals':float(over.sum())})
    policy=pd.DataFrame(scenarios)
    cv.to_csv(ROOT/'backtest_folds.csv',index=False);predictions.to_csv(ROOT/'test_predictions.csv',index=False);policy.to_csv(ROOT/'capacity_scenarios.csv',index=False)
    save_json('metrics.json',{'selected_model':selected,'test':metrics,'seasonal_naive_test':base,'calibration_radius':radius,'train_end':frame.dteday.iloc[train_end-1],'calibration_start':frame.dteday.iloc[train_end],'calibration_end':frame.dteday.iloc[cal_end-1],'test_start':frame.dteday.iloc[cal_end],'test_end':frame.dteday.iloc[-1],'source_sha256':manifest([source])})
    chart=go.Figure([go.Scatter(x=predictions.date,y=upper,line={'width':0},name='Upper 90%'),go.Scatter(x=predictions.date,y=lower,fill='tonexty',fillcolor='rgba(8,127,140,.15)',line={'width':0},name='Lower 90%'),go.Scatter(x=predictions.date,y=truth,name='Observed'),go.Scatter(x=predictions.date,y=pred,name='Forecast')]);chart.update_layout(title='Final holdout: rolling one-day-ahead forecasts',xaxis_title='Date',yaxis_title='Daily rental count')
    figs=[chart,px.bar(cv,x='train_rows',y='mae',color='model',barmode='group',title='Expanding-window model selection; MAE by fold'),px.line(policy,x='shortage_unit_cost',y='scenario_total_cost',color='policy',markers=True,title='Service capacity sensitivity: hypothetical unit costs'),px.scatter(predictions,x='forecast',y=truth-pred,title='Final holdout residuals',labels={'y':'Actual minus forecast'})]
    notes={'Decision':f"Validation selects {selected}. Final-holdout MAE is {metrics['mae']:.0f} rentals/day, versus {base['mae']:.0f} for seasonal naive. The reported nominal 90% interval covers {metrics['interval_coverage']:.1%} of holdout days. Compare these results before choosing a planning policy.",'Forecast contract':'Each forecast is for the next day, assuming the preceding day has fully closed. Lagged actual observations update each day, but model parameters remain fixed after the training window. This is not a multi-step forecast from one fixed origin. Calendar variables are known in advance; same-day actual weather is excluded.','Intervals':'Absolute residuals from a disjoint 100-day calibration window determine a finite-sample corrected radius. Serial dependence and distribution shift violate exchangeability, so 90% coverage is a target, not a guarantee. No retraining follows calibration.','Operations':'Capacity is an abstract daily rental-service budget. Rentals are flows, not a count of bikes required at a station. Cost ratios are hypothetical and exclude rebalancing, bike reuse and lost-demand censoring. Policies are compared on holdout data for reporting, not selected using it.','Limitations':'Only two historical years and a changing demand level. No station-level inventory, advance weather forecasts or real costs. Interval undercoverage or a weak model is retained in the report rather than hidden.'}
    report('Demand forecasting operations','Chronological model selection, calibration and an untouched final holdout.',{'Daily observations':f'{len(raw):,}','Selected model':selected,'Holdout MAE':f"{metrics['mae']:,.0f}",'90% interval coverage':f"{metrics['interval_coverage']:.1%}"},figs,notes)
    averages=cv.groupby('model').mae.mean()
    preview('Chronological validation: forecast error',averages.index,averages.values,'Mean absolute error (rentals/day)')
    (ROOT/'FINDINGS.md').write_text('# Results\n\n'+'\n\n'.join(f'## {k}\n\n{v}' for k,v in notes.items())+'\n')
    print(selected,metrics)

if __name__=='__main__': main()
