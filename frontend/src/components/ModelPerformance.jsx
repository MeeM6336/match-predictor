import React, { useState, useEffect } from 'react';
import './ModelPerformance.css';
import { fetchModelMetrics, fetchMatchPredictionStats } from '../assets/util/matches';


const ModelPerformance = () => {
  const [modelMetric, setModelMetric] = useState();
  const [upcomingMatchStats, setUpcomingMatchStats] = useState();
  const [calculatedMetrics, setCalculatedMetrics] = useState();

  useEffect(() => {
    const loadModelMetric = async () => {
      const metric = await fetchModelMetrics("logistic regression", "2025-04-14 09:23:00");
      setModelMetric(metric[0]);
    };

    loadModelMetric();
  }, []);

  useEffect (() => {
    const loadUpcomingMatchStats = async () => {
      const matchPredictionsStats = await fetchMatchPredictionStats();
      let t_neg = 0, t_pos = 0, f_neg = 0, f_pos = 0, totalMatches = 0;

      if(!matchPredictionsStats)
        return;

      matchPredictionsStats.forEach(match => {
        if (!((match.outcome == null) || (match.actual_outcome == null))) {
          totalMatches++;

          if (match.outcome == 1 && match.actual_outcome == 1) {
            t_pos++;
          }

          else if (match.outcome == 1 && match.actual_outcome == 0) {
            f_pos++;
          }

          else if (match.outcome == 0 && match.actual_outcome == 0) {
            t_neg++;
          }

          else if (match.outcome == 0 && match.actual_outcome == 1) {
            f_neg++;
          }
        }
      });

      setUpcomingMatchStats({t_neg, t_pos, f_neg, f_pos});
      console.log({t_neg, t_pos, f_neg, f_pos, totalMatches})
    }

    loadUpcomingMatchStats();
  }, []);

  useEffect(() => {
    if(!modelMetric)
      return;

    const accuracy = (modelMetric.t_pos + modelMetric.t_neg)/(modelMetric.t_pos + modelMetric.t_neg + modelMetric.f_neg + modelMetric.f_pos);
    const precision = (modelMetric.t_pos)/(modelMetric.t_pos + modelMetric.f_pos);
    const recall = (modelMetric.t_pos)/(modelMetric.t_pos + modelMetric.f_neg);
    const f1 = (2 * precision * recall)/(precision + recall); 

    setCalculatedMetrics([accuracy, precision, recall, f1, modelMetric.log_loss, modelMetric.roc_auc]);

  }, [modelMetric])

  const getMatrixCellStyle = (value) => {
    const maxVal = modelMetric['t_neg'] + modelMetric['t_pos'] + modelMetric['f_neg'] + modelMetric['f_pos'];
    
    const intensity = Math.round((value / maxVal) * 255);

    return {
      backgroundColor: `rgb(${intensity}, 0, ${255 - intensity})`,
      color: "white",
      padding: "1rem",
      paddingLeft: "3rem",
      paddingRight: "3rem"
    };
  };

  return (
    <div className='ModelPerformance'>
      <div className='performance-header'>
        <p>Model Performance</p>
      </div>
      {calculatedMetrics ? (
        <div className='performance-metrics-container'>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[0]).toFixed(4)}</p>
            <p className='performance-metric-name'>Accuracy</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[1]).toFixed(4)}</p>
            <p className='performance-metric-name'>Precision</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[2]).toFixed(4)}</p>
            <p className='performance-metric-name'>Recall</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[3]).toFixed(4)}</p>
            <p className='performance-metric-name'>F1-Score</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[4]).toFixed(4)}</p>
            <p className='performance-metric-name'>Log Loss</p>
          </div>
          <div className='performance-metric'>
            <p className='performance-metric-number'>{(calculatedMetrics[5]).toFixed(4)}</p>
            <p className='performance-metric-name'>ROC AUC</p>
          </div>
        </div>
      ) : (<div></div>)}
        <div className='performance-grid-container'>
          <div className='confusion-matrix-container'>
            <p>Training Data Confusion Matrix</p>
              <div className='confusion-matrix-table-container'>
                <table className='confusion-matrix-table'>
                  <thead>
                    <tr>
                      <th></th>
                      <th>0</th>
                      <th>1</th>
                    </tr>
                  </thead>
                  {upcomingMatchStats ? (
                    <tbody>
                      <tr>
                        <th>0</th>
                        <td style={getMatrixCellStyle(modelMetric.t_neg)}>{modelMetric.t_neg}</td>
                        <td style={getMatrixCellStyle(modelMetric.f_pos)}>{modelMetric.f_pos}</td>
                      </tr>
                      <tr>
                        <th>1</th>
                        <td style={getMatrixCellStyle(modelMetric.f_neg)}>{modelMetric.f_neg}</td>
                        <td style={getMatrixCellStyle(modelMetric.t_pos)}>{modelMetric.t_pos}</td>
                      </tr>
                    </tbody>
                    ) : (<tbody></tbody>)}
                </table>
              <div className='confusion-matrix-legend'></div>
          </div>
        </div>
        <div className='confusion-matrix-container'>
        <p>Live Data Confusion Matrix</p>
              <div className='confusion-matrix-table-container'>
                <table className='confusion-matrix-table'>
                  <thead>
                    <tr>
                      <th></th>
                      <th>0</th>
                      <th>1</th>
                    </tr>
                  </thead>
                  {upcomingMatchStats ? (
                    <tbody>
                      <tr>
                        <th>0</th>
                        <td style={getMatrixCellStyle(upcomingMatchStats.t_neg)}>{upcomingMatchStats.t_neg}</td>
                        <td style={getMatrixCellStyle(upcomingMatchStats.f_pos)}>{upcomingMatchStats.f_pos}</td>
                      </tr>
                      <tr>
                        <th>1</th>
                        <td style={getMatrixCellStyle(upcomingMatchStats.f_neg)}>{upcomingMatchStats.f_neg}</td>
                        <td style={getMatrixCellStyle(upcomingMatchStats.t_pos)}>{upcomingMatchStats.t_pos}</td>
                      </tr>
                    </tbody>
                    ) : (<tbody></tbody>)}
                </table>
              <div className='confusion-matrix-legend'></div>
          </div>
        </div>
        <div className='accuracy-history-container'>
          
        </div>
      </div>
    </div>
  );
};

export default ModelPerformance